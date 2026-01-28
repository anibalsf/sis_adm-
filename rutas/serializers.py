from rest_framework import serializers
from .models import Ruta


class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruta
        fields = ['id', 'nombre', 'origen', 'destino', 'tarifa_base', 'prefijo', 'created_at', 'updated_at']