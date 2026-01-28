"""
Validadores personalizados para el sistema
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_ci_boliviano(value):
    """
    Valida Cédula de Identidad boliviana
    Formato: 6-10 dígitos, opcionalmente con extensión
    Ejemplos válidos: 12345678, 12345678-1A, 1234567-LP
    """
    if not value:
        return
    
    pattern = r'^\d{6,10}(-[0-9A-Z]{1,2})?$'
    if not re.match(pattern, str(value).upper()):
        raise ValidationError(
            _('CI inválido. Formato: 12345678 o 12345678-1A'),
            code='invalid_ci'
        )


def validate_telefono_boliviano(value):
    """
    Valida teléfono boliviano
    Formato: 8 dígitos, comenzando con 6 o 7
    Ejemplos válidos: 71234567, 69876543
    """
    if not value:
        return
    
    # Limpiar espacios y guiones
    cleaned = str(value).replace(' ', '').replace('-', '')
    
    pattern = r'^[67]\d{7}$'
    if not re.match(pattern, cleaned):
        raise ValidationError(
            _('Teléfono inválido. Debe tener 8 dígitos y comenzar con 6 o 7'),
            code='invalid_phone'
        )


def validate_placa_vehiculo(value):
    """
    Valida placa de vehículo boliviano
    Formato antiguo: ABC-1234 (3 letras + 4 números)
    Formato nuevo: 1234-ABC (4 números + 3 letras)
    """
    if not value:
        return
    
    # Limpiar espacios
    cleaned = str(value).replace(' ', '').upper()
    
    # Formato antiguo: ABC-1234
    # Formato nuevo: 1234-ABC
    pattern = r'^([A-Z]{3}-?\d{4}|\d{4}-?[A-Z]{3})$'
    if not re.match(pattern, cleaned):
        raise ValidationError(
            _('Placa inválida. Formato: ABC-1234 o 1234-ABC'),
            code='invalid_plate'
        )


def validate_monto_positivo(value):
    """
    Valida que el monto sea positivo
    """
    if value is not None and value <= 0:
        raise ValidationError(
            _('El monto debe ser mayor a 0'),
            code='invalid_amount'
        )


def validate_email_format(value):
    """
    Validación adicional de email
    """
    if not value:
        return
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        raise ValidationError(
            _('Email inválido'),
            code='invalid_email'
        )
