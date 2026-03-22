from rest_framework import serializers
from .models import HojaRuta, TurnoSalida


class HojaRutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = HojaRuta
        fields = ['id', 'nro', 'fecha_emision', 'fecha_salida', 'afiliado', 'vehiculo', 'ruta', 'agente_parada', 'estado', 'precio', 'archivo_url', 'created_at', 'updated_at']
        extra_kwargs = {
            'nro': {'required': False, 'allow_blank': True},
            'agente_parada': {'required': False, 'allow_blank': True}
        }


    def validate_afiliado(self, value):
        """Validar que el afiliado esté activo"""
        if value and not value.is_active:
            raise serializers.ValidationError(
                f'El afiliado {value.apellidos} {value.nombres} no está activo. '
                'Solo se pueden designar afiliados activos como agentes de parada.'
            )
        if value and value.estado != 'activo':
            raise serializers.ValidationError(
                f'El afiliado {value.apellidos} {value.nombres} tiene estado "{value.estado}". '
                'Solo se pueden designar afiliados con estado "activo".'
            )
        return value
    
    def validate_vehiculo(self, value):
        if value and (getattr(value, 'estado', '') or '').strip().lower() != 'activo':
            raise serializers.ValidationError('El vehículo seleccionado no está activo')
        return value

    def validate_precio(self, value):
        # Si el valor viene como string con coma, DRF podría haber fallado antes si el campo es DecimalField.
        # Pero si DRF lo acepta (ej. string), lo convertimos.
        # Sin embargo, validate_FIELD recibe el valor YA convertido por el Field.
        # Si el Field es DecimalField, fallará antes de llegar aquí si el formato es incorrecto.
        # Para soportar "80,00", necesitamos un Custom Field o interceptar to_internal_value.
        return value

    def to_internal_value(self, data):
        # Interceptar precio antes de validación para reemplazar coma por punto
        if 'precio' in data and isinstance(data['precio'], str):
            data = data.copy()
            data['precio'] = data['precio'].replace(',', '.')
        return super().to_internal_value(data)

    def validate(self, attrs):
        ruta = attrs.get('ruta') or getattr(self.instance, 'ruta', None)
        vehiculo = attrs.get('vehiculo') or getattr(self.instance, 'vehiculo', None)
        fecha_emision = attrs.get('fecha_emision') or getattr(self.instance, 'fecha_emision', None)
        fecha_salida = attrs.get('fecha_salida') or getattr(self.instance, 'fecha_salida', None)
        
        if fecha_emision and fecha_salida and fecha_salida < fecha_emision:
            raise serializers.ValidationError({'fecha_salida': 'La fecha de salida debe ser igual o posterior a la fecha de emisión'})
        
        # Validar que vehículos indocumentados solo puedan ir a Caranavi
        if vehiculo and getattr(vehiculo, 'indocumentado', False):
            if ruta and ruta.nombre.lower() != 'caranavi':
                raise serializers.ValidationError({
                    'ruta': f'El vehículo "{vehiculo.placa}" es indocumentado y solo puede realizar el servicio a Caranavi. '
                           f'No puede realizar servicio a "{ruta.nombre}".'
                })
        
        # Validar que vehículos de Convenio Caranavi solo puedan ir a La Paz
        if vehiculo and getattr(vehiculo, 'es_convenio_caranavi', False):
            if ruta and ruta.nombre.lower() != 'la paz':
                raise serializers.ValidationError({
                    'ruta': f'El vehículo "{vehiculo.placa}" es de Convenio Caranavi y solo puede realizar el servicio a La Paz. '
                           f'No puede realizar servicio a "{ruta.nombre}".'
                })
        
        if ruta and ruta.nombre.strip().lower() == 'la paz':
            if vehiculo and (getattr(vehiculo, 'tipo', '') or '').strip().lower() not in {'minibus', 'ipsum'}:
                raise serializers.ValidationError({'vehiculo': 'El vehículo no es apto para la ruta La Paz (solo Minibus/Ipsum)'})
        
        # Ajustar precio según tarifa base
        precio = attrs.get('precio')
        if ruta and (precio is None or precio < ruta.tarifa_base):
            attrs['precio'] = ruta.tarifa_base
            
        return attrs

    def create(self, validated_data):
        afiliado = validated_data.get('afiliado')
        if not validated_data.get('agente_parada') and afiliado and getattr(afiliado, 'telefono', ''):
            validated_data['agente_parada'] = afiliado.telefono
        return super().create(validated_data)

    def update(self, instance, validated_data):
        afiliado = validated_data.get('afiliado') or instance.afiliado
        if not validated_data.get('agente_parada') and afiliado and getattr(afiliado, 'telefono', ''):
            validated_data['agente_parada'] = afiliado.telefono
        return super().update(instance, validated_data)


class TurnoSalidaSerializer(serializers.ModelSerializer):
    afiliado_nombre = serializers.ReadOnlyField(source='afiliado.nombre_completo')
    ruta_nombre = serializers.ReadOnlyField(source='ruta.nombre')

    class Meta:
        model = TurnoSalida
        fields = '__all__'
