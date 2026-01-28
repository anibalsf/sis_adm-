# Código para agregar a tesoreria/views.py
# Agregar este método dentro de la clase PagoViewSet (después de la línea 23)

"""
@action(detail=True, methods=['get'])
def generar_recibo(self, request, pk=None):
    \"\"\"Generar recibo de pago en PDF mejorado\"\"\"
    from datetime import datetime
    from django.http import FileResponse
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    import io
    
    pago = self.get_object()
    buffer = io.BytesIO()
    
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
"""
