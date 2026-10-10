from django.db import models


class Reunion(models.Model):
    fecha = models.DateField()
    tema = models.CharField(max_length=200)
    tipo = models.CharField(max_length=30, default='ordinaria')
    quorum = models.PositiveIntegerField(default=0)
    monto_multa = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Monto de Multa (Bs)',
        help_text='Multa por inasistencia. Si es 0 se usa el monto por defecto según el tipo.',
    )
    ESTADO_CHOICES = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='abierta')
    
    # Libro de Actas Digital
    acta_texto = models.TextField(blank=True, verbose_name='Contenido del Acta')
    acuerdos = models.TextField(blank=True, verbose_name='Acuerdos de la Reunión', help_text='Resumen de puntos acordados')
    documento_adjunto = models.CharField(max_length=255, blank=True, null=True, help_text='URL o ruta del acta escaneada')
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)


    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} - {self.fecha}"