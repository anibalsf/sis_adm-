from rest_framework import serializers
from .models import Sancion


class SancionSerializer(serializers.ModelSerializer):
    afiliado_nombre = serializers.SerializerMethodField()
    afiliado_telefono = serializers.CharField(source='afiliado.telefono', read_only=True)
    
    class Meta:
        model = Sancion
        fields = ['id', 'afiliado', 'afiliado_nombre', 'afiliado_telefono', 'tipo', 'motivo', 'monto', 'estado', 'referencia_asistencia', 'created_at', 'updated_at']
    
    def get_afiliado_nombre(self, obj):
        """Retorna el nombre completo del afiliado"""
        return f"{obj.afiliado.apellidos} {obj.afiliado.nombres}"