# Nuevos Reportes - Backend Views

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from tesoreria.models import Pago, Egreso
from reportes.query_helpers import INGRESO_ESTADOS_VALIDOS, EGRESO_ESTADOS_VALIDOS
from hojasruta.models import HojaRuta
from afiliados.models import Afiliado
from vehiculos.models import Vehiculo
from rutas.models import Ruta
from reservas.models import Reserva

# Porcentaje estimado de costo operativo sobre la tarifa base, usado como fallback
# cuando la ruta no tiene un costo real configurado.
COSTO_ESTIMADO_PORCENTAJE = 0.30

# Nombres de mes en español: strftime('%B') depende del locale del sistema
# y devolvía nombres en inglés en servidores no configurados.
MESES_ES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

# Umbrales por defecto de los KPIs (orden: valor, direccion, objetivo)
# direccion 'min' = menor es mejor, 'max' = mayor es mejor
KPI_CONFIG = {
    'tasa_ocupacion': {'objetivo': 75, 'direccion': 'min'},
    'ingreso_por_vehiculo': {'objetivo': 5000, 'direccion': 'min'},
    'ratio_ingresos_egresos': {'objetivo': 1.5, 'direccion': 'min'},
    'crecimiento_mensual': {'objetivo': 5, 'direccion': 'min'},
    'afiliados_morosos': {'objetivo': 10, 'direccion': 'max'},
    'eficiencia_operativa': {'objetivo': 95, 'direccion': 'min'},
}


def _estado_kpi(valor, objetivo, direccion, tolerancia_pct=0.0):
    """Clasifica un KPI como bueno/regular/malo según objetivo y dirección."""
    if objetivo in (None, 0):
        return 'regular'
    if direccion == 'max':
        if valor <= objetivo:
            return 'bueno'
        if valor <= objetivo * (1 + tolerancia_pct):
            return 'regular'
        return 'malo'
    if valor >= objetivo:
        return 'bueno'
    if valor >= objetivo * (1 - tolerancia_pct):
        return 'regular'
    return 'malo'


def _kpi(valor, unidad, descripcion, clave_config, formato=None):
    """Construye el dict de un KPI con objetivo y estado consistentes."""
    cfg = KPI_CONFIG.get(clave_config, {})
    objetivo = cfg.get('objetivo')
    direccion = cfg.get('direccion', 'min')
    valor = round(float(valor or 0), 2)
    if formato:
        valor = formato(valor)
    return {
        'valor': valor,
        'unidad': unidad,
        'descripcion': descripcion,
        'objetivo': objetivo,
        'estado': _estado_kpi(valor, objetivo, direccion, tolerancia_pct=0.10),
    }


class RentabilidadRutasView(APIView):
    """
    Reporte de rentabilidad por ruta
    Calcula ingresos vs costos operativos por cada ruta
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            meses = int(request.GET.get('meses', 3))
        except (TypeError, ValueError):
            meses = 3
        meses = max(1, min(meses, 36))
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - relativedelta(months=meses)
        
        rutas = Ruta.objects.all()
        resultados = []
        
        for ruta in rutas:
            hojas = HojaRuta.objects.filter(
                ruta=ruta,
                fecha_emision__gte=fecha_inicio,
                fecha_emision__lte=fecha_fin
            )
            
            total_viajes = hojas.count()
            if total_viajes == 0:
                continue
            
            # Ingresos acumulados de hojas de ruta o reservas por pasaje
            ingresos_hojas = float(hojas.aggregate(total=Sum('precio'))['total'] or 0)
            reservas_asientos = Reserva.objects.filter(
                ruta=ruta,
                fecha_viaje__gte=fecha_inicio,
                fecha_viaje__lte=fecha_fin
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            ingresos_reservas = float(reservas_asientos) * float(ruta.tarifa_base or 0)
            
            # Las hojas de ruta y las reservas son fuentes distintas de ingreso:
            # se suman (antes setomaba el máximo, subestimando rutas con ambos canales).
            ingresos = ingresos_hojas + ingresos_reservas
            
            # Costos operativos estimados como % de la tarifa.
            # TODO(costos): sustituir por costo real por ruta cuando exista tabla de costos.
            costo_por_viaje_estimado = float(ruta.tarifa_base or 0) * COSTO_ESTIMADO_PORCENTAJE
            costos_totales = costo_por_viaje_estimado * total_viajes
            
            utilidad = float(ingresos) - float(costos_totales)
            margen = (utilidad / float(ingresos) * 100) if ingresos > 0 else 0
            
            # Ocupación promedio
            total_asientos = hojas.aggregate(
                total=Sum('vehiculo__capacidad')
            )['total'] or (total_viajes * 15)
            
            asientos_ocupados = Reserva.objects.filter(
                ruta=ruta,
                fecha_viaje__gte=fecha_inicio,
                fecha_viaje__lte=fecha_fin
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            ocupacion = (asientos_ocupados / total_asientos * 100) if total_asientos > 0 else 0
            
            resultados.append({
                'ruta_id': ruta.id,
                'ruta_nombre': f"{ruta.origen} - {ruta.destino}",
                'total_viajes': total_viajes,
                'ingresos_totales': float(ingresos),
                'costos_estimados': float(costos_totales),
                'utilidad': float(utilidad),
                'margen_porcentaje': round(margen, 2),
                'ocupacion_promedio': round(ocupacion, 2),
                'ingreso_por_viaje': float(ingresos / total_viajes) if total_viajes > 0 else 0
            })
        
        resultados.sort(key=lambda x: x['utilidad'], reverse=True)
        
        return Response({
            'periodo': f'{fecha_inicio} a {fecha_fin}',
            'rutas': resultados,
            'resumen': {
                'total_rutas': len(resultados),
                'ingresos_totales': sum(r['ingresos_totales'] for r in resultados),
                'utilidad_total': sum(r['utilidad'] for r in resultados)
            }
        })


class KPIsEjecutivosView(APIView):
    """
    Dashboard de KPIs ejecutivos
    Métricas clave para la toma de decisiones
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
        
        # 1. Tasa de ocupación promedio
        hojas_mes = HojaRuta.objects.filter(fecha_emision__gte=inicio_mes)
        total_asientos = hojas_mes.aggregate(
            total=Sum('vehiculo__capacidad')
        )['total'] or (hojas_mes.count() * 15)
        
        reservas_mes = Reserva.objects.filter(
            fecha_viaje__gte=inicio_mes
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        tasa_ocupacion = (reservas_mes / total_asientos * 100) if total_asientos > 0 else 0
        
        # 2. Ingresos por vehículo
        vehiculos_activos = Vehiculo.objects.filter(estado='activo').count()
        ingresos_mes = Pago.objects.filter(
            fecha_pago__gte=inicio_mes,
            estado__in=INGRESO_ESTADOS_VALIDOS
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        ingreso_por_vehiculo = (float(ingresos_mes) / vehiculos_activos) if vehiculos_activos > 0 else 0
        
        # 3. Ratio ingresos/egresos
        egresos_mes = Egreso.objects.filter(
            fecha__gte=inicio_mes,
            estado__in=EGRESO_ESTADOS_VALIDOS
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        ratio_ie = (float(ingresos_mes) / float(egresos_mes)) if egresos_mes > 0 else (float(ingresos_mes) if ingresos_mes > 0 else 1.0)
        
        # 4. Crecimiento mensual
        ingresos_mes_anterior = Pago.objects.filter(
            fecha_pago__gte=mes_anterior,
            fecha_pago__lt=inicio_mes,
            estado__in=INGRESO_ESTADOS_VALIDOS
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        crecimiento = 0
        if ingresos_mes_anterior > 0:
            crecimiento = ((float(ingresos_mes) - float(ingresos_mes_anterior)) / float(ingresos_mes_anterior) * 100)
        
        # 5. Afiliados con deuda real (cuotas + sanciones pendientes).
        # Antes se usaba estado='pasivo' como aproximación, lo que reportaba
        # como morosos a afiliados sin deuda y omitía a los que sí la tienen.
        from cuotas.models import Cuota
        from sanciones.models import Sancion

        afiliados_activos = Afiliado.objects.filter(estado='activo', is_active=True)
        total_afiliados = afiliados_activos.count()

        ids_con_cuota_pendiente = set(
            Cuota.objects.filter(estado='pendiente', afiliado__in=afiliados_activos)
            .values_list('afiliado_id', flat=True)
        )
        ids_con_sancion_pendiente = set(
            Sancion.objects.filter(estado='pendiente', afiliado__in=afiliados_activos)
            .values_list('afiliado_id', flat=True)
        )
        afiliados_morosos = len(ids_con_cuota_pendiente | ids_con_sancion_pendiente)
        porcentaje_morosos = (afiliados_morosos / total_afiliados * 100) if total_afiliados > 0 else 0

        # 6. Eficiencia operativa (viajes no anulados vs emitidos)
        viajes_programados = hojas_mes.count()
        viajes_completados = hojas_mes.exclude(estado='anulada').count()

        eficiencia = (viajes_completados / viajes_programados * 100) if viajes_programados > 0 else 100.0

        return Response({
            'periodo': str(inicio_mes)[:7],
            'kpis': {
                'tasa_ocupacion': _kpi(
                    tasa_ocupacion, '%',
                    'Ocupación promedio de vehículos', 'tasa_ocupacion'
                ),
                'ingreso_por_vehiculo': _kpi(
                    ingreso_por_vehiculo, 'Bs',
                    'Ingreso promedio por vehículo', 'ingreso_por_vehiculo'
                ),
                'ratio_ingresos_egresos': _kpi(
                    ratio_ie, 'x',
                    'Relación ingresos/egresos', 'ratio_ingresos_egresos'
                ),
                'crecimiento_mensual': _kpi(
                    crecimiento, '%',
                    'Crecimiento vs mes anterior', 'crecimiento_mensual'
                ),
                'afiliados_morosos': _kpi(
                    porcentaje_morosos, '%',
                    'Afiliados activos con deuda pendiente', 'afiliados_morosos'
                ),
                'eficiencia_operativa': _kpi(
                    eficiencia, '%',
                    'Viajes vigentes vs emitidos', 'eficiencia_operativa'
                )
            },
            'resumen_financiero': {
                'ingresos_mes': float(ingresos_mes),
                'egresos_mes': float(egresos_mes),
                'saldo_mes': float(ingresos_mes - egresos_mes)
            },
            'detalle_deuda': {
                'afiliados_activos': total_afiliados,
                'afiliados_con_cuota_pendiente': len(ids_con_cuota_pendiente),
                'afiliados_con_sancion_pendiente': len(ids_con_sancion_pendiente),
                'afiliados_con_cualquier_deuda': afiliados_morosos,
            }
        })


class TendenciasMensualesView(APIView):
    """
    Análisis de tendencias mensuales
    Datos históricos de los últimos 12 meses
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            meses = int(request.GET.get('meses', 12))
        except (TypeError, ValueError):
            meses = 12
        meses = max(1, min(meses, 36))
        hoy = timezone.now().date()
        
        # Ventana de meses calendario completa (evita el drift de timedelta(days=30))
        primer_mes = (hoy.replace(day=1) - relativedelta(months=meses - 1))
        rango_inicio = primer_mes.replace(day=1)
        rango_fin = hoy.replace(day=1) + relativedelta(months=1)

        # Agregación en base de datos: una consulta por modelo en vez de 4 x N
        pagos_mes = (Pago.objects
                     .filter(fecha_pago__gte=rango_inicio, fecha_pago__lt=rango_fin,
                             estado__in=INGRESO_ESTADOS_VALIDOS)
                     .annotate(mes=TruncMonth('fecha_pago'))
                     .values('mes')
                     .annotate(total=Sum('monto'))
                     .order_by('mes'))
        ingresos_por_mes = {row['mes']: row['total'] or 0 for row in pagos_mes}

        egresos_por_mes = {
            row['mes']: row['total'] or 0
            for row in (Egreso.objects
                        .filter(fecha__gte=rango_inicio, fecha__lt=rango_fin,
                                estado__in=EGRESO_ESTADOS_VALIDOS)
                        .annotate(mes=TruncMonth('fecha'))
                        .values('mes')
                        .annotate(total=Sum('monto'))
                        .order_by('mes'))
        }

        viajes_por_mes = {
            row['mes']: row['total']
            for row in (HojaRuta.objects
                        .filter(fecha_emision__gte=rango_inicio, fecha_emision__lt=rango_fin)
                        .annotate(mes=TruncMonth('fecha_emision'))
                        .values('mes')
                        .annotate(total=Count('id'))
                        .order_by('mes'))
        }

        nuevos_por_mes = {
            row['mes']: row['total']
            for row in (Afiliado.objects
                        .filter(fecha_ingreso__gte=rango_inicio, fecha_ingreso__lt=rango_fin)
                        .annotate(mes=TruncMonth('fecha_ingreso'))
                        .values('mes')
                        .annotate(total=Count('id'))
                        .order_by('mes'))
        }

        resultados = []
        for i in range(meses - 1, -1, -1):
            fecha_inicio = (hoy.replace(day=1) - relativedelta(months=i)).replace(day=1)
            clave = fecha_inicio

            ingresos = ingresos_por_mes.get(clave, 0)
            egresos = egresos_por_mes.get(clave, 0)

            resultados.append({
                'mes': fecha_inicio.strftime('%Y-%m'),
                'mes_nombre': f'{MESES_ES[fecha_inicio.month - 1]} {fecha_inicio.year}',
                'ingresos': float(ingresos),
                'egresos': float(egresos),
                'saldo': float(ingresos - egresos),
                'viajes': viajes_por_mes.get(clave, 0),
                'nuevos_afiliados': nuevos_por_mes.get(clave, 0)
            })
        
        if len(resultados) >= 3:
            ultimos_3 = resultados[-3:]
            promedio_ingresos = sum(r['ingresos'] for r in ultimos_3) / 3
            promedio_egresos = sum(r['egresos'] for r in ultimos_3) / 3
            
            proyeccion = {
                'mes': 'Proyección',
                'ingresos_proyectados': round(promedio_ingresos, 2),
                'egresos_proyectados': round(promedio_egresos, 2),
                'saldo_proyectado': round(promedio_ingresos - promedio_egresos, 2)
            }
        else:
            proyeccion = None
        
        ingreso_promedio = round(sum(r['ingresos'] for r in resultados) / len(resultados), 2) if resultados else 0
        egreso_promedio = round(sum(r['egresos'] for r in resultados) / len(resultados), 2) if resultados else 0
        mejor_mes = max(resultados, key=lambda x: x['ingresos'])['mes'] if resultados else 'N/A'
        peor_mes = min(resultados, key=lambda x: x['ingresos'])['mes'] if resultados else 'N/A'

        return Response({
            'periodo': f'Últimos {meses} meses',
            'tendencias': resultados,
            'proyeccion_proximo_mes': proyeccion,
            'estadisticas': {
                'ingreso_promedio': ingreso_promedio,
                'egreso_promedio': egreso_promedio,
                'mejor_mes': mejor_mes,
                'peor_mes': peor_mes
            }
        })
