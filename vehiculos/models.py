from django.db import models
from afiliados.models import Afiliado
from sistema.validators import validate_placa_vehiculo


class Vehiculo(models.Model):
    placa = models.CharField(max_length=15, unique=True, validators=[validate_placa_vehiculo])
    tipo = models.CharField(max_length=50)
    color = models.CharField(max_length=50, blank=True, verbose_name='Color')
    capacidad = models.PositiveIntegerField(default=0)
    afiliado = models.ForeignKey(Afiliado, on_delete=models.PROTECT, related_name='vehiculos')
    indocumentado = models.BooleanField(default=False, help_text="Vehículo sin placa registrada (solo puede ir a Caranavi)")
    es_convenio_caranavi = models.BooleanField(default=False, help_text="Vehículo de Convenio Caranavi (solo puede ir a La Paz)")
    estado = models.CharField(max_length=20, default='activo', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['placa']

    def __str__(self):
        return self.placa

# Create your models here.
