from django.contrib import admin
from .models import ReporteGenerado, ConfiguracionReporte

@admin.register(ReporteGenerado)
class ReporteGeneradoAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'fecha_periodo', 'fecha_generacion', 'estado', 'mensajes_enviados']
    list_filter = ['tipo', 'estado', 'fecha_generacion']
    search_fields = ['contenido', 'destinatarios_whatsapp', 'destinatarios_email']
    readonly_fields = ['fecha_generacion', 'contenido', 'mensajes_enviados']
    date_hierarchy = 'fecha_generacion'
    
    fieldsets = (
        ('Información General', {
            'fields': ('tipo', 'fecha_periodo', 'fecha_generacion', 'estado')
        }),
        ('Contenido', {
            'fields': ('contenido',),
            'classes': ('collapse',)
        }),
        ('Destinatarios', {
            'fields': ('destinatarios_whatsapp', 'destinatarios_email', 'mensajes_enviados')
        }),
        ('Errores', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConfiguracionReporte)
class ConfiguracionReporteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'activo', 'hora_envio', 'updated_at']
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre', 'destinatarios_whatsapp', 'destinatarios_email']
    
    fieldsets = (
        ('Configuración Básica', {
            'fields': ('nombre', 'tipo', 'activo', 'hora_envio')
        }),
        ('Destinatarios', {
            'fields': ('destinatarios_whatsapp', 'destinatarios_email'),
            'description': 'Ingrese los números de teléfono o emails separados por coma'
        }),
    )
