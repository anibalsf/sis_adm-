from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView  
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Egreso, Pago, TipoPago, ArqueoCaja
from .serializers import EgresoSerializer, PagoSerializer, TipoPagoSerializer, ArqueoCajaSerializer
from pagos_qr.services import QRService
from django.http import HttpResponse, FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
import qrcode
from io import BytesIO
import locale

class EgresoViewSet(viewsets.ModelViewSet):
    queryset = Egreso.objects.all()
    serializer_class = EgresoSerializer

    def perform_create(self, serializer):
        monto = float(self.request.data.get('monto', 0))
        estado = 'pendiente_aprobacion' if monto > 500 else 'aprobado'
        serializer.save(estado=estado)

    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        egreso = self.get_object()
        motivo = request.data.get('motivo_anulacion', '')
        if not motivo:
            return Response({'error': 'Debe proporcionar un motivo de anulación'}, status=400)
        egreso.estado = 'anulado'
        egreso.motivo_anulacion = motivo
        egreso.save()
        return Response({'status': 'Egreso anulado'})

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        egreso = self.get_object()
        if egreso.estado != 'pendiente_aprobacion':
            return Response({'error': 'El egreso no está pendiente de aprobación'}, status=400)
        egreso.estado = 'aprobado'
        egreso.aprobado_por = request.user if request.user.is_authenticated else None
        egreso.save()
        return Response({'status': 'Egreso aprobado'})

    @action(detail=True, methods=['get'])
    def generar_comprobante(self, request, pk=None):
        from datetime import datetime
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT

        egreso = self.get_object()
        buffer = BytesIO()

        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#B71C1C'), spaceAfter=2, alignment=TA_CENTER, fontName='Helvetica-Bold')
        right_style = ParagraphStyle('Right', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT, spaceAfter=2)

        elements.append(Paragraph("SINDICATO MIXTO \"INTEGRACIÓN TAIPIPLAYA\"", title_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("COMPROBANTE DE EGRESO", title_style))
        elements.append(Spacer(1, 6))

        comprobante_nro = f"EGR-{egreso.id:04d}"
        fecha_str = egreso.fecha.strftime("%d/%m/%Y") if egreso.fecha else datetime.now().strftime("%d/%m/%Y")

        elements.append(Paragraph(f"<b>Nº:</b> {comprobante_nro}", right_style))
        elements.append(Paragraph(f"<b>Fecha:</b> {fecha_str}", right_style))
        
        status_text = ""
        if egreso.estado == 'anulado':
            status_text = " (ANULADO)"
        elif egreso.estado == 'pendiente_aprobacion':
            status_text = " (PENDIENTE DE APROBACIÓN)"
        elements.append(Paragraph(f"<b>Estado:</b> {egreso.get_estado_display()}{status_text}", right_style))
        elements.append(Spacer(1, 10))

        data = [
            ['<b>Detalle</b>', '<b>Información</b>'],
            ['Tipo de Egreso', egreso.tipo_pago.nombre if egreso.tipo_pago else '-'],
            ['Descripción', egreso.descripcion],
            ['Método de Pago', egreso.get_metodo_pago_display()],
        ]
        if egreso.metodo_pago == 'transferencia':
            data.append(['Datos Transfer', f"Banco: {egreso.banco or '-'} | Operación: {egreso.nro_operacion or '-'}"])
        
        if egreso.aprobado_por:
            data.append(['Aprobado por', egreso.aprobado_por.username])

        data.append(['Monto', f"Bs. {float(egreso.monto):.2f}"])

        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#B71C1C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 40))

        # Firmas
        firmas_data = [
            ['_________________________', '_________________________'],
            ['Entregué Conforme', 'Recibí Conforme'],
            ['Tesorero / Responsable', 'Beneficiario / Proveedor']
        ]
        firmas_table = Table(firmas_data, colWidths=[3*inch, 3*inch])
        firmas_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('FONTSIZE', (0, 2), (-1, -1), 8),
            ('TEXTCOLOR', (0, 2), (-1, -1), colors.grey),
        ]))
        elements.append(firmas_table)
        
        elements.append(Spacer(1, 20))
        
        # Nota al pie
        nota_style = ParagraphStyle(
            'Nota',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#424242'),
            alignment=TA_CENTER,
            spaceAfter=4
        )
        
        hora_impresion = datetime.now().strftime('%d de %B de %Y a las %H:%M')
        elements.append(Paragraph(
            f"<b>Impreso el:</b> {hora_impresion}",
            nota_style
        ))
        
        nota_sub_style = ParagraphStyle(
            'NotaSub',
            parent=nota_style,
            fontSize=8,
            textColor=colors.grey
        )
        elements.append(Paragraph(
            "Documento generado por el Sistema de Administración",
            nota_sub_style
        ))

        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f'comprobante_egreso_{comprobante_nro}.pdf')

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Exportar lista de egresos a Excel"""
        from openpyxl import Workbook
        from django.http import HttpResponse
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Egresos"
        
        headers = ['ID', 'Fecha', 'Descripción/Concepto', 'Monto', 'Tipo de Egreso']
        ws.append(headers)
        
        for obj in self.get_queryset().order_by('-fecha'):
            ws.append([
                obj.id,
                obj.fecha.strftime('%Y-%m-%d') if obj.fecha else '',
                obj.descripcion,
                obj.monto,
                obj.tipo_pago.nombre if obj.tipo_pago else ''
            ])
            
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=egresos.xlsx'
        wb.save(response)
        return response

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    
    def perform_create(self, serializer):
        # Si es QR, el estado inicial es pendiente hasta que se verifique
        metodo = self.request.data.get('metodo_pago', 'efectivo')
        estado_inicial = 'pendiente' if metodo == 'qr' else 'completado'

        from django.db.models import Max
        ultimo = Pago.objects.filter(nro_recibo__isnull=False).aggregate(m=Max('nro_recibo'))['m'] or 0
        obj = serializer.save(estado=estado_inicial, nro_recibo=ultimo + 1)
        
        # Actualizar estado de la hoja de ruta si existe el vínculo
        if obj.hoja_ruta:
            obj.hoja_ruta.estado = 'pagada'
            obj.hoja_ruta.save(update_fields=['estado'])
            
        # La notificación de WhatsApp se maneja vía Signals en signals.py
        return obj

    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        pago = self.get_object()
        motivo = request.data.get('motivo_anulacion', '')
        if not motivo:
            return Response({'error': 'Debe proporcionar un motivo de anulación'}, status=400)
        pago.estado = 'anulado'
        pago.motivo_anulacion = motivo
        pago.save()
        return Response({'status': 'Pago anulado'})
    
    @action(detail=True, methods=['get'])
    def generar_recibo(self, request, pk=None):
        """Generar recibo de pago en PDF mejorado"""
        from datetime import datetime
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        
        pago = self.get_object()
        buffer = BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(buffer, pagesize=letter, 
                                topMargin=0.5*inch, bottomMargin=0.5*inch,
                                leftMargin=0.75*inch, rightMargin=0.75*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=2,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        right_style = ParagraphStyle(
            'Right',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            spaceAfter=2
        )
        
        # Encabezado sin logo
        elements.append(Paragraph("SINDICATO MIXTO \"INTEGRACIÓN TAIPIPLAYA\"", title_style))
        
        info_sub_style = ParagraphStyle(
            'InfoSub',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            spaceAfter=4
        )
        info_text = "FUNDADO EL 22 DE SEPTIEMBRE DEL 2011 CON PERSONERÍA JURÍDICA R.S. NRO. 20095<br/>TAIPIPLAYA – CARANAVI LA PAZ BOLIVIA"
        elements.append(Paragraph(info_text, info_sub_style))
        
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("RECIBO DE PAGO", title_style))
        elements.append(Spacer(1, 6))
        
        # Número de recibo y fecha
        recibo_nro = f"NRO-{pago.nro_recibo or pago.id:03d}"
        fecha_str = pago.fecha_pago.strftime("%d/%m/%Y") if hasattr(pago, 'fecha_pago') and pago.fecha_pago else datetime.now().strftime("%d/%m/%Y")
        
        elements.append(Paragraph(f"<b>Recibo Nº:</b> {recibo_nro}", right_style))
        elements.append(Paragraph(f"<b>Fecha:</b> {fecha_str}", right_style))
        elements.append(Spacer(1, 10))
        
        # Datos del pago
        afiliado_nombre = pago.afiliado.nombre_completo if pago.afiliado else 'N/A'
        afiliado_ci = pago.afiliado.ci if pago.afiliado else 'N/A'
        concepto_principal = pago.tipo_pago.nombre if pago.tipo_pago else 'Pago'
        observaciones = getattr(pago, 'observaciones', '') or getattr(pago, 'concepto', '') or 'Sin descripción'
        
        data = [
            ['<b>Detalle</b>', '<b>Información</b>'],
            ['Pagado por', afiliado_nombre],
            ['CI', afiliado_ci],
            ['Concepto', concepto_principal],
            ['Descripción', observaciones],
            ['Método de Pago', pago.get_metodo_pago_display()],
        ]
        
        if pago.metodo_pago == 'transferencia':
            data.append(['Datos Transferencia', f"Banco: {pago.banco or '-'} | Operación: {pago.nro_operacion or '-'}"])
            
        data.append(['Monto', f"Bs. {float(pago.monto):.2f}"])
        
        # Crear tabla
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Cuerpo
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 10))

        # Generar QR para el recibo
        qr_data = f"RECIBO:{recibo_nro}|FECHA:{fecha_str}|MONTO:{pago.monto}|AFILIADO:{afiliado_nombre}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img_qr = qr.make_image(fill_color="black", back_color="white")
        qr_img_buffer = BytesIO()
        img_qr.save(qr_img_buffer)
        qr_img_buffer.seek(0)
        
        # Añadir QR al PDF (centrado)
        from reportlab.lib.utils import ImageReader
        qr_flowable = Image(qr_img_buffer, width=1.2*inch, height=1.2*inch)
        qr_flowable.hAlign = 'CENTER'
        elements.append(qr_flowable)
        
        elements.append(Spacer(1, 6))
        
        # Nota al pie
        nota_style = ParagraphStyle(
            'Nota',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#424242'),
            alignment=TA_CENTER,
            spaceAfter=4
        )
        
        hora_impresion = datetime.now().strftime('%d de %B de %Y a las %H:%M')
        elements.append(Paragraph(
            f"<b>Impreso el:</b> {hora_impresion}",
            nota_style
        ))
        
        nota_sub_style = ParagraphStyle(
            'NotaSub',
            parent=nota_style,
            fontSize=8,
            textColor=colors.grey
        )
        elements.append(Paragraph(
            "Documento generado por el Sistema de Administración",
            nota_sub_style
        ))
        
        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=True, filename=f'recibo_{recibo_nro}.pdf')
    
    @action(detail=True, methods=['post'], url_path='generar_pago_qr')
    def generar_pago_qr(self, request, pk=None):
        """Generar cobro QR para un pago ya registrado"""
        pago = self.get_object()
        glosa = f"Pago {pago.tipo_pago.nombre} - ID: {pago.id} - Afiliado: {pago.afiliado.nombre_completo}"
        
        qr_obj = QRService.generate_qr(
            monto=pago.monto, 
            glosa=glosa, 
            content_object=pago
        )
        
        return Response({
            'qr_string': qr_obj.qr_string,
            'imagen_base64': qr_obj.imagen_base64,
            'transaction_id': qr_obj.transaction_id,
            'monto': qr_obj.monto,
            'glosa': qr_obj.glosa
        })

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Exportar lista de pagos a Excel"""
        from openpyxl import Workbook
        from django.http import HttpResponse
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Pagos"
        
        headers = ['ID', 'Fecha', 'Afiliado', 'Tipo de Pago', 'Monto', 'Observaciones']
        ws.append(headers)
        
        for obj in self.get_queryset().order_by('-fecha_pago'):
            afiliado = obj.afiliado.nombre_completo if obj.afiliado else "N/A"
            tipo = obj.tipo_pago.nombre if obj.tipo_pago else "N/A"
            ws.append([
                obj.id,
                obj.fecha_pago.strftime('%Y-%m-%d') if obj.fecha_pago else '',
                afiliado,
                tipo,
                obj.monto,
                obj.observaciones or ''
            ])
            
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=pagos.xlsx'
        wb.save(response)
        return response

class TipoPagoViewSet(viewsets.ModelViewSet):
    queryset = TipoPago.objects.all()
    serializer_class = TipoPagoSerializer
    pagination_class = None
    
    @action(detail=True, methods=['post'])
    def calcular_monto(self, request, pk=None):
        """
        Calcula el monto a pagar considerando multas por retraso.
        Es pera: { "monto_base": 20 }
        Retorna: { "monto_total": 70, "tiene_multa": true, "multa": 50, "mensaje": "..." }
        """
        from datetime import datetime, time
        
        tipo_pago = self.get_object()
        nombre = (tipo_pago.nombre or '').lower()
        monto_base = float(request.data.get('monto_base', 0))

        if monto_base <= 0:
            return Response({'detail': 'El monto base debe ser mayor a 0'}, status=400)

        if 'hoja' in nombre and 'ruta' in nombre and 'caranavi' in nombre:
            ahora = datetime.now()
            dia_actual = ahora.weekday()
            hora_actual = ahora.time()
            dentro_plazo = (dia_actual == 0 and hora_actual <= time(22, 0))
            
            # Si el usuario explícitamente dice que NO aplique multa, o está dentro de plazo
            forzar_sin_multa = not request.data.get('aplicar_multa', True)
            
            if dentro_plazo or forzar_sin_multa:
                return Response({
                    'monto_total': monto_base,
                    'tiene_multa': False,
                    'multa': 0,
                    'monto_base': monto_base,
                    'mensaje': f'🎉 Pago sin multa. Costo: {monto_base} Bs' if forzar_sin_multa else f'🎉 Pago a tiempo. Costo: {monto_base} Bs'
                })
            
            multa = 50.0
            monto_total = monto_base + multa
            return Response({
                'monto_total': monto_total,
                'tiene_multa': True,
                'multa': multa,
                'monto_base': monto_base,
                'mensaje': f'⚠️ Pago fuera de plazo. Multa de {multa} Bs aplicada. Total a pagar: {monto_total} Bs'
            })
        
        if not tipo_pago.tiene_plazo:
            return Response({
                'monto_total': monto_base,
                'tiene_multa': False,
                'multa': 0,
                'mensaje': 'No aplica multa para este tipo de pago'
            })
        
        ahora = datetime.now()
        dia_actual = ahora.weekday()
        hora_actual = ahora.time()
        
        esta_en_plazo = False
        if dia_actual == tipo_pago.dia_plazo:
            if tipo_pago.hora_inicio_plazo <= hora_actual <= tipo_pago.hora_fin_plazo:
                esta_en_plazo = True
        
        if esta_en_plazo:
            return Response({
                'monto_total': monto_base,
                'tiene_multa': False,
                'multa': 0,
                'mensaje': f'Pago dentro del plazo (Lunes {tipo_pago.hora_inicio_plazo.strftime("%H:%M")} - {tipo_pago.hora_fin_plazo.strftime("%H:%M")})'
            })
        
        multa = float(tipo_pago.monto_multa)
        monto_total = monto_base + multa
        return Response({
            'monto_total': monto_total,
            'tiene_multa': True,
            'multa': multa,
            'monto_base': monto_base,
            'mensaje': f'⚠️ Pago fuera de plazo. Multa de {multa} Bs aplicada. Total a pagar: {monto_total} Bs'
        })

class ReciboView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            pago = Pago.objects.select_related('afiliado', 'tipo_pago').get(pk=pk)
        except Pago.DoesNotExist:
            return Response({'detail': 'Pago no encontrado'}, status=404)

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter # 612 x 792 points
        
        # MÁRGENES DE SEGURIDAD EXTREMOS
        # Dejamos 1 pulgada (2.54cm) libre arriba y abajo para evitar cualquier 'zona muerta' de impresora
        # Y achicamos el recibo para que entre super cómodo
        SAFE_MARGIN_Y = 0.8 * inch  
        SAFE_MARGIN_X = 0.8 * inch
        
        # Área útil disponible verticalmente
        AVAILABLE_HEIGHT = height - (2 * SAFE_MARGIN_Y)
        
        # Altura de CADA recibo individual (será un poco menos de la mitad del área útil)
        RECEIPT_HEIGHT = AVAILABLE_HEIGHT / 2
        
        from django.conf import settings
        logo_path = settings.BASE_DIR / 'frontend' / 'public' / 'logo-taipiplaya.png'

        def dibujar_recibo_individual(c, start_y, etiqueta_copia):
            # start_y es donde comienza la cabecera (parte superior del recibo)
            
            # --- Logotipo ---
            if logo_path.exists():
                c.drawImage(str(logo_path), width / 2 - 0.4*inch, start_y + 10, width=0.8*inch, height=0.8*inch, mask='auto')

            # --- Cabecera ---
            c.setFont("Helvetica-Bold", 11) # Letra un poco más pequeña
            c.drawCentredString(width / 2, start_y, "SINDICATO MIXTO DE TRANSPORTE")
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(width / 2, start_y - 12, "INTEGRACIÓN TAIPIPLAYA")
            
            # Etiqueta (Original/Copia)
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.grey)
            c.drawCentredString(width / 2, start_y - 24, f"--- {etiqueta_copia} ---")
            c.setFillColor(colors.black)
            
            # Línea separadora
            c.setLineWidth(0.5)
            c.line(SAFE_MARGIN_X, start_y - 30, width - SAFE_MARGIN_X, start_y - 30)
            
            # --- Título y Nro ---
            c.setFont("Helvetica-Bold", 13)
            c.drawString(SAFE_MARGIN_X, start_y - 50, "RECIBO DE INGRESO")
            
            c.setFont("Helvetica-Bold", 11)
            c.drawRightString(width - SAFE_MARGIN_X, start_y - 50, f"N° {(pago.nro_recibo or pago.id):06d}")
            
            # --- Cuerpo ---
            current_y = start_y - 75
            line_step = 20 # Espaciado más compacto
            
            # Función auxiliar para renglones
            def renglon(label, value, y):
                c.setFont("Helvetica", 9)
                c.drawString(SAFE_MARGIN_X, y, label)
                c.setFont("Helvetica-Bold", 9)
                c.drawString(SAFE_MARGIN_X + 1.0 * inch, y, value) 
                # Línea guía visual suave
                c.setLineWidth(0.2)
                c.setStrokeColor(colors.lightgrey)
                c.line(SAFE_MARGIN_X + 0.9 * inch, y - 2, width - SAFE_MARGIN_X - 1.2*inch, y - 2)
                c.setStrokeColor(colors.black)

            renglon("Fecha:", pago.fecha_pago.strftime('%d/%m/%Y'), current_y)
            current_y -= line_step
            
            renglon("Recibí de:", pago.afiliado.nombre_completo.upper()[0:45], current_y)
            current_y -= line_step
            
            renglon("La suma de:", f"{pago.monto} BS.", current_y)
            current_y -= line_step
            
            renglon("Por:", pago.tipo_pago.nombre[0:45], current_y)
            current_y -= line_step
            
            renglon("Método de Pago:", pago.get_metodo_pago_display(), current_y)
            current_y -= line_step
            
            if hasattr(pago, 'metodo_pago') and pago.metodo_pago == 'transferencia':
                banco_str = pago.banco or '-'
                nro_str = pago.nro_operacion or '-'
                renglon("Transferencia:", f"Banco: {banco_str} | Nro: {nro_str}", current_y)
                current_y -= line_step

            if pago.observaciones:
                c.setFont("Helvetica-Oblique", 8)
                c.drawString(SAFE_MARGIN_X + 1.0 * inch, current_y, f"({pago.observaciones[0:70]})")
                current_y -= line_step

            # --- QR y Firmas ---
            # QR
            qr_data = f"RECIBO:{(pago.nro_recibo or pago.id):06d}|{pago.fecha_pago}|{pago.monto}"
            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = BytesIO()
            img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            
            import reportlab.lib.utils
            qr_size = 0.9 * inch # QR compacto
            # Posición QR: Derecha, alineado con las firmas más o menos
            qr_pos_y = current_y - 25 
            c.drawImage(reportlab.lib.utils.ImageReader(qr_buffer), 
                       width - SAFE_MARGIN_X - qr_size, 
                       qr_pos_y, 
                       width=qr_size, height=qr_size)
            
            # Firmas
            firma_y = qr_pos_y + 10
            c.setLineWidth(0.5)
            
            # Firma única centrada (más limpio) o a la izquierda
            center_x = width / 2 - 0.5 * inch
            c.line(center_x - 0.8*inch, firma_y, center_x + 0.8*inch, firma_y)
            c.setFont("Helvetica", 6)
            c.drawCentredString(center_x, firma_y - 8, "RESPONSABLE / TESORERO")

        # Calculamos posiciones para centrar verticalmente todo el bloque en la hoja
        # | --- Espacio Libre Superior --- |
        # | [ Recibo 1 ]                   |
        # | - - - - Corte - - - -          |
        # | [ Recibo 2 ]                   |
        # | --- Espacio Libre Inferior --- |
        
        TOP_RECIBO_Y = height - SAFE_MARGIN_Y - 20
        BOTTOM_RECIBO_Y = SAFE_MARGIN_Y + RECEIPT_HEIGHT - 20 # Un poco ajustado
        
        # Mejor enfoque: Usar height/2 como eje
        # Recibo 1 (Arriba) empieza un poco más abajo del tope
        dibujar_recibo_individual(c, height/2 + RECEIPT_HEIGHT - 30, "ORIGINAL")
        
        # Línea de corte (Exactamente al medio)
        middle_y = height / 2
        c.setDash(4, 4)
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.grey)
        c.line(0.5 * inch, middle_y, width - 0.5 * inch, middle_y)
        c.setFont("Helvetica", 6)
        c.drawCentredString(width/2, middle_y - 3, "✂ CORTAR AQUÍ")
        c.setStrokeColor(colors.black)
        c.setDash([]) 
        
        # Recibo 2 (Abajo) empieza justo debajo de la línea de corte
        dibujar_recibo_individual(c, middle_y - 30, "COPIA") # 30 pts de margen interno

        c.showPage()
        c.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recibo_{(pago.nro_recibo or pago.id):06d}.pdf"'
        return response

class ArqueoCajaViewSet(viewsets.ModelViewSet):
    queryset = ArqueoCaja.objects.all()
    serializer_class = ArqueoCajaSerializer

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=False, methods=['post'])
    def calcular(self, request):
        """Calcula teóricamente los ingresos y egresos hasta la fecha_fin, para que coincida con TODAS las transacciones"""
        from django.db.models import Sum
        fecha_inicio = request.data.get('fecha_inicio')
        fecha_fin = request.data.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response({'error': 'Debe proporcionar fecha_inicio y fecha_fin'}, status=400)
            
        # Para que coincida con la caja física real acumulada, sumamos TODAS las transacciones hasta la fecha_fin
        ingresos = Pago.objects.filter(fecha_pago__lte=fecha_fin, estado='completado').aggregate(Sum('monto'))['monto__sum'] or 0
        egresos = Egreso.objects.filter(fecha__lte=fecha_fin, estado__in=['aprobado', 'completado']).aggregate(Sum('monto'))['monto__sum'] or 0
        
        # Opcional: mostrar lo del periodo actual
        pagos_periodo_qs = Pago.objects.filter(fecha_pago__range=[fecha_inicio, fecha_fin], estado='completado')
        egresos_periodo_qs = Egreso.objects.filter(fecha__range=[fecha_inicio, fecha_fin], estado__in=['aprobado', 'completado'])

        ingresos_periodo = pagos_periodo_qs.aggregate(Sum('monto'))['monto__sum'] or 0
        egresos_periodo = egresos_periodo_qs.aggregate(Sum('monto'))['monto__sum'] or 0

        ingresos_breakdown = list(pagos_periodo_qs.values('tipo_pago__nombre').annotate(total=Sum('monto')).order_by('-total'))
        egresos_breakdown = list(egresos_periodo_qs.values('tipo_pago__nombre').annotate(total=Sum('monto')).order_by('-total'))

        saldo_teorico = float(ingresos) - float(egresos)
        
        return Response({
            'total_ingresos': ingresos,
            'total_egresos': egresos,
            'ingresos_periodo': ingresos_periodo,
            'egresos_periodo': egresos_periodo,
            'saldo_teorico': saldo_teorico,
            'ingresos_breakdown': ingresos_breakdown,
            'egresos_breakdown': egresos_breakdown
        })

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Exportar lista de arqueos a Excel (Informe Económico)"""
        from openpyxl import Workbook
        from django.http import HttpResponse
        import json
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Informe Económico - Arqueos"
        
        headers = [
            'ID', 'Mes', 'Año', 'Periodo (Inicio)', 'Periodo (Fin)', 
            'Ingresos (Acum.)', 'Egresos (Acum.)', 'Saldo Teórico', 
            'Saldo Real', 'Diferencia', 'Billetes 200', 'Billetes 100', 
            'Billetes 50', 'Billetes 20', 'Billetes 10', 'Monedas 5', 
            'Monedas 2', 'Monedas 1', 'M 0.50', 'M 0.20', 'M 0.10',
            'Estado', 'Observaciones', 'Creado El'
        ]
        ws.append(headers)
        
        for obj in self.get_queryset().order_by('-anho', '-mes', '-fecha_fin'):
            # Convert timestamp to timezone naive
            created_str = obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else ''
            
            # Desglose fallback
            desg = obj.detalle_efectivo or {}
            
            ws.append([
                obj.id,
                obj.mes,
                obj.anho,
                obj.fecha_inicio.strftime('%Y-%m-%d') if obj.fecha_inicio else '',
                obj.fecha_fin.strftime('%Y-%m-%d') if obj.fecha_fin else '',
                float(obj.total_ingresos),
                float(obj.total_egresos),
                float(obj.saldo_teorico),
                float(obj.saldo_real),
                float(obj.diferencia),
                desg.get('b200', 0),
                desg.get('b100', 0),
                desg.get('b50', 0),
                desg.get('b20', 0),
                desg.get('b10', 0),
                desg.get('m5', 0),
                desg.get('m2', 0),
                desg.get('m1', 0),
                desg.get('m050', 0),
                desg.get('m020', 0),
                desg.get('m010', 0),
                obj.estado.upper(),
                obj.observaciones or '',
                created_str
            ])
            
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=informe_economico_arqueos.xlsx'
        wb.save(response)
        return response

    @action(detail=True, methods=['get'])
    def export_excel_individual(self, request, pk=None):
        """Exportar formato físico de arqueo para un registro individual"""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
        from django.http import HttpResponse
        
        arqueo = self.get_object()
        desg = arqueo.detalle_efectivo or {}
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Arqueo Físico"
        
        ws.sheet_view.showGridLines = False

        # Styles
        title_font = Font(name='Calibri', size=18, bold=True)
        subtitle_font = Font(name='Calibri', size=14, bold=True)
        bold_font = Font(name='Calibri', size=11, bold=True)
        normal_font = Font(name='Calibri', size=11)
        
        center_align = Alignment(horizontal='center', vertical='center')
        right_align = Alignment(horizontal='right', vertical='center')
        left_align = Alignment(horizontal='left', vertical='center')
        
        medium_border = Border(
            left=Side(style='medium'), right=Side(style='medium'),
            top=Side(style='medium'), bottom=Side(style='medium')
        )
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        cyan_fill = PatternFill(start_color="99FFFF", end_color="99FFFF", fill_type="solid")

        def set_border(ws, cell_range, border_style=thin_border):
            from openpyxl.utils import range_boundaries
            min_col, min_row, max_col, max_row = range_boundaries(cell_range)
            for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
                for cell in row:
                    cell.border = border_style

        # Headers
        ws.merge_cells('B1:E1')
        ws['B1'] = "SINDICATO MIXTO DE TRANSPORTE INTEGRACIÓN TAIPIPLAYA"
        ws['B1'].font = subtitle_font
        ws['B1'].alignment = center_align

        ws.merge_cells('B2:E2')
        ws['B2'] = "ARQUEO DE CAJA CHICA"
        ws['B2'].font = title_font
        ws['B2'].alignment = center_align

        # --- Bloque Fecha y Hora ---
        # FECHA
        ws.merge_cells('B4:D4')
        ws['B4'] = "FECHA:"
        ws['B4'].font = bold_font
        ws['E4'] = arqueo.fecha_fin.strftime('%d/%m/%Y') if arqueo.fecha_fin else ''
        ws['E4'].fill = cyan_fill
        ws['E4'].alignment = right_align
        
        # Hr. INICIO
        ws.merge_cells('B5:D5')
        ws['B5'] = "Hr. INICIO:"
        ws['B5'].font = bold_font
        ws['E5'] = ""
        ws['E5'].fill = cyan_fill
        ws['E5'].alignment = right_align
        
        # Hr. TERMINO
        ws.merge_cells('B6:D6')
        ws['B6'] = "Hr. TÉRMINO:"
        ws['B6'].font = bold_font
        ws['E6'] = arqueo.created_at.strftime('%H:%M') if arqueo.created_at else ''
        ws['E6'].fill = cyan_fill
        ws['E6'].alignment = right_align
        
        set_border(ws, 'B4:E6', medium_border)
        set_border(ws, 'B4:E4', medium_border)
        set_border(ws, 'B5:E5', medium_border)
        ws['E4'].border = thin_border
        ws['E5'].border = thin_border
        ws['E6'].border = thin_border

        # --- Saldo Inicial ---
        ws.merge_cells('B8:D8')
        ws['B8'] = "SALDO INICIAL:"
        ws['B8'].font = bold_font
        ws['E8'] = ""
        ws['E8'].fill = cyan_fill
        set_border(ws, 'B8:E8', medium_border)
        ws['E8'].border = medium_border

        # --- Titulo Efectivo ---
        ws['A11'] = "1.-"
        ws['A11'].font = bold_font
        ws['B11'] = "EFECTIVO"
        ws['B11'].font = bold_font

        # --- BILLETES ---
        ws.merge_cells('C13:E13')
        ws['C13'] = "BILLETES"
        ws['C13'].font = bold_font
        ws['C13'].alignment = center_align
        
        headers_b = ['Valor', 'Cantidad', 'Total']
        for col, val in enumerate(headers_b, start=3):
            cell = ws.cell(row=14, column=col)
            cell.value = val
            cell.font = bold_font
            cell.alignment = center_align
            
        billetes = [
            (200.00, desg.get('b200', 0)),
            (100.00, desg.get('b100', 0)),
            (50.00, desg.get('b50', 0)),
            (20.00, desg.get('b20', 0)),
            (10.00, desg.get('b10', 0)),
        ]
        
        r = 15
        total_billetes = 0
        for val, cant in billetes:
            tot = val * cant
            total_billetes += tot
            
            ws.cell(row=r, column=3, value=val).number_format = '0.00'
            ws.cell(row=r, column=3).alignment = right_align
            
            ws.cell(row=r, column=4, value=cant if cant > 0 else '').fill = cyan_fill
            ws.cell(row=r, column=4).alignment = center_align
            
            ws.cell(row=r, column=5, value=tot if tot > 0 else '-').number_format = '#,##0.00'
            ws.cell(row=r, column=5).alignment = right_align
            r += 1
            
        # Total Billetes
        ws.merge_cells(f'C{r}:D{r}')
        ws.cell(row=r, column=3, value="Total Billetes").font = bold_font
        ws.cell(row=r, column=3).alignment = right_align
        ws.cell(row=r, column=5, value=total_billetes if total_billetes > 0 else '-').font = bold_font
        ws.cell(row=r, column=5).number_format = '#,##0.00'
        
        set_border(ws, f'C13:E{r}', thin_border)
        # Apply thick border outside
        set_border(ws, f'C13:E{r}', medium_border)
        for i in range(13, r+1):
            ws.cell(row=i, column=3).border = thin_border
            ws.cell(row=i, column=4).border = thin_border
            ws.cell(row=i, column=5).border = thin_border
        
        # Fix outer border of Billetes
        from openpyxl.utils import range_boundaries
        min_col, min_row, max_col, max_row = range_boundaries(f'C13:E{r}')
        for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
            for cell in row:
                b = cell.border
                cell.border = Border(
                    left=Side(style='medium') if cell.column == min_col else b.left,
                    right=Side(style='medium') if cell.column == max_col else b.right,
                    top=Side(style='medium') if cell.row == min_row else b.top,
                    bottom=Side(style='medium') if cell.row == max_row else b.bottom
                )

        # --- MONEDAS ---
        r += 2
        ws.merge_cells(f'C{r}:E{r}')
        ws.cell(row=r, column=3, value="MONEDAS").font = bold_font
        ws.cell(row=r, column=3).alignment = center_align
        r += 1
        
        for col, val in enumerate(headers_b, start=3):
            cell = ws.cell(row=r, column=col)
            cell.value = val
            cell.font = bold_font
            cell.alignment = center_align
        r += 1
            
        monedas = [
            (5.00, desg.get('m5', 0)),
            (2.00, desg.get('m2', 0)),
            (1.00, desg.get('m1', 0)),
            (0.50, desg.get('m050', 0)),
            (0.20, desg.get('m020', 0)),
            (0.10, desg.get('m010', 0)),
        ]
        
        total_monedas = 0
        start_monedas = r - 2
        for val, cant in monedas:
            tot = val * cant
            total_monedas += tot
            
            ws.cell(row=r, column=3, value=val).number_format = '0.00'
            ws.cell(row=r, column=3).alignment = right_align
            
            ws.cell(row=r, column=4, value=cant if cant > 0 else '').fill = cyan_fill
            ws.cell(row=r, column=4).alignment = center_align
            
            ws.cell(row=r, column=5, value=tot if tot > 0 else '-').number_format = '#,##0.00'
            ws.cell(row=r, column=5).alignment = right_align
            r += 1
            
        # Total Monedas
        ws.merge_cells(f'C{r}:D{r}')
        ws.cell(row=r, column=3, value="Total Monedas").font = bold_font
        ws.cell(row=r, column=3).alignment = right_align
        ws.cell(row=r, column=5, value=total_monedas if total_monedas > 0 else '-').font = bold_font
        ws.cell(row=r, column=5).number_format = '#,##0.00'
        
        for i in range(start_monedas, r+1):
            ws.cell(row=i, column=3).border = thin_border
            ws.cell(row=i, column=4).border = thin_border
            ws.cell(row=i, column=5).border = thin_border
            
        min_col, min_row, max_col, max_row = range_boundaries(f'C{start_monedas}:E{r}')
        for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
            for cell in row:
                b = cell.border
                cell.border = Border(
                    left=Side(style='medium') if cell.column == min_col else b.left,
                    right=Side(style='medium') if cell.column == max_col else b.right,
                    top=Side(style='medium') if cell.row == min_row else b.top,
                    bottom=Side(style='medium') if cell.row == max_row else b.bottom
                )
        
        # Anchos de columna exactos para simular la imagen
        ws.column_dimensions['A'].width = 4
        ws.column_dimensions['B'].width = 8
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=arqueo_fisico_{arqueo.id}.xlsx'
        wb.save(response)
        return response
