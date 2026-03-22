from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Encomienda
from .serializers import EncomiendaSerializer
from hojasruta.models import HojaRuta

class EncomiendaViewSet(viewsets.ModelViewSet):
    queryset = Encomienda.objects.all()
    serializer_class = EncomiendaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'pagado', 'hoja_ruta']
    search_fields = ['codigo_tracking', 'remitente_nombre', 'destinatario_nombre']
    ordering_fields = ['fecha_registro', 'fecha_entrega', 'precio']

    @action(detail=True, methods=['get'])
    def generar_qr(self, request, pk=None):
        encomienda = self.get_object()
        import qrcode
        import base64
        from io import BytesIO
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(encomienda.codigo_tracking)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return Response({'qr_base64': img_str, 'codigo': encomienda.codigo_tracking})

    @action(detail=True, methods=['post'])
    def notificar_whatsapp(self, request, pk=None):
        encomienda = self.get_object()
        tipo = request.data.get('tipo', 'registro') # registro | llegada | entrega
        
        if tipo == 'registro':
            mensaje = (
                f"📦 *Sindicato Integración Taipiplaya - Encomienda Registrada*\n\n"
                f"Su envío con código *{encomienda.codigo_tracking}* ha sido recibido en oficina.\n"
                f"• Contenido: {encomienda.descripcion}\n"
                f"• De: {encomienda.remitente_nombre}\n"
                f"• Para: {encomienda.destinatario_nombre}\n\n"
                f"Le notificaremos cuando esté disponible para recojo."
            )
            telefono = encomienda.remitente_telefono
        elif tipo == 'llegada':
            mensaje = (
                f"🚌 *AVISO: Su encomienda ha llegado*\n\n"
                f"Sr(a). {encomienda.destinatario_nombre}, su paquete con código *{encomienda.codigo_tracking}* ya se encuentra en oficina de destino.\n"
                f"Por favor pase a recogerlo.\n\n"
                f"_Sindicato Integración Taipiplaya_"
            )
            telefono = encomienda.destinatario_telefono
        elif tipo == 'entrega':
            mensaje = (
                f"✅ *SU ENCOMIENDA HA SIDO ENTREGADA*\n\n"
                f"El paquete *{encomienda.codigo_tracking}* dirigido a {encomienda.destinatario_nombre} fue entregado con éxito.\n"
                f"¡Gracias por confiar en nosotros!"
            )
            telefono = encomienda.remitente_telefono
        else:
            return Response({'detail': 'Tipo de notificación inválido'}, status=400)
            
        try:
            from whatsapp_notif.services import whatsapp_service
            # Limpiar teléfono
            clean_phone = ''.join(filter(str.isdigit, str(telefono)))
            if clean_phone.startswith('0'): clean_phone = clean_phone[1:]
            
            res = whatsapp_service.send_message(
                phone=clean_phone,
                message=mensaje,
                message_type=f'encomienda_{tipo}',
                recipient_name=encomienda.destinatario_nombre if tipo=='llegada' else encomienda.remitente_nombre
            )
            return Response({'detail': 'Notificación enviada', 'res': res})
        except Exception as e:
            return Response({'detail': f'Error al enviar WhatsApp: {str(e)}'}, status=500)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        encomienda = self.get_object()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado in dict(Encomienda.ESTADOS):
            encomienda.estado = nuevo_estado
            if nuevo_estado == 'entregado' and not encomienda.fecha_entrega:
                encomienda.fecha_entrega = timezone.now()
            encomienda.save()
            return Response(self.get_serializer(encomienda).data)
        return Response({'detail': 'Estado inválido'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def asignar_hoja(self, request, pk=None):
        encomienda = self.get_object()
        hoja_id = request.data.get('hoja_ruta_id')
        if hoja_id:
            try:
                hoja = HojaRuta.objects.get(id=hoja_id)
                encomienda.hoja_ruta = hoja
                encomienda.estado = 'en_transito'
                encomienda.save()
                return Response(self.get_serializer(encomienda).data)
            except HojaRuta.DoesNotExist:
                return Response({'detail': 'Hoja de ruta no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'detail': 'ID de hoja de ruta requerido'}, status=status.HTTP_400_BAD_REQUEST)
