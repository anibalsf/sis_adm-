"""
Fase 3: Reservas Mejoradas con QR y WhatsApp
Código para agregar a reservas/views.py
"""

# ========================================
# INSTALACIÓN REQUERIDA
# ========================================
"""
pip install qrcode pillow
"""

# ========================================
# IMPORTS NECESARIOS AL INICIO DEL ARCHIVO
# ========================================
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
import qrcode
import io
from datetime import datetime
"""

# ========================================
# MÉTODO 1: Generar código QR para reserva
# ========================================
"""
@action(detail=True, methods=['get'])
def generar_qr(self, request, pk=None):
    '''
    Generar código QR con información de la reserva.
    URL: GET /api/reservas/{id}/generar_qr/
    Retorna: Imagen PNG del código QR
    '''
    reserva = self.get_object()
    
    # Datos para el QR
    qr_data = f'''RESERVA:{reserva.id}
CLIENTE:{reserva.cliente}
TEL:{reserva.telefono}
FECHA:{reserva.fecha_viaje}
ASIENTO:{reserva.asiento}
HOJA:{reserva.hoja_ruta.id if reserva.hoja_ruta else 'N/A'}
RUTA:{reserva.hoja_ruta.ruta.nombre if reserva.hoja_ruta and reserva.hoja_ruta.ruta else 'N/A'}
VERIFICACION:{reserva.id}-{reserva.fecha_viaje}'''
    
    # Generar QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar en buffer
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return FileResponse(buffer, content_type='image/png', as_attachment=False, filename=f'reserva_qr_{reserva.id}.png')
"""

# ========================================
# MÉTODO 2: Generar confirmación en PDF con QR
# ========================================
"""
@action(detail=True, methods=['get'])
def generar_confirmacion_pdf(self, request, pk=None):
    '''
    Generar PDF de confirmación de reserva con código QR incluido.
    URL: GET /api/reservas/{id}/generar_confirmacion_pdf/
    '''
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    
    reserva = self.get_object()
    buffer = io.BytesIO()
    
    # Generar QR primero
    qr_data = f"RESERVA:{reserva.id}|CLIENTE:{reserva.cliente}|FECHA:{reserva.fecha_viaje}|ASIENTO:{reserva.asiento}"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar QR en buffer temporal
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Crear PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2E7D32'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Encabezado
    elements.append(Paragraph("SINDICATO MIXTO INTEGRACIÓN TAIPIPLAYA", title_style))
    elements.append(Paragraph("CONFIRMACIÓN DE RESERVA", title_style))
    elements.append(Spacer(1, 20))
    
    # Código QR centrado
    from reportlab.platypus import Image as RLImage
    qr_image = RLImage(qr_buffer, width=2*inch, height=2*inch)
    qr_image.hAlign = 'CENTER'
    elements.append(qr_image)
    elements.append(Spacer(1, 20))
    
    # Información de la reserva
    hoja_info = reserva.hoja_ruta
    ruta_nombre = hoja_info.ruta.nombre if hoja_info and hoja_info.ruta else 'N/A'
    conductor = hoja_info.afiliado.nombre_completo if hoja_info and hoja_info.afiliado else 'N/A'
    vehiculo = hoja_info.vehiculo.placa if hoja_info and hoja_info.vehiculo else 'N/A'
    
    data = [
        ['<b>Detalle</b>', '<b>Información</b>'],
        ['Nº de Reserva', str(reserva.id)],
        ['Pasajero', reserva.cliente],
        ['Teléfono', reserva.telefono],
        ['Fecha de Viaje', str(reserva.fecha_viaje)],
        ['Asiento Nº', str(reserva.asiento)],
        ['Ruta', ruta_nombre],
        ['Conductor', conductor],
        ['Vehículo', vehiculo],
    ]
    
    table = Table(data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Notas
    nota_style = ParagraphStyle('Nota', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph("Presente este código QR al abordar el vehículo", nota_style))
    elements.append(Paragraph("Conserve este comprobante hasta finalizar su viaje", nota_style))
    
    doc.build(elements)
    buffer.seek(0)
    
    return FileResponse(buffer, as_attachment=True, filename=f'confirmacion_reserva_{reserva.id}.pdf')
"""

# ========================================
# MÉTODO 3: Enviar confirmación por WhatsApp
# ========================================
"""
@action(detail=True, methods=['post'])
def enviar_confirmacion_whatsapp(self, request, pk=None):
    '''
    Enviar confirmación de reserva por WhatsApp.
    URL: POST /api/reservas/{id}/enviar_confirmacion_whatsapp/
    Body: { "telefono": "+59171234567" } (opcional, usa el de la reserva si no se especifica)
    '''
    reserva = self.get_object()
    telefono = request.data.get('telefono', reserva.telefono)
    
    if not telefono:
        return Response({'error': 'No se proporcionó número de teléfono'}, status=400)
    
    # Obtener información
    hoja_info = reserva.hoja_ruta
    ruta_nombre = hoja_info.ruta.nombre if hoja_info and hoja_info.ruta else 'N/A'
    conductor = hoja_info.afiliado.nombre_completo if hoja_info and hoja_info.afiliado else 'N/A'
    vehiculo = hoja_info.vehiculo.placa if hoja_info and hoja_info.vehiculo else 'N/A'
    fecha_salida = hoja_info.fecha_salida if hoja_info else reserva.fecha_viaje
    
    # Construir mensaje
    mensaje = f'''✅ *RESERVA CONFIRMADA*

📋 *Nº de Reserva:* {reserva.id}
👤 *Pasajero:* {reserva.cliente}
📅 *Fecha de Viaje:* {reserva.fecha_viaje}
🪑 *Asiento Nº:* {reserva.asiento}

🗺️ *Ruta:* {ruta_nombre}
👨‍✈️ *Conductor:* {conductor}
🚐 *Vehículo:* {vehiculo}
🕐 *Hora de Salida:* {fecha_salida}

💡 *Importante:*
• Llegue 15 minutos antes
• Presente su DNI al abordar
• Su asiento está reservado

📞 Consultas: Sindicato Mixto Integración Taipiplaya

_Para ver su código QR, ingrese a: http://localhost:5173/reservas/{reserva.id}/qr_
'''
    
    # Aquí iría la integración con API de WhatsApp
    # Por ahora solo simulamos el envío
    try:
        # TODO: Integrar con API de WhatsApp (Twilio, WhatsApp Business API, etc.)
        # Example:
        # import requests
        # response = requests.post('https://api.whatsapp.com/send', data={...})
        
        print(f"Mensaje enviado a {telefono}:")
        print(mensaje)
        
        return Response({
            'success': True,
            'mensaje': 'Confirmación enviada por WhatsApp',
            'telefono': telefono,
            'preview': mensaje
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
"""

# ========================================
# MÉTODO 4: Reservas del día (para conductores)
# ========================================
"""
@action(detail=False, methods=['get'])
def reservas_hoy_por_conductor(self, request):
    '''
    Obtener reservas del día agrupadas por conductor/hoja de ruta.
    Útil para que los conductores vean sus pasajeros del día.
    URL: GET /api/reservas/reservas_hoy_por_conductor/?conductor_id=5
    '''
    from django.db.models import Count
    from datetime import date
    
    conductor_id = request.GET.get('conductor_id')
    fecha = request.GET.get('fecha', date.today())
    
    # Filtrar reservas
    reservas = self.get_queryset().filter(
        fecha_viaje=fecha
    ).select_related('hoja_ruta__afiliado', 'hoja_ruta__ruta', 'hoja_ruta__vehiculo')
    
    if conductor_id:
        reservas = reservas.filter(hoja_ruta__afiliado_id=conductor_id)
    
    # Agrupar por hoja de ruta
    hojas_rutas = {}
    for reserva in reservas:
        hoja_id = reserva.hoja_ruta.id if reserva.hoja_ruta else 'sin_hoja'
        
        if hoja_id not in hojas_rutas:
            hojas_rutas[hoja_id] = {
                'hoja_ruta_id': hoja_id,
                'conductor': reserva.hoja_ruta.afiliado.nombre_completo if reserva.hoja_ruta else 'N/A',
                'ruta': reserva.hoja_ruta.ruta.nombre if reserva.hoja_ruta and reserva.hoja_ruta.ruta else 'N/A',
                'vehiculo': reserva.hoja_ruta.vehiculo.placa if reserva.hoja_ruta and reserva.hoja_ruta.vehiculo else 'N/A',
                'total_pasajeros': 0,
                'pasajeros': []
            }
        
        hojas_rutas[hoja_id]['total_pasajeros'] += 1
        hojas_rutas[hoja_id]['pasajeros'].append({
            'id': reserva.id,
            'nombre': reserva.cliente,
            'telefono': reserva.telefono,
            'asiento': reserva.asiento,
            'hora_reserva': reserva.created_at.strftime('%H:%M') if hasattr(reserva, 'created_at') else 'N/A'
        })
    
    return Response({
        'fecha': str(fecha),
        'total_hojas': len(hojas_rutas),
        'hojas_rutas': list(hojas_rutas.values())
    })
"""

# ========================================
# INTEGRACIÓN EN FRONTEND
# ========================================
"""
// En api.js, agregar:
generarQrReserva: (id) => axios.get(`/reservas/${id}/generar_qr/`, { responseType: 'blob' }),
generarConfirmacionPdf: (id) => axios.get(`/reservas/${id}/generar_confirmacion_pdf/`, { responseType: 'blob' }),
enviarConfirmacionWhatsapp: (id, data) => axios.post(`/reservas/${id}/enviar_confirmacion_whatsapp/`, data),
getReservasHoyPorConductor: (params) => axios.get('/reservas/reservas_hoy_por_conductor/', { params }),

// En Reservas.jsx, agregar botones:
<button onClick={() => descargarQR(reserva.id)}>
    📱 Ver QR
</button>
<button onClick={() => descargarPDF(reserva.id)}>
    📄 Descargar Confirmación
</button>
<button onClick={() => enviarWhatsApp(reserva.id)}>
    💬 Enviar WhatsApp
</button>

// Funciones:
const descargarQR = async (id) => {
    const response = await api.generarQrReserva(id);
    const url = window.URL.createObjectURL(new Blob([response.data]));
    window.open(url, '_blank');
};

const descargarPDF = async (id) => {
    const response = await api.generarConfirmacionPdf(id);
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = `confirmacion_${id}.pdf`;
    link.click();
};

const enviarWhatsApp = async (id) => {
    const confirmado = window.confirm('¿Enviar confirmación por WhatsApp?');
    if (confirmado) {
        await api.enviarConfirmacionWhatsapp(id, {});
        alert('Confirmación enviada');
    }
};
"""

print("Código de Reservas Mejoradas listo para integrar")
