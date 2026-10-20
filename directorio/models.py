from django.db import models
from datetime import date
from dateutil.relativedelta import relativedelta
from afiliados.models import Afiliado

VIGENCIA_ANIOS = 1

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

    @property
    def vigencia_hasta(self):
        """Fin de la vigencia de 1 año a partir de fecha_inicio."""
        return self.fecha_inicio + relativedelta(years=VIGENCIA_ANIOS)

    @property
    def esta_vencido(self):
        """True si la gestión ya venció y sigue marcado como activo."""
        return self.estado == 'activo' and self.vigencia_hasta <= date.today()

    @classmethod
    def directorio_vigente(cls, hoy=None):
        """Miembros del directorio vigente (activos dentro de su vigencia de 1 año)."""
        hoy = hoy or date.today()
        return cls.objects.select_related('afiliado').filter(
            estado='activo', fecha_fin__isnull=True, fecha_inicio__lte=hoy
        ).filter(fecha_inicio__gt=hoy - relativedelta(years=VIGENCIA_ANIOS))

    @classmethod
    def concluir_vencidos(cls, hoy=None):
        """Cierra el directorio vencido: estado='concluido' y fecha_fin=fin de vigencia."""
        hoy = hoy or date.today()
        vencidos = list(cls.objects.filter(
            estado='activo', fecha_inicio__lte=hoy - relativedelta(years=VIGENCIA_ANIOS)
        ))
        for m in vencidos:
            m.estado = 'concluido'
            m.fecha_fin = m.vigencia_hasta
            m.save(update_fields=['estado', 'fecha_fin', 'updated_at'])
        return vencidos

    @classmethod
    def gestiones(cls):
        """Histórico de gestiones agrupadas por año de fecha_inicio."""
        anios = (
            cls.objects.exclude(fecha_inicio__isnull=True)
            .order_by().values_list('fecha_inicio__year', flat=True).distinct()
        )
        resultado = []
        for anio in sorted(anios, reverse=True):
            miembros = cls.objects.select_related('afiliado').filter(
                fecha_inicio__year=anio
            ).order_by('cargo', 'fecha_inicio')
            activos = [m for m in miembros if m.estado == 'activo']
            resultado.append({
                'anio': anio,
                'fecha_inicio': min((m.fecha_inicio for m in miembros), default=None),
                'fecha_fin': max((m.vigencia_hasta for m in miembros), default=None),
                'total_miembros': miembros.count(),
                'activos': len(activos),
                'miembros': miembros,
            })
        return resultado

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