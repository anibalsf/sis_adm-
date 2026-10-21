from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from afiliados.models import Afiliado
from rutas.models import Ruta

ESTADOS = (
    ('pendiente', 'Pendiente'),
    ('confirmada', 'Confirmada'),
    ('cancelada', 'Cancelada'),
)
ESTADOS_ACTIVOS = ('pendiente', 'confirmada')


class Reserva(models.Model):
    afiliado = models.ForeignKey(Afiliado, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    cliente = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20, blank=True)
    ruta = models.ForeignKey(Ruta, on_delete=models.PROTECT, related_name='reservas')
    hoja_ruta = models.ForeignKey(
        'hojasruta.HojaRuta',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='reservas',
    )
    fecha_viaje = models.DateField()
    cantidad = models.PositiveIntegerField(default=1)
    asiento = models.PositiveIntegerField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente', db_index=True)
    monto_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    grupo_id = models.UUIDField(null=True, blank=True, db_index=True)
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_viaje']
        indexes = [
            models.Index(fields=['ruta', 'fecha_viaje', 'estado'], name='reserva_ruta_fecha_estado_idx'),
            models.Index(fields=['fecha_viaje'], name='reserva_fecha_idx'),
        ]
        constraints = [
            models.CheckConstraint(check=Q(cantidad__gte=1), name='reserva_cantidad_positiva'),
            models.UniqueConstraint(
                fields=['ruta', 'fecha_viaje', 'asiento'],
                condition=Q(estado__in=ESTADOS_ACTIVOS),
                name='reserva_asiento_unico',
            ),
        ]

    def __str__(self):
        return f"{self.cliente} - {self.ruta_id} - {self.fecha_viaje}"

    def clean(self):
        if self.cantidad is not None and self.cantidad < 1:
            raise ValidationError({'cantidad': 'La cantidad debe ser al menos 1.'})
        if self.asiento is not None and self.asiento < 1:
            raise ValidationError({'asiento': 'El número de asiento debe ser al menos 1.'})
