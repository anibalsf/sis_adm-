from django.contrib import admin
from .models import WhatsAppMessage, WhatsAppTemplate, WhatsAppConfig


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'recipient_name',
        'recipient_phone',
        'message_type',
        'status',
        'created_at',
        'sent_at'
    ]
    list_filter = ['status', 'message_type', 'created_at']
    search_fields = ['recipient_name', 'recipient_phone', 'message_content']
    readonly_fields = [
        'external_message_id',
        'created_at',
        'sent_at',
        'delivered_at',
        'status'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Destinatario', {
            'fields': ('recipient_phone', 'recipient_name')
        }),
        ('Mensaje', {
            'fields': ('message_type', 'message_content', 'status')
        }),
        ('IDs Relacionados', {
            'fields': (
                'related_payment_id',
                'related_reservation_id',
                'related_sanction_id'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'external_message_id',
                'error_message',
                'created_at',
                'sent_at',
                'delivered_at'
            )
        }),
    )


@admin.register(WhatsAppTemplate)
class WhatsAppTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'message_type', 'is_active', 'created_at']
    list_filter = ['message_type', 'is_active']
    search_fields = ['name', 'template_content']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'message_type', 'is_active')
        }),
        ('Contenido', {
            'fields': ('template_content',),
            'description': 'Use {variable} para variables dinámicas. Ej: Hola {nombre}, su pago de {monto} Bs fue recibido.'
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WhatsAppConfig)
class WhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ['provider', 'is_enabled', 'daily_message_limit', 'updated_at']
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('provider', 'is_enabled')
        }),
        ('Límites y Reintentos', {
            'fields': (
                'max_retries',
                'retry_delay_minutes',
                'daily_message_limit'
            )
        }),
    )
    
    def has_add_permission(self, request):
        # Solo permitir una configuración
        return not WhatsAppConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False
