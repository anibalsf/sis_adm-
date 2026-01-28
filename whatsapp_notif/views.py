"""
Views y ViewSets para API de WhatsApp
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import WhatsAppMessage, WhatsAppTemplate, WhatsAppConfig
from .serializers import (
    WhatsAppMessageSerializer,
    WhatsAppTemplateSerializer,
    WhatsAppConfigSerializer,
    SendMessageSerializer,
    SendTemplateMessageSerializer
)
from .services import whatsapp_service


class WhatsAppMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para consultar mensajes WhatsApp enviados
    Solo lectura - los mensajes se crean automáticamente
    """
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'status': ['exact'],
        'message_type': ['exact'],
        'recipient_phone': ['exact', 'icontains'],
        'created_at': ['gte', 'lte', 'date'],
    }
    search_fields = ['recipient_name', 'recipient_phone', 'message_content']
    ordering_fields = ['created_at', 'sent_at', 'delivered_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['post'])
    def send_manual(self, request):
        """
        Endpoint para envío manual de mensajes
        POST /api/whatsapp/messages/send_manual/
        """
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enviar mensaje
        result = whatsapp_service.send_message(
            phone=serializer.validated_data['phone'],
            message=serializer.validated_data['message'],
            message_type=serializer.validated_data['message_type'],
            recipient_name=serializer.validated_data.get('recipient_name', ''),
        )
        
        if result:
            return Response(
                WhatsAppMessageSerializer(result).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'error': 'No se pudo enviar el mensaje. Verifique la configuración.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def send_from_template(self, request):
        """
        Endpoint para envío de mensajes usando plantilla
        POST /api/whatsapp/messages/send_from_template/
        """
        serializer = SendTemplateMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enviar mensaje usando plantilla
        result = whatsapp_service.send_from_template(
            template_name=serializer.validated_data['template_name'],
            phone=serializer.validated_data['phone'],
            context=serializer.validated_data['context'],
            recipient_name=serializer.validated_data.get('recipient_name', ''),
        )
        
        if result:
            return Response(
                WhatsAppMessageSerializer(result).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'error': 'No se pudo enviar el mensaje. Verifique la plantilla y configuración.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Estadísticas de mensajes enviados
        GET /api/whatsapp/messages/stats/
        """
        from django.db.models import Count
        
        stats = {
            'total': WhatsAppMessage.objects.count(),
            'by_status': dict(
                WhatsAppMessage.objects.values('status')
                .annotate(count=Count('id'))
                .values_list('status', 'count')
            ),
            'by_type': dict(
                WhatsAppMessage.objects.values('message_type')
                .annotate(count=Count('id'))
                .values_list('message_type', 'count')
            ),
            'today': WhatsAppMessage.objects.filter(
                created_at__date=request.query_params.get('date', 'today')
            ).count() if request.query_params.get('date') else 0,
        }
        
        return Response(stats)
        
    @action(detail=False, methods=['post'], url_path='trigger-reminders')
    def trigger_reminders(self, request):
        """
        Gatillar manualmente los recordatorios de turno para mañana
        POST /api/whatsapp/messages/trigger-reminders/
        """
        from .tasks import send_shift_reminders
        
        result = send_shift_reminders()
        
        if result.get('success'):
            return Response({
                'message': f"Se procesaron los recordatorios. Enviados: {result.get('sent')}, Errores: {result.get('errors')}",
                'data': result
            })
        else:
            return Response({
                'error': f"Error al procesar recordatorios: {result.get('error')}",
                'data': result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WhatsAppTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para plantillas de WhatsApp
    """
    queryset = WhatsAppTemplate.objects.all()
    serializer_class = WhatsAppTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['message_type', 'is_active']
    search_fields = ['name', 'template_content']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Probar una plantilla con datos de ejemplo
        POST /api/whatsapp/templates/{id}/test/
        Body: {"context": {"nombre": "Juan", "monto": "50"}}
        """
        template = self.get_object()
        context = request.data.get('context', {})
        
        rendered = template.render(context)
        
        return Response({
            'template_name': template.name,
            'context': context,
            'rendered_message': rendered
        })


class WhatsAppConfigViewSet(viewsets.ModelViewSet):
    """
    Configuración global de WhatsApp (solo una instancia)
    """
    queryset = WhatsAppConfig.objects.all()
    serializer_class = WhatsAppConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Siempre retornar la configuración única"""
        return WhatsAppConfig.get_config()
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Obtener configuración actual"""
        config = WhatsAppConfig.get_config()
        return Response(WhatsAppConfigSerializer(config).data)
    
    @action(detail=False, methods=['post'])
    def test_connection(self, request):
        """
        Probar conexión con el proveedor de WhatsApp
        POST /api/whatsapp/config/test_connection/
        """
        # Enviar mensaje de prueba
        test_phone = request.data.get('test_phone')
        if not test_phone:
            return Response(
                {'error': 'Se requiere test_phone'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = whatsapp_service.send_message(
            phone=test_phone,
            message="🔔 Mensaje de prueba del sistema.\n\nSi recibiste este mensaje, la configuración de WhatsApp funciona correctamente. ✅",
            message_type='general',
            recipient_name='Prueba'
        )
        
        if result and result.status == 'sent':
            return Response({
                'success': True,
                'message': 'Mensaje de prueba enviado correctamente',
                'message_id': result.id
            })
        else:
            return Response({
                'success': False,
                'error': result.error_message if result else 'Error desconocido'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
