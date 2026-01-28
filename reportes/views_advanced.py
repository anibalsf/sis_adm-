# Nuevos Reportes - Backend Views

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from tesoreria.models import Pago, Egreso
from hojasruta.models import HojaRuta
from afiliados.models import Afiliado
from vehiculos.models import Vehiculo
from rutas.models import Ruta
from reservas.models import Reserva


class RentabilidadRutasView(APIView):
    """
    Reporte de rentabilidad por ruta
    Calcula ingresos vs costos operativos por cada ruta
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Parámetros de fecha
        meses = int(request.GET.get('meses', 3))
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=meses * 30)
        
        rutas = Ruta.objects.all()
        resultados = []
        
        for ruta in rutas:
            # Ingresos de la ruta (pasajes)
            hojas = HojaRuta.objects.filter(
                ruta=ruta,
                fecha_emision__gte=fecha_inicio,
                fecha_emision__lte=fecha_fin
            )
            
            total_viajes = hojas.count()
            if total_viajes == 0:
                continue
            
            # Calcular ingresos totales (reservas pagadas)
            ingresos = Reserva.objects.filter(
                hoja_ruta__in=hojas,
                estado='confirmada'
            ).aggregate(total=Sum('monto_pagado'))['total'] or 0
            
            # Calcular costos operativos estimados
            # (combustible, mantenimiento, etc. - simplificado)
            costo_por_viaje = ruta.tarifa_base * Decimal('0.3')  # 30% de la tarifa como costo
            costos_totales = costo_por_viaje * total_viajes
            
            # Calcular rentabilidad
            utilidad = float(ingresos) - float(costos_totales)
            margen = (utilidad / float(ingresos) * 100) if ingresos > 0 else 0
            
            # Ocupación promedio
            total_asientos = hojas.aggregate(
                total=Sum('vehiculo__capacidad')
            )['total'] or 0
            
            asientos_ocupados = Reserva.objects.filter(
                hoja_ruta__in=hojas
            ).count()
            
            ocupacion = (asientos_ocupados / total_asientos * 100) if total_asientos > 0 else 0
            
            resultados.append({
                'ruta_id': ruta.id,
                'ruta_nombre': f"{ruta.origen} - {ruta.destino}",
                'total_viajes': total_viajes,
                'ingresos_totales': float(ingresos),
                'costos_estimados': float(costos_totales),
                'utilidad': utilidad,
                'margen_porcentaje': round(margen, 2),
                'ocupacion_promedio': round(ocupacion, 2),
                'ingreso_por_viaje': float(ingresos / total_viajes) if total_viajes > 0 else 0
            })
        
        # Ordenar por rentabilidad
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
        )['total'] or 0
        
        reservas_mes = Reserva.objects.filter(
            hoja_ruta__in=hojas_mes
        ).count()
        
        tasa_ocupacion = (reservas_mes / total_asientos * 100) if total_asientos > 0 else 0
        
        # 2. Ingresos por vehículo
        vehiculos_activos = Vehiculo.objects.filter(estado='activo').count()
        ingresos_mes = Pago.objects.filter(
            fecha_pago__gte=inicio_mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        ingreso_por_vehiculo = (ingresos_mes / vehiculos_activos) if vehiculos_activos > 0 else 0
        
        # 3. Ratio ingresos/egresos
        egresos_mes = Egreso.objects.filter(
            fecha__gte=inicio_mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        ratio_ie = (ingresos_mes / egresos_mes) if egresos_mes > 0 else 0
        
        # 4. Crecimiento mensual
        ingresos_mes_anterior = Pago.objects.filter(
            fecha_pago__gte=mes_anterior,
            fecha_pago__lt=inicio_mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        crecimiento = 0
        if ingresos_mes_anterior > 0:
            crecimiento = ((ingresos_mes - ingresos_mes_anterior) / ingresos_mes_anterior * 100)
        
        # 5. Afiliados morosos (%)
        total_afiliados = Afiliado.objects.count()
        afiliados_morosos = Afiliado.objects.filter(
            saldo_deuda__gt=0
        ).count()
        
        porcentaje_morosos = (afiliados_morosos / total_afiliados * 100) if total_afiliados > 0 else 0
        
        # 6. Eficiencia operativa (viajes completados vs programados)
        viajes_programados = HojaRuta.objects.filter(
            fecha_emision__gte=inicio_mes
        ).count()
        
        viajes_completados = HojaRuta.objects.filter(
            fecha_emision__gte=inicio_mes,
            estado='completada'
        ).count()
        
        eficiencia = (viajes_completados / viajes_programados * 100) if viajes_programados > 0 else 0
        
        return Response({
            'periodo': str(inicio_mes)[:7],
            'kpis': {
                'tasa_ocupacion': {
                    'valor': round(tasa_ocupacion, 2),
                    'unidad': '%',
                    'descripcion': 'Ocupación promedio de vehículos',
                    'objetivo': 75,
                    'estado': 'bueno' if tasa_ocupacion >= 75 else 'regular' if tasa_ocupacion >= 50 else 'malo'
                },
                'ingreso_por_vehiculo': {
                    'valor': round(float(ingreso_por_vehiculo), 2),
                    'unidad': 'Bs',
                    'descripcion': 'Ingreso promedio por vehículo',
                    'objetivo': 5000
                },
                'ratio_ingresos_egresos': {
                    'valor': round(float(ratio_ie), 2),
                    'unidad': 'x',
                    'descripcion': 'Relación ingresos/egresos',
                    'objetivo': 1.5,
                    'estado': 'bueno' if ratio_ie >= 1.5 else 'regular' if ratio_ie >= 1.0 else 'malo'
                },
                'crecimiento_mensual': {
                    'valor': round(float(crecimiento), 2),
                    'unidad': '%',
                    'descripcion': 'Crecimiento vs mes anterior',
                    'objetivo': 5
                },
                'afiliados_morosos': {
                    'valor': round(porcentaje_morosos, 2),
                    'unidad': '%',
                    'descripcion': 'Porcentaje de afiliados con deuda',
                    'objetivo': 10,
                    'estado': 'bueno' if porcentaje_morosos <= 10 else 'regular' if porcentaje_morosos <= 20 else 'malo'
                },
                'eficiencia_operativa': {
                    'valor': round(eficiencia, 2),
                    'unidad': '%',
                    'descripcion': 'Viajes completados vs programados',
                    'objetivo': 95,
                    'estado': 'bueno' if eficiencia >= 95 else 'regular' if eficiencia >= 85 else 'malo'
                }
            },
            'resumen_financiero': {
                'ingresos_mes': float(ingresos_mes),
                'egresos_mes': float(egresos_mes),
                'saldo_mes': float(ingresos_mes - egresos_mes)
            }
        })


class TendenciasMensualesView(APIView):
    """
    Análisis de tendencias mensuales
    Datos históricos de los últimos 12 meses
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        meses = int(request.GET.get('meses', 12))
        hoy = timezone.now().date()
        
        resultados = []
        
        for i in range(meses - 1, -1, -1):
            fecha_fin = hoy.replace(day=1) - timedelta(days=i * 30)
            fecha_inicio = (fecha_fin - timedelta(days=30)).replace(day=1)
            
            # Ingresos del mes
            ingresos = Pago.objects.filter(
                fecha_pago__gte=fecha_inicio,
                fecha_pago__lt=fecha_fin
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # Egresos del mes
            egresos = Egreso.objects.filter(
                fecha__gte=fecha_inicio,
                fecha__lt=fecha_fin
            ).aggregate(total=Sum('monto'))['total'] or 0
            
            # Viajes del mes
            viajes = HojaRuta.objects.filter(
                fecha_emision__gte=fecha_inicio,
                fecha_emision__lt=fecha_fin
            ).count()
            
            # Nuevos afiliados
            nuevos_afiliados = Afiliado.objects.filter(
                fecha_ingreso__gte=fecha_inicio,
                fecha_ingreso__lt=fecha_fin
            ).count() if hasattr(Afiliado, 'fecha_ingreso') else 0
            
            resultados.append({
                'mes': fecha_inicio.strftime('%Y-%m'),
                'mes_nombre': fecha_inicio.strftime('%B %Y'),
                'ingresos': float(ingresos),
                'egresos': float(egresos),
                'saldo': float(ingresos - egresos),
                'viajes': viajes,
                'nuevos_afiliados': nuevos_afiliados
            })
        
        # Calcular proyección simple (promedio últimos 3 meses)
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
        
        return Response({
            'periodo': f'Últimos {meses} meses',
            'tendencias': resultados,
            'proyeccion_proximo_mes': proyeccion,
            'estadisticas': {
                'ingreso_promedio': round(sum(r['ingresos'] for r in resultados) / len(resultados), 2) if resultados else 0,
                'egreso_promedio': round(sum(r['egresos'] for r in resultados) / len(resultados), 2) if resultados else 0,
                'mejor_mes': max(resultados, key=lambda x: x['ingresos'])['mes'] if resultados else None,
                'peor_mes': min(resultados, key=lambda x: x['ingresos'])['mes'] if resultados else None
            }
        })
