from rest_framework import serializers
from .models import Afiliado
import re

class AfiliadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Afiliado
        fields = ['id', 'user', 'nombres', 'apellidos', 'ci', 'telefono', 'email', 'direccion', 'estado', 'fecha_ingreso', 'is_active', 'created_at', 'updated_at']

    def validate_ci(self, value):
        """Validar formato CI boliviano (7-8 dígitos + opcionalmente extensión)"""
        if not value:
            return value
        pattern = r'^\d{7,8}(-[A-Z]{2})?$'
        if not re.match(pattern, value.upper()):
            raise serializers.ValidationError("CI inválido. Debe tener 7-8 dígitos y opcionalmente extensión (ej. 1234567-LP).")
        return value.upper()

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