from django.db import models
from django.contrib.auth.models import User
from sistema.validators import validate_ci_boliviano, validate_telefono_boliviano


class Afiliado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='afiliado', null=True, blank=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    ci = models.CharField(max_length=20, unique=True, validators=[validate_ci_boliviano])
    telefono = models.CharField(max_length=20, blank=True, validators=[validate_telefono_boliviano])
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, default='activo')
    fecha_ingreso = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"

    def save(self, *args, **kwargs):
        # Capitalizar nombres y apellidos (Title Case)
        if self.nombres:
            self.nombres = self.nombres.title().strip()
        if self.apellidos:
            self.apellidos = self.apellidos.title().strip()
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


class TurnoAgente(models.Model):
    fecha = models.DateField(unique=True)
    afiliado = models.ForeignKey(Afiliado, on_delete=models.CASCADE, related_name='turnos')
    observacion = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"{self.fecha} - {self.afiliado}"