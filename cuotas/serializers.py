from rest_framework import serializers
from .models import Cuota


class CuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuota
        fields = ['id', 'afiliado', 'periodo', 'tipo', 'monto', 'estado', 'fecha_pago', 'created_at', 'updated_at']