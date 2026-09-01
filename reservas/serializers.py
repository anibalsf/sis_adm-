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
    afiliado_direccion = serializers.CharField(source='afiliado.direccion', read_only=True)
    hora_salida = serializers.SerializerMethodField()
    
    # Campos relacionados de Vehículo
    vehiculo_tipo = serializers.SerializerMethodField()
    vehiculo_placa = serializers.SerializerMethodField()
    
    class Meta:
        model = Reserva
        fields = [
            'id', 'afiliado', 'cliente', 'telefono', 'ruta', 'fecha_viaje', 'cantidad', 'asiento', 'estado',
            'ruta_nombre', 'ruta_origen', 'ruta_destino', 'ruta_tarifa',
            'afiliado_nombre', 'afiliado_telefono', 'afiliado_direccion',
            'vehiculo_tipo', 'vehiculo_placa',
            'hora_salida',
            'created_at', 'updated_at'
        ]
    
    def get_afiliado_nombre(self, obj):
        if obj.afiliado:
            return f"{obj.afiliado.apellidos} {obj.afiliado.nombres}"
        return None

    def get_vehiculo_tipo(self, obj):
        from hojasruta.models import HojaRuta
        hoja = HojaRuta.objects.filter(
            ruta=obj.ruta,
            fecha_salida=obj.fecha_viaje,
            estado__in=['emitida', 'notificada', 'pagada']
        ).first()
        return hoja.vehiculo.tipo if hoja and hoja.vehiculo else "No asignado"

    def get_vehiculo_placa(self, obj):
        from hojasruta.models import HojaRuta
        hoja = HojaRuta.objects.filter(
            ruta=obj.ruta,
            fecha_salida=obj.fecha_viaje,
            estado__in=['emitida', 'notificada', 'pagada']
        ).first()
        return hoja.vehiculo.placa if hoja and hoja.vehiculo else None

    def get_hora_salida(self, obj):
        from hojasruta.models import HojaRuta
        hoja = HojaRuta.objects.filter(
            ruta=obj.ruta,
            fecha_salida=obj.fecha_viaje,
            estado__in=['emitida', 'notificada', 'pagada']
        ).first()
        return hoja.hora_salida.strftime('%H:%M') if hoja and hoja.hora_salida else None
