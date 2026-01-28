from rest_framework import serializers
from .models import Reserva


class ReservaSerializer(serializers.ModelSerializer):
    # Campos relacionados de Ruta
    ruta_nombre = serializers.CharField(source='ruta.nombre', read_only=True)
    ruta_origen = serializers.CharField(source='ruta.origen', read_only=True)
    ruta_destino = serializers.CharField(source='ruta.destino', read_only=True)
    ruta_tarifa = serializers.DecimalField(source='ruta.tarifa_base', max_digits=10, decimal_places=2, read_only=True)
    
    # Campos relacionados de Afiliado
    afiliado_nombre = serializers.SerializerMethodField()
    afiliado_telefono = serializers.CharField(source='afiliado.telefono', read_only=True)
    
    class Meta:
        model = Reserva
        fields = [
            'id', 'afiliado', 'cliente', 'telefono', 'ruta', 'fecha_viaje', 'cantidad', 'asiento', 'estado',
            'ruta_nombre', 'ruta_origen', 'ruta_destino', 'ruta_tarifa',
            'afiliado_nombre', 'afiliado_telefono',
            'created_at', 'updated_at'
        ]
    
    def get_afiliado_nombre(self, obj):
        if obj.afiliado:
            return f"{obj.afiliado.apellidos} {obj.afiliado.nombres}"
        return None