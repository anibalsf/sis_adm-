from rest_framework import serializers
from .models import Egreso, Pago, TipoPago

class TipoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoPago
        fields = '__all__'

class PagoSerializer(serializers.ModelSerializer):
    afiliado_nombre = serializers.CharField(source='afiliado.nombre_completo', read_only=True)
    tipo_pago_nombre = serializers.CharField(source='tipo_pago.nombre', read_only=True)

    class Meta:
        model = Pago
        fields = ['id', 'afiliado', 'afiliado_nombre', 'tipo_pago', 'tipo_pago_nombre', 'monto', 'saldo_anterior_gestion', 'fecha_pago', 'metodo_pago', 'banco', 'nro_operacion', 'estado', 'observaciones', 'hoja_ruta', 'created_at']
    
    def validate_monto(self, value):
        try:
            v = float(value)
        except Exception:
            raise serializers.ValidationError('Monto inválido')
        if v <= 0:
            raise serializers.ValidationError('El monto debe ser mayor a 0')
        return value
    
    def validate(self, attrs):
        # Eliminamos la validación estricta aquí para permitir que el controlador 
        # (o la lógica del frontend que envía el monto calculado) maneje la flexibilidad 
        # de aplicar o no la multa de 50 Bs.
        return attrs

class EgresoSerializer(serializers.ModelSerializer):
    tipo_pago_nombre = serializers.CharField(source='tipo_pago.nombre', read_only=True)

    class Meta:
        model = Egreso
        fields = ['id', 'fecha', 'monto', 'descripcion', 'tipo_pago', 'tipo_pago_nombre', 'metodo_pago', 'banco', 'nro_operacion', 'created_at']
