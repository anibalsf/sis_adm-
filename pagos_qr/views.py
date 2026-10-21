import hashlib
import hmac

from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import QRTransaccion
from .serializers import QRTransaccionSerializer, QRGenerationSerializer
from .services import QRService

class QRTransactionViewSet(viewsets.ModelViewSet):
    queryset = QRTransaccion.objects.all()
    serializer_class = QRTransaccionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        """
        Generar un nuevo QR.
        Payload: { "monto": 50.00, "glosa": "Pago Sanción" }
        """
        serializer = QRGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        monto = serializer.validated_data['monto']
        glosa = serializer.validated_data['glosa']
        valid_hours = serializer.validated_data.get('valid_hours', 24)
        
        try:
            qr_obj = QRService.generate_qr(monto, glosa, valid_hours)
            response_serializer = QRTransaccionSerializer(qr_obj)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def webhook(self, request):
        """
        Endpoint público para recibir callbacks del banco.
        Requiere la firma HMAC-SHA256 del cuerpo en el header X-QR-Signature,
        calculada con QR_WEBHOOK_SECRET. En desarrollo (sin secreto y DEBUG=True)
        se permite sin firma para poder simular.
        """
        if not self._firma_valida(request):
            return Response({'error': 'Firma inválida'}, status=status.HTTP_401_UNAUTHORIZED)

        transaction_id = request.data.get('transaction_id')
        if not transaction_id:
            return Response({'error': 'transaction_id missing'}, status=status.HTTP_400_BAD_REQUEST)
        
        success, msg = QRService.verify_payment(transaction_id)
        
        if success:
            # Aquí se podría mejorar para notificar al usuario (WhatsApp, WebSocket, etc)
            return Response({'status': 'ok', 'message': msg})
        else:
            return Response({'status': 'error', 'message': msg}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def _firma_valida(request):
        secret = (getattr(settings, 'QR_WEBHOOK_SECRET', '') or '').strip()
        if not secret:
            # Sin secreto configurado: solo se permite en entorno de desarrollo.
            return settings.DEBUG
        signature = request.headers.get('X-QR-Signature', '')
        expected = hmac.new(secret.encode('utf-8'), request.body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

    @action(detail=False, methods=['post'])
    def verify(self, request):
        """
        Verificación autenticada de un QR (botón "Verificar pago" del cajero).
        Confirma con el banco y, si el pago se completó, marca el Pago y las
        sanciones/cuotas vinculadas como pagadas.
        """
        transaction_id = request.data.get('transaction_id')
        if not transaction_id:
            return Response({'error': 'transaction_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = QRService.verify_payment(transaction_id)
        if success:
            return Response({'status': 'ok', 'message': msg})
        return Response({'status': 'error', 'message': msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='verify-public')
    def verify_public(self, request):
        """
        Verificación desde la pizarra pública de reservas.
        El transaction_id es un UUID no adivinable que el pasajero recibe al
        generar su QR; en producción el pago real lo confirma el banco por webhook.
        """
        transaction_id = request.data.get('transaction_id')
        if not transaction_id:
            return Response({'error': 'transaction_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

        success, msg = QRService.verify_payment(transaction_id)
        if success:
            return Response({'status': 'ok', 'message': msg})
        return Response({'status': 'error', 'message': msg}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        instance = self.get_object()
        # En producción, aquí consultaríamos al API del banco si sigue pendiente
        return Response({
            'transaction_id': instance.transaction_id,
            'estado': instance.estado,
            'expiration_date': instance.expiration_date,
            'updated_at': instance.updated_at
        })
