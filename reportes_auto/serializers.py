from rest_framework import serializers
from .models import ReporteGenerado, ConfiguracionReporte


class ReporteGeneradoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = ReporteGenerado
        fields = [
            'id', 'tipo', 'tipo_display', 'fecha_generacion', 'fecha_periodo',
            'contenido', 'estado', 'estado_display', 'destinatarios_whatsapp',
            'destinatarios_email', 'mensajes_enviados', 'error_message'
        ]
        read_only_fields = ['id', 'fecha_generacion']


class ConfiguracionReporteSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = ConfiguracionReporte
        fields = [
            'id', 'nombre', 'tipo', 'tipo_display', 'activo', 'hora_envio',
            'destinatarios_whatsapp', 'destinatarios_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
