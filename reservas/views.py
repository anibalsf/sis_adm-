from rest_framework import viewsets, filters, permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .models import Reserva
from .serializers import ReservaSerializer
from comunicacion.models import Notificacion
from django.conf import settings
import urllib.request
import json
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from pagos_qr.services import QRService


class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.select_related('afiliado', 'ruta').all()
    serializer_class = ReservaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cliente', 'ruta__nombre', 'afiliado__ci']
    ordering_fields = ['fecha_viaje', 'cantidad']

    def get_permissions(self):
        """
        Permisos especiales:
        - Crear reservas y generar QR de pago es público (para pasajeros).
        - Ver detalles o editar requiere ser personal autorizado.
        """
        if self.action in ['create', 'generar_pago_qr', 'public_retrieve']:
            return [permissions.AllowAny()]
        
        if self.action == 'notificar':
            class OnlySecretaria(BasePermission):
                def has_permission(self, request, view):
                    return request.user and request.user.is_authenticated and \
                           request.user.groups.filter(name='Secretaria').exists()
            return [OnlySecretaria()]
            
        # Para el resto de acciones (LIST, RETRIEVE, UPDATE, DELETE)
        class IsStaffOrAuthenticatedReadOnly(BasePermission):
            def has_permission(self, request, view):
                if request.method in SAFE_METHODS:
                    return True # Ver lista de reservas requiere login (o no?)
                return request.user and request.user.is_authenticated and \
                       (request.user.is_superuser or \
                        request.user.groups.filter(name__in=['Secretaria', 'Directiva']).exists())
        
        return [IsStaffOrAuthenticatedReadOnly()]

    def create(self, request, *args, **kwargs):
        """Validar capacidad antes de crear reserva"""
        from django.db.models import Sum
        from hojasruta.models import HojaRuta
        
        ruta_id = request.data.get('ruta')
        fecha_viaje = request.data.get('fecha_viaje')
        cantidad = int(request.data.get('cantidad', 1))
        
        # Buscar hoja de ruta correspondiente
        try:
            hoja = HojaRuta.objects.select_related('vehiculo').get(
                ruta_id=ruta_id,
                fecha_salida=fecha_viaje,
                estado='emitida'
            )
        except HojaRuta.DoesNotExist:
            return Response(
                {'detail': 'No hay hoja de ruta disponible para esta fecha'},
                status=400
            )
        
        # Calcular cupos disponibles
        reservas_activas = Reserva.objects.filter(
            ruta_id=ruta_id,
            fecha_viaje=fecha_viaje,
            estado__in=['pendiente', 'confirmada']
        ).aggregate(total=Sum('cantidad'))
        
        cupos_reservados = reservas_activas['total'] or 0
        capacidad_total = hoja.vehiculo.capacidad if hoja.vehiculo else 0
        cupos_disponibles = capacidad_total - cupos_reservados
        
        # Validar capacidad
        if cantidad > cupos_disponibles:
            return Response(
                {
                    'detail': f'No hay suficientes cupos. Disponibles: {cupos_disponibles}, Solicitados: {cantidad}',
                    'cupos_disponibles': cupos_disponibles,
                    'cantidad_solicitada': cantidad
                },
                status=400
            )
        
        # Continuar con la creación normal
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        # Enviar confirmación automática por WhatsApp
        try:
            from comunicacion.services import WhatsAppService
            WhatsAppService().send_reserva_confirmation(instance)
        except Exception as e:
            print(f"Error enviando confirmación WhatsApp: {e}")

    @action(detail=True, methods=['post'])
    def notificar(self, request, pk=None):
        obj = self.get_object()
        telefono = request.data.get('telefono')
        mensaje = request.data.get('mensaje')
        
        from comunicacion.services import WhatsAppService
        success, result = WhatsAppService().send_message(telefono, mensaje or f"Reserva {obj.id} actualizada")
        
        return Response({
            'detail': 'Notificación procesada',
            'success': success,
            'result': result
        })
    
    @action(detail=True, methods=['get'])
    def generar_qr(self, request, pk=None):
        """Genera código QR para la reserva"""
        reserva = self.get_object()
        
        # Datos del QR
        qr_data = {
            'tipo': 'reserva',
            'id': reserva.id,
            'cliente': reserva.cliente,
            'ruta': reserva.ruta.nombre if reserva.ruta else '',
            'fecha_viaje': str(reserva.fecha_viaje),
            'cantidad': reserva.cantidad,
            'asiento': reserva.asiento,
            'estado': reserva.estado
        }
        
        # Generar QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return HttpResponse(buffer.getvalue(), content_type='image/png')
    
    @action(detail=True, methods=['get'])
    def generar_confirmacion_pdf(self, request, pk=None):
        """Genera PDF de confirmación con QR integrado"""
        reserva = self.get_object()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E7D32'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        elements.append(Paragraph("CONFIRMACIÓN DE RESERVA", title_style))
        elements.append(Paragraph("Sindicato Taipiplaya", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Número de confirmación
        conf_style = ParagraphStyle(
            'Confirmation',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#1976D2'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        elements.append(Paragraph(
            f"<b>Nº Confirmación: RES-{str(reserva.id).zfill(6)}</b>", 
            conf_style
        ))
        elements.append(Spacer(1, 0.2*inch))
        
        # Datos de la reserva
        data = [
            ['Cliente:', reserva.cliente],
            ['Ruta:', reserva.ruta.nombre if reserva.ruta else 'N/A'],
            ['Fecha de Viaje:', reserva.fecha_viaje.strftime('%d/%m/%Y')],
            ['Cantidad de Pasajes:', str(reserva.cantidad)],
            ['Asiento:', str(reserva.asiento) if reserva.asiento else 'Por asignar'],
            ['Estado:', reserva.estado.upper()],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E9')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Generar QR y agregarlo
        qr_buffer = BytesIO()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps({
            'tipo': 'reserva',
            'id': reserva.id,
            'cliente': reserva.cliente,
            'fecha': str(reserva.fecha_viaje)
        }))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Agregar QR al PDF
        qr_image = Image(qr_buffer, width=2*inch, height=2*inch)
        elements.append(qr_image)
        
        # Nota al pie
        elements.append(Spacer(1, 0.3*inch))
        note_style = ParagraphStyle(
            'Note',
            parent=styles['Italic'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            "Presente este código QR al momento de abordar.",
            note_style
        ))
        elements.append(Paragraph(
            f"Documento generado el {reserva.created_at.strftime('%d/%m/%Y %H:%M') if reserva.created_at else 'N/A'}",
            note_style
        ))
        
        doc.build(elements)
        buffer.seek(0)
        
        return HttpResponse(
            buffer.getvalue(),
            content_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="confirmacion_RES-{str(reserva.id).zfill(6)}.pdf"'}
        )
    
    @action(detail=True, methods=['post'])
    def enviar_confirmacion_whatsapp(self, request, pk=None):
        """Envía confirmación de reserva por WhatsApp"""
        reserva = self.get_object()
        telefono = request.data.get('telefono')
        
        if not telefono:
            return Response(
                {'detail': 'Debe proporcionar un número de teléfono'},
                status=400
            )
        
        # Crear mensaje de confirmación
        mensaje = f"""✅ CONFIRMACIÓN DE RESERVA

Nº: RES-{str(reserva.id).zfill(6)}
Cliente: {reserva.cliente}
Ruta: {reserva.ruta.nombre if reserva.ruta else 'N/A'}
Fecha: {reserva.fecha_viaje.strftime('%d/%m/%Y')}
Pasajes: {reserva.cantidad}
Asiento: {reserva.asiento if reserva.asiento else 'Por asignar'}

🚌 Sindicato Taipiplaya
Por favor conserve este mensaje."""
        
        # Crear notificación
        notif = Notificacion.objects.create(
            canal='whatsapp',
            destinatario=telefono,
            mensaje=mensaje,
            estado='pendiente'
        )
        
        # Intentar enviar por webhook si existe
        url = getattr(settings, 'WHATSAPP_WEBHOOK_URL', None)
        if url:
            try:
                data = json.dumps({'to': telefono, 'message': mensaje}).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req, timeout=5)
                notif.estado = 'enviado'
                notif.save()
            except Exception as e:
                notif.estado = 'error'
                notif.save()
                return Response(
                    {'detail': 'Error al enviar WhatsApp', 'error': str(e)},
                    status=500
                )
        
        return Response({
            'detail': 'Confirmación enviada por WhatsApp',
            'notificacion_id': notif.id,
            'mensaje': mensaje
        })

    @action(detail=True, methods=['post'])
    def generar_pago_qr(self, request, pk=None):
        """Generar QR de pago para una reserva (Simulación Yape)"""
        reserva = self.get_object()
        # Intentar obtener el precio de la hoja de ruta relacionada
        from hojasruta.models import HojaRuta
        try:
            hoja = HojaRuta.objects.get(
                ruta=reserva.ruta,
                fecha_salida=reserva.fecha_viaje,
                estado='emitida'
            )
            monto = float(hoja.precio)
        except:
            monto = float(reserva.ruta.tarifa_base) if reserva.ruta else 10.0
            
        glosa = f"Pago Reserva {reserva.id} - A nombre de: Anibal Choque Aguirre"
        
        try:
            qr_obj = QRService.generate_qr(
                monto=monto,
                glosa=glosa,
                content_object=reserva
            )
            return Response({
                'id': qr_obj.id,
                'qr_string': qr_obj.qr_string,
                'imagen_base64': qr_obj.imagen_base64,
                'monto': qr_obj.monto,
                'transaction_id': qr_obj.transaction_id,
                'metodo': 'Yape'
            })
        except Exception as e:
            return Response({'detail': f'Error al generar QR: {str(e)}'}, status=500)

    @action(detail=True, methods=['get'], url_path='public-retrieve')
    def public_retrieve(self, request, pk=None):
        """Versión pública de retrieve para el voucher del pasajero"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)