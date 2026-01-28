from django.db import models
from afiliados.models import Afiliado
from reuniones.models import Reunion


class Asistencia(models.Model):
    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='asistencias')
    afiliado = models.ForeignKey(Afiliado, on_delete=models.CASCADE, related_name='asistencias')
    ESTADO_CHOICES = [
        ('presente', 'Presente'),
        ('falta', 'Falta'),
        ('permiso', 'Permiso'),
        ('atraso', 'Atraso'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='presente')
    presente = models.BooleanField(default=True) # Deprecated, use estado
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('reunion', 'afiliado')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reunion_id}-{self.afiliado_id}-{self.presente}"