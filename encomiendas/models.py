from django.db import models
import random
import string

def generar_codigo_tracking():
    # Genera un codigo unico tipo TRK-XXXXXX
    caracteres = string.ascii_uppercase + string.digits
    codigo = ''.join(random.choices(caracteres, k=6))
    return f"TRK-{codigo}"

class Encomienda(models.Model):
    ESTADOS = [
        ('registrado', 'Registrado (En Oficina)'),
        ('en_transito', 'En Tránsito'),
        ('entregado', 'Entregado'),
    ]

    codigo_tracking = models.CharField(max_length=15, unique=True, default=generar_codigo_tracking)
    
    # Datos del Remitente
    remitente_nombre = models.CharField(max_length=100)
    remitente_ci = models.CharField(max_length=20, blank=True, null=True)
    remitente_telefono = models.CharField(max_length=20)
    
    # Datos del Destinatario
    destinatario_nombre = models.CharField(max_length=100)
    destinatario_ci = models.CharField(max_length=20, blank=True, null=True)
    destinatario_telefono = models.CharField(max_length=20)
    
    # Detalle del paquete
    descripcion = models.CharField(max_length=200, help_text="Ej: Caja de ropa, Sobre, Repuestos")
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    precio = models.DecimalField(max_digits=8, decimal_places=2, help_text="Costo del envío")
    pagado = models.BooleanField(default=False)
    
    # Asignación a vehículo/viaje (Opcional al inicio)
    hoja_ruta = models.ForeignKey('hojasruta.HojaRuta', on_delete=models.SET_NULL, null=True, blank=True, related_name='encomiendas')
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='registrado')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = "Encomienda"
        verbose_name_plural = "Encomiendas"

    def __str__(self):
        return f"{self.codigo_tracking} - {self.descripcion} ({self.get_estado_display()})"
