from django.db import models
from afiliados.models import Afiliado
from asistencias.models import Asistencia


class Sancion(models.Model):
    afiliado = models.ForeignKey(Afiliado, on_delete=models.CASCADE, related_name='sanciones')
    tipo = models.CharField(max_length=50)
    motivo = models.CharField(max_length=255, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, default='pendiente')
    referencia_asistencia = models.ForeignKey(Asistencia, on_delete=models.CASCADE, null=True, blank=True, related_name='sancion')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('afiliado', 'referencia_asistencia', 'tipo')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.afiliado_id}-{self.tipo}-{self.estado}"



    def clean(self):
        if self.monto is not None and self.monto < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError({'monto': 'Monto no puede ser negativo'})
        if self.estado not in {'pendiente', 'notificada', 'pagada', 'anulada'}:
            from django.core.exceptions import ValidationError
            raise ValidationError({'estado': 'Estado inválido'})