from rest_framework import serializers
from .models import ReporteGenerado, ConfiguracionReporte


class ReporteGeneradoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    origen_display = serializers.CharField(source='get_origen_display', read_only=True)
    tasa_exito = serializers.SerializerMethodField()
    envio_completo = serializers.SerializerMethodField()

    class Meta:
        model = ReporteGenerado
        fields = [
            'id', 'tipo', 'tipo_display', 'origen', 'origen_display',
            'fecha_generacion', 'fecha_periodo', 'contenido', 'datos', 'adjuntos',
            'estado', 'estado_display', 'destinatarios_whatsapp', 'destinatarios_email',
            'mensajes_enviados', 'destinatarios_fallidos', 'intentos', 'pendientes',
            'error_message', 'tasa_exito', 'envio_completo',
        ]
        read_only_fields = [
            'id', 'fecha_generacion', 'contenido', 'datos', 'adjuntos', 'pendientes',
            'mensajes_enviados', 'destinatarios_fallidos', 'intentos', 'error_message',
        ]

    def get_tasa_exito(self, obj):
        total = (obj.mensajes_enviados or 0) + (obj.destinatarios_fallidos or 0)
        if not total:
            return None
        return round((obj.mensajes_enviados or 0) / total * 100, 1)

    def get_envio_completo(self, obj):
        """
        False cuando el estado es 'enviado' pero quedaron destinatarios sin
        recibir, para que la UI ofrezca reenviar solo a esos.
        """
        return obj.estado == 'enviado' and not obj.pendientes


class ConfiguracionReporteSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    dia_semana_display = serializers.CharField(
        source='get_dia_semana_display', read_only=True, default='Todos'
    )
    formato_adjunto_display = serializers.CharField(
        source='get_formato_adjunto_display', read_only=True
    )
    programacion = serializers.CharField(source='descripcion_programacion', read_only=True)
    proximo_envio = serializers.SerializerMethodField()
    estado_salud = serializers.SerializerMethodField()

    class Meta:
        model = ConfiguracionReporte
        fields = [
            'id', 'nombre', 'tipo', 'tipo_display', 'activo',
            'hora_envio', 'dia_semana', 'dia_semana_display', 'dia_mes',
            'formato_adjunto', 'formato_adjunto_display', 'incluir_kpis',
            'destinatarios_whatsapp', 'destinatarios_email',
            'ultimo_envio', 'ultimo_intento', 'fallos_consecutivos',
            'programacion', 'proximo_envio', 'estado_salud',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'ultimo_envio', 'ultimo_intento', 'fallos_consecutivos',
            'created_at', 'updated_at',
        ]

    def validate_dia_mes(self, value):
        # Tope en 28: garantiza que el día exista en todos los meses.
        if value is not None and not (1 <= value <= 28):
            raise serializers.ValidationError('El día debe estar entre 1 y 28.')
        return value

    def get_proximo_envio(self, obj):
        from datetime import timedelta

        from django.utils import timezone

        if not obj.activo:
            return None

        ahora = timezone.localtime()
        candidato = ahora.replace(
            hour=obj.hora_envio.hour, minute=obj.hora_envio.minute,
            second=0, microsecond=0,
        )
        if candidato <= ahora:
            candidato += timedelta(days=1)

        # Avanza hasta que el día de la semana/mes coincida (máx. ~14 meses)
        for _ in range(400):
            if _coincide(obj, candidato.date()):
                return candidato
            candidato += timedelta(days=1)
        return None

    def get_estado_salud(self, obj):
        if not obj.activo:
            return 'inactivo'
        if obj.fallos_consecutivos >= 3:
            return 'fallando'
        if obj.fallos_consecutivos > 0:
            return 'degradado'
        if not (obj.destinatarios_whatsapp or '').strip():
            return 'sin_destinatarios'
        return 'ok'


def _coincide(obj, fecha):
    if obj.dia_semana is not None and fecha.weekday() != obj.dia_semana:
        return False
    if obj.dia_mes is not None and fecha.day != obj.dia_mes:
        return False
    return True
