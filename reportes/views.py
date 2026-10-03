from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.http import HttpResponse, FileResponse
import io
import csv
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER


def _get_decimal_param(request, name):
    value = request.GET.get(name)
    if value in [None, '']:
        return None
    try:
        from decimal import Decimal
        value = Decimal(str(value))
    except Exception:
        return None
    return value if value >= 0 else None


def _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio=None, fecha_fin=None, estados=None):
    pagos = Pago.objects.filter(tipo_pago=tipo_pago).select_related('afiliado', 'tipo_pago')
    if estados:
        pagos = pagos.filter(estado__in=estados)
    if fecha_inicio:
        pagos = pagos.filter(fecha_pago__gte=fecha_inicio)
    if fecha_fin:
        pagos = pagos.filter(fecha_pago__lte=fecha_fin)
    return pagos


def _es_reporte_egresos(request):
    """El reporte por categoría también cubre egresos cuando ?tipo=egreso."""
    return request.GET.get('tipo') == 'egreso'


# Tope de afiliados pendientes que se envían al frontend; evita respuestas
# enormes cuando "todas las categorías" cruza muchas categorías con socios.
LIMITE_PENDIENTES = 500


def _pendientes_por_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin,
                              monto_esperado, afiliados_activos, limite=LIMITE_PENDIENTES):
    """Calcula qué afiliados activos todavía deben cancelar una categoría.

    Sin ``monto_esperado`` solo se reportan los que no registraron ningún pago
    completado. Con monto esperado se reportan también los pagos parciales,
    calculando la deuda como la diferencia entre lo esperado y lo pagado.

    ``limite`` recorta la lista devuelta (el JSON la acota para no saturar al
    navegador); las exportaciones pasan ``None`` para obtenerla completa.

    Devuelve un dict con la lista de pendientes, el conteo real, el total
    adeudado y el desglose entre pagos parciales y pendientes totales.
    """
    monto_esperado = float(monto_esperado) if monto_esperado is not None else None

    pagos_completados = _filtrar_pagos_categoria(
        Pago, tipo_pago, fecha_inicio, fecha_fin, ['completado']
    )
    pagado_por_afiliado = {
        fila['afiliado_id']: float(fila['total'] or 0)
        for fila in pagos_completados
        .values('afiliado_id')
        .annotate(total=Sum('monto'))
        if fila['afiliado_id']
    }

    pendientes = []
    count_pendientes = 0
    count_parciales = 0
    count_sin_pago = 0
    monto_total_pendiente = 0.0

    for afiliado in afiliados_activos:
        pagado = pagado_por_afiliado.get(afiliado.id, 0.0)

        if monto_esperado is not None:
            if pagado >= monto_esperado:
                continue
            deuda = round(monto_esperado - pagado, 2)
            if pagado > 0:
                count_parciales += 1
            else:
                count_sin_pago += 1
        else:
            if pagado > 0:
                continue
            deuda = None
            count_sin_pago += 1

        count_pendientes += 1
        monto_total_pendiente += deuda or 0.0
        pendientes.append({
            'afiliado_id': afiliado.id,
            'nombre': afiliado.nombre_completo,
            'ci': afiliado.ci,
            'telefono': afiliado.telefono,
            'deuda': deuda,
            'pagado': round(pagado, 2),
        })

    pendientes.sort(key=lambda fila: fila['nombre'])
    recortada = pendientes[:limite] if limite else pendientes

    return {
        'pendientes': recortada,
        'pendientes_truncados': len(recortada) < len(pendientes),
        'count_pendientes': count_pendientes,
        'count_parciales': count_parciales,
        'count_sin_pago': count_sin_pago,
        'monto_total_pendiente': round(monto_total_pendiente, 2) if monto_esperado is not None else None,
    }


def _duplicados_por_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin):
    """Detecta posibles pagos duplicados: mismo afiliado con más de un pago
    completado en la categoría y el período seleccionados.

    Devuelve el detalle con los pagos individuales para que el frontend pueda
    mostrar qué registros hay que revisar.
    """
    pagos_completados = _filtrar_pagos_categoria(
        Pago, tipo_pago, fecha_inicio, fecha_fin, ['completado']
    )

    conteo = {
        fila['afiliado_id']: fila['cantidad']
        for fila in pagos_completados.values('afiliado_id')
        .annotate(cantidad=Count('id'))
        .filter(cantidad__gt=1)
        if fila['afiliado_id']
    }
    if not conteo:
        return []

    pagos_por_afiliado = {}
    for pago in pagos_completados.filter(afiliado_id__in=conteo).order_by('fecha_pago'):
        pagos_por_afiliado.setdefault(pago.afiliado_id, []).append(pago)

    duplicados = []
    for afiliado_id, cantidad in conteo.items():
        pagos = pagos_por_afiliado.get(afiliado_id, [])
        afiliado = pagos[0].afiliado if pagos else None
        total_pagado = float(sum((p.monto for p in pagos), 0))
        duplicados.append({
            'afiliado_id': afiliado_id,
            'nombre': afiliado.nombre_completo if afiliado else 'N/A',
            'ci': afiliado.ci if afiliado else '',
            'telefono': getattr(afiliado, 'telefono', '') if afiliado else '',
            'cantidad_pagos': cantidad,
            'total_pagado': round(total_pagado, 2),
            'pagos': [
                {
                    'id': p.id,
                    'fecha_pago': str(p.fecha_pago),
                    'monto': float(p.monto),
                    'nro_recibo': p.nro_recibo,
                    'metodo_pago': p.get_metodo_pago_display() if hasattr(p, 'get_metodo_pago_display') else (p.metodo_pago or ''),
                }
                for p in pagos
            ],
        })

    duplicados.sort(key=lambda fila: -fila['total_pagado'])
    return duplicados


def _resumen_categoria(Pago, tipo_pago, total_activos, fecha_inicio=None, fecha_fin=None, monto_esperado=None):
    pagos_completados = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['completado'])
    pagos_pendientes = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['pendiente'])
    pagos_no_validos = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['anulado', 'cancelado'])

    afiliados_pagaron_ids = set(pagos_completados.values_list('afiliado_id', flat=True))
    afiliados_pagaron_ids.discard(None)
    total_recaudado = pagos_completados.aggregate(total=Sum('monto'))['total'] or 0
    total_pendiente_revision = pagos_pendientes.aggregate(total=Sum('monto'))['total'] or 0
    total_no_valido = pagos_no_validos.aggregate(total=Sum('monto'))['total'] or 0

    duplicados = pagos_completados.values('afiliado_id').annotate(cantidad=Count('id')).filter(cantidad__gt=1)
    count_pagaron = len(afiliados_pagaron_ids)
    count_pendientes = max(total_activos - count_pagaron, 0)
    total_esperado = monto_esperado * total_activos if monto_esperado is not None else None
    monto_faltante = max(total_esperado - total_recaudado, 0) if total_esperado is not None else None

    return {
        'categoria': {
            'id': tipo_pago.id,
            'nombre': tipo_pago.nombre,
        },
        'total_recaudado': float(total_recaudado),
        'monto_esperado_por_afiliado': float(monto_esperado) if monto_esperado is not None else None,
        'total_esperado': float(total_esperado) if total_esperado is not None else None,
        'monto_faltante': float(monto_faltante) if monto_faltante is not None else None,
        'total_afiliados_activos': total_activos,
        'count_pagaron': count_pagaron,
        'count_pendientes': count_pendientes,
        'count_pagos_completados': pagos_completados.count(),
        'count_pagos_pendientes_revision': pagos_pendientes.count(),
        'total_pagos_pendientes_revision': float(total_pendiente_revision),
        'count_pagos_anulados_cancelados': pagos_no_validos.count(),
        'total_pagos_anulados_cancelados': float(total_no_valido),
        'count_afiliados_con_pago_duplicado': duplicados.count(),
        'porcentaje_cobertura': round((count_pagaron / total_activos * 100), 1) if total_activos > 0 else 0,
    }


class AfiliadosMorososView(APIView):
    """
    Reporte de afiliados con pagos pendientes.
    URL: GET /api/reportes/afiliados-morosos/?meses=3
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from dateutil.relativedelta import relativedelta

        from reportes_auto.morosidad import (
            CAMPOS_MOROSO, _deuda_queryset, nivel_morosidad, serializar_filas,
        )

        try:
            meses_atras = max(1, min(int(request.GET.get('meses', 3)), 36))
        except (TypeError, ValueError):
            meses_atras = 3
        fecha_limite = datetime.now().date() - relativedelta(months=meses_atras)

        try:
            page = max(1, int(request.GET.get('page', 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = max(1, min(int(request.GET.get('page_size', 20)), 200))
        except (TypeError, ValueError):
            page_size = 20

        # La deuda se agrega en SQL (subqueries) en vez de una consulta por
        # afiliado, y el nivel se clasifica con la misma regla que usan el
        # KPI de morosos y la alerta semanal.
        morosos_qs = _deuda_queryset(periodo_limite=fecha_limite).order_by('-deuda_total')

        hoy = datetime.now().date()
        total_items = morosos_qs.count()
        deuda_total = morosos_qs.aggregate(total=Sum('deuda_total'))['total'] or 0

        # Solo se trae la página pedida a memoria.
        filas = morosos_qs.values(*CAMPOS_MOROSO)[(page - 1) * page_size: page * page_size]
        morosos = list(serializar_filas(filas, hoy))

        # El resumen por nivel se cuenta sobre toda la lista, no solo la página,
        # para que los badges reflejen el total real.
        niveles = {'critico': 0, 'alto': 0, 'moderado': 0, 'bajo': 0}
        for ultimo in morosos_qs.values_list('ultimo_pago', flat=True):
            dias = (hoy - ultimo).days if ultimo else None
            clave = nivel_morosidad(dias).lower()
            if clave in niveles:
                niveles[clave] += 1

        return Response({
            'count': total_items,
            'total_pages': (total_items + page_size - 1) // page_size,
            'current_page': page,
            'page_size': page_size,
            'deuda_total_sistema': float(deuda_total),
            'meses_analizados': meses_atras,
            'morosos': morosos,
            'resumen_por_nivel': niveles,
        })


class AfiliadosMorososPDFView(APIView):
    """
    Genera PDF de afiliados morosos.
    URL: GET /api/reportes/afiliados-morosos/pdf/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import io
        from django.http import HttpResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle
        from afiliados.models import Afiliado
        from tesoreria.models import Pago
        
        # Logica similar a AfiliadosMorososView para obtener datos
        afiliados = Afiliado.objects.filter(estado='activo', is_active=True)
        morosos = []
        for afiliado in afiliados:
            try:
                deuda_cuotas = afiliado.cuotas.filter(estado='pendiente').aggregate(total=Sum('monto'))['total'] or 0
                deuda_sanciones = afiliado.sanciones.filter(estado='pendiente').aggregate(total=Sum('monto'))['total'] or 0
                deuda_total = deuda_cuotas + deuda_sanciones
                cantidad_faltas = afiliado.asistencias.filter(estado='falta').count()
                
                if deuda_total > 0 or cantidad_faltas > 0: # Incluir si tiene deudas O faltas
                    morosos.append({
                        'nombre': afiliado.nombre_completo,
                        'ci': afiliado.ci,
                        'cuotas': deuda_cuotas,
                        'sanciones': deuda_sanciones,
                        'total': deuda_total,
                        'faltas': cantidad_faltas
                    })
            except Exception as e:
                pass
                
        morosos.sort(key=lambda x: x['total'], reverse=True)
        
        # Generar PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)
        
        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height - 50, "REPORTE DE ESTADO DE CUENTAS POR AFILIADO")
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, height - 70, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Tabla
        data = [['AFILIADO', 'CARNET', 'FALTAS', 'DEUDA CUOTAS', 'DEUDA MULTAS', 'TOTAL DEUDA']]
        for m in morosos:
            data.append([
                m['nombre'],
                m['ci'],
                str(m['faltas']),
                f"{m['cuotas']:.2f}",
                f"{m['sanciones']:.2f}",
                f"{m['total']:.2f}"
            ])
            
        table = Table(data, colWidths=[250, 80, 60, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Alinear nombres a la izquierda
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        # Dibujar tabla
        table.wrapOn(c, width, height)
        table.drawOn(c, 50, height - 120 - (len(data) * 18))
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')


class RutasRentablesView(APIView):
    """
    Análisis de rentabilidad por ruta.
    URL: GET /api/reportes/rutas-rentables/?meses=6
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from hojasruta.models import HojaRuta
        from rutas.models import Ruta
        
        meses = int(request.GET.get('meses', 6))
        fecha_inicio = datetime.now() - timedelta(days=30 * meses)
        
        # Obtener todas las rutas
        rutas = Ruta.objects.all()
        
        resultados = []
        for ruta in rutas:
            # Hojas de ruta de esta ruta en el período
            hojas = HojaRuta.objects.filter(
                ruta=ruta,
                fecha_emision__gte=fecha_inicio
            )
            
            total_hojas = hojas.count()
            
            if total_hojas == 0:
                continue
            
            # Calcular ingresos totales
            ingresos_totales = hojas.aggregate(total=Sum('precio'))['total'] or 0
            
            # Promedio de ingresos por viaje
            promedio_por_viaje = ingresos_totales / total_hojas if total_hojas > 0 else 0
            
            # Obtener reservas asociadas a estas hojas
            try:
                from reservas.models import Reserva
                total_reservas = Reserva.objects.filter(
                    ruta=ruta,
                    fecha_viaje__gte=fecha_inicio
                ).count()
            except:
                total_reservas = 0
            
            resultados.append({
                'ruta_id': ruta.id,
                'ruta_nombre': ruta.nombre,
                'origen': getattr(ruta, 'origen', 'N/A'),
                'destino': getattr(ruta, 'destino', 'N/A'),
                'total_viajes': total_hojas,
                'ingresos_totales': float(ingresos_totales),
                'promedio_por_viaje': float(promedio_por_viaje),
                'total_reservas': total_reservas,
                'promedio_reservas_por_viaje': round(total_reservas / total_hojas, 2) if total_hojas > 0 else 0
            })
        
        # Ordenar por ingresos totales
        resultados.sort(key=lambda x: x['ingresos_totales'], reverse=True)
        
        # Calcular totales
        total_ingresos = sum(r['ingresos_totales'] for r in resultados)
        total_viajes = sum(r['total_viajes'] for r in resultados)
        
        return Response({
            'periodo_meses': meses,
            'fecha_desde': fecha_inicio.date(),
            'total_rutas_analizadas': len(resultados),
            'total_viajes_sistema': total_viajes,
            'ingresos_totales_sistema': float(total_ingresos),
            'promedio_por_viaje_sistema': float(total_ingresos / total_viajes) if total_viajes > 0 else 0,
            'rutas': resultados
        })


class OcupacionHistoricaView(APIView):
    """
    Análisis de ocupación de vehículos por mes.
    URL: GET /api/reportes/ocupacion-historica/?meses=12
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from hojasruta.models import HojaRuta
        from django.db.models.functions import TruncMonth
        
        meses = int(request.GET.get('meses', 12))
        fecha_inicio = datetime.now() - timedelta(days=30 * meses)
        
        # Agrupar hojas de ruta por mes
        hojas_por_mes = HojaRuta.objects.filter(
            fecha_emision__gte=fecha_inicio
        ).annotate(
            mes=TruncMonth('fecha_emision')
        ).values('mes').annotate(
            total_hojas=Count('id')
        ).order_by('mes')
        
        # Pre-cargar todas las reservas en el período para evitar N+1
        from reservas.models import Reserva
        reservas_por_mes = Reserva.objects.filter(
            fecha_viaje__gte=fecha_inicio
        ).annotate(
            mes=TruncMonth('fecha_viaje')
        ).values('mes').annotate(
            total_reservas=Count('id')
        )
        
        # Crear un mapa rápido {mes: total_reservas}
        mapa_reservas = {str(r['mes']): r['total_reservas'] for r in reservas_por_mes}
        
        resultados_mensuales = []
        for item in hojas_por_mes:
            mes_key = str(item['mes'])
            total_reservas = mapa_reservas.get(mes_key, 0)
            
            # Estimación: capacidad promedio de 15 pasajeros por hoja
            total_cupos = item['total_hojas'] * 15
            porcentaje_ocupacion = (total_reservas / total_cupos * 100) if total_cupos > 0 else 0
            
            resultados_mensuales.append({
                'mes': item['mes'].strftime('%Y-%m'),
                'mes_nombre': item['mes'].strftime('%B %Y'),
                'total_hojas': item['total_hojas'],
                'total_cupos_disponibles': total_cupos,
                'total_cupos_reservados': total_reservas,
                'cupos_libres': total_cupos - total_reservas,
                'porcentaje_ocupacion': round(porcentaje_ocupacion, 2)
            })
        
        # Promedios generales
        if resultados_mensuales:
            promedio_ocupacion = sum(r['porcentaje_ocupacion'] for r in resultados_mensuales) / len(resultados_mensuales)
        else:
            promedio_ocupacion = 0
        
        return Response({
            'periodo_meses': meses,
            'fecha_desde': fecha_inicio.date(),
            'promedio_ocupacion_general': round(promedio_ocupacion, 2),
            'meses': resultados_mensuales
        })


class BalanceView(APIView):
    """
    Balance financiero general del sindicato.
    Solo considera transacciones válidas (ingresos 'completado', egresos 'aprobado').
    URL: GET /api/reportes/balance?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from reportes.query_helpers import resumen_periodo, pagos_validos, egresos_validos

        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        resumen = resumen_periodo(fecha_inicio, fecha_fin)

        # Registros individuales de ingresos (pagos completados)
        pagos_qs = pagos_validos(fecha_inicio, fecha_fin).order_by('-fecha_pago')
        lista_ingresos = []
        for p in pagos_qs:
            lista_ingresos.append({
                'id': p.id,
                'fecha': p.fecha_pago.strftime('%Y-%m-%d') if p.fecha_pago else '',
                'afiliado': p.afiliado.nombre_completo if p.afiliado else 'Sin afiliado',
                'concepto': p.tipo_pago.nombre if p.tipo_pago else 'Ingreso',
                'metodo_pago': p.get_metodo_pago_display() if hasattr(p, 'get_metodo_pago_display') else (p.metodo_pago or ''),
                'observaciones': p.observaciones or '',
                'monto': float(p.monto),
                'nro_recibo': p.nro_recibo or p.id,
            })

        # Registros individuales de egresos (aprobados/completados)
        egresos_qs = egresos_validos(fecha_inicio, fecha_fin).order_by('-fecha')
        lista_egresos = []
        for e in egresos_qs:
            lista_egresos.append({
                'id': e.id,
                'fecha': e.fecha.strftime('%Y-%m-%d') if e.fecha else '',
                'concepto': e.tipo_pago.nombre if e.tipo_pago else 'Egreso',
                'descripcion': e.descripcion or '',
                'metodo_pago': e.get_metodo_pago_display() if hasattr(e, 'get_metodo_pago_display') else (e.metodo_pago or ''),
                'monto': float(e.monto),
                'estado': e.estado,
            })

        # Listado completo de egresos (incluye pendientes de aprobación y
        # anulados) para que el balance muestre la misma información que el
        # módulo de Pagos y Egresos.
        from tesoreria.models import Egreso
        from reportes.query_helpers import EGRESO_ESTADOS_VALIDOS
        from django.db.models import Q

        egresos_todos_qs = Egreso.objects.select_related('tipo_pago').all()
        if fecha_inicio:
            egresos_todos_qs = egresos_todos_qs.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            egresos_todos_qs = egresos_todos_qs.filter(fecha__lte=fecha_fin)
        egresos_todos_qs = egresos_todos_qs.order_by('-fecha')

        lista_egresos_todos = [
            {
                'id': e.id,
                'fecha': e.fecha.strftime('%Y-%m-%d') if e.fecha else '',
                'concepto': e.tipo_pago.nombre if e.tipo_pago else 'Egreso',
                'descripcion': e.descripcion or '',
                'metodo_pago': e.get_metodo_pago_display() if hasattr(e, 'get_metodo_pago_display') else (e.metodo_pago or ''),
                'monto': float(e.monto),
                'estado': e.estado,
                'es_valido': e.estado in EGRESO_ESTADOS_VALIDOS,
            }
            for e in egresos_todos_qs
        ]

        agregados_egresos = egresos_todos_qs.aggregate(
            total_monto=Sum('monto'),
            total_aprobado=Sum('monto', filter=Q(estado__in=EGRESO_ESTADOS_VALIDOS)),
            total_pendiente_aprobacion=Sum('monto', filter=Q(estado='pendiente_aprobacion')),
            total_anulado=Sum('monto', filter=Q(estado='anulado')),
        )
        totales_egresos = {clave: float(valor or 0) for clave, valor in agregados_egresos.items()}
        totales_egresos.update({
            'count_todos': egresos_todos_qs.count(),
            'count_aprobado': egresos_todos_qs.filter(estado__in=EGRESO_ESTADOS_VALIDOS).count(),
            'count_pendiente_aprobacion': egresos_todos_qs.filter(estado='pendiente_aprobacion').count(),
            'count_anulado': egresos_todos_qs.filter(estado='anulado').count(),
        })

        response_data = {
            'total_ingresos': resumen['total_ingresos'],
            'count_ingresos': resumen['count_ingresos'],
            'total_egresos': resumen['total_egresos'],
            'count_egresos': resumen['count_egresos'],
            'saldo': resumen['saldo'],
            'ingresos_por_tipo': resumen['ingresos_por_tipo'],
            'egresos_por_tipo': resumen['egresos_por_tipo'],
            'excluidos_por_estado': resumen['anulados_cancelados'],
            'lista_ingresos': lista_ingresos,
            'lista_egresos': lista_egresos,
            'totales_egresos': totales_egresos,
            'lista_egresos_todos': lista_egresos_todos,
        }

        # Agregar información del período si se filtró
        if fecha_inicio:
            response_data['fecha_inicio'] = fecha_inicio
        if fecha_fin:
            response_data['fecha_fin'] = fecha_fin

        return Response(response_data)


class ReportesGraficosView(APIView):
    """
    Datos para gráficos financieros.
    URL: GET /api/reportes/graficos?tipo=mensual&fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from tesoreria.models import Pago, Egreso, TipoPago
        from hojasruta.models import HojaRuta
        from django.db.models.functions import TruncMonth, TruncDay
        from reportes.query_helpers import INGRESO_ESTADOS_VALIDOS, EGRESO_ESTADOS_VALIDOS
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        tipo = request.GET.get('tipo', 'mensual')
        
        # Filtrar por fechas y solo transacciones válidas
        pagos_query = Pago.objects.filter(estado__in=INGRESO_ESTADOS_VALIDOS)
        egresos_query = Egreso.objects.filter(estado__in=EGRESO_ESTADOS_VALIDOS)
        
        if not fecha_inicio and tipo == 'mensual':
            # Por defecto mostrar últimos 6 meses si no se especifica
            fecha_inicio = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

        if fecha_inicio:
            pagos_query = pagos_query.filter(fecha_pago__gte=fecha_inicio)
            egresos_query = egresos_query.filter(fecha__gte=fecha_inicio)
        
        if fecha_fin:
            pagos_query = pagos_query.filter(fecha_pago__lte=fecha_fin)
            egresos_query = egresos_query.filter(fecha__lte=fecha_fin)
        
        if tipo == 'mensual':
            # Agrupar por mes
            ingresos_mensuales = pagos_query.annotate(
                mes=TruncMonth('fecha_pago')
            ).values('mes').annotate(
                total=Sum('monto')
            ).order_by('mes')
            
            egresos_mensuales = egresos_query.annotate(
                mes=TruncMonth('fecha')
            ).values('mes').annotate(
                total=Sum('monto')
            ).order_by('mes')
            
            return Response({
                'ingresos': [
                    {
                        'mes': item['mes'].strftime('%Y-%m') if item['mes'] else 'N/A',
                        'total': float(item['total'] or 0)
                    } for item in ingresos_mensuales
                ],
                'egresos': [
                    {
                        'mes': item['mes'].strftime('%Y-%m') if item['mes'] else 'N/A',
                        'total': float(item['total'] or 0)
                    } for item in egresos_mensuales
                ]
            })
        
        elif tipo == 'por_tipo':
            # Agrupar por tipo de pago
            ingresos_por_tipo = pagos_query.values(
                'tipo_pago__nombre'
            ).annotate(
                total=Sum('monto')
            ).order_by('-total')
            
            egresos_por_tipo = egresos_query.values(
                'tipo_pago__nombre'
            ).annotate(
                total=Sum('monto')
            ).order_by('-total')
            
            return Response({
                'ingresos': [
                    {
                        'tipo': item['tipo_pago__nombre'] or 'Sin tipo',
                        'total': float(item['total'] or 0)
                    } for item in ingresos_por_tipo
                ],
                'egresos': [
                    {
                        'tipo': item['tipo_pago__nombre'] or 'Sin categoría',
                        'total': float(item['total'] or 0)
                    } for item in egresos_por_tipo[:10]  # Top 10
                ]
            })
        
        elif tipo == 'salidas':
            # Salidas por día (últimos 14 días)
            fecha_referencia = datetime.now() - timedelta(days=14)
            salidas_por_dia = HojaRuta.objects.filter(
                fecha_emision__gte=fecha_referencia
            ).annotate(
                dia=TruncDay('fecha_emision')
            ).values('dia').annotate(
                total=Count('id')
            ).order_by('dia')
            
            return Response({
                'salidas': [
                    {
                        'fecha': item['dia'].strftime('%Y-%m-%d') if item['dia'] else 'N/A',
                        'dia_semana': item['dia'].strftime('%A') if item['dia'] else 'N/A',
                        'total': item['total']
                    } for item in salidas_por_dia
                ]
            })

        elif tipo == 'semanal':
            # Ingresos diarios de la semana actual
            hoy = datetime.now()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            
            ingresos_diarios = pagos_query.filter(
                fecha_pago__gte=inicio_semana
            ).annotate(
                dia=TruncDay('fecha_pago')
            ).values('dia').annotate(
                total=Sum('monto')
            ).order_by('dia')
            
            return Response({
                'semana': [
                    {
                        'fecha': item['dia'].strftime('%Y-%m-%d') if item['dia'] else 'N/A',
                        'dia_semana': item['dia'].strftime('%A') if item['dia'] else 'N/A',
                        'total': float(item['total'] or 0)
                    } for item in ingresos_diarios
                ]
            })

        return Response({'error': 'Tipo no válido'}, status=400)


class TransaccionesView(APIView):
    """
    Lista de todas las transacciones válidas (ingresos y egresos).
    URL: GET /api/reportes/transacciones?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from reportes.query_helpers import pagos_validos, egresos_validos, pagos_excluidos, egresos_excluidos
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        # Solo transacciones con estado válido
        pagos_query = pagos_validos(fecha_inicio, fecha_fin)
        egresos_query = egresos_validos(fecha_inicio, fecha_fin)
        
        # Convertir a lista de transacciones
        transacciones = []
        
        for pago in pagos_query:
            transacciones.append({
                'fecha': str(pago.fecha_pago) if pago.fecha_pago else 'N/A',
                'tipo': 'INGRESO',
                'afiliado': pago.afiliado.nombre_completo if pago.afiliado else 'N/A',
                'tipo_pago': pago.tipo_pago.nombre if pago.tipo_pago else 'N/A',
                'descripcion': pago.observaciones or f"Pago por {pago.tipo_pago.nombre if pago.tipo_pago else 'cuota'}",
                'monto': float(pago.monto or 0),
                'estado': pago.estado,
                'nro_recibo': pago.nro_recibo,
            })
        
        for egreso in egresos_query:
            transacciones.append({
                'fecha': str(egreso.fecha) if egreso.fecha else 'N/A',
                'tipo': 'EGRESO',
                'afiliado': None,
                'tipo_pago': egreso.tipo_pago.nombre if egreso.tipo_pago else 'General',
                'descripcion': egreso.descripcion or 'Egreso',
                'monto': float(egreso.monto or 0),
                'estado': egreso.estado,
                'nro_recibo': None,
            })
        
        # Ordenar por fecha descendente
        transacciones.sort(key=lambda x: x['fecha'], reverse=True)
        
        # Totales del período (solo transacciones válidas)
        total_ingresos = sum(t['monto'] for t in transacciones if t['tipo'] == 'INGRESO')
        total_egresos = sum(t['monto'] for t in transacciones if t['tipo'] == 'EGRESO')
        count_ingresos = sum(1 for t in transacciones if t['tipo'] == 'INGRESO')
        count_egresos = sum(1 for t in transacciones if t['tipo'] == 'EGRESO')
        
        # Registros excluidos por estado no válido (transparencia)
        excluidos = {
            'ingresos': {
                'count': pagos_excluidos(fecha_inicio, fecha_fin).count(),
                'monto': float(pagos_excluidos(fecha_inicio, fecha_fin).aggregate(total=Sum('monto'))['total'] or 0),
            },
            'egresos': {
                'count': egresos_excluidos(fecha_inicio, fecha_fin).count(),
                'monto': float(egresos_excluidos(fecha_inicio, fecha_fin).aggregate(total=Sum('monto'))['total'] or 0),
            },
        }
        
        resumen = {
            'total_ingresos': float(total_ingresos),
            'total_egresos': float(total_egresos),
            'saldo': float(total_ingresos - total_egresos),
            'count_ingresos': count_ingresos,
            'count_egresos': count_egresos,
        }
        
        total_items = len(transacciones)
        
        # Paginación manual
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
        except ValueError:
            page = 1
            page_size = 20

        start = (page - 1) * page_size
        end = start + page_size
        transacciones_paginadas = transacciones[start:end]
        
        return Response({
            'count': total_items,
            'total_pages': (total_items + page_size - 1) // page_size,
            'current_page': page,
            'page_size': page_size,
            'resumen': resumen,
            'excluidos_por_estado': excluidos,
            'transacciones': transacciones_paginadas
        })
        
class FinanzasView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from tesoreria.models import Pago, Egreso
        from afiliados.models import Afiliado
        from sanciones.models import Sancion
        from hojasruta.models import HojaRuta
        from reservas.models import Reserva
        from rutas.models import Ruta
        from django.utils.timezone import now
        from datetime import timedelta
        
        hoy = now().date()
        inicio_mes = hoy.replace(day=1)
        
        # Rango mes anterior
        ultimo_dia_mes_anterior = inicio_mes - timedelta(days=1)
        inicio_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
        
        # 1. Ingresos y Egresos del mes actual (solo transacciones válidas)
        from reportes.query_helpers import INGRESO_ESTADOS_VALIDOS, EGRESO_ESTADOS_VALIDOS
        ingresos_mes = Pago.objects.filter(fecha_pago__gte=inicio_mes, estado__in=INGRESO_ESTADOS_VALIDOS).aggregate(total=Sum('monto'))['total'] or 0
        egresos_mes = Egreso.objects.filter(fecha__gte=inicio_mes, estado__in=EGRESO_ESTADOS_VALIDOS).aggregate(total=Sum('monto'))['total'] or 0
        saldo_mes = ingresos_mes - egresos_mes
        
        # 2. Porcentaje de cambio ingresos vs mes anterior
        ingresos_mes_anterior = Pago.objects.filter(
            fecha_pago__gte=inicio_mes_anterior, 
            fecha_pago__lte=ultimo_dia_mes_anterior,
            estado__in=INGRESO_ESTADOS_VALIDOS
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        porcentaje_cambio = 0
        if ingresos_mes_anterior > 0:
            porcentaje_cambio = round(((ingresos_mes - ingresos_mes_anterior) / ingresos_mes_anterior) * 100, 1)
        elif ingresos_mes > 0:
            porcentaje_cambio = 100.0
            
        # 3. Afiliados
        total_afiliados = Afiliado.objects.count()
        nuevos_afiliados = Afiliado.objects.filter(fecha_ingreso__gte=inicio_mes).count() if hasattr(Afiliado, 'fecha_ingreso') else 0
        if nuevos_afiliados == 0:
             # Fallback si no hay fecha_ingreso o es 0, usar el count de los que se unieron este mes por ID si es autoincremental (no muy fiable) 
             # o simplemente dejar en 0 si el modelo no tiene el campo.
             pass

        # 4. Sanciones
        sanciones_pend = Sancion.objects.filter(estado='pendiente')
        count_sanciones = sanciones_pend.count()
        monto_sanciones = sanciones_pend.aggregate(total=Sum('monto'))['total'] or 0
        
        # 5. Operaciones (Hojas de Ruta y Reservas)
        hojas_hoy = HojaRuta.objects.filter(fecha_emision=hoy).count()
        hojas_mes = HojaRuta.objects.filter(fecha_emision__gte=inicio_mes).count()
        rutas_activas = HojaRuta.objects.filter(fecha_emision__gte=inicio_mes).values('ruta').distinct().count()
        reservas_activas = Reserva.objects.filter(estado='pendiente').count()
        
        # 6. Datos históricos (7 días)
        siete_dias = hoy - timedelta(days=7)
        ingresos_7 = Pago.objects.filter(fecha_pago__gte=siete_dias, estado__in=INGRESO_ESTADOS_VALIDOS).aggregate(total=Sum('monto'))['total'] or 0
        egresos_7 = Egreso.objects.filter(fecha__gte=siete_dias, estado__in=EGRESO_ESTADOS_VALIDOS).aggregate(total=Sum('monto'))['total'] or 0
        
        top_tipos = Pago.objects.filter(estado__in=INGRESO_ESTADOS_VALIDOS).values('tipo_pago__nombre').annotate(total=Sum('monto')).order_by('-total')[:5]
        
        return Response({
            'mes': str(inicio_mes)[:7],
            'ingresos_mes': float(ingresos_mes),
            'egresos_mes': float(egresos_mes),
            'saldo_mes': float(saldo_mes),
            'porcentaje_cambio_ingresos': float(porcentaje_cambio),
            'total_afiliados': total_afiliados,
            'afiliados_nuevos_mes': nuevos_afiliados,
            'sanciones_pendientes': count_sanciones,
            'monto_sanciones_pendientes': float(monto_sanciones),
            'hojas_hoy': hojas_hoy,
            'hojas_ruta_mes': hojas_mes,
            'rutas_activas': rutas_activas,
            'reservas_activas': reservas_activas,
            'ingresos_7dias': float(ingresos_7),
            'egresos_7dias': float(egresos_7),
            'top_ingresos_por_tipo': [
                {'tipo': t['tipo_pago__nombre'] or 'Sin tipo', 'total': float(t['total'])} for t in top_tipos
            ]
        })


class ReportesOperativosView(APIView):
    """
    Estadísticas operativas del sindicato.
    URL: GET /api/reportes/operativos
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from afiliados.models import Afiliado
        from vehiculos.models import Vehiculo
        from hojasruta.models import HojaRuta
        from reservas.models import Reserva
        from sanciones.models import Sancion
        from rutas.models import Ruta
        
        # Estadísticas de afiliados
        afiliados_total = Afiliado.objects.count()
        afiliados_activos = Afiliado.objects.filter(estado='activo').count()
        afiliados_pasivos = Afiliado.objects.filter(estado='pasivo').count()
        afiliados_sancionados = Afiliado.objects.filter(estado='sancionado').count()
        
        # Estadísticas de vehículos
        vehiculos_total = Vehiculo.objects.count()
        vehiculos_por_tipo = Vehiculo.objects.values('tipo').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Estadísticas de hojas de ruta
        hojas_total = HojaRuta.objects.count()
        top_rutas = HojaRuta.objects.values(
            'ruta__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:5]
        
        # Estadísticas de reservas
        reservas_total = Reserva.objects.count()
        reservas_por_estado = Reserva.objects.values('estado').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Estadísticas de sanciones
        sanciones_total = Sancion.objects.count()
        sanciones_pendientes = Sancion.objects.filter(estado='pendiente').count()
        
        return Response({
            'afiliados': {
                'total': afiliados_total,
                'activos': afiliados_activos,
                'pasivos': afiliados_pasivos,
                'sancionados': afiliados_sancionados
            },
            'vehiculos': {
                'total': vehiculos_total,
                'por_tipo': [
                    {
                        'tipo': v['tipo'] or 'Sin tipo',
                        'total': v['total']
                    } for v in vehiculos_por_tipo
                ]
            },
            'hojas_ruta': {
                'total': hojas_total,
                'top_rutas': [
                    {
                        'nombre': r['ruta__nombre'] or 'Sin nombre',
                        'total': r['total']
                    } for r in top_rutas
                ]
            },
            'reservas': {
                'total': reservas_total,
                'por_estado': [
                    {
                        'estado': r['estado'],
                        'total': r['total']
                    } for r in reservas_por_estado
                ]
            },
            'sanciones': {
                'total': sanciones_total,
                'pendientes': sanciones_pendientes
            }
        })

class TransaccionesCSVView(APIView):
    """
    Exporta todas las transacciones a Excel (XLSX).
    URL: GET /api/reportes/transacciones/csv
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from reportes.query_helpers import pagos_validos, egresos_validos
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        pagos = pagos_validos(fecha_inicio, fecha_fin)
        egresos = egresos_validos(fecha_inicio, fecha_fin)
            
        wb = Workbook()
        ws = wb.active
        ws.title = "Transacciones"
        
        headers = ['Fecha', 'Tipo', 'Afiliado', 'Tipo Pago', 'Descripción', 'Monto (Bs)', 'Estado']
        ws.append(headers)
        
        # Combinar y ordenar
        transacciones = []
        for p in pagos:
            transacciones.append([
                p.fecha_pago.strftime('%Y-%m-%d') if p.fecha_pago else '',
                'INGRESO',
                p.afiliado.nombre_completo if p.afiliado else 'N/A',
                p.tipo_pago.nombre if p.tipo_pago else 'N/A',
                p.observaciones or f"Pago por {p.tipo_pago.nombre if p.tipo_pago else 'cuota'}",
                float(p.monto),
                p.estado,
            ])
        for e in egresos:
            transacciones.append([
                e.fecha.strftime('%Y-%m-%d') if e.fecha else '',
                'EGRESO',
                'N/A',
                e.tipo_pago.nombre if e.tipo_pago else 'General',
                e.descripcion or 'Egreso',
                float(e.monto),
                e.estado,
            ])
            
        transacciones.sort(key=lambda x: x[0], reverse=True)
        for t in transacciones:
            ws.append(t)
            
        # Fila de totales
        ws.append([])
        ws.append(['TOTAL INGRESOS', '', '', '', '', self._suma(transacciones, 'INGRESO'), ''])
        ws.append(['TOTAL EGRESOS', '', '', '', '', self._suma(transacciones, 'EGRESO'), ''])
        ws.append(['SALDO', '', '', '', '', self._saldo(transacciones), ''])
            
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=transacciones_{datetime.now().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        return response

    def _suma(self, transacciones, tipo):
        return round(sum(t[5] for t in transacciones if t[1] == tipo), 2)

    def _saldo(self, transacciones):
        ingresos = sum(t[5] for t in transacciones if t[1] == 'INGRESO')
        egresos = sum(t[5] for t in transacciones if t[1] == 'EGRESO')
        return round(ingresos - egresos, 2)

class TransaccionesPDFView(APIView):
    """
    Exporta todas las transacciones válidas a PDF (Informe económico para afiliados).
    URL: GET /api/reportes/transacciones/pdf
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from reportes.query_helpers import pagos_validos, egresos_validos, resumen_periodo
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        pagos = pagos_validos(fecha_inicio, fecha_fin)
        egresos = egresos_validos(fecha_inicio, fecha_fin)
        resumen = resumen_periodo(fecha_inicio, fecha_fin)
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        elements.append(Paragraph("SINDICATO MIXTO \"INTEGRACIÓN TAIPIPLAYA\"", title_style))
        subtitle = ParagraphStyle('subtitle', parent=styles['Normal'], fontSize=13, alignment=TA_CENTER,
                                  textColor=colors.HexColor('#1a237e'), spaceAfter=10)
        elements.append(Paragraph("INFORME DE TRANSACCIONES (INGRESOS Y EGRESOS)", subtitle))
        if fecha_inicio or fecha_fin:
            rango = f"Período: {fecha_inicio or '...'} al {fecha_fin or '...'}"
        else:
            rango = "Período: Todo el historial"
        elements.append(Paragraph(rango, ParagraphStyle('rango', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=14)))
        
        # Resumen financiero del período
        resumen_data = [
            ['Total Ingresos', 'Total Egresos', 'Saldo', 'N° Ingresos', 'N° Egresos'],
            [
                f"Bs. {resumen['total_ingresos']:,.2f}",
                f"Bs. {resumen['total_egresos']:,.2f}",
                f"Bs. {resumen['saldo']:,.2f}",
                str(resumen['count_ingresos']),
                str(resumen['count_egresos']),
            ]
        ]
        tabla_resumen = Table(resumen_data, colWidths=[3.2*cm, 3.2*cm, 3.2*cm, 3.2*cm, 3.2*cm])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, 1), [colors.HexColor('#f1f8e9')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(tabla_resumen)
        elements.append(Spacer(1, 18))
        
        data = [['Fecha', 'Tipo', 'Afiliado', 'Tipo Pago', 'Descripción', 'Monto (Bs)', 'Estado']]
        
        transacciones = []
        for p in pagos:
            transacciones.append([
                p.fecha_pago.strftime('%Y-%m-%d') if p.fecha_pago else '',
                'INGRESO',
                p.afiliado.nombre_completo if p.afiliado else 'N/A',
                p.tipo_pago.nombre if p.tipo_pago else 'N/A',
                p.observaciones or f"Pago por {p.tipo_pago.nombre if p.tipo_pago else 'cuota'}",
                float(p.monto),
                'VÁLIDO',
            ])
        for e in egresos:
            transacciones.append([
                e.fecha.strftime('%Y-%m-%d') if e.fecha else '',
                'EGRESO',
                'N/A',
                e.tipo_pago.nombre if e.tipo_pago else 'General',
                e.descripcion or 'Egreso',
                float(e.monto),
                'VÁLIDO',
            ])
            
        transacciones.sort(key=lambda x: x[0], reverse=True)
        for t in transacciones:
            data.append(t)
        
        # Fila de totales
        data.append(['', 'TOTAL INGRESOS', '', '', '', f"Bs. {resumen['total_ingresos']:,.2f}", ''])
        data.append(['', 'TOTAL EGRESOS', '', '', '', f"Bs. {resumen['total_egresos']:,.2f}", ''])
        data.append(['', 'SALDO DEL PERÍODO', '', '', '', f"Bs. {resumen['saldo']:,.2f}", ''])
            
        table = Table(data, repeatRows=1, colWidths=[70, 85, 155, 110, 175, 75, 50])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,1), (-1,-3), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (1,-3), (-1,-1), colors.HexColor('#e8f5e9')),
            ('FONTNAME', (0,-3), (-1,-1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-4), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 10))
        excl = resumen['anulados_cancelados']
        nota = ("*Registros excluidos del informe por estado no válido:* "
                f"{excl['count_ingresos']} ingreso(s) "
                f"(Bs. {excl['monto_ingresos']:,.2f}) y "
                f"{excl['count_egresos']} egreso(s) (Bs. {excl['monto_egresos']:,.2f}).")
        elements.append(Paragraph(
            nota,
            ParagraphStyle('nota', parent=styles['Normal'], fontSize=8, textColor=colors.grey, spaceBefore=6)
        ))
        doc.build(elements)
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')

class ReportesOperativosCSVView(APIView):
    """
    Exporta estadísticas operativas a Excel.
    URL: GET /api/reportes/operativos/csv
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from afiliados.models import Afiliado
        from vehiculos.models import Vehiculo
        from hojasruta.models import HojaRuta
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte Operativo"
        
        ws.append(['Reporte de Estadísticas Operativas'])
        ws.append(['Generado:', datetime.now().strftime('%Y-%m-%d %H:%M')])
        ws.append([])
        
        # Afiliados
        ws.append(['RESUMEN DE AFILIADOS'])
        ws.append(['Estado', 'Cantidad'])
        ws.append(['Activos', Afiliado.objects.filter(estado='activo').count()])
        ws.append(['Pasivos', Afiliado.objects.filter(estado='pasivo').count()])
        ws.append(['Sancionados', Afiliado.objects.filter(estado='sancionado').count()])
        ws.append(['Total', Afiliado.objects.count()])
        ws.append([])
        
        # Vehículos
        ws.append(['RESUMEN DE VEHÍCULOS'])
        ws.append(['Tipo', 'Cantidad'])
        vehiculos = Vehiculo.objects.values('tipo').annotate(total=Count('id'))
        for v in vehiculos:
            ws.append([v['tipo'] or 'N/A', v['total']])
        ws.append([])
        
        # Hojas de Ruta
        ws.append(['RESUMEN DE OPERACIONES'])
        ws.append(['Indicador', 'Valor'])
        ws.append(['Total Hojas de Ruta', HojaRuta.objects.count()])
        ws.append([])
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=reporte_operativo.xlsx'
        wb.save(response)
        return response

class ReportesOperativosPDFView(APIView):
    """
    Exporta estadísticas operativas a PDF.
    URL: GET /api/reportes/operativos/pdf
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from afiliados.models import Afiliado
        from vehiculos.models import Vehiculo
        from hojasruta.models import HojaRuta
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph("REPORTE OPERATIVO GENERAL", styles['Title']))
        elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Afiliados
        elements.append(Paragraph("Resumen de Afiliados", styles['Heading2']))
        data_af = [
            ['Estado', 'Cantidad'],
            ['Activos', str(Afiliado.objects.filter(estado='activo').count())],
            ['Pasivos', str(Afiliado.objects.filter(estado='pasivo').count())],
            ['Sancionados', str(Afiliado.objects.filter(estado='sancionado').count())],
            ['Total', str(Afiliado.objects.count())]
        ]
        t_af = Table(data_af, colWidths=[150, 100])
        t_af.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        elements.append(t_af)
        elements.append(Spacer(1, 20))
        
        # Vehículos
        elements.append(Paragraph("Distribución de Vehículos", styles['Heading2']))
        data_ve = [['Tipo', 'Cantidad']]
        for v in Vehiculo.objects.values('tipo').annotate(total=Count('id')):
            data_ve.append([v['tipo'] or 'N/A', str(v['total'])])
        t_ve = Table(data_ve, colWidths=[150, 100])
        t_ve.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)]))
        elements.append(t_ve)
        
        doc.build(elements)
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')


class ReporteCategoriaView(APIView):
    """
    Reporte por categoría de ingreso o de egreso.
    Con ?tipo=egreso agrupa los egresos registrados por categoría en lugar de
    medir la cobertura de pagos de los afiliados.

    URL: GET /api/reportes/por-categoria/?tipo_pago_id=6&fecha_inicio=2026-01-01&fecha_fin=2026-12-31
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from tesoreria.models import Pago, TipoPago
        from afiliados.models import Afiliado

        tipo_pago_id = request.GET.get('tipo_pago_id')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        todas = request.GET.get('todas') in ['1', 'true', 'True', 'si', 'todos']
        monto_esperado = _get_decimal_param(request, 'monto_esperado')

        if _es_reporte_egresos(request):
            from . import egresos_categoria
            reporte = egresos_categoria.construir_reporte(
                tipo_pago_id=tipo_pago_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                todas=todas,
            )
            if 'error' in reporte:
                return Response(reporte, status=404)
            return Response(reporte)

        afiliados_activos_query = Afiliado.objects.filter(estado='activo', is_active=True)
        total_afiliados_activos = afiliados_activos_query.count()

        if todas:
            categorias = []
            total_general_recaudado = 0
            total_general_esperado = 0
            total_general_faltante = 0
            total_pagos_pendientes_revision = 0
            total_afiliados_con_pago_duplicado = 0
            total_pendientes_deuda = 0
            duplicados_global = []
            # Se materializa una sola vez: el cálculo de pendientes lo recorre
            # por cada categoría y no debe volver a la base en cada vuelta.
            afiliados_activos = list(
                afiliados_activos_query.only('id', 'nombres', 'apellidos', 'ci', 'telefono')
            )
            for tipo_pago in TipoPago.objects.filter(tipo='ingreso').order_by('nombre'):
                resumen = _resumen_categoria(Pago, tipo_pago, total_afiliados_activos, fecha_inicio, fecha_fin, monto_esperado)
                total_general_recaudado += resumen['total_recaudado']
                total_pagos_pendientes_revision += resumen['count_pagos_pendientes_revision']
                total_afiliados_con_pago_duplicado += resumen['count_afiliados_con_pago_duplicado']
                if resumen['total_esperado'] is not None:
                    total_general_esperado += resumen['total_esperado']

                pendientes = _pendientes_por_categoria(
                    Pago, tipo_pago, fecha_inicio, fecha_fin, monto_esperado, afiliados_activos
                )
                total_pendientes_deuda += pendientes['count_pendientes']
                # El KPI de faltante usa la deuda real por afiliado para que
                # cuadre exactamente con el detalle "Faltan Cancelar".
                if pendientes['monto_total_pendiente'] is not None:
                    resumen['monto_faltante'] = pendientes['monto_total_pendiente']
                if resumen['monto_faltante'] is not None:
                    total_general_faltante += resumen['monto_faltante']

                resumen.update(pendientes)
                # Detalle de posibles pagos duplicados por categoría.
                duplicados_categoria = _duplicados_por_categoria(
                    Pago, tipo_pago, fecha_inicio, fecha_fin
                )
                for duplicado in duplicados_categoria:
                    duplicado['categoria'] = {
                        'id': tipo_pago.id,
                        'nombre': tipo_pago.nombre,
                    }
                resumen['duplicados'] = duplicados_categoria
                duplicados_global.extend(duplicados_categoria)
                categorias.append(resumen)

            return Response({
                'modo': 'todas',
                'filtros': {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                },
                'resumen': {
                    'total_recaudado': float(total_general_recaudado),
                    'monto_esperado_por_afiliado': float(monto_esperado) if monto_esperado is not None else None,
                    'total_esperado': float(total_general_esperado) if monto_esperado is not None else None,
                    'monto_faltante': float(total_general_faltante) if monto_esperado is not None else None,
                    'total_categorias': len(categorias),
                    'total_afiliados_activos': total_afiliados_activos,
                    'total_pagos_pendientes_revision': total_pagos_pendientes_revision,
                    'total_afiliados_con_pago_duplicado': total_afiliados_con_pago_duplicado,
                    'total_pendientes': total_pendientes_deuda,
                    'total_monto_duplicado': round(
                        sum(d['total_pagado'] for d in duplicados_global), 2
                    ),
                },
                'categorias': categorias,
                'duplicados': sorted(
                    duplicados_global, key=lambda fila: -fila['total_pagado']
                ),
            })

        if not tipo_pago_id:
            # Sin filtro: listar todos los tipos de ingreso disponibles
            tipos = TipoPago.objects.filter(tipo='ingreso').values('id', 'nombre').order_by('nombre')
            return Response({'tipos_pago': list(tipos)})

        try:
            tipo_pago = TipoPago.objects.get(id=tipo_pago_id, tipo='ingreso')
        except TipoPago.DoesNotExist:
            return Response({'error': 'Categoría de ingreso no encontrada'}, status=404)

        # Filtrar pagos completados del tipo seleccionado
        pagos_query = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['completado'])

        resumen = _resumen_categoria(Pago, tipo_pago, total_afiliados_activos, fecha_inicio, fecha_fin, monto_esperado)

        # Detalle de pagos realizados
        pagos_detalle = []
        for pago in pagos_query.order_by('afiliado__apellidos', 'afiliado__nombres', 'fecha_pago'):
            pagos_detalle.append({
                'afiliado_id': pago.afiliado_id,
                'nombre': pago.afiliado.nombre_completo if pago.afiliado else 'N/A',
                'ci': pago.afiliado.ci if pago.afiliado else '',
                'telefono': pago.afiliado.telefono if pago.afiliado else '',
                'fecha_pago': str(pago.fecha_pago),
                'monto': float(pago.monto),
                'estado': pago.estado,
                'nro_recibo': pago.nro_recibo,
            })

        pagos_revision_detalle = []
        pagos_revision_query = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['pendiente', 'anulado', 'cancelado'])
        for pago in pagos_revision_query.order_by('estado', 'afiliado__apellidos', 'afiliado__nombres', 'fecha_pago'):
            pagos_revision_detalle.append({
                'afiliado_id': pago.afiliado_id,
                'nombre': pago.afiliado.nombre_completo if pago.afiliado else 'N/A',
                'ci': pago.afiliado.ci if pago.afiliado else '',
                'telefono': pago.afiliado.telefono if pago.afiliado else '',
                'fecha_pago': str(pago.fecha_pago),
                'monto': float(pago.monto),
                'estado': pago.estado,
                'nro_recibo': pago.nro_recibo,
            })

        duplicados_detalle = _duplicados_por_categoria(
            Pago, tipo_pago, fecha_inicio, fecha_fin
        )

        # Calcular afiliados pendientes y deudas para categoría individual
        pendientes_info = _pendientes_por_categoria(
            Pago, tipo_pago, fecha_inicio, fecha_fin, monto_esperado,
            list(afiliados_activos_query.only('id', 'nombres', 'apellidos', 'ci', 'telefono')),
        )
        # El KPI de faltante usa la deuda real por afiliado para que cuadre con
        # el total de la tabla de pendientes.
        if pendientes_info['monto_total_pendiente'] is not None:
            resumen['monto_faltante'] = pendientes_info['monto_total_pendiente']
        resumen.update(pendientes_info)

        return Response({
            'categoria': {
                'id': tipo_pago.id,
                'nombre': tipo_pago.nombre,
            },
            'filtros': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
            },
            'resumen': resumen,
            'pagaron': pagos_detalle,
            'pendientes': pendientes_info['pendientes'],
            'pagos_revision': pagos_revision_detalle,
            'duplicados': duplicados_detalle,
        })


class ReporteCategoriaPDFView(APIView):
    """
    Exporta a PDF el reporte por categoría de ingreso o de egreso.
    URL: GET /api/reportes/por-categoria/pdf/?tipo=egreso&todas=1&fecha_inicio=...&fecha_fin=...
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from tesoreria.models import Pago, TipoPago
        from afiliados.models import Afiliado
        from reportlab.lib.units import cm

        tipo_pago_id = request.GET.get('tipo_pago_id')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        todas = request.GET.get('todas') in ['1', 'true', 'True', 'si', 'todos']
        monto_esperado = _get_decimal_param(request, 'monto_esperado')

        if _es_reporte_egresos(request):
            from . import egresos_categoria
            contenido, nombre = egresos_categoria.generar_pdf(
                tipo_pago_id=tipo_pago_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                todas=todas,
            )
            if contenido is None:
                status = 404 if 'no encontrada' in nombre else 400
                return Response({'error': nombre}, status=status)
            response = HttpResponse(contenido, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={nombre}'
            return response

        afiliados_activos = Afiliado.objects.filter(estado='activo', is_active=True)
        total_activos = afiliados_activos.count()

        if todas:
            rows = []
            total_general = 0
            total_esperado_general = 0
            total_faltante_general = 0
            total_pendientes_general = 0
            total_parciales_general = 0
            activos = list(afiliados_activos.only('id', 'nombres', 'apellidos', 'ci', 'telefono'))
            for tipo_pago in TipoPago.objects.filter(tipo='ingreso').order_by('nombre'):
                resumen = _resumen_categoria(Pago, tipo_pago, total_activos, fecha_inicio, fecha_fin, monto_esperado)
                pendientes = _pendientes_por_categoria(
                    Pago, tipo_pago, fecha_inicio, fecha_fin, monto_esperado, activos, limite=None
                )
                total_general += resumen['total_recaudado']
                total_pendientes_general += pendientes['count_pendientes']
                total_parciales_general += pendientes['count_parciales']
                if resumen['total_esperado'] is not None:
                    total_esperado_general += resumen['total_esperado']
                    # El faltante usa la deuda real por afiliado (idéntico al detalle).
                    resumen['monto_faltante'] = pendientes['monto_total_pendiente']
                    total_faltante_general += resumen['monto_faltante']
                resumen.update(pendientes)
                rows.append(resumen)

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm,
                                    leftMargin=1.5*cm, rightMargin=1.5*cm)
            elements = []
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TitleAll', parent=styles['Title'], fontSize=16, alignment=TA_CENTER,
                                         textColor=colors.HexColor('#1a237e'), spaceAfter=8)
            subtitle_style = ParagraphStyle('SubAll', parent=styles['Normal'], fontSize=10,
                                            alignment=TA_CENTER, textColor=colors.HexColor('#555'), spaceAfter=10)
            heading_all = ParagraphStyle('HeadAll', parent=styles['Heading2'], fontSize=11,
                                         textColor=colors.HexColor('#c62828'), spaceBefore=14, spaceAfter=6)

            elements.append(Paragraph("SINDICATO MIXTO \"INTEGRACIÓN TAIPIPLAYA\"", title_style))
            elements.append(Paragraph("Reporte General por Categorías de Ingreso", subtitle_style))
            periodo = f"Período: {fecha_inicio or 'inicio'} al {fecha_fin or 'hoy'}"
            elements.append(Paragraph(periodo, subtitle_style))
            elements.append(Paragraph(f"Total recaudado: Bs. {float(total_general):,.2f}", subtitle_style))
            if monto_esperado is not None:
                elements.append(Paragraph(f"Total esperado: Bs. {float(total_esperado_general):,.2f} | Faltante estimado: Bs. {float(total_faltante_general):,.2f}", subtitle_style))
            elements.append(Paragraph(f"Afiliados con deuda en alguna categoría: {total_pendientes_general} (de los cuales {total_parciales_general} pagan parcial)", subtitle_style))
            elements.append(Spacer(1, 8))

            data = [['Categoría', 'Ya cancelaron', 'Faltan pagar', 'Cobertura', 'Recaudado', 'Esperado', 'Faltante', 'Revisión']]
            for r in rows:
                data.append([
                    r['categoria']['nombre'],
                    str(r['count_pagaron']),
                    str(r['count_pendientes']),
                    f"{r['porcentaje_cobertura']}%",
                    f"{r['total_recaudado']:,.2f}",
                    f"{r['total_esperado']:,.2f}" if r['total_esperado'] is not None else '-',
                    f"{r['monto_faltante']:,.2f}" if r['monto_faltante'] is not None else '-',
                    str(r['count_pagos_pendientes_revision'] + r['count_pagos_anulados_cancelados'] + r['count_afiliados_con_pago_duplicado']),
                ])
            data.append(['TOTAL', '', str(total_pendientes_general), '', f"Bs. {float(total_general):,.2f}", f"Bs. {float(total_esperado_general):,.2f}" if monto_esperado is not None else '-', f"Bs. {float(total_faltante_general):,.2f}" if monto_esperado is not None else '-', ''])

            table = Table(data, repeatRows=1, colWidths=[5.7*cm, 2.5*cm, 2.5*cm, 2.1*cm, 2.7*cm, 2.7*cm, 2.7*cm, 2.1*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f7ff')]),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 14))

            # Detalle de pendientes por categoría (solo categorías con deuda)
            for r in rows:
                lista_pend = r.get('pendientes') or []
                if not lista_pend:
                    continue
                elements.append(Paragraph(
                    f"❌ {r['categoria']['nombre']} — {r['count_pendientes']} afiliado(s) sin cancelación completa",
                    heading_all,
                ))
                if r.get('monto_total_pendiente') is not None:
                    elements.append(Paragraph(
                        f"Monto pendiente: Bs. {r['monto_total_pendiente']:,.2f}",
                        ParagraphStyle('DeudaCat', parent=styles['Normal'], fontSize=9,
                                       textColor=colors.HexColor('#9f1239'), spaceAfter=4),
                    ))
                encabezado = ['#', 'Nombre Completo', 'C.I.', 'Teléfono']
                anchos = [1*cm, 9*cm, 5*cm, 5*cm]
                if r.get('monto_total_pendiente') is not None:
                    encabezado += ['Pagado (Bs)', 'Deuda (Bs)']
                    anchos += [3.5*cm, 3.5*cm]
                filas_pend = [encabezado]
                for i, af in enumerate(lista_pend, 1):
                    fila = [str(i), af['nombre'], af['ci'], af['telefono'] or '-']
                    if r.get('monto_total_pendiente') is not None:
                        fila += [f"{af['pagado']:,.2f}", f"{af['deuda']:,.2f}"]
                    filas_pend.append(fila)
                style_pend = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c62828')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff8f8')]),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]
                if len(anchos) > 4:
                    style_pend.append(('ALIGN', (len(anchos) - 2, 0), (-1, -1), 'RIGHT'))
                tabla_pend = Table(filas_pend, repeatRows=1, colWidths=anchos)
                tabla_pend.setStyle(TableStyle(style_pend))
                elements.append(tabla_pend)
                elements.append(Spacer(1, 10))

            doc.build(elements)
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=reporte_categorias_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response

        if not tipo_pago_id:
            return Response({'error': 'Se requiere tipo_pago_id'}, status=400)

        try:
            tipo_pago = TipoPago.objects.get(id=tipo_pago_id, tipo='ingreso')
        except TipoPago.DoesNotExist:
            return Response({'error': 'Categoría no encontrada'}, status=404)

        pagos_query = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['completado'])

        total_recaudado = pagos_query.aggregate(total=Sum('monto'))['total'] or 0
        resumen = _resumen_categoria(Pago, tipo_pago, total_activos, fecha_inicio, fecha_fin, monto_esperado)

        pendientes_info = _pendientes_por_categoria(
            Pago, tipo_pago, fecha_inicio, fecha_fin, monto_esperado, list(afiliados_activos), limite=None
        )
        if pendientes_info['monto_total_pendiente'] is not None:
            resumen['monto_faltante'] = pendientes_info['monto_total_pendiente']

        count_pagaron = resumen['count_pagaron']
        count_pendientes = pendientes_info['count_pendientes']
        cobertura = resumen['porcentaje_cobertura']
        monto_esperado_afiliado = resumen['monto_esperado_por_afiliado']

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm,
                                leftMargin=1.5*cm, rightMargin=1.5*cm)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, alignment=TA_CENTER,
                                     textColor=colors.HexColor('#1a237e'), spaceAfter=6)
        subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10,
                                        alignment=TA_CENTER, textColor=colors.HexColor('#555'), spaceAfter=12)
        heading_style = ParagraphStyle('Head', parent=styles['Heading2'], fontSize=12,
                                       textColor=colors.HexColor('#1a237e'), spaceBefore=16, spaceAfter=6)

        elements.append(Paragraph("SINDICATO MIXTO \"INTEGRACIÓN TAIPIPLAYA\"", title_style))
        elements.append(Paragraph(f"Reporte de Cobertura — {tipo_pago.nombre}", subtitle_style))

        periodo = ""
        if fecha_inicio or fecha_fin:
            periodo = f"Período: {fecha_inicio or '...'} al {fecha_fin or '...'}"
        else:
            periodo = "Período: Todo el historial"
        elements.append(Paragraph(periodo, subtitle_style))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 8))

        # Resumen tarjetas
        resumen_data = [
            ['Total Recaudado', 'Total Esperado', 'Monto Faltante', 'Ya Pagaron', 'Faltan Pagar', 'Cobertura'],
            [
                f"Bs. {float(total_recaudado):,.2f}",
                f"Bs. {resumen['total_esperado']:,.2f}" if resumen['total_esperado'] is not None else '-',
                f"Bs. {resumen['monto_faltante']:,.2f}" if resumen['monto_faltante'] is not None else '-',
                str(count_pagaron),
                str(count_pendientes),
                f"{cobertura}%"
            ]
        ]
        resumen_table = Table(resumen_data, colWidths=[2.8*cm, 2.8*cm, 2.8*cm, 2.6*cm, 2.6*cm, 2.4*cm])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#e8f5e9')),
            ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#e8f5e9')),
            ('BACKGROUND', (3, 1), (3, 1), colors.HexColor('#ffebee')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, 1), [colors.white]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 10))

        revision_data = [
            ['Indicador de Revisión', 'Cantidad', 'Monto (Bs)'],
            ['Pagos pendientes', str(resumen['count_pagos_pendientes_revision']), f"{resumen['total_pagos_pendientes_revision']:,.2f}"],
            ['Pagos anulados/cancelados', str(resumen['count_pagos_anulados_cancelados']), f"{resumen['total_pagos_anulados_cancelados']:,.2f}"],
            ['Afiliados con pago duplicado', str(resumen['count_afiliados_con_pago_duplicado']), '-'],
            ['Pagos parciales (deuda menor al monto esperado)', str(pendientes_info['count_parciales']), '-'],
        ]
        revision_table = Table(revision_data, colWidths=[8*cm, 4*cm, 4*cm])
        revision_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#455a64')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(revision_table)
        elements.append(Spacer(1, 10))

        # Tabla de pendientes
        elements.append(Paragraph(f"❌ Afiliados que FALTAN Pagar ({count_pendientes})", heading_style))
        if count_pendientes > 0:
            if pendientes_info['monto_total_pendiente'] is not None:
                elements.append(Paragraph(
                    f"Monto total pendiente de pago: Bs. {pendientes_info['monto_total_pendiente']:,.2f}",
                    ParagraphStyle('DeudaTotal', parent=styles['Normal'], fontSize=10,
                                   textColor=colors.HexColor('#9f1239'), alignment=TA_CENTER,
                                   spaceAfter=6),
                ))
            con_deuda = monto_esperado_afiliado is not None
            pend_data = [['#', 'Nombre Completo', 'C.I.', 'Teléfono', 'Pagado (Bs)', 'Monto a Pagar (Bs)']]
            for i, af in enumerate(pendientes_info['pendientes'], 1):
                if con_deuda:
                    monto_celda = f"{af['deuda']:,.2f}" if af['deuda'] is not None else '-'
                    pagado_celda = f"{af['pagado']:,.2f}" if af['pagado'] else '-'
                else:
                    monto_celda = f"{monto_esperado_afiliado or 0:,.2f}"
                    pagado_celda = '-'
                pend_data.append([
                    str(i), af['nombre'], af['ci'], af['telefono'] or '-',
                    pagado_celda, monto_celda,
                ])
            if pendientes_info['monto_total_pendiente'] is not None:
                pend_data.append([
                    '', 'TOTAL A DEUDAR', '', '',
                    f"{resumen['total_recaudado']:,.2f}",
                    f"{pendientes_info['monto_total_pendiente']:,.2f}",
                ])
            pend_table = Table(pend_data, repeatRows=1,
                               colWidths=[1*cm, 6.6*cm, 3.2*cm, 3.2*cm, 2.4*cm, 2.6*cm])
            pend_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c62828')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff8f8')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ])
            if pendientes_info['monto_total_pendiente'] is not None:
                pend_style.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ffebee'))
                pend_style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
            pend_table.setStyle(pend_style)
            elements.append(pend_table)
        else:
            elements.append(Paragraph("✅ ¡Todos los afiliados activos han pagado!", styles['Normal']))

        elements.append(Spacer(1, 16))

        # Tabla de pagados
        elements.append(Paragraph(f"✅ Afiliados que YA Pagaron ({count_pagaron} pagos)", heading_style))
        pagos_ord = pagos_query.order_by('afiliado__apellidos', 'afiliado__nombres', 'fecha_pago')
        if pagos_ord.count() > 0:
            pag_data = [['#', 'Nombre Completo', 'C.I.', 'Fecha Pago', 'Monto (Bs)']]
            for i, pago in enumerate(pagos_ord, 1):
                nombre = pago.afiliado.nombre_completo if pago.afiliado else 'N/A'
                ci = pago.afiliado.ci if pago.afiliado else '-'
                pag_data.append([
                    str(i),
                    nombre,
                    ci,
                    pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '-',
                    f"{float(pago.monto):,.2f}"
                ])
            # Fila total
            pag_data.append(['', 'TOTAL RECAUDADO', '', '', f"Bs. {float(total_recaudado):,.2f}"])
            pag_table = Table(pag_data, colWidths=[1*cm, 7*cm, 3*cm, 3*cm, 2*cm])
            pag_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f1f8e9')]),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(pag_table)

        doc.build(elements)
        buffer.seek(0)
        nombre_archivo = f"reporte_{tipo_pago.nombre.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.pdf"
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={nombre_archivo}'
        return response


class ReporteCategoriaExcelView(APIView):
    """
    Exporta a Excel el reporte por categoría de ingreso o de egreso.
    URL: GET /api/reportes/por-categoria/excel/?tipo=egreso&todas=1&fecha_inicio=...&fecha_fin=...
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from tesoreria.models import Pago, TipoPago
        from afiliados.models import Afiliado
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        tipo_pago_id = request.GET.get('tipo_pago_id')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        todas = request.GET.get('todas') in ['1', 'true', 'True', 'si', 'todos']
        monto_esperado = _get_decimal_param(request, 'monto_esperado')

        if _es_reporte_egresos(request):
            from . import egresos_categoria
            contenido, nombre = egresos_categoria.generar_excel(
                tipo_pago_id=tipo_pago_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                todas=todas,
            )
            if contenido is None:
                status = 404 if 'no encontrada' in nombre else 400
                return Response({'error': nombre}, status=status)
            response = HttpResponse(
                contenido,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = f'attachment; filename={nombre}'
            return response

        afiliados_activos = Afiliado.objects.filter(estado='activo', is_active=True)
        total_activos = afiliados_activos.count()

        if todas:
            wb = Workbook()
            ws = wb.active
            ws.title = "Resumen por Categoria"

            header_fill = PatternFill("solid", fgColor="1a237e")
            header_font = Font(color="FFFFFF", bold=True)
            total_fill = PatternFill("solid", fgColor="e8f5e9")
            center = Alignment(horizontal='center', vertical='center')

            ws.merge_cells('A1:K1')
            ws['A1'] = "REPORTE GENERAL POR CATEGORÍAS DE INGRESO"
            ws['A1'].font = Font(color="FFFFFF", bold=True, size=14)
            ws['A1'].fill = header_fill
            ws['A1'].alignment = center

            ws.merge_cells('A2:K2')
            ws['A2'] = f"Período: {fecha_inicio or 'inicio'} al {fecha_fin or 'hoy'}"
            ws['A2'].alignment = center

            ws.merge_cells('A3:K3')
            ws['A3'] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ws['A3'].alignment = center

            ws.append([])
            ws.append(['Categoría', 'Ya Cancelaron', 'Faltan Pagar', 'Afiliados Activos', '% Cobertura', 'Total Recaudado (Bs)', 'Total Esperado (Bs)', 'Monto Faltante (Bs)', 'Pagos Pendientes', 'Anulados/Cancelados', 'Duplicados'])
            for cell in ws[5]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = center

            total_general = 0
            total_esperado_general = 0
            total_faltante_general = 0
            total_pendientes_general = 0
            activos = list(afiliados_activos.only('id', 'nombres', 'apellidos', 'ci', 'telefono'))
            pendientes_por_categoria = {}
            for tipo_pago in TipoPago.objects.filter(tipo='ingreso').order_by('nombre'):
                resumen = _resumen_categoria(Pago, tipo_pago, total_activos, fecha_inicio, fecha_fin, monto_esperado)
                pendientes = _pendientes_por_categoria(
                    Pago, tipo_pago, fecha_inicio, fecha_fin, monto_esperado, activos, limite=None
                )
                total_general += resumen['total_recaudado']
                total_pendientes_general += pendientes['count_pendientes']
                if resumen['total_esperado'] is not None:
                    total_esperado_general += resumen['total_esperado']
                    # El faltante usa la deuda real por afiliado (idéntico al detalle).
                    resumen['monto_faltante'] = pendientes['monto_total_pendiente']
                    total_faltante_general += resumen['monto_faltante']
                pendientes_por_categoria[tipo_pago.id] = pendientes

                ws.append([
                    tipo_pago.nombre,
                    resumen['count_pagaron'],
                    pendientes['count_pendientes'],
                    resumen['total_afiliados_activos'],
                    f"{resumen['porcentaje_cobertura']}%",
                    resumen['total_recaudado'],
                    resumen['total_esperado'] if resumen['total_esperado'] is not None else '',
                    resumen['monto_faltante'] if resumen['monto_faltante'] is not None else '',
                    resumen['count_pagos_pendientes_revision'],
                    resumen['count_pagos_anulados_cancelados'],
                    resumen['count_afiliados_con_pago_duplicado'],
                ])

            total_row = ws.max_row + 1
            ws.cell(row=total_row, column=1, value='TOTAL GENERAL')
            ws.cell(row=total_row, column=3, value=total_pendientes_general)
            ws.cell(row=total_row, column=6, value=float(total_general))
            if monto_esperado is not None:
                ws.cell(row=total_row, column=7, value=float(total_esperado_general))
                ws.cell(row=total_row, column=8, value=float(total_faltante_general))
            for col in range(1, 12):
                ws.cell(row=total_row, column=col).font = Font(bold=True)
                ws.cell(row=total_row, column=col).fill = total_fill

            for col_letter, width in [('A', 38), ('B', 16), ('C', 16), ('D', 18), ('E', 14), ('F', 20), ('G', 20), ('H', 20), ('I', 18), ('J', 20), ('K', 14)]:
                ws.column_dimensions[col_letter].width = width

            ws_pag = wb.create_sheet("Pagos Completados")
            ws_pag.append(['Categoría', 'Afiliado', 'C.I.', 'Teléfono', 'Fecha Pago', 'Monto (Bs)', 'Nro. Recibo'])
            for cell in ws_pag[1]:
                cell.fill = PatternFill("solid", fgColor="2e7d32")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = center

            ws_faltan = wb.create_sheet("Faltan Pagar")
            ws_faltan.append(['Categoría', 'Afiliado', 'C.I.', 'Teléfono', 'Pagado (Bs)',
                              'Monto a Pagar (Bs)', 'Deuda (Bs)', 'Deuda Total Categoría (Bs)'])
            for cell in ws_faltan[1]:
                cell.fill = PatternFill("solid", fgColor="c62828")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = center

            ws_rev = wb.create_sheet("Revision")
            ws_rev.append(['Tipo Alerta', 'Categoría', 'Afiliado', 'C.I.', 'Fecha Pago', 'Monto (Bs)', 'Estado', 'Nro. Recibo', 'Detalle'])
            for cell in ws_rev[1]:
                cell.fill = PatternFill("solid", fgColor="455a64")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = center

            monto_esperado_afiliado = float(monto_esperado) if monto_esperado is not None else None
            for tipo_pago in TipoPago.objects.filter(tipo='ingreso').order_by('nombre'):
                pagos_completados = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['completado'])

                for pago in pagos_completados.order_by('afiliado__apellidos', 'afiliado__nombres', 'fecha_pago'):
                    ws_pag.append([
                        tipo_pago.nombre,
                        pago.afiliado.nombre_completo if pago.afiliado else 'N/A',
                        pago.afiliado.ci if pago.afiliado else '',
                        pago.afiliado.telefono if pago.afiliado else '',
                        pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '',
                        float(pago.monto),
                        pago.nro_recibo or '',
                    ])

                pendientes = pendientes_por_categoria.get(tipo_pago.id) or {}
                for af in pendientes.get('pendientes') or []:
                    ws_faltan.append([
                        tipo_pago.nombre,
                        af['nombre'],
                        af['ci'],
                        af['telefono'] or '',
                        af['pagado'],
                        monto_esperado_afiliado if monto_esperado_afiliado is not None else '',
                        af['deuda'] if af['deuda'] is not None else '',
                        pendientes.get('monto_total_pendiente')
                        if pendientes.get('monto_total_pendiente') is not None else '',
                    ])

                pagos_revision = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['pendiente', 'anulado', 'cancelado'])
                for pago in pagos_revision.order_by('estado', 'afiliado__apellidos', 'afiliado__nombres'):
                    ws_rev.append([
                        'Pago pendiente/anulado',
                        tipo_pago.nombre,
                        pago.afiliado.nombre_completo if pago.afiliado else 'N/A',
                        pago.afiliado.ci if pago.afiliado else '',
                        pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '',
                        float(pago.monto),
                        pago.estado,
                        pago.nro_recibo or '',
                        pago.motivo_anulacion or '',
                    ])

                duplicados = pagos_completados.values('afiliado_id').annotate(
                    cantidad=Count('id'), total=Sum('monto')
                ).filter(cantidad__gt=1).order_by('-total')
                for item in duplicados:
                    afiliado = Afiliado.objects.filter(id=item['afiliado_id']).only(
                        'id', 'nombres', 'apellidos', 'ci'
                    ).first()
                    ws_rev.append([
                        'Posible duplicado',
                        tipo_pago.nombre,
                        afiliado.nombre_completo if afiliado else 'N/A',
                        afiliado.ci if afiliado else '',
                        '',
                        float(item['total'] or 0),
                        'completado',
                        '',
                        f"{item['cantidad']} pagos completados para el mismo afiliado",
                    ])

            for sheet in [ws_pag, ws_faltan, ws_rev]:
                for column_cells in sheet.columns:
                    column_letter = column_cells[0].column_letter
                    sheet.column_dimensions[column_letter].width = min(max(len(str(cell.value or '')) for cell in column_cells) + 2, 45)

            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename=reporte_categorias_{datetime.now().strftime("%Y%m%d")}.xlsx'
            wb.save(response)
            return response

        if not tipo_pago_id:
            return Response({'error': 'Se requiere tipo_pago_id'}, status=400)

        try:
            tipo_pago = TipoPago.objects.get(id=tipo_pago_id, tipo='ingreso')
        except TipoPago.DoesNotExist:
            return Response({'error': 'Categoría no encontrada'}, status=404)

        pagos_query = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['completado'])
        total_recaudado = pagos_query.aggregate(total=Sum('monto'))['total'] or 0
        resumen = _resumen_categoria(Pago, tipo_pago, total_activos, fecha_inicio, fecha_fin, monto_esperado)

        pendientes_info = _pendientes_por_categoria(
            Pago, tipo_pago, fecha_inicio, fecha_fin, monto_esperado, list(afiliados_activos), limite=None
        )
        if pendientes_info['monto_total_pendiente'] is not None:
            resumen['monto_faltante'] = pendientes_info['monto_total_pendiente']

        count_pagaron = resumen['count_pagaron']
        cobertura = resumen['porcentaje_cobertura']

        wb = Workbook()

        # --- Hoja 1: Resumen ---
        ws_res = wb.active
        ws_res.title = "Resumen"

        header_fill = PatternFill("solid", fgColor="1a237e")
        header_font = Font(color="FFFFFF", bold=True, size=12)
        green_fill = PatternFill("solid", fgColor="2e7d32")
        red_fill = PatternFill("solid", fgColor="c62828")
        green_light = PatternFill("solid", fgColor="e8f5e9")
        red_light = PatternFill("solid", fgColor="ffebee")
        bold_font = Font(bold=True)
        center = Alignment(horizontal='center', vertical='center')

        ws_res.merge_cells('A1:E1')
        ws_res['A1'] = f"REPORTE DE COBERTURA — {tipo_pago.nombre.upper()}"
        ws_res['A1'].font = Font(color="FFFFFF", bold=True, size=14)
        ws_res['A1'].fill = header_fill
        ws_res['A1'].alignment = center

        periodo_txt = f"Período: {fecha_inicio or 'inicio'} al {fecha_fin or 'hoy'}"
        ws_res.merge_cells('A2:E2')
        ws_res['A2'] = periodo_txt
        ws_res['A2'].alignment = center

        ws_res.merge_cells('A3:E3')
        ws_res['A3'] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws_res['A3'].alignment = center

        ws_res.append([])
        ws_res.append(['INDICADOR', 'VALOR'])
        ws_res['A5'].font = bold_font
        ws_res['B5'].font = bold_font
        ws_res['A5'].fill = header_fill
        ws_res['A5'].font = Font(color="FFFFFF", bold=True)
        ws_res['B5'].fill = header_fill
        ws_res['B5'].font = Font(color="FFFFFF", bold=True)

        resumen_rows = [
            ('Total Afiliados Activos', total_activos),
            ('Afiliados que Pagaron', count_pagaron),
            ('Afiliados Pendientes', pendientes_info['count_pendientes']),
            ('  de los cuales pagan parcial', pendientes_info['count_parciales']),
            ('  de los cuales no pagan nada', pendientes_info['count_sin_pago']),
            ('% Cobertura', f"{cobertura}%"),
            ('Total Recaudado (Bs)', float(total_recaudado)),
            ('Monto Esperado por Afiliado (Bs)', resumen['monto_esperado_por_afiliado'] or ''),
            ('Total Esperado (Bs)', resumen['total_esperado'] or ''),
            ('Monto Faltante (Bs)', resumen['monto_faltante'] or ''),
            ('Pagos Pendientes de Revisión', resumen['count_pagos_pendientes_revision']),
            ('Pagos Anulados/Cancelados', resumen['count_pagos_anulados_cancelados']),
            ('Afiliados con Posible Duplicado', resumen['count_afiliados_con_pago_duplicado']),
        ]
        for label, val in resumen_rows:
            ws_res.append([label, val])

        ws_res.column_dimensions['A'].width = 30
        ws_res.column_dimensions['B'].width = 20

        # --- Hoja 2: Ya Pagaron ---
        ws_pag = wb.create_sheet("Ya Pagaron")
        ws_pag.append(['#', 'Nombre Completo', 'C.I.', 'Teléfono', 'Fecha de Pago', 'Monto (Bs)', 'Estado', 'Nro. Recibo'])
        for cell in ws_pag[1]:
            cell.fill = green_fill
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = center

        for i, pago in enumerate(pagos_query.order_by('afiliado__apellidos', 'afiliado__nombres', 'fecha_pago'), 1):
            ws_pag.append([
                i,
                pago.afiliado.nombre_completo if pago.afiliado else 'N/A',
                pago.afiliado.ci if pago.afiliado else '-',
                pago.afiliado.telefono if pago.afiliado else '-',
                pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '-',
                float(pago.monto),
                pago.estado,
                pago.nro_recibo or '-',
            ])

        # Fila de total
        total_row = ws_pag.max_row + 1
        ws_pag.cell(row=total_row, column=1, value='TOTAL')
        ws_pag.cell(row=total_row, column=6, value=float(total_recaudado))
        for col in range(1, 9):
            ws_pag.cell(row=total_row, column=col).font = bold_font
            ws_pag.cell(row=total_row, column=col).fill = green_light

        for col_letter, width in [('A', 5), ('B', 35), ('C', 15), ('D', 15), ('E', 15), ('F', 15), ('G', 15), ('H', 12)]:
            ws_pag.column_dimensions[col_letter].width = width

        # --- Hoja 3: Pendientes ---
        monto_esperado_afiliado = resumen['monto_esperado_por_afiliado']
        ws_pend = wb.create_sheet("Pendientes")
        if monto_esperado_afiliado is not None:
            ws_pend.append(['#', 'Nombre Completo', 'C.I.', 'Teléfono',
                            f'Monto a Pagar (Bs)', 'Pagado (Bs)', 'Deuda (Bs)'])
        else:
            ws_pend.append(['#', 'Nombre Completo', 'C.I.', 'Teléfono'])
        for cell in ws_pend[1]:
            cell.fill = red_fill
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = center

        total_columnas = 7 if monto_esperado_afiliado is not None else 4
        for i, af in enumerate(pendientes_info['pendientes'], 1):
            fila = [i, af['nombre'], af['ci'], af['telefono'] or '-']
            if monto_esperado_afiliado is not None:
                fila += [monto_esperado_afiliado, af['pagado'],
                         af['deuda'] if af['deuda'] is not None else '']
            ws_pend.append(fila)
            if i % 2 == 0:
                for col in range(1, total_columnas + 1):
                    ws_pend.cell(row=i + 1, column=col).fill = red_light

        if pendientes_info['monto_total_pendiente'] is not None:
            fila_total = ws_pend.max_row + 1
            ws_pend.cell(row=fila_total, column=1, value='TOTAL')
            ws_pend.cell(row=fila_total, column=6, value=float(total_recaudado))
            ws_pend.cell(row=fila_total, column=7,
                         value=float(pendientes_info['monto_total_pendiente']))
            for col in range(1, total_columnas + 1):
                ws_pend.cell(row=fila_total, column=col).font = bold_font
                ws_pend.cell(row=fila_total, column=col).fill = red_light

        for col_letter, width in [('A', 5), ('B', 35), ('C', 15), ('D', 15), ('E', 18), ('F', 15), ('G', 15)]:
            ws_pend.column_dimensions[col_letter].width = width

        # --- Hoja 4: Revisión ---
        ws_rev = wb.create_sheet("Revision")
        ws_rev.append(['Tipo Alerta', 'Nombre Completo', 'C.I.', 'Fecha Pago', 'Monto (Bs)', 'Estado', 'Nro. Recibo', 'Detalle'])
        for cell in ws_rev[1]:
            cell.fill = PatternFill("solid", fgColor="455a64")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = center

        pagos_revision = _filtrar_pagos_categoria(Pago, tipo_pago, fecha_inicio, fecha_fin, ['pendiente', 'anulado', 'cancelado'])
        for pago in pagos_revision.order_by('estado', 'afiliado__apellidos', 'afiliado__nombres'):
            ws_rev.append([
                'Pago pendiente/anulado',
                pago.afiliado.nombre_completo if pago.afiliado else 'N/A',
                pago.afiliado.ci if pago.afiliado else '',
                pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '',
                float(pago.monto),
                pago.estado,
                pago.nro_recibo or '',
                pago.motivo_anulacion or '',
            ])

        duplicados = pagos_query.values('afiliado_id').annotate(
            cantidad=Count('id'), total=Sum('monto')
        ).filter(cantidad__gt=1).order_by('-total')
        for item in duplicados:
            afiliado = Afiliado.objects.filter(id=item['afiliado_id']).only(
                'id', 'nombres', 'apellidos', 'ci'
            ).first()
            ws_rev.append([
                'Posible duplicado',
                afiliado.nombre_completo if afiliado else 'N/A',
                afiliado.ci if afiliado else '',
                '',
                float(item['total'] or 0),
                'completado',
                '',
                f"{item['cantidad']} pagos completados para el mismo afiliado",
            ])

        for col_letter, width in [('A', 24), ('B', 35), ('C', 15), ('D', 15), ('E', 15), ('F', 15), ('G', 12), ('H', 45)]:
            ws_rev.column_dimensions[col_letter].width = width

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        nombre_archivo = f"cobertura_{tipo_pago.nombre.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename={nombre_archivo}'
        wb.save(response)
        return response
