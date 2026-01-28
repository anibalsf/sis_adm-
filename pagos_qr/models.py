from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class QRTransaccion(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('expirado', 'Expirado'),
        ('fallido', 'Fallido'),
    )
    
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='BOB')
    glosa = models.CharField(max_length=255)
    expiration_date = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    # Datos técnicos del QR
    qr_string = models.TextField(help_text="Contenido raw del código QR")
    imagen_base64 = models.TextField(blank=True, null=True, help_text="Imagen en base64 para mostrar directo")
    transaction_id = models.CharField(max_length=100, unique=True, help_text="ID único de transacción (uuid)")
    
    # Relación polimórfica (quien originó el pago)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadata adicional
    response_data = models.JSONField(default=dict, blank=True) # Respuesta del banco/servicio
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QR-{self.transaction_id} ({self.monto} {self.moneda})" # Changed bs to BOB standard ISO or symbol if preferred, keeping as field default but string logic here. Let's use currency symbol or code.

