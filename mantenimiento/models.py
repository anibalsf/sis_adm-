from django.db import models
from vehiculos.models import Vehiculo

class DocumentacionVehiculo(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('soat', 'SOAT'),
        ('inspeccion', 'Inspección Técnica'),
        ('seguro', 'Seguro Vehicular'),
        ('otro', 'Otro Documento'),
    ]
    
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='documentacion')
    tipo = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES)
    fecha_vencimiento = models.DateField()
    observaciones = models.TextField(blank=True, null=True)
    alerta_enviada = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Documentación de Vehículo'
        verbose_name_plural = 'Documentaciones de Vehículos'
        ordering = ['fecha_vencimiento']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.vehiculo.placa} ({self.fecha_vencimiento})"

class MantenimientoHistorial(models.Model):
    TIPO_SERVICIO_CHOICES = [
        ('aceite', 'Cambio de Aceite'),
        ('frenos', 'Frenos'),
        ('llantas', 'Llantas / Alineación'),
        ('motor', 'Reparación de Motor'),
        ('electrico', 'Sistema Eléctrico'),
        ('limpieza', 'Limpieza / Estético'),
        ('otro', 'Otro'),
    ]
    
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='mantenimientos')
    fecha = models.DateField()
    kilometraje = models.PositiveIntegerField(help_text="Kilometraje al momento del servicio")
    tipo_servicio = models.CharField(max_length=20, choices=TIPO_SERVICIO_CHOICES)
    descripcion = models.TextField()
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    taller = models.CharField(max_length=150, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historial de Mantenimiento'
        verbose_name_plural = 'Historiales de Mantenimientos'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_servicio_display()} - {self.vehiculo.placa} ({self.fecha})"
