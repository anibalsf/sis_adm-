from django.db import models
from django.utils import timezone
from django.db.models import Q


class ReporteGenerado(models.Model):
    """
    Registro de reportes generados y enviados
    """
    TIPO_CHOICES = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('lunes_control', 'Control Lunes (Hojas Ruta)'),
        ('puntero_la_paz', 'Puntero La Paz (operativo)'),
    ]

    ESTADO_CHOICES = [
        ('generado', 'Generado'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
        ('omitido', 'Omitido'),
    ]

    ORIGEN_CHOICES = [
        ('programado', 'Programado'),
        ('manual', 'Manual'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo de Reporte')
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Generación')
    fecha_periodo = models.DateField(verbose_name='Fecha del Período', help_text='Fecha del día/semana/mes reportado')

    contenido = models.TextField(verbose_name='Contenido del Reporte')
    # Datos estructurados del reporte: alimenta el PDF/Excel y la vista de detalle
    # sin depender de parsear el texto de WhatsApp.
    datos = models.JSONField(default=dict, blank=True, verbose_name='Datos Estructurados')
    # Archivos generados (PDF/Excel). `adjuntos` guarda los nombres para poder
    # listarlos y descargarlos aunque el archivo se borre del disco.
    adjuntos = models.JSONField(default=list, blank=True, verbose_name='Adjuntos')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='generado', verbose_name='Estado')
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES, default='programado', verbose_name='Origen')

    # Destinatarios
    destinatarios_whatsapp = models.TextField(blank=True, verbose_name='Teléfonos Destinatarios', help_text='Separados por coma')
    destinatarios_email = models.TextField(blank=True, verbose_name='Emails Destinatarios', help_text='Separados por coma')
    # Destinatarios que aún no recibieron el reporte. Permite que el reintento
    # escriba solo a los que faltan, sin duplicar los que sí lo recibieron.
    pendientes = models.JSONField(default=list, blank=True, verbose_name='Destinatarios Pendientes')

    # Metadata
    mensajes_enviados = models.IntegerField(default=0, verbose_name='Mensajes Enviados')
    destinatarios_fallidos = models.IntegerField(default=0, verbose_name='Destinatarios con Error')
    error_message = models.TextField(blank=True, verbose_name='Mensaje de Error')
    intentos = models.PositiveSmallIntegerField(default=0, verbose_name='Intentos de Envío')

    class Meta:
        verbose_name = 'Reporte Generado'
        verbose_name_plural = 'Reportes Generados'
        ordering = ['-fecha_generacion']
        indexes = [
            models.Index(fields=['-fecha_generacion']),
            models.Index(fields=['tipo', 'estado']),
            # Una sola ejecución programada por tipo y período.
            models.Index(fields=['tipo', 'fecha_periodo', 'origen'], name='rep_auto_periodo_idx'),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_periodo.strftime('%d/%m/%Y')}"


class ConfiguracionReporte(models.Model):
    """
    Configuración de reportes automáticos.

    `hora_envio` + `dia_semana` / `dia_mes` son la fuente de verdad de la
    programación: el dispatcher lee estos campos en cada tick, por lo que
    editar la configuración surte efecto sin reiniciar Celery Beat.
    """
    DIAS_SEMANA_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    FORMATO_ADJUNTO_CHOICES = [
        ('ninguno', 'Solo texto'),
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('ambos', 'PDF + Excel'),
    ]

    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    tipo = models.CharField(max_length=20, choices=ReporteGenerado.TIPO_CHOICES, verbose_name='Tipo')

    # Configuración de envío
    activo = models.BooleanField(default=True, verbose_name='Activo')
    hora_envio = models.TimeField(default='08:00', verbose_name='Hora de Envío')
    # None = todos los días de la semana
    dia_semana = models.IntegerField(
        choices=DIAS_SEMANA_CHOICES, null=True, blank=True,
        verbose_name='Día de la Semana',
        help_text='Dejar vacío para todos los días',
    )
    # None = cualquier día del mes (1-28). El tope en 28 garantiza que todos
    # los meses tengan ese día.
    dia_mes = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='Día del Mes',
        help_text='1-28. Dejar vacío para cualquier día',
    )

    # Contenido
    formato_adjunto = models.CharField(
        max_length=10, choices=FORMATO_ADJUNTO_CHOICES, default='ninguno',
        verbose_name='Adjunto',
    )
    incluir_kpis = models.BooleanField(
        default=False, verbose_name='Incluir KPIs',
        help_text='Agrega indicadores financieros al reporte',
    )

    # Destinatarios por defecto
    destinatarios_whatsapp = models.TextField(blank=True, verbose_name='Teléfonos WhatsApp', help_text='Separados por coma')
    destinatarios_email = models.TextField(blank=True, verbose_name='Emails', help_text='Separados por coma')

    # Metadata
    ultimo_envio = models.DateTimeField(null=True, blank=True, verbose_name='Último Envío Exitoso')
    ultimo_intento = models.DateTimeField(null=True, blank=True, verbose_name='Último Intento')
    fallos_consecutivos = models.PositiveSmallIntegerField(default=0, verbose_name='Fallos Consecutivos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'
        ordering = ['tipo']
        constraints = [
            # Un tipo = una programación. Sin esto el dispatcher enviaría el
            # mismo reporte varias veces por tick.
            models.UniqueConstraint(fields=['tipo'], name='rep_auto_config_tipo_unico'),
            models.CheckConstraint(
                check=Q(dia_mes__isnull=True) | Q(dia_mes__gte=1, dia_mes__lte=28),
                name='rep_auto_config_dia_mes_rango',
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({'Activo' if self.activo else 'Inactivo'})"

    def descripcion_programacion(self):
        """Texto legible de la programación, para la UI y los logs."""
        partes = []
        if self.dia_semana is not None:
            partes.append(f"cada {self.get_dia_semana_display()}")
        if self.dia_mes is not None:
            partes.append(f"el día {self.dia_mes} de cada mes")
        if not partes:
            partes.append("todos los días")
        partes.append(f"a las {str(self.hora_envio)[:5]}")
        return " ".join(partes)

    def corresponde_hoy(self, fecha=None):
        """True si la fecha de hoy cumple dia_semana / dia_mes."""
        fecha = fecha or timezone.localdate()
        if self.dia_semana is not None and fecha.weekday() != self.dia_semana:
            return False
        if self.dia_mes is not None and fecha.day != self.dia_mes:
            return False
        return True
