from django.db import models
from django.contrib.auth.models import User
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
        ('anulado', 'Anulado'),
        ('cancelado', 'Cancelado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completado')
    motivo_anulacion = models.TextField(blank=True, null=True, help_text="Justificación si el pago es anulado")

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
    
    ESTADO_CHOICES = [
        ('pendiente_aprobacion', 'Pendiente de Aprobación'),
        ('aprobado', 'Aprobado/Completado'),
        ('anulado', 'Anulado')
    ]
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='aprobado')
    motivo_anulacion = models.TextField(blank=True, null=True, help_text="Justificación si el egreso es anulado")
    aprobado_por = models.ForeignKey(User, related_name='egresos_aprobados', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.fecha} - {self.descripcion} - {self.monto}"

    class Meta:
        ordering = ['-fecha']


class ArqueoCaja(models.Model):
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    total_ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_egresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_teorico = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total Ingresos - Total Egresos")
    saldo_real = models.DecimalField(max_digits=12, decimal_places=2, help_text="Dinero físico real en caja")
    diferencia = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Saldo Real - Saldo Teórico")
    
    mes = models.CharField(max_length=20, null=True, blank=True)
    anho = models.IntegerField(null=True, blank=True)
    
    observaciones = models.TextField(blank=True, null=True)
    detalle_efectivo = models.JSONField(null=True, blank=True, help_text="Desglose de billetes y monedas")
    
    estado = models.CharField(max_length=20, choices=[('abierto', 'Abierto'), ('cerrado', 'Cerrado')], default='cerrado')
    
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.saldo_teorico = self.total_ingresos - self.total_egresos
        self.diferencia = self.saldo_real - self.saldo_teorico
        if not self.mes:
            import locale
            from datetime import datetime
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            self.mes = self.fecha_fin.strftime('%B').capitalize()
        if not self.anho:
            self.anho = self.fecha_fin.year
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Arqueo {self.mes} {self.anho} - Saldo: {self.saldo_real}"

    class Meta:
        ordering = ['-anho', '-mes', '-fecha_fin']