from django.db import models
from django.contrib.auth.models import User
from sistema.validators import validate_ci_boliviano, validate_telefono_boliviano


class Afiliado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='afiliado', null=True, blank=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    ci = models.CharField(max_length=20, unique=True, validators=[validate_ci_boliviano])
    ci_exp = models.CharField(
        max_length=5, 
        choices=[
            ('LP', 'La Paz'),
            ('CB', 'Cochabamba'),
            ('SC', 'Santa Cruz'),
            ('OR', 'Oruro'),
            ('PT', 'Potosí'),
            ('TJ', 'Tarija'),
            ('CH', 'Chuquisaca'),
            ('BN', 'Beni'),
            ('PA', 'Pando'),
        ],
        default='LP',
        verbose_name="Expedido en"
    )
    telefono = models.CharField(max_length=20, blank=True, validators=[validate_telefono_boliviano])
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, default='activo', db_index=True)
    fecha_ingreso = models.DateField()
    is_active = models.BooleanField(default=True, db_index=True)
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
        
        # Guardar primero el afiliado
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Crear usuario automáticamente si no tiene uno
        if not self.user:
            try:
                username = self.ci.split('-')[0] # Usar solo números del CI si tiene extensión
                # Verificar si el username ya existe
                if not User.objects.filter(username=username).exists():
                    new_user = User.objects.create_user(
                        username=username,
                        password=username, # Password inicial es su CI
                        first_name=self.nombres,
                        last_name=self.apellidos,
                        email=self.email or ""
                    )
                    # Asignar al grupo Afiliado
                    from django.contrib.auth.models import Group
                    group, _ = Group.objects.get_or_create(name='Afiliado')
                    new_user.groups.add(group)
                    
                    self.user = new_user
                    super().save(update_fields=['user'])
            except Exception as e:
                print(f"Error al crear usuario automático: {e}")

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def ci_completo(self):
        return f"{self.ci} {self.ci_exp}"


class TurnoAgente(models.Model):
    fecha = models.DateField(unique=True)
    afiliado = models.ForeignKey(Afiliado, on_delete=models.CASCADE, related_name='turnos')
    observacion = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"{self.fecha} - {self.afiliado}"