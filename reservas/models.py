from django.db import models
from afiliados.models import Afiliado
from rutas.models import Ruta


class Reserva(models.Model):
    afiliado = models.ForeignKey(Afiliado, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    cliente = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20, blank=True)
    ruta = models.ForeignKey(Ruta, on_delete=models.PROTECT, related_name='reservas')
    fecha_viaje = models.DateField()
    cantidad = models.PositiveIntegerField(default=1)
    asiento = models.PositiveIntegerField(null=True, blank=True)
    estado = models.CharField(max_length=20, default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_viaje']

    def __str__(self):
        return f"{self.cliente} - {self.ruta_id} - {self.fecha_viaje}"