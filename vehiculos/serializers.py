import re
import uuid
from rest_framework import serializers
from .models import Vehiculo


class VehiculoSerializer(serializers.ModelSerializer):
    # La placa se valida manualmente en validate() para permitir vehículos
    # indocumentados (sin placa), a los que se les genera una referencia única.
    placa = serializers.CharField(required=False, allow_blank=True, max_length=15, validators=[])

    class Meta:
        model = Vehiculo
        fields = ['id', 'placa', 'tipo', 'color', 'capacidad', 'afiliado', 'estado',
                  'indocumentado', 'es_convenio_caranavi', 'created_at', 'updated_at']

    def _generar_placa_temporal(self):
        """Genera una referencia única para vehículos sin placa registrada."""
        while True:
            candidata = f'S/P-{uuid.uuid4().hex[:6].upper()}'
            if not Vehiculo.objects.filter(placa=candidata).exists():
                return candidata

    def validate_placa(self, value):
        return value

    def validate(self, attrs):
        indocumentado = attrs.get('indocumentado', getattr(self.instance, 'indocumentado', False))
        if indocumentado is None:
            indocumentado = False
        placa = (attrs.get('placa') or getattr(self.instance, 'placa', '') or '').strip()

        if indocumentado:
            # Sin placa real: se genera una referencia temporal única.
            if not placa:
                attrs['placa'] = self._generar_placa_temporal()
            elif placa.upper().startswith('S/P'):
                # Conservar la referencia si ya pertenece a este mismo registro
                if not (self.instance and self.instance.placa == placa.upper()):
                    attrs['placa'] = self._generar_placa_temporal()
            else:
                attrs['placa'] = placa.upper().replace(' ', '')
        else:
            if not placa:
                raise serializers.ValidationError({'placa': 'La placa es requerida'})
            limpia = placa.upper().replace(' ', '').replace('-', '')
            if not re.match(r'^\d{3,4}[A-Z]{3}$', limpia) and len(limpia) < 5:
                raise serializers.ValidationError({
                    'placa': 'Formato de placa inválido. Debe tener al menos 3 números y 3 letras.'
                })
            normalizada = placa.upper().replace(' ', '').replace('-', '')
            qs = Vehiculo.objects.filter(placa=normalizada)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'placa': 'La placa ya está registrada'})
            attrs['placa'] = normalizada

        return attrs

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
