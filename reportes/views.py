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
from reportlab.lib.enums import TA_CENTER


class AfiliadosMorososView(APIView):
    """
    Reporte de afiliados con pagos pendientes.
    URL: GET /api/reportes/afiliados-morosos/?meses=3
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from afiliados.models import Afiliado
        from tesoreria.models import Pago
        from sanciones.models import Sancion
        
        meses_atras = int(request.GET.get('meses', 3))
        fecha_limite = datetime.now() - timedelta(days=30 * meses_atras)
        
        # Obtener todos los afiliados activos
        afiliados = Afiliado.objects.filter(estado='activo', is_active=True)
        
        morosos = []
        for afiliado in afiliados:
            # Calcular deuda total de cuotas pendientes
            try:
                cuotas_pendientes = afiliado.cuotas.filter(estado='pendiente')
                deuda_cuotas = cuotas_pendientes.aggregate(total=Sum('monto'))['total'] or 0
            except:
                deuda_cuotas = 0
            
            # Calcular deuda de sanciones pendientes
            try:
                sanciones_pendientes = afiliado.sanciones.filter(estado='pendiente')
                deuda_sanciones = sanciones_pendientes.aggregate(total=Sum('monto'))['total'] or 0
            except:
                deuda_sanciones = 0
            
            deuda_total = deuda_cuotas + deuda_sanciones
            
            # Si tiene deuda, agregar a la lista
            if deuda_total > 0:
                # Obtener último pago
                try:
                    ultimo_pago = Pago.objects.filter(afiliado=afiliado).order_by('-fecha_pago').first()
                    dias_sin_pagar = (datetime.now().date() - ultimo_pago.fecha_pago).days if ultimo_pago and hasattr(ultimo_pago, 'fecha_pago') else 999
                except:
                    dias_sin_pagar = 999
                
                # Determinar nivel de morosidad
                if dias_sin_pagar > 90:
                    nivel = 'CRÍTICO'
                elif dias_sin_pagar > 60:
                    nivel = 'ALTO'
                elif dias_sin_pagar > 30:
                    nivel = 'MODERADO'
                else:
                    nivel = 'BAJO'
                
                try:
                    cantidad_cuotas = cuotas_pendientes.count()
                except:
                    cantidad_cuotas = 0
                    
                try:
                    cantidad_sanciones = sanciones_pendientes.count()
                except:
                    cantidad_sanciones = 0
                
                try:
                    cantidad_faltas = afiliado.asistencias.filter(estado='falta').count()
                except:
                    cantidad_faltas = 0

                morosos.append({
                    'afiliado_id': afiliado.id,
                    'nombre_completo': afiliado.nombre_completo,
                    'ci': afiliado.ci,
                    'telefono': afiliado.telefono,
                    'deuda_cuotas': float(deuda_cuotas),
                    'deuda_sanciones': float(deuda_sanciones),
                    'deuda_total': float(deuda_total),
                    'cantidad_cuotas_pendientes': cantidad_cuotas,
                    'cantidad_sanciones_pendientes': cantidad_sanciones,
                    'cantidad_faltas': cantidad_faltas,
                    'ultimo_pago': str(ultimo_pago.fecha_pago) if ultimo_pago and hasattr(ultimo_pago, 'fecha_pago') else 'Nunca',
                    'dias_sin_pagar': dias_sin_pagar,
                    'nivel_morosidad': nivel
                })
        
        # Ordenar por deuda total descendente
        morosos.sort(key=lambda x: x['deuda_total'], reverse=True)
        
        # Calcular totales (sobre la lista completa)
        total_deuda = sum(m['deuda_total'] for m in morosos)
        total_items = len(morosos)
        
        # Paginación manual
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
        except ValueError:
            page = 1
            page_size = 20

        start = (page - 1) * page_size
        end = start + page_size
        morosos_paginados = morosos[start:end]
        
        return Response({
            'count': total_items,
            'total_pages': (total_items + page_size - 1) // page_size,
            'current_page': page,
            'page_size': page_size,
            'deuda_total_sistema': float(total_deuda),
            'morosos': morosos_paginados,
            'resumen_por_nivel': {
                'critico': len([m for m in morosos if m['nivel_morosidad'] == 'CRÍTICO']),
                'alto': len([m for m in morosos if m['nivel_morosidad'] == 'ALTO']),
                'moderado': len([m for m in morosos if m['nivel_morosidad'] == 'MODERADO']),
                'bajo': len([m for m in morosos if m['nivel_morosidad'] == 'BAJO'])
            }
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
    URL: GET /api/reportes/balance?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from tesoreria.models import Pago, Egreso
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        # Query base para pagos (ingresos)
        pagos_query = Pago.objects.all()
        
        # Query base para egresos
        egresos_query = Egreso.objects.all()
        
        # Aplicar filtros de fecha si existen
        if fecha_inicio:
            pagos_query = pagos_query.filter(fecha_pago__gte=fecha_inicio)
            egresos_query = egresos_query.filter(fecha__gte=fecha_inicio)
        
        if fecha_fin:
            pagos_query = pagos_query.filter(fecha_pago__lte=fecha_fin)
            egresos_query = egresos_query.filter(fecha__lte=fecha_fin)
        
        # Calcular totales
        total_ingresos = pagos_query.aggregate(total=Sum('monto'))['total'] or 0
        count_ingresos = pagos_query.count()
        
        total_egresos = egresos_query.aggregate(total=Sum('monto'))['total'] or 0
        count_egresos = egresos_query.count()
        
        saldo = total_ingresos - total_egresos
        
        # Calcular gastos por tipo para el desglose
        egresos_por_tipo = egresos_query.values(
            'tipo_pago__nombre'
        ).annotate(
            total=Sum('monto'),
            count=Count('id')
        ).order_by('-total')

        response_data = {
            'total_ingresos': float(total_ingresos),
            'count_ingresos': count_ingresos,
            'total_egresos': float(total_egresos),
            'count_egresos': count_egresos,
            'saldo': float(saldo),
            'egresos_por_tipo': [
                {
                    'tipo': item['tipo_pago__nombre'] or 'Otros',
                    'total': float(item['total']),
                    'count': item['count']
                } for item in egresos_por_tipo
            ]
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
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        tipo = request.GET.get('tipo', 'mensual')
        
        # Filtrar por fechas
        pagos_query = Pago.objects.all()
        egresos_query = Egreso.objects.all()
        
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
    Lista de todas las transacciones (ingresos y egresos).
    URL: GET /api/reportes/transacciones?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from tesoreria.models import Pago, Egreso
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        # Obtener pagos
        pagos_query = Pago.objects.select_related('afiliado', 'tipo_pago').all()
        if fecha_inicio:
            pagos_query = pagos_query.filter(fecha_pago__gte=fecha_inicio)
        if fecha_fin:
            pagos_query = pagos_query.filter(fecha_pago__lte=fecha_fin)
        
        # Obtener egresos
        egresos_query = Egreso.objects.all()
        if fecha_inicio:
            egresos_query = egresos_query.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            egresos_query = egresos_query.filter(fecha__lte=fecha_fin)
        
        # Convertir a lista de transacciones
        transacciones = []
        
        for pago in pagos_query:
            transacciones.append({
                'fecha': str(pago.fecha_pago) if pago.fecha_pago else 'N/A',
                'tipo': 'INGRESO',
                'afiliado': pago.afiliado.nombre_completo if pago.afiliado else 'N/A',
                'tipo_pago': pago.tipo_pago.nombre if pago.tipo_pago else 'N/A',
                'descripcion': pago.observaciones or 'Pago',
                'monto': float(pago.monto or 0)
            })
        
        for egreso in egresos_query:
            transacciones.append({
                'fecha': str(egreso.fecha) if egreso.fecha else 'N/A',
                'tipo': 'EGRESO',
                'afiliado': None,
                'tipo_pago': None,
                'descripcion': egreso.descripcion or 'Egreso',
                'monto': float(egreso.monto or 0)
            })
        
        # Ordenar por fecha descendente
        transacciones.sort(key=lambda x: x['fecha'], reverse=True)
        
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
        
        # 1. Ingresos y Egresos del mes actual
        ingresos_mes = Pago.objects.filter(fecha_pago__gte=inicio_mes).aggregate(total=Sum('monto'))['total'] or 0
        egresos_mes = Egreso.objects.filter(fecha__gte=inicio_mes).aggregate(total=Sum('monto'))['total'] or 0
        saldo_mes = ingresos_mes - egresos_mes
        
        # 2. Porcentaje de cambio ingresos vs mes anterior
        ingresos_mes_anterior = Pago.objects.filter(
            fecha_pago__gte=inicio_mes_anterior, 
            fecha_pago__lte=ultimo_dia_mes_anterior
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
        ingresos_7 = Pago.objects.filter(fecha_pago__gte=siete_dias).aggregate(total=Sum('monto'))['total'] or 0
        egresos_7 = Egreso.objects.filter(fecha__gte=siete_dias).aggregate(total=Sum('monto'))['total'] or 0
        
        top_tipos = Pago.objects.values('tipo_pago__nombre').annotate(total=Sum('monto')).order_by('-total')[:5]
        
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
        from tesoreria.models import Pago, Egreso
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        pagos = Pago.objects.select_related('afiliado', 'tipo_pago').all()
        egresos = Egreso.objects.all()
        
        if fecha_inicio:
            pagos = pagos.filter(fecha_pago__gte=fecha_inicio)
            egresos = egresos.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            pagos = pagos.filter(fecha_pago__lte=fecha_fin)
            egresos = egresos.filter(fecha__lte=fecha_fin)
            
        wb = Workbook()
        ws = wb.active
        ws.title = "Transacciones"
        
        headers = ['Fecha', 'Tipo', 'Afiliado', 'Tipo Pago', 'Descripción', 'Monto (Bs)']
        ws.append(headers)
        
        # Combinar y ordenar
        transacciones = []
        for p in pagos:
            transacciones.append([
                p.fecha_pago.strftime('%Y-%m-%d') if p.fecha_pago else '',
                'INGRESO',
                p.afiliado.nombre_completo if p.afiliado else 'N/A',
                p.tipo_pago.nombre if p.tipo_pago else 'N/A',
                p.observaciones or 'Pago',
                float(p.monto)
            ])
        for e in egresos:
            transacciones.append([
                e.fecha.strftime('%Y-%m-%d') if e.fecha else '',
                'EGRESO',
                'N/A',
                'N/A',
                e.descripcion or 'Egreso',
                float(e.monto)
            ])
            
        transacciones.sort(key=lambda x: x[0], reverse=True)
        for t in transacciones:
            ws.append(t)
            
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=transacciones_{datetime.now().strftime("%Y%m%d")}.xlsx'
        wb.save(response)
        return response

class TransaccionesPDFView(APIView):
    """
    Exporta todas las transacciones a PDF.
    URL: GET /api/reportes/transacciones/pdf
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from tesoreria.models import Pago, Egreso
        
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        pagos = Pago.objects.select_related('afiliado', 'tipo_pago').all()
        egresos = Egreso.objects.all()
        
        if fecha_inicio:
            pagos = pagos.filter(fecha_pago__gte=fecha_inicio)
            egresos = egresos.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            pagos = pagos.filter(fecha_pago__lte=fecha_fin)
            egresos = egresos.filter(fecha__lte=fecha_fin)
            
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
        
        elements.append(Paragraph("DETALLE DE TRANSACCIONES (INGRESOS Y EGRESOS)", title_style))
        if fecha_inicio or fecha_fin:
            rango = f"Período: {fecha_inicio or '...'} al {fecha_fin or '...'}"
            elements.append(Paragraph(rango, styles['Normal']))
            elements.append(Spacer(1, 10))
            
        data = [['Fecha', 'Tipo', 'Afiliado', 'Tipo Pago', 'Descripción', 'Monto (Bs)']]
        
        transacciones = []
        for p in pagos:
            transacciones.append([
                p.fecha_pago.strftime('%Y-%m-%d') if p.fecha_pago else '',
                'INGRESO',
                p.afiliado.nombre_completo if p.afiliado else 'N/A',
                p.tipo_pago.nombre if p.tipo_pago else 'N/A',
                p.observaciones or 'Pago',
                float(p.monto)
            ])
        for e in egresos:
            transacciones.append([
                e.fecha.strftime('%Y-%m-%d') if e.fecha else '',
                'EGRESO',
                'N/A',
                'N/A',
                e.descripcion or 'Egreso',
                float(e.monto)
            ])
            
        transacciones.sort(key=lambda x: x[0], reverse=True)
        for t in transacciones:
            data.append(t)
            
        table = Table(data, repeatRows=1, colWidths=[80, 70, 180, 120, 200, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        elements.append(table)
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
