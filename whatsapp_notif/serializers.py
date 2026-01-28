from rest_framework import serializers
from .models import WhatsAppMessage, WhatsAppTemplate, WhatsAppConfig


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    """Serializer para mensajes WhatsApp"""
    
    message_type_display = serializers.CharField(
        source='get_message_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = WhatsAppMessage
        fields = [
            'id',
            'recipient_phone',
            'recipient_name',
            'message_type',
            'message_type_display',
            'message_content',
            'status',
            'status_display',
            'external_message_id',
            'related_payment_id',
            'related_reservation_id',
            'related_sanction_id',
            'error_message',
            'created_at',
            'sent_at',
            'delivered_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'external_message_id',
            'sent_at',
            'delivered_at',
            'created_at',
        ]


class WhatsAppTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas WhatsApp"""
    
    message_type_display = serializers.CharField(
        source='get_message_type_display',
        read_only=True
    )
    
    class Meta:
        model = WhatsAppTemplate
        fields = [
            'id',
            'name',
            'message_type',
            'message_type_display',
            'template_content',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WhatsAppConfigSerializer(serializers.ModelSerializer):
    """Serializer para configuración WhatsApp"""
    
    provider_display = serializers.CharField(
        source='get_provider_display',
        read_only=True
    )
    
    class Meta:
        model = WhatsAppConfig
        fields = [
            'id',
            'provider',
            'provider_display',
            'is_enabled',
            'max_retries',
            'retry_delay_minutes',
            'daily_message_limit',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class SendMessageSerializer(serializers.Serializer):
    """Serializer para endpoint de envío manual de mensajes"""
    
    phone = serializers.CharField(
        max_length=20,
        required=True,
        help_text='Número de teléfono (+591XXXXXXXX)'
    )
    message = serializers.CharField(
        required=True,
        help_text='Contenido del mensaje'
    )
    recipient_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default=''
    )
    message_type = serializers.ChoiceField(
        choices=WhatsAppMessage.TYPE_CHOICES,
        default='general'
    )


class SendTemplateMessageSerializer(serializers.Serializer):
    """Serializer para envío de mensajes con plantilla"""
    
    template_name = serializers.CharField(
        required=True,
        help_text='Nombre de la plantilla'
    )
    phone = serializers.CharField(
        max_length=20,
        required=True,
        help_text='Número de teléfono (+591XXXXXXXX)'
    )
    context = serializers.JSONField(
        required=True,
        help_text='Variables para la plantilla {"nombre": "Juan", "monto": "50"}'
    )
    recipient_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default=''
    )
