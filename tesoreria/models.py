from django.db import models
from afiliados.models import Afiliado
from hojasruta.models import HojaRuta


class TipoPago(models.Model):
    TIPO_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    
    # Campos para configuración de plazos y multas
    tiene_plazo = models.BooleanField(default=False, help_text="¿Este tipo de pago tiene plazo límite?")
    dia_plazo = models.IntegerField(null=True, blank=True, help_text="Día de la semana (0=Lunes, 6=Domingo)")
    hora_inicio_plazo = models.TimeField(null=True, blank=True, help_text="Hora de inicio del plazo (ej: 17:00)")
    hora_fin_plazo = models.TimeField(null=True, blank=True, help_text="Hora de fin del plazo (ej: 22:00)")
    monto_multa = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto de multa por pago fuera de plazo")

    def __str__(self):
        return self.nombre

class Pago(models.Model):
    afiliado = models.ForeignKey(Afiliado, on_delete=models.CASCADE, related_name='pagos')
    tipo_pago = models.ForeignKey(TipoPago, on_delete=models.PROTECT, limit_choices_to={'tipo': 'ingreso'})
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField()
    saldo_anterior_gestion = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Saldo de la gestión anterior")
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('qr', 'QR / Yape'),
        ('transferencia', 'Transferencia'),
    ]
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo')
    banco = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre del banco si es transferencia")
    nro_operacion = models.CharField(max_length=100, blank=True, null=True, help_text="Número de operación / transacción")
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completado')

    observaciones = models.TextField(blank=True, null=True)
    hoja_ruta = models.ForeignKey(HojaRuta, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_tesoreria')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pago de {self.afiliado} - {self.monto} por {self.tipo_pago.nombre}"

    class Meta:
        ordering = ['-fecha_pago']

class Egreso(models.Model):
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    tipo_pago = models.ForeignKey(TipoPago, on_delete=models.PROTECT, limit_choices_to={'tipo': 'egreso'})
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('qr', 'QR / Yape'),
        ('transferencia', 'Transferencia'),
    ]
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, default='efectivo')
    banco = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre del banco si es transferencia")
    nro_operacion = models.CharField(max_length=100, blank=True, null=True, help_text="Número de operación / transacción")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.fecha} - {self.descripcion} - {self.monto}"

    class Meta:
        ordering = ['-fecha']