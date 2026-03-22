from rest_framework import serializers
from .models import Afiliado
import re

class AfiliadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Afiliado
        fields = ['id', 'user', 'nombres', 'apellidos', 'nombre_completo', 'ci', 'ci_exp', 'telefono', 'email', 'direccion', 'estado', 'fecha_ingreso', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'nombre_completo']

    def validate_ci(self, value):
        """Validar formato CI boliviano (6-10 dígitos)"""
        if not value:
            return value
        # Pattern solo para números para simplificar, la extensión va en otro campo
        pattern = r'^\d{6,10}$'
        if not re.match(pattern, value):
            # Si ya trae guión, lo permitimos si cumple el patrón general de la app
            if '-' in value:
                from sistema.validators import validate_ci_boliviano
                try:
                    validate_ci_boliviano(value)
                    return value.upper()
                except:
                    pass
            raise serializers.ValidationError("CI inválido. Debe tener entre 6 y 10 dígitos.")
        return value

    def validate_telefono(self, value):
        """Validar número de teléfono boliviano (8 dígitos, empieza con 6 o 7)"""
        if value:
            pattern = r'^[67]\d{7}$'
            if not re.match(pattern, str(value)):
                raise serializers.ValidationError("Teléfono inválido. Debe tener 8 dígitos y empezar con 6 o 7.")
        return value

    def validate_nombres(self, value):
        return value.title().strip() if value else value

    def validate_apellidos(self, value):
        return value.title().strip() if value else value