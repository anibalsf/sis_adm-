from django.db import models


class Notificacion(models.Model):
    canal = models.CharField(max_length=30)
    destinatario = models.CharField(max_length=50)
    mensaje = models.TextField()
    estado = models.CharField(max_length=20, default='pendiente')
    webhook_url = models.CharField(max_length=255, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.canal}-{self.destinatario}-{self.estado}"