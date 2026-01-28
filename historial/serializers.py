from rest_framework import serializers
from .models import CambioEstado, LogAuditoria

class CambioEstadoSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='usuario.username')
    model_name = serializers.SerializerMethodField()
    content_object_str = serializers.SerializerMethodField()

    class Meta:
        model = CambioEstado
        fields = [
            'id', 'content_type', 'object_id', 'model_name', 
            'content_object_str', 'estado_anterior', 'estado_nuevo', 
            'usuario', 'username', 'timestamp'
        ]

    def get_model_name(self, obj):
        return obj.content_type.model

    def get_content_object_str(self, obj):
        return str(obj.content_object) if obj.content_object else f"ID: {obj.object_id}"

class LogAuditoriaSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='usuario.username')
    full_name = serializers.SerializerMethodField()
    accion_display = serializers.CharField(source='get_accion_display', read_only=True)

    class Meta:
        model = LogAuditoria
        fields = [
            'id', 'usuario', 'username', 'full_name', 'accion', 
            'accion_display', 'tabla', 'objeto_id', 'descripcion', 
            'cambios', 'ip_address', 'fecha_hora'
        ]

    def get_full_name(self, obj):
        if obj.usuario:
            return f"{obj.usuario.first_name} {obj.usuario.last_name}".strip() or obj.usuario.username
        return "Sistema"