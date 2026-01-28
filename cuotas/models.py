from django.db import models
from afiliados.models import Afiliado


class Cuota(models.Model):
    afiliado = models.ForeignKey(Afiliado, on_delete=models.PROTECT, related_name='cuotas')
    periodo = models.DateField()  # usar primer día del mes
    tipo = models.CharField(max_length=10, default='mensual')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, default='pendiente')
    fecha_pago = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('afiliado', 'periodo', 'tipo')
        ordering = ['-periodo']

    def __str__(self):
        return f"{self.afiliado_id}-{self.periodo}-{self.tipo}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.monto is not None and self.monto < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError({'monto': 'Monto no puede ser negativo'})
        if self.estado not in {'pendiente', 'pagada', 'anulada'}:
            from django.core.exceptions import ValidationError
            raise ValidationError({'estado': 'Estado inválido'})
        if self.periodo:
            from datetime import date
            self.periodo = date(self.periodo.year, self.periodo.month, 1)

# Create your models here.
