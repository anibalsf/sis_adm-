from django.db import models
from afiliados.models import Afiliado
from vehiculos.models import Vehiculo
from rutas.models import Ruta


class HojaRuta(models.Model):
    nro = models.CharField(max_length=30)
    fecha_emision = models.DateField()
    fecha_salida = models.DateField(null=True, blank=True, db_index=True)
    hora_salida = models.TimeField(null=True, blank=True)
    afiliado = models.ForeignKey(Afiliado, on_delete=models.PROTECT, related_name='hojas_ruta')
    estado = models.CharField(max_length=20, default='emitida', db_index=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    archivo_url = models.CharField(max_length=255, blank=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name='hojas_ruta', null=True, blank=True)
    ruta = models.ForeignKey(Ruta, on_delete=models.PROTECT, related_name='hojas_ruta', null=True, blank=True)
    agente_parada = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_emision']

    def __str__(self):
        return self.nro

    def save(self, *args, **kwargs):
        if not (self.nro and str(self.nro).strip()):
            nxt = self._next_nro()
            if nxt:
                self.nro = nxt
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.fecha_emision:
            year = self.fecha_emision.year
            month = self.fecha_emision.month
            base_qs = HojaRuta.objects.exclude(pk=self.pk).filter(fecha_emision__year=year, fecha_emision__month=month)
            if self.ruta_id:
                base_qs = base_qs.filter(ruta_id=self.ruta_id)
            exists = base_qs.filter(nro=self.nro).exists()
            if exists:
                from django.core.exceptions import ValidationError
                raise ValidationError({'nro': 'Ya existe este número en el periodo para la ruta.'})
        if self.estado not in {'emitida', 'anulada', 'notificada', 'pagada'}:
            from django.core.exceptions import ValidationError
            raise ValidationError({'estado': 'Estado inválido'})
        if self.precio is not None and self.precio < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError({'precio': 'Monto no puede ser negativo'})

    def _next_nro(self):
        fecha = self.fecha_emision
        if not fecha:
            return None
        year = fecha.year
        month = fecha.month
        qs = HojaRuta.objects.filter(fecha_emision__year=year, fecha_emision__month=month)
        if self.ruta_id:
            qs = qs.filter(ruta_id=self.ruta_id)
        maxn = 0
        for val in qs.values_list('nro', flat=True):
            s = str(val or '').strip()
            # intenta usar el último segmento numérico
            num = None
            parts = s.split('-')
            for part in reversed(parts):
                if part.isdigit():
                    num = int(part)
                    break
            if num is None:
                digits = ''.join([c for c in s if c.isdigit()])
                num = int(digits) if digits else 0
            if num > maxn:
                maxn = num
        prefix = ''
        if self.ruta_id and getattr(self, 'ruta', None) and getattr(self.ruta, 'prefijo', ''):
            prefix = f"{self.ruta.prefijo}-"
        return f"{prefix}{maxn+1:04d}"


class TurnoSalida(models.Model):
    fecha = models.DateField(db_index=True)
    hora_salida = models.TimeField(null=True, blank=True)
    afiliado = models.ForeignKey(Afiliado, on_delete=models.CASCADE, related_name='turnos_salida')
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, related_name='turnos_programados')
    orden = models.PositiveIntegerField(default=1) # Posición en la salida del día (1º, 2º, etc.)
    observacion = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'orden']
        unique_together = ['fecha', 'afiliado', 'ruta']

    def __str__(self):
        return f"{self.fecha} - {self.ruta} - {self.afiliado} ({self.orden}º)"
