from django.db import models


class Ruta(models.Model):
    nombre = models.CharField(max_length=100)
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    tarifa_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prefijo = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre