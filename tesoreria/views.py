from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView  
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Egreso, Pago, TipoPago
from .serializers import EgresoSerializer, PagoSerializer, TipoPagoSerializer
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
        obj = serializer.save()
        
        # Actualizar estado de la hoja de ruta si existe el vínculo
        if obj.hoja_ruta:
            obj.hoja_ruta.estado = 'pagada'
            obj.hoja_ruta.save(update_fields=['estado'])
            
        # La notificación de WhatsApp se maneja vía Signals en signals.py
        return obj
    
    @action(detail=True, methods=['get'])
    def generar_recibo(self, request, pk=None):
        """Generar recibo de pago en PDF mejorado"""
        from datetime import datetime
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
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
            fontSize=18,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        right_style = ParagraphStyle(
            'Right',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT
        )
        
        # Encabezado
        elements.append(Paragraph("SINDICATO MIXTO INTEGRACIÓN TAIPIPLAYA", title_style))
        elements.append(Paragraph("RECIBO DE PAGO", title_style))
        elements.append(Spacer(1, 12))
        
        # Número de recibo y fecha
        recibo_nro = f"NRO-{pago.id:06d}"
        fecha_str = pago.fecha_pago.strftime("%d/%m/%Y") if hasattr(pago, 'fecha_pago') and pago.fecha_pago else datetime.now().strftime("%d/%m/%Y")
        
        elements.append(Paragraph(f"<b>Recibo Nº:</b> {recibo_nro}", right_style))
        elements.append(Paragraph(f"<b>Fecha:</b> {fecha_str}", right_style))
        elements.append(Spacer(1, 20))
        
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
            ['Monto', f"Bs. {float(pago.monto):.2f}"],
        ]
        
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
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 30))
        
        # Nota al pie
        nota_style = ParagraphStyle(
            'Nota',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Este recibo fue generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            nota_style
        ))
        elements.append(Paragraph(
            "Para cualquier aclaración, comunicarse con la administración del sindicato.",
            nota_style
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
        
        if 'hoja' in nombre and 'ruta' in nombre:
            monto_base = 20.0
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
                    'mensaje': '🎉 Pago sin multa. Costo: 20 Bs' if forzar_sin_multa else '🎉 Pago a tiempo. Costo: 20 Bs'
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
        
        def dibujar_recibo_individual(c, start_y, etiqueta_copia):
            # start_y es donde comienza la cabecera (parte superior del recibo)
            
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
            c.drawRightString(width - SAFE_MARGIN_X, start_y - 50, f"N° {pago.id:06d}")
            
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
            
            if pago.observaciones:
                c.setFont("Helvetica-Oblique", 8)
                c.drawString(SAFE_MARGIN_X + 1.0 * inch, current_y, f"({pago.observaciones[0:70]})")
                current_y -= line_step

            # --- QR y Firmas ---
            # QR
            qr_data = f"RECIBO:{pago.id}|{pago.fecha_pago}|{pago.monto}"
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
        response['Content-Disposition'] = f'attachment; filename="recibo_{pago.id}.pdf"'
        return response
