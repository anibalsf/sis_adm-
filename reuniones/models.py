from django.db import models


class Reunion(models.Model):
    fecha = models.DateField()
    tema = models.CharField(max_length=200)
    tipo = models.CharField(max_length=30, default='ordinaria')
    quorum = models.PositiveIntegerField(default=0)
    ESTADO_CHOICES = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    ]
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='abierta')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)


    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} - {self.fecha}"