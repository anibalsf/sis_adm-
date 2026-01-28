from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User


class CambioEstado(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    estado_anterior = models.CharField(max_length=30)
    estado_nuevo = models.CharField(max_length=30)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.content_type_id}-{self.object_id}-{self.estado_anterior}->{self.estado_nuevo}"


class LogAuditoria(models.Model):
    ACCION_CHOICES = [
        ('crear', 'Creación'),
        ('editar', 'Edición'),
        ('eliminar', 'Eliminación'),
        ('login', 'Inicio de Sesión'),
        ('otro', 'Otro'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    tabla = models.CharField(max_length=50)  # Nombre del modelo
    objeto_id = models.CharField(max_length=50, null=True, blank=True)
    descripcion = models.TextField()
    cambios = models.JSONField(null=True, blank=True)  # {'campo': {'antes': 'x', 'despues': 'y'}}
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'

    def __str__(self):
        return f"{self.fecha_hora} - {self.usuario} - {self.accion} en {self.tabla}"