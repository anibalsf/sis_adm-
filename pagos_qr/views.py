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
        Simulación: { "transaction_id": "uuid..." }
        """
        transaction_id = request.data.get('transaction_id')
        if not transaction_id:
            return Response({'error': 'transaction_id missing'}, status=status.HTTP_400_BAD_REQUEST)
        
        success, msg = QRService.verify_payment(transaction_id)
        
        if success:
            # Aquí se podría mejorar para notificar al usuario (WhatsApp, WebSocket, etc)
            return Response({'status': 'ok', 'message': msg})
        else:
            return Response({'status': 'error', 'message': msg}, status=status.HTTP_400_BAD_REQUEST)
            
    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        instance = self.get_object()
        # En producción, aquí consultaríamos al API del banco si sigue pendiente
        return Response({
            'transaction_id': instance.transaction_id,
            'estado': instance.estado,
            'updated_at': instance.updated_at
        })
