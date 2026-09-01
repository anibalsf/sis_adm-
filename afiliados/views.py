from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Afiliado
from .serializers import AfiliadoSerializer
from sistema.permissions import IsSecretariaOrDirectivaOrReadOnly
from pagos_qr.services import QRService
from cuotas.models import Cuota
from sanciones.models import Sancion
from hojasruta.models import HojaRuta
from tesoreria.models import Pago
from django.utils import timezone

class AfiliadoViewSet(viewsets.ModelViewSet):
    queryset = Afiliado.objects.all()
    serializer_class = AfiliadoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ci', 'apellidos', 'nombres', 'telefono', 'direccion']
    ordering_fields = ['apellidos', 'nombres', 'ci', 'fecha_ingreso']
    permission_classes = [IsSecretariaOrDirectivaOrReadOnly]

    def get_queryset(self):
        queryset = Afiliado.objects.all()
        
        # Filtro para solo mostrar afiliados elegibles para Agente de Parada
        if self.request.query_params.get('para_agente_parada') == 'true':
            from django.db.models import Q
            la_paz_ids = Afiliado.objects.filter(
                Q(vehiculos__tipo__iexact='IPSUM') | Q(vehiculos__tipo__iexact='MINIBUS'),
                vehiculos__indocumentado=False
            ).values_list('id', flat=True)
            
            convenio_ids = Afiliado.objects.filter(
                vehiculos__es_convenio_caranavi=True
            ).values_list('id', flat=True)
            
            queryset = queryset.filter(estado='activo', is_active=True).exclude(id__in=la_paz_ids).exclude(id__in=convenio_ids).distinct()
            
        return queryset

    @action(detail=False, methods=['get'])
    def reporte(self, request):
        """Generar reporte PDF de afiliados"""
        import io
        from django.http import FileResponse
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        elements.append(Paragraph("Reporte General de Afiliados", styles['Title']))
        elements.append(Spacer(1, 12))

        # Datos
        data = [['Apellidos', 'Nombres', 'CI', 'Teléfono', 'Estado']]
        for afiliado in self.queryset.all().order_by('apellidos'):
            data.append([
                afiliado.apellidos,
                afiliado.nombres,
                afiliado.ci,
                afiliado.telefono,
                afiliado.estado.capitalize()
            ])

        # Tabla
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='afiliados.pdf')

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Exportar lista de afiliados a Excel"""
        from openpyxl import Workbook
        from django.http import HttpResponse
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Afiliados"
        
        # Estilos y encabezados
        headers = ['ID', 'Nombres', 'Apellidos', 'CI', 'Teléfono', 'Email', 'Estado', 'Fecha Ingreso']
        ws.append(headers)
        
        # Datos
        for obj in self.get_queryset().order_by('apellidos'):
            ws.append([
                obj.id,
                obj.nombres,
                obj.apellidos,
                obj.ci,
                obj.telefono,
                obj.email,
                obj.estado.capitalize() if obj.estado else '',
                obj.fecha_ingreso.strftime('%Y-%m-%d') if obj.fecha_ingreso else ''
            ])
            
        # Formatear encabezados (opcional pero profesional)
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=afiliados.xlsx'
        wb.save(response)
        return response

    @action(detail=False, methods=['get'])
    def lista_turno_la_paz(self, request):
        """
        Retorna la lista de afiliados activos con vehículos IPSUM/MINIBUS 
        con placa (no indocumentados) para el turno a La Paz.
        """
        from django.db.models import Q
        queryset = Afiliado.objects.filter(
            estado='activo',
            is_active=True
        ).filter(
            Q(vehiculos__tipo__iexact='IPSUM') | Q(vehiculos__tipo__iexact='MINIBUS')
        ).filter(
            vehiculos__indocumentado=False
        ).distinct().order_by('apellidos', 'nombres')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def generar_lista_punteros(self, request):
        """Generar lista de punteros (rotación de turnos) en PDF"""
        import io
        from datetime import datetime, timedelta
        from django.http import FileResponse
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch,
                                leftMargin=0.5*inch, rightMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()

        # Estilo personalizado para título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        # Encabezado
        elements.append(Paragraph("SINDICATO MIXTO INTEGRACIÓN TAIPIPLAYA", title_style))
        elements.append(Paragraph("LISTA DE PUNTEROS - PROGRAMACIÓN DE TURNOS", title_style))
        elements.append(Spacer(1, 20))

        # Obtener solo afiliados activos que NO tienen vehiculo indocumentado (que pueden ir a La Paz)
        # Y que NO son de convenio caranavi
        from django.db.models import Q
        afiliados_activos = list(Afiliado.objects.filter(
            estado='activo',
            is_active=True
        ).filter(
            Q(vehiculos__tipo__iexact='IPSUM') | Q(vehiculos__tipo__iexact='MINIBUS')
        ).filter(
            vehiculos__indocumentado=False
        ).exclude(vehiculos__es_convenio_caranavi=True).distinct().order_by('apellidos', 'nombres'))

        if not afiliados_activos:
            elements.append(Paragraph("No hay afiliados activos para generar la programación.", styles['Normal']))
        else:
            # Generar programación para días laborables (lunes a viernes)
            fecha_actual = datetime.now().date()
            dias_laborables_necesarios = 30  # Cantidad de días laborables a programar
            afiliados_por_dia = 3  # Número de afiliados por día
            
            data = []
            afiliado_idx = 0
            total_afiliados = len(afiliados_activos)
            dias_generados = 0
            dia_offset = 0

            while dias_generados < dias_laborables_necesarios:
                fecha = fecha_actual + timedelta(days=dia_offset)
                dia_offset += 1
                
                # Saltar sábados (5) y domingos (6)
                # weekday(): 0=lunes, 1=martes, 2=miércoles, 3=jueves, 4=viernes, 5=sábado, 6=domingo
                if fecha.weekday() >= 5:
                    continue
                
                fecha_str = fecha.strftime("%d/%m/%Y")
                
                # Encabezado amarillo para cada grupo de fecha
                data.append([
                    Paragraph('<b>FECHA</b>', styles['Normal']),
                    Paragraph('<b>N.</b>', styles['Normal']),
                    Paragraph('<b>NOMBRE</b>', styles['Normal'])
                ])
                
                # Agregar afiliados para esta fecha
                for n in range(1, afiliados_por_dia + 1):
                    afiliado = afiliados_activos[afiliado_idx % total_afiliados]
                    nombre_completo = f"{afiliado.apellidos} {afiliado.nombres}".upper()
                    
                    if n == 1:
                        # Primera fila: mostrar fecha
                        data.append([fecha_str, str(n), nombre_completo])
                    else:
                        # Filas siguientes: celda de fecha vacía
                        data.append(['', str(n), nombre_completo])
                    
                    afiliado_idx += 1
                
                dias_generados += 1

            # Crear tabla con diseño compacto
            col_widths = [1.5*inch, 0.5*inch, 4*inch]
            table = Table(data, colWidths=col_widths, repeatRows=0)
            
            # Aplicar estilos
            table_style = [
                # Bordes
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]
            
            # Aplicar fondo amarillo a las filas de encabezado y alinear
            row_idx = 0
            for dia in range(dias_generados):
                # Encabezado de fecha (fondo amarillo)
                table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#FFD700')))
                table_style.append(('ALIGN', (0, row_idx), (-1, row_idx), 'CENTER'))
                table_style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
                row_idx += 1
                
                # Filas de afiliados para esta fecha
                for n in range(afiliados_por_dia):
                    table_style.append(('ALIGN', (0, row_idx), (0, row_idx), 'CENTER'))  # Fecha centrada
                    table_style.append(('ALIGN', (1, row_idx), (1, row_idx), 'CENTER'))  # N. centrado
                    table_style.append(('ALIGN', (2, row_idx), (2, row_idx), 'LEFT'))    # Nombre izquierda
                    row_idx += 1
            
            table.setStyle(TableStyle(table_style))
            elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='lista_punteros.pdf')

    @action(detail=False, methods=['post'])
    def generar_turnos(self, request):
        """
        Genera turnos para Agentes de Parada y los guarda en base de datos.
        """
        from datetime import datetime, timedelta
        from .models import TurnoAgente

        # 1. Determinar fecha de inicio
        # Si ya hay turnos, empezar después del último. Si no, empezar hoy.
        ultimo_turno = TurnoAgente.objects.order_by('-fecha').first()
        if ultimo_turno:
            fecha_inicio = ultimo_turno.fecha + timedelta(days=1)
        else:
            fecha_inicio = datetime.now().date()
            
        # 2. Obtener afiliados activos
        # EXCLUIR: 
        # - Los que van a La Paz (Ipsum/Minibus con placa)
        # - Los de Convenio Integración Caranavi
        from django.db.models import Q
        
        la_paz_ids = Afiliado.objects.filter(
            Q(vehiculos__tipo__iexact='IPSUM') | Q(vehiculos__tipo__iexact='MINIBUS'),
            vehiculos__indocumentado=False
        ).values_list('id', flat=True)
        
        convenio_ids = Afiliado.objects.filter(
            vehiculos__es_convenio_caranavi=True
        ).values_list('id', flat=True)

        afiliados = list(Afiliado.objects.filter(
            estado='activo', 
            is_active=True
        ).exclude(id__in=la_paz_ids).exclude(id__in=convenio_ids).distinct().order_by('apellidos', 'nombres'))
        
        if not afiliados:
            return Response({'detail': 'No hay afiliados disponibles para Agente de Parada (la mayoría están en La Paz o Convenio)'}, status=400)

        # 3. Calcular índice de rotación
        # Si continuamos, debemos saber a quién le toca.
        # Una forma simple: (total_turnos_historicos) % total_afiliados
        total_historico = TurnoAgente.objects.count()
        idx_actual = total_historico % len(afiliados)
        
        # 4. Generar turnos para 365 días laborables (aprox un año calendario)
        turnos_creados = []
        dias_a_generar = 365
        dias_generados = 0
        dia_offset = 0
        
        while dias_generados < dias_a_generar:
            fecha = fecha_inicio + timedelta(days=dia_offset)
            dia_offset += 1
            
            # Excluir fin de semana (5=Sab, 6=Dom)
            if fecha.weekday() >= 5:
                continue
                
            afiliado_toca = afiliados[idx_actual % len(afiliados)]
            
            TurnoAgente.objects.create(
                fecha=fecha,
                afiliado=afiliado_toca
            )
            turnos_creados.append(f"{fecha}: {afiliado_toca}")
            
            dias_generados += 1
            idx_actual += 1
            
        return Response({'detail': f'Se generaron {len(turnos_creados)} turnos nuevos.', 'muestra': turnos_creados[:5]})

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def turno_del_dia(self, request):
        """
        Retorna el Agente de Parada asignado para una fecha específica.
        Query param: ?fecha=YYYY-MM-DD
        Público: accesible sin autenticación (para la página de reservas con QR).
        """
        from .models import TurnoAgente
        fecha_str = request.query_params.get('fecha')
        if not fecha_str:
            return Response({'detail': 'Fecha requerida'}, status=400)
            
        try:
            turno = TurnoAgente.objects.filter(fecha=fecha_str).first()
            if turno:
                return Response({
                    'found': True,
                    'afiliado': {
                        'id': turno.afiliado.id,
                        'nombre_completo': turno.afiliado.nombre_completo,
                        'ci': turno.afiliado.ci,
                        'telefono': turno.afiliado.telefono
                    }
                })
            else:
                return Response({'found': False, 'detail': 'No hay turno asignado para esta fecha'})
        except Exception as e:
            return Response({'detail': str(e)}, status=400)

    @action(detail=False, methods=['get'])
    def generar_nomina_agentes(self, request):
        """Generar nómina de agentes (basado en DB) en PDF"""
        import io
        from django.http import FileResponse
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER
        from .models import TurnoAgente
        from datetime import date

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch,
                                leftMargin=0.5*inch, rightMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.black,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(f"NÓMINA DE AGENTE DE PARADA {date.today().year}", title_style))
        elements.append(Spacer(1, 15))

        # Obtener turnos futuros desde hoy
        hoy = date.today()
        turnos = TurnoAgente.objects.filter(fecha__gte=hoy).select_related('afiliado').order_by('fecha')[:30] # Próximos 30 días laborables

        if not turnos.exists():
             elements.append(Paragraph("No hay turnos generados. Por favor genere los turnos primero.", styles['Normal']))
        else:
            data = []
            data.append([
                Paragraph('<b>Nº</b>', styles['Normal']),
                Paragraph('<b>FECHA</b>', styles['Normal']),
                Paragraph('<b>NOMBRE Y APELLIDO</b>', styles['Normal']),
                Paragraph('<b>OBSERVACIONES</b>', styles['Normal'])
            ])
            
            for idx, turno in enumerate(turnos, 1):
                fecha_str = turno.fecha.strftime("%d/%m/%Y")
                nombre = turno.afiliado.nombre_completo.upper()
                data.append([
                    str(idx),
                    fecha_str,
                    nombre,
                    turno.observacion
                ])
                
            col_widths = [0.5*inch, 1.2*inch, 3*inch, 1.8*inch]
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFD700')),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),
                ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#FFB6C1')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(table)
            
            # Notas al pie
            elements.append(Spacer(1, 15))
            nota_style = ParagraphStyle('Nota', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
            elements.append(Paragraph(
                "<b>Nota:</b> el agente de turno debe estar en la parada a horas 4 a.m., anotarse a las 6 a.m. y entrar en carril a las 7 a.m.",
                nota_style
            ))
            elements.append(Spacer(1, 5))
            elements.append(Paragraph(
                "<b>AFILIADO QUE NO CUMPLA SERÁ SANCIONADO CON 50 BS.</b>",
                nota_style
            ))

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='nomina_agentes.pdf')

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mi_perfil(self, request):
        """
        Retorna la información del afiliado autenticado, incluyendo deudas pendientes.
        """
        try:
            afiliado = request.user.afiliado
        except Exception:
            if request.user.is_superuser or request.user.is_staff:
                return Response({
                    'detail': f'Hola {request.user.username}, eres Administrador/Staff. '
                              'Este módulo es para Afiliados. Como administrador no tienes un perfil de afiliado ni deudas asociadas.',
                    'is_admin': True
                }, status=200) # Devolvemos 200 con flag de admin
            return Response({'detail': 'No se encontró un perfil de afiliado asociado a este usuario. Si eres un nuevo afiliado, por favor solicita que vinculen tu cuenta.'}, status=404)

        # 1. Datos básicos
        data = AfiliadoSerializer(afiliado).data

        # 2. Deudas pendientes (Cuotas)
        cuotas_pendientes = Cuota.objects.filter(afiliado=afiliado, estado='pendiente').order_by('-periodo')
        data['cuotas_pendientes'] = [{
            'id': c.id,
            'periodo': c.periodo,
            'monto': str(c.monto),
            'tipo': c.tipo
        } for c in cuotas_pendientes]

        # 3. Sanciones pendientes
        sanciones_pendientes = Sancion.objects.filter(
            afiliado=afiliado, 
            estado__in=['pendiente', 'notificada']
        ).order_by('-created_at')
        data['sanciones_pendientes'] = [{
            'id': s.id,
            'tipo': s.tipo,
            'motivo': s.motivo,
            'monto': str(s.monto),
            'fecha': s.created_at,
            'estado': s.estado
        } for s in sanciones_pendientes]

        # 4. Hojas de ruta recientes (Sus viajes)
        hojas_recientes_qs = HojaRuta.objects.filter(
            afiliado=afiliado
        ).order_by('-fecha_salida', '-id')
        
        # Encontrar hoja de HOY específicamente para mostrarla en el Dashboard del Chofer
        hoy = timezone.now().date()
        hoja_hoy = hojas_recientes_qs.filter(fecha_salida=hoy).first()
        
        data['hoja_hoy'] = {
            'id': hoja_hoy.id,
            'nro': hoja_hoy.nro,
            'fecha': hoja_hoy.fecha_salida,
            'ruta': hoja_hoy.ruta.nombre if hoja_hoy.ruta else 'N/A',
            'estado': hoja_hoy.estado,
            'precio': str(hoja_hoy.precio),
            'qr_url': f"/verificar-hoja/{hoja_hoy.id}"
        } if hoja_hoy else None

        data['hojas_recientes'] = [{
            'id': h.id,
            'nro': h.nro,
            'fecha_salida': h.fecha_salida,
            'ruta': h.ruta.nombre if h.ruta else 'N/A',
            'estado': h.estado,
            'precio': str(h.precio)
        } for h in hojas_recientes_qs[:20]]

        # 5. Historial de Pagos Realizados
        pagos_recientes = Pago.objects.filter(afiliado=afiliado).order_by('-fecha_pago')[:10]
        data['pagos_recientes'] = [{
            'id': p.id,
            'fecha': p.fecha_pago,
            'monto': str(p.monto),
            'tipo': p.tipo_pago.nombre,
            'observaciones': p.observaciones
        } for p in pagos_recientes]

        # 6. Resumen total
        data['total_deuda_cuotas'] = sum(c.monto for c in cuotas_pendientes)
        data['total_deuda_sanciones'] = sum(s.monto for s in sanciones_pendientes)
        data['total_faltas'] = sanciones_pendientes.count()
        data['total_deuda'] = data['total_deuda_cuotas'] + data['total_deuda_sanciones']

        return Response(data)

    @action(detail=True, methods=['post'])
    def generar_pago_qr_total(self, request, pk=None):
        afiliado = self.get_object()
        from cuotas.models import Cuota
        from sanciones.models import Sancion
        
        deuda_cuotas = sum(c.monto for c in Cuota.objects.filter(afiliado=afiliado, estado='pendiente'))
        deuda_sanciones = sum(s.monto for s in Sancion.objects.filter(afiliado=afiliado, estado__in=['pendiente', 'notificada']))
        monto_total = float(deuda_cuotas + deuda_sanciones)
        
        if monto_total <= 0:
            return Response({'error': 'El afiliado no tiene deudas pendientes'}, status=400)
            
        glosa = f"Pago Total Deudas - {afiliado.nombre_completo} - A nombre de: Anibal Choque Aguirre"
        
        qr_obj = QRService.generate_qr(
            monto=monto_total,
            glosa=glosa,
            content_object=afiliado
        )
        
        return Response({
            'qr_string': qr_obj.qr_string,
            'imagen_base64': qr_obj.imagen_base64,
            'transaction_id': qr_obj.transaction_id,
            'monto': qr_obj.monto,
            'glosa': qr_obj.glosa
        })



    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def kiosco_consulta(self, request):
        """
        Consulta rápida para Kiosko mediante CI y Extensión.
        """
        from cuotas.models import Cuota
        from sanciones.models import Sancion
        from .models import TurnoAgente
        from datetime import date

        ci = request.query_params.get('ci')
        ci_exp = request.query_params.get('ci_exp')

        if not ci:
            return Response({'detail': 'CI es requerido'}, status=400)

        afiliado = Afiliado.objects.filter(ci=ci, ci_exp=ci_exp).first() if ci_exp else Afiliado.objects.filter(ci=ci).first()

        if not afiliado:
            return Response({'detail': 'Afiliado no encontrado'}, status=404)

        # 1. Datos básicos
        resumen = {
            'id': afiliado.id,
            'nombre_completo': afiliado.nombre_completo,
            'estado': afiliado.estado,
            'ci_completo': afiliado.ci_completo,
        }

        # 2. Deudas
        deuda_cuotas = sum(c.monto for c in Cuota.objects.filter(afiliado=afiliado, estado='pendiente'))
        deuda_sanciones = sum(s.monto for s in Sancion.objects.filter(afiliado=afiliado, estado__in=['pendiente', 'notificada']))
        
        resumen['finanzas'] = {
            'total_deuda': float(deuda_cuotas + deuda_sanciones),
            'deuda_cuotas': float(deuda_cuotas),
            'deuda_sanciones': float(deuda_sanciones),
            'tiene_deuda': (deuda_cuotas + deuda_sanciones) > 0
        }

        # 3. Próximos Turnos (Puntero/Agente de Parada)
        proximos_turnos = TurnoAgente.objects.filter(
            afiliado=afiliado, 
            fecha__gte=date.today()
        ).order_by('fecha')[:3]

        resumen['turnos'] = [{
            'fecha': t.fecha,
            'dia_nombre': t.fecha.strftime('%A'),
            'observacion': t.observacion
        } for t in proximos_turnos]

        return Response(resumen)
