from rest_framework import serializers
from .models import Encomienda

class MinimalHojaRutaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ruta_nombre = serializers.CharField(source='ruta.nombre', read_only=True)
    fecha_salida = serializers.DateTimeField(read_only=True)
    vehiculo_placa = serializers.CharField(source='vehiculo.placa', read_only=True)
    chofer_nombre = serializers.CharField(source='afiliado.nombre_completo', read_only=True)

class EncomiendaSerializer(serializers.ModelSerializer):
    hoja_ruta_detalle = MinimalHojaRutaSerializer(source='hoja_ruta', read_only=True)

    class Meta:
        model = Encomienda
        fields = '__all__'
        read_only_fields = ['codigo_tracking', 'fecha_registro']
