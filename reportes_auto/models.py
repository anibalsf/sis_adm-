from django.db import models
from django.utils import timezone

class ReporteGenerado(models.Model):
    """
    Registro de reportes generados y enviados
    """
    TIPO_CHOICES = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('lunes_control', 'Control Lunes (Hojas Ruta)'),
    ]
    
    ESTADO_CHOICES = [
        ('generado', 'Generado'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo de Reporte')
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Generación')
    fecha_periodo = models.DateField(verbose_name='Fecha del Período', help_text='Fecha del día/semana/mes reportado')
    
    contenido = models.TextField(verbose_name='Contenido del Reporte')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='generado', verbose_name='Estado')
    
    # Destinatarios
    destinatarios_whatsapp = models.TextField(blank=True, verbose_name='Teléfonos Destinatarios', help_text='Separados por coma')
    destinatarios_email = models.TextField(blank=True, verbose_name='Emails Destinatarios', help_text='Separados por coma')
    
    # Metadata
    mensajes_enviados = models.IntegerField(default=0, verbose_name='Mensajes Enviados')
    error_message = models.TextField(blank=True, verbose_name='Mensaje de Error')
    
    class Meta:
        verbose_name = 'Reporte Generado'
        verbose_name_plural = 'Reportes Generados'
        ordering = ['-fecha_generacion']
        indexes = [
            models.Index(fields=['-fecha_generacion']),
            models.Index(fields=['tipo', 'estado']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_periodo.strftime('%d/%m/%Y')}"


class ConfiguracionReporte(models.Model):
    """
    Configuración de reportes automáticos
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    tipo = models.CharField(max_length=20, choices=ReporteGenerado.TIPO_CHOICES, verbose_name='Tipo')
    
    # Configuración de envío
    activo = models.BooleanField(default=True, verbose_name='Activo')
    hora_envio = models.TimeField(default='08:00', verbose_name='Hora de Envío')
    
    # Destinatarios por defecto
    destinatarios_whatsapp = models.TextField(blank=True, verbose_name='Teléfonos WhatsApp', help_text='Separados por coma')
    destinatarios_email = models.TextField(blank=True, verbose_name='Emails', help_text='Separados por coma')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'
    
    def __str__(self):
        return f"{self.nombre} ({'Activo' if self.activo else 'Inactivo'})"
