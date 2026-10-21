from rest_framework import serializers

from .models import Reserva
from .services import precio_de


class ReservaSerializer(serializers.ModelSerializer):
    cantidad = serializers.IntegerField(min_value=1, default=1)
    asiento = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    # Campos relacionados de Ruta
    ruta_nombre = serializers.CharField(source='ruta.nombre', read_only=True)
    ruta_origen = serializers.CharField(source='ruta.origen', read_only=True)
    ruta_destino = serializers.CharField(source='ruta.destino', read_only=True)
    ruta_tarifa = serializers.DecimalField(
        source='ruta.tarifa_base', max_digits=10, decimal_places=2, read_only=True
    )

    # Campos relacionados de Afiliado
    afiliado_nombre = serializers.SerializerMethodField()
    afiliado_telefono = serializers.CharField(source='afiliado.telefono', read_only=True)
    afiliado_direccion = serializers.CharField(source='afiliado.direccion', read_only=True)
    hora_salida = serializers.SerializerMethodField()

    # Campos relacionados de Vehículo
    vehiculo_tipo = serializers.SerializerMethodField()
    vehiculo_placa = serializers.SerializerMethodField()

    # Montos calculados para filas antiguas sin monto guardado
    monto_unitario = serializers.SerializerMethodField()
    monto_total = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = [
            'id', 'afiliado', 'cliente', 'telefono', 'ruta', 'hoja_ruta', 'fecha_viaje',
            'cantidad', 'asiento', 'estado',
            'monto_unitario', 'monto_total', 'grupo_id',
            'fecha_anulacion', 'motivo_anulacion',
            'ruta_nombre', 'ruta_origen', 'ruta_destino', 'ruta_tarifa',
            'afiliado_nombre', 'afiliado_telefono', 'afiliado_direccion',
            'vehiculo_tipo', 'vehiculo_placa',
            'hora_salida',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'estado', 'grupo_id', 'fecha_anulacion', 'motivo_anulacion',
            'created_at', 'updated_at',
        ]
        validators = []

    def _get_hoja(self, obj):
        if getattr(obj, 'hoja_ruta', None):
            return obj.hoja_ruta
        if hasattr(obj, '_hoja_cache'):
            return obj._hoja_cache
        from hojasruta.models import HojaRuta

        hoja = (
            HojaRuta.objects.select_related('vehiculo', 'afiliado')
            .filter(
                ruta_id=obj.ruta_id,
                fecha_salida=obj.fecha_viaje,
                estado__in=['emitida', 'notificada', 'pagada'],
            )
            .order_by('id')
            .first()
        )
        obj._hoja_cache = hoja
        return hoja

    def get_afiliado_nombre(self, obj):
        afiliado = obj.afiliado
        if not afiliado:
            hoja = self._get_hoja(obj)
            afiliado = hoja.afiliado if hoja else None
        if afiliado:
            return f"{afiliado.apellidos} {afiliado.nombres}"
        return None

    def get_vehiculo_tipo(self, obj):
        hoja = self._get_hoja(obj)
        return hoja.vehiculo.tipo if hoja and hoja.vehiculo else "No asignado"

    def get_vehiculo_placa(self, obj):
        hoja = self._get_hoja(obj)
        return hoja.vehiculo.placa if hoja and hoja.vehiculo else None

    def get_hora_salida(self, obj):
        hoja = self._get_hoja(obj)
        return hoja.hora_salida.strftime('%H:%M') if hoja and hoja.hora_salida else None

    def get_monto_unitario(self, obj):
        if obj.monto_unitario is not None:
            return f"{obj.monto_unitario:.2f}"
        return f"{precio_de(self._get_hoja(obj), obj.ruta):.2f}"

    def get_monto_total(self, obj):
        if obj.monto_total is not None:
            return f"{obj.monto_total:.2f}"
        return f"{precio_de(self._get_hoja(obj), obj.ruta) * obj.cantidad:.2f}"


class ReservaPublicaSerializer(ReservaSerializer):
    """Datos del voucher público: sin teléfono del cliente ni dirección del afiliado."""

    class Meta(ReservaSerializer.Meta):
        fields = [
            'id', 'cliente', 'ruta', 'fecha_viaje', 'cantidad', 'asiento', 'estado',
            'monto_unitario', 'monto_total', 'grupo_id',
            'ruta_nombre', 'ruta_origen', 'ruta_destino', 'ruta_tarifa',
            'afiliado_nombre', 'afiliado_telefono',
            'vehiculo_tipo', 'vehiculo_placa',
            'hora_salida',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
