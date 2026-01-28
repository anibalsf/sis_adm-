from rest_framework import serializers
from .models import DocumentacionVehiculo, MantenimientoHistorial
from vehiculos.models import Vehiculo

class DocumentacionVehiculoSerializer(serializers.ModelSerializer):
    vehiculo_placa = serializers.ReadOnlyField(source='vehiculo.placa')
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = DocumentacionVehiculo
        fields = '__all__'

class MantenimientoHistorialSerializer(serializers.ModelSerializer):
    vehiculo_placa = serializers.ReadOnlyField(source='vehiculo.placa')
    tipo_servicio_display = serializers.CharField(source='get_tipo_servicio_display', read_only=True)
    
    class Meta:
        model = MantenimientoHistorial
        fields = '__all__'
