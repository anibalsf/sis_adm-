from rest_framework import serializers
from .models import Asistencia


class AsistenciaSerializer(serializers.ModelSerializer):
    afiliado_nombre = serializers.SerializerMethodField()
    reunion_tema = serializers.CharField(source='reunion.tema', read_only=True)
    
    class Meta:
        model = Asistencia
        fields = ['id', 'reunion', 'reunion_tema', 'afiliado', 'afiliado_nombre', 'presente', 'estado', 'observaciones', 'created_at']
        read_only_fields = ['created_at', 'updated_at', 'presente']
    
    def get_afiliado_nombre(self, obj):
        """Retorna el nombre completo del afiliado"""
        return f"{obj.afiliado.apellidos} {obj.afiliado.nombres}"