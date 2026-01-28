from django.db import models
from afiliados.models import Afiliado

CARGOS_CHOICES = (
    ('secretario_general', 'Secretario General'),
    ('secretario_relaciones', 'Secretario de Relaciones'),
    ('secretario_hacienda', 'Secretario de Hacienda'),
    ('secretario_actas', 'Secretario de Actas'),
    ('secretario_conflictos', 'Secretario de Conflictos'),
    ('secretario_deportes', 'Secretario de Deportes'),
    ('vocal', 'Vocal'),
)

ESTADO_CHOICES = (
    ('activo', 'Activo'),
    ('concluido', 'Concluido'),
)


class MiembroDirectorio(models.Model):
    afiliado = models.ForeignKey(Afiliado, on_delete=models.PROTECT, related_name='gestiones_directorio')
    cargo = models.CharField(max_length=50, choices=CARGOS_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, default='activo', choices=ESTADO_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-fecha_inicio', 'cargo']

    def __str__(self):
        return f"{self.afiliado_id}-{self.cargo}-{self.estado}"

    def save(self, *args, **kwargs):
        canon_map = {
            'secretario general': 'secretario_general',
            'secretario de relaciones': 'secretario_relaciones',
            'secretario de hacienda': 'secretario_hacienda',
            'secretario de actas': 'secretario_actas',
            'secretario de conflictos': 'secretario_conflictos',
            'secretario de deportes': 'secretario_deportes',
            'vocal': 'vocal',
        }
        if self.cargo:
            key = str(self.cargo).strip().lower().replace('_', ' ')
            self.cargo = canon_map.get(key, self.cargo)
        if self.estado:
            self.estado = str(self.estado).strip().lower()
        super().save(*args, **kwargs)