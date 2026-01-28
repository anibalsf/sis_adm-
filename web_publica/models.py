from django.db import models

class Multimedia(models.Model):
    TIPO_CHOICES = [
        ('IMAGEN', 'Imagen'),
        ('VIDEO', 'Video'),
        ('VIDEO_EXTERNO', 'Video Externo (YouTube/Link)'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='IMAGEN')
    archivo = models.FileField(upload_to='web_publica/multimedia/', blank=True, null=True, help_text="Para imágenes o videos cortos")
    url_externa = models.URLField(blank=True, null=True, help_text="Para videos de YouTube o enlaces externos")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_publicacion']
        verbose_name = 'Contenido Multimedia'
        verbose_name_plural = 'Galería Multimedia'

    def __str__(self):
        return self.titulo
