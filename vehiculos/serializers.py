from rest_framework import serializers
from .models import Vehiculo


class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = ['id', 'placa', 'tipo', 'capacidad', 'afiliado', 'estado', 'created_at', 'updated_at']

    def validate_placa(self, value):
        import re
        if not value:
            raise serializers.ValidationError('La placa es requerida')
        
        placa = value.strip().upper().replace(" ", "").replace("-", "")
        # Formato boliviano: 3-4 números + 3 letras (ej. 1234ABC o 123ABC)
        pattern = r'^\d{3,4}[A-Z]{3}$'
        if not re.match(pattern, placa):
            # Intentar formato antiguo o especial si es necesario, pero alertar
            if len(placa) < 5:
                raise serializers.ValidationError('Formato de placa inválido. Debe tener al menos 3 números y 3 letras.')
        
        qs = Vehiculo.objects.filter(placa=placa)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('La placa ya está registrada')
        return placa

    def validate_capacidad(self, value):
        if value is None:
            raise serializers.ValidationError('La capacidad es requerida')
        if value <= 0:
            raise serializers.ValidationError('La capacidad debe ser mayor a 0')
        return value

    def validate_estado(self, value):
        permitido = {'activo', 'inactivo'}
        v = (value or '').strip().lower()
        if v not in permitido:
            raise serializers.ValidationError('Estado inválido')
        return v

    def validate_tipo(self, value):
        permitido = {
            'minibus', 'ipsum', 'micro', 'bus', 'taxi', 'camioneta',
            'camion', 'trufi', 'coaster', 'vagoneta', 'otros'
        }
        v = (value or '').strip().lower()
        if v not in permitido:
            raise serializers.ValidationError('Tipo inválido')
        return v