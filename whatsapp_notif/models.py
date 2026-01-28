"""
Modelos para el sistema de notificaciones WhatsApp
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class WhatsAppMessage(models.Model):
    """
    Registro de todos los mensajes de WhatsApp enviados
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('delivered', 'Entregado'),
        ('read', 'Leído'),
        ('failed', 'Fallido'),
    ]

    TYPE_CHOICES = [
        ('payment_confirmation', 'Confirmación de Pago'),
        ('shift_reminder', 'Recordatorio de Turno'),
        ('sanction_notice', 'Notificación de Sanción'),
        ('reservation_confirmation', 'Confirmación de Reserva'),
        ('meeting_reminder', 'Recordatorio de Reunión'),
        ('debt_reminder', 'Recordatorio de Deuda'),
        ('cuota_payment', 'Pago de Cuota'),
        ('general', 'General'),
    ]

    # Información del destinatario
    recipient_phone = models.CharField(
        max_length=20,
        verbose_name='Teléfono Destinatario',
        help_text='Formato: +591XXXXXXXX'
    )
    recipient_name = models.CharField(
        max_length=255,
        verbose_name='Nombre Destinatario',
        blank=True
    )

    # Contenido del mensaje
    message_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default='general',
        verbose_name='Tipo de Mensaje'
    )
    message_content = models.TextField(
        verbose_name='Contenido del Mensaje'
    )
    
    # Metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )
    
    # IDs externos (Twilio, etc.)
    external_message_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ID Externo',
        help_text='SID de Twilio u otro identificador'
    )
    
    # Relaciones opcionales
    related_payment_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='ID de Pago Relacionado'
    )
    related_reservation_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='ID de Reserva Relacionada'
    )
    related_sanction_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='ID de Sanción Relacionada'
    )
    related_cuota_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='ID de Cuota Relacionada'
    )
    
    # Información de error (si falla)
    error_message = models.TextField(
        blank=True,
        verbose_name='Mensaje de Error'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Envío'
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Entrega'
    )
    
    # Usuario que generó el mensaje (opcional)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Creado Por'
    )

    class Meta:
        verbose_name = 'Mensaje WhatsApp'
        verbose_name_plural = 'Mensajes WhatsApp'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['recipient_phone']),
            models.Index(fields=['message_type']),
        ]

    def __str__(self):
        return f"{self.get_message_type_display()} - {self.recipient_phone} ({self.status})"

    def mark_as_sent(self, external_id=None):
        """Marcar mensaje como enviado"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if external_id:
            self.external_message_id = external_id
        self.save(update_fields=['status', 'sent_at', 'external_message_id'])

    def mark_as_delivered(self):
        """Marcar mensaje como entregado"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])

    def mark_as_failed(self, error_msg):
        """Marcar mensaje como fallido"""
        self.status = 'failed'
        self.error_message = error_msg
        self.save(update_fields=['status', 'error_message'])


class WhatsAppTemplate(models.Model):
    """
    Plantillas predefinidas para mensajes de WhatsApp
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de Plantilla'
    )
    message_type = models.CharField(
        max_length=50,
        choices=WhatsAppMessage.TYPE_CHOICES,
        verbose_name='Tipo de Mensaje'
    )
    template_content = models.TextField(
        verbose_name='Contenido de Plantilla',
        help_text='Use {variable} para variables dinámicas. Ej: Hola {nombre}, su pago de {monto} Bs fue recibido.'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        verbose_name = 'Plantilla WhatsApp'
        verbose_name_plural = 'Plantillas WhatsApp'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_message_type_display()})"

    def render(self, context):
        """
        Renderizar plantilla con variables del contexto
        
        Args:
            context (dict): Diccionario con variables {nombre: 'Juan', monto: 50}
        
        Returns:
            str: Mensaje renderizado
        """
        message = self.template_content
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            message = message.replace(placeholder, str(value))
        return message


class WhatsAppConfig(models.Model):
    """
    Configuración global del sistema WhatsApp
    """
    PROVIDER_CHOICES = [
        ('twilio', 'Twilio'),
        ('baileys', 'Baileys'),
        ('whatsapp_business', 'WhatsApp Business API'),
    ]

    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        default='twilio',
        verbose_name='Proveedor'
    )
    is_enabled = models.BooleanField(
        default=False,
        verbose_name='Habilitado',
        help_text='Activar/desactivar envío de mensajes'
    )
    
    # Configuración de reintentos
    max_retries = models.IntegerField(
        default=3,
        verbose_name='Máximo de Reintentos'
    )
    retry_delay_minutes = models.IntegerField(
        default=5,
        verbose_name='Delay entre Reintentos (minutos)'
    )
    
    # Límites
    daily_message_limit = models.IntegerField(
        default=1000,
        verbose_name='Límite Diario de Mensajes',
        help_text='0 = sin límite'
    )
    
    # Timestamps
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        verbose_name = 'Configuración WhatsApp'
        verbose_name_plural = 'Configuración WhatsApp'

    def __str__(self):
        status = "Habilitado" if self.is_enabled else "Deshabilitado"
        return f"WhatsApp - {self.get_provider_display()} ({status})"

    @classmethod
    def get_config(cls):
        """Obtener o crear configuración única"""
        config, _ = cls.objects.get_or_create(pk=1)
        return config
