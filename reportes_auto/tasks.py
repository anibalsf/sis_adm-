"""
Tareas de envío automático de reportes vía Celery.

Todas las tareas delegan en `_ejecutar_reporte`, que:
  1. genera el contenido y los datos estructurados,
  2. persiste el `ReporteGenerado` con estado 'generado',
  3. resuelve destinatarios desde ConfiguracionReporte → settings → admin,
  4. envía por WhatsApp (con reintentos) y actualiza el estado real.

Si algo falla, la excepción se propaga para que Celery la registre y
reintente (antes se tragaba el error y devolvía un string, dejando el
reporte marcado como enviado aunque ningún mensaje hubiera salido).
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import ConfiguracionReporte, ReporteGenerado
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)

TAREAS_POR_TIPO = {
    'diario': 'reportes_auto.tasks.send_daily_report_task',
    'semanal': 'reportes_auto.tasks.send_weekly_report_task',
    'mensual': 'reportes_auto.tasks.send_monthly_report_task',
    'lunes_control': 'reportes_auto.tasks.send_monday_hojas_ruta_report_task',
}

GENERADORES = {
    'diario': ReportGenerator.get_daily_summary,
    'semanal': ReportGenerator.get_weekly_financial_summary,
    'mensual': ReportGenerator.get_monthly_summary,
    'lunes_control': ReportGenerator.get_monday_hojas_pagadas_report,
}

NOMBRES = {
    'diario': 'Reporte diario',
    'semanal': 'Reporte semanal',
    'mensual': 'Reporte mensual',
    'lunes_control': 'Control de lunes',
    'puntero_la_paz': 'Control del puntero La Paz',
}

# Tope de reintentos automáticos del dispatcher. Sin esto, un destino caído
# (número mal escrito, Twilio caído) provoca un envío cada 10 minutos para siempre.
MAX_FALLOS_CONSECUTIVOS = 5


def _split(valor):
    """Normaliza una lista separada por comas/saltos de línea."""
    if not valor:
        return []
    if isinstance(valor, (list, tuple)):
        items = valor
    else:
        items = str(valor).replace('\n', ',').replace(';', ',').split(',')
    return [str(i).strip() for i in items if str(i).strip()]


def _destinatarios(tipo, config=None):
    """
    Prioridad: ConfiguracionReporte del tipo → settings → ADMIN_PHONE_NUMBER.
    Si la configuración existe pero está inactiva, no se envía nada.
    """
    if config is None:
        try:
            config = ConfiguracionReporte.objects.filter(tipo=tipo).order_by('id').first()
        except Exception:
            logger.warning('No se pudo leer ConfiguracionReporte para %s', tipo, exc_info=True)
            config = None

    if config is not None:
        if not config.activo:
            logger.info('Reporte %s omitido: configuración inactiva', tipo)
            return [], config
        dest = _split(config.destinatarios_whatsapp)
        if dest:
            return dest, config
        # config activa pero sin destinatarios → cae a settings
    else:
        config = None

    dest = _split(getattr(settings, 'REPORT_RECIPIENTS_WHATSAPP', ''))
    if dest:
        return dest, config

    admin = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
    if admin:
        return [str(admin)], config

    return [], config


def _enviar_whatsapp(phone, mensaje, tipo, media_url=None):
    """
    Envía un mensaje y **verifica el resultado real**.

    `use_celery=False` es intencional: encolando el envío, `send_message`
    devuelve el mensaje en estado `pending` y el reporte se marcaría como
    enviado aunque Twilio nunca lo recibiera. El servicio tampoco lanza
    excepciones ante un fallo, marca el mensaje como `failed`, así que el
    estado se valida aquí.

    Lanza RuntimeError si el envío no se concretó, para que Celery reintente.
    """
    from whatsapp_notif.services import whatsapp_service

    kwargs = {
        'phone': phone,
        'message': mensaje,
        'message_type': 'general',
        'recipient_name': 'Directivo',
        'use_celery': False,
    }
    if media_url:
        kwargs['media_url'] = media_url

    resultado = whatsapp_service.send_message(**kwargs)

    if resultado is None:
        raise RuntimeError('WhatsApp deshabilitado o sin configuración válida')

    if resultado.status == 'failed':
        raise RuntimeError(resultado.error_message or 'Twilio rechazó el mensaje')

    return resultado


def _formatos(config):
    """Traduce `formato_adjunto` a la lista de formatos a generar."""
    if not config:
        return ()
    return {
        'pdf': ('pdf',),
        'excel': ('excel',),
        'ambos': ('pdf', 'excel'),
    }.get(config.formato_adjunto, ())


def _primer_adjunto_publico(adjuntos):
    """Primer adjunto con URL absoluta (Twilio necesita descargarlo)."""
    for adjunto in adjuntos or []:
        url = adjunto.get('url') or ''
        if url.startswith('http://') or url.startswith('https://'):
            return adjunto
    return None


def _fecha_periodo(tipo, hoy=None):
    """
    Período que cubre cada reporte. Se usa un período ya cerrado para que
    reintentar mañana no cambie los números del reporte.
    """
    hoy = hoy or timezone.localdate()
    if tipo == 'diario':
        return hoy - timedelta(days=1)
    if tipo == 'mensual':
        from dateutil.relativedelta import relativedelta
        return (hoy.replace(day=1) - relativedelta(months=1)).replace(day=1)
    return hoy


def _registro_previo(tipo, fecha_periodo, origen):
    """
    Registro de la ejecución anterior del mismo tipo/período/origen.

    Sirve para dos cosas: no duplicar envíos cuando corren el dispatcher y el
    crontab de respaldo, y reintentar sobre el mismo registro en vez de
    crear uno nuevo por intento.
    """
    return (
        ReporteGenerado.objects
        .filter(tipo=tipo, fecha_periodo=fecha_periodo, origen=origen)
        .order_by('-id')
        .first()
    )


def _ejecutar_reporte(tipo, origen='programado', config=None, permitir_repetido=False):
    """
    Núcleo compartido por todas las tareas. Devuelve un dict con el resumen
    de la ejecución.
    """
    generador = GENERADORES.get(tipo)
    if generador is None:
        raise ValueError(f'Tipo de reporte no soportado: {tipo}')

    fecha_periodo = _fecha_periodo(tipo)
    previo = _registro_previo(tipo, fecha_periodo, origen)

    # El dispatcher y el crontab de respaldo pueden coincidir en la misma
    # ventana; si el reporte ya salió, no se reenvía a los mismos contactos.
    if (
        not permitir_repetido
        and origen == 'programado'
        and previo is not None
        and previo.estado == 'enviado'
        and not previo.pendientes
    ):
        logger.info('Reporte %s de %s ya enviado, se omite', tipo, fecha_periodo)
        return {
            'tipo': tipo, 'estado': 'omitido', 'enviados': 0,
            'motivo': 'ya_enviado', 'reporte_id': previo.id,
        }

    destinatarios, config = _destinatarios(tipo, config=config)
    if not destinatarios:
        logger.warning('Reporte %s sin destinatarios configurados', tipo)
        return {'tipo': tipo, 'estado': 'omitido', 'enviados': 0, 'motivo': 'sin_destinatarios'}

    texto, datos = generador()

    if previo is not None and previo.estado in ('fallido', 'generado'):
        # Reintento: se reutiliza el registro para no duplicar el historial.
        reporte = previo
        reporte.contenido = texto
        reporte.datos = datos
        reporte.intentos = (reporte.intentos or 0) + 1
        reporte.pendientes = destinatarios
        reporte.save(update_fields=['contenido', 'datos', 'intentos', 'pendientes'])
    else:
        reporte = ReporteGenerado.objects.create(
            tipo=tipo,
            fecha_periodo=fecha_periodo,
            contenido=texto,
            datos=datos,
            destinatarios_whatsapp=','.join(destinatarios),
            estado='generado',
            origen=origen,
            intentos=1,
            pendientes=destinatarios,
        )

    if config is not None:
        config.ultimo_intento = timezone.now()

    # Adjuntos: se persisten en disco para que el usuario pueda descargarlos
    # desde la UI incluso si el envío por WhatsApp falla.
    adjuntos = reporte.adjuntos or []
    formatos = _formatos(config)
    if formatos:
        try:
            from .documentos import guardar_adjuntos
            # El sufijo evita que un reintento pise el archivo del intento anterior.
            sufijo = '' if reporte.intentos <= 1 else f'_intento{reporte.intentos}'
            adjuntos = guardar_adjuntos(datos, tipo, fecha_periodo, formatos, sufijo=sufijo)
            reporte.adjuntos = adjuntos
        except Exception:
            logger.error('No se pudieron generar los adjuntos del reporte %s', tipo, exc_info=True)
            reporte.error_message = 'Error generando adjuntos: ver logs.'

    # El adjunto solo puede viajarse por WhatsApp si Twilio puede alcanzarlo
    # por URL pública; sin MEDIA_BASE_URL solo se envía el resumen en texto.
    adjunto_publico = _primer_adjunto_publico(adjuntos)
    if formatos and not adjunto_publico:
        logger.warning(
            'El reporte %s tiene adjuntos configurados pero MEDIA_BASE_URL no está definido; '
            'se enviará solo el texto', tipo,
        )

    pendientes = list(reporte.pendientes or destinatarios)
    errores = []
    for phone in pendientes:
        try:
            _enviar_whatsapp(phone, texto, tipo, media_url=adjunto_publico['url'] if adjunto_publico else None)
        except Exception as exc:
            logger.error('Error enviando reporte %s a %s: %s', tipo, phone, exc)
            errores.append(f'{phone}: {exc}')

    ya_enviados = reporte.mensajes_enviados or 0
    enviados_total = ya_enviados + (len(pendientes) - len(errores))
    fallidos = [e.split(':', 1)[0].strip() for e in errores]

    reporte.mensajes_enviados = enviados_total
    reporte.destinatarios_fallidos = len(errores)
    reporte.pendientes = fallidos
    if errores:
        reporte.error_message = '\n'.join(errores)
        # Envío parcial: queda pendiente para que el reintento escriba solo a los
        # que faltan, sin volver a enviar a los que sí lo recibieron.
        reporte.estado = 'enviado' if enviados_total else 'fallido'
    else:
        reporte.estado = 'enviado'
        reporte.error_message = ''
    reporte.save(update_fields=[
        'mensajes_enviados', 'destinatarios_fallidos', 'pendientes',
        'error_message', 'estado', 'adjuntos',
    ])

    if config is not None:
        if not errores:
            config.ultimo_envio = timezone.now()
            config.fallos_consecutivos = 0
        else:
            config.fallos_consecutivos += 1
        config.save(update_fields=['ultimo_intento', 'ultimo_envio', 'fallos_consecutivos'])

    if enviados_total == 0:
        raise RuntimeError(
            f'No se pudo enviar el {NOMBRES.get(tipo, tipo)} a ningún destinatario: '
            + '; '.join(errores)
        )

    return {
        'tipo': tipo,
        'estado': reporte.estado,
        'enviados': enviados_total,
        'fallidos': len(errores),
        'reporte_id': reporte.id,
    }


# --------------------------------------------------------------------- tareas
@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_daily_report_task(self):
    """Reporte diario (ayer) a la directiva."""
    try:
        return _ejecutar_reporte('diario')
    except Exception as exc:
        logger.warning('Reporte diario falló, reintentando: %s', exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_weekly_report_task(self):
    """Reporte semanal (últimos 7 días)."""
    try:
        return _ejecutar_reporte('semanal')
    except Exception as exc:
        logger.warning('Reporte semanal falló, reintentando: %s', exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_monthly_report_task(self):
    """Cierre del mes calendario anterior."""
    try:
        return _ejecutar_reporte('mensual')
    except Exception as exc:
        logger.warning('Reporte mensual falló, reintentando: %s', exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def send_monday_hojas_ruta_report_task(self):
    """Lista de control de hojas de ruta del lunes."""
    try:
        return _ejecutar_reporte('lunes_control')
    except Exception as exc:
        logger.warning('Reporte de control del lunes falló, reintentando: %s', exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def send_daily_puntero_la_paz_task(self):
    """
    Control diario del puntero La Paz.

    Es un aviso operativo, no un reporte financiero: se envía siempre al
    número configurado en settings (PUNTERO_LA_PAZ_PHONE_NUMBER) con
    fallback a ADMIN_PHONE_NUMBER.
    """
    try:
        texto, datos = ReportGenerator.get_daily_puntero_la_paz_report()
    except Exception as exc:
        logger.error('No se pudo generar el reporte del puntero: %s', exc)
        raise self.retry(exc=exc)

    destino = (
        getattr(settings, 'PUNTERO_LA_PAZ_PHONE_NUMBER', None)
        or getattr(settings, 'ADMIN_PHONE_NUMBER', None)
    )
    if not destino:
        logger.warning('Sin PUNTERO_LA_PAZ_PHONE_NUMBER ni ADMIN_PHONE_NUMBER configurados')
        return {'estado': 'omitido', 'motivo': 'sin_destinatarios'}

    reporte = ReporteGenerado.objects.create(
        tipo='puntero_la_paz',
        fecha_periodo=timezone.localdate(),
        contenido=texto,
        datos=datos,
        destinatarios_whatsapp=str(destino),
        estado='generado',
        origen='programado',
        intentos=1,
    )

    try:
        _enviar_whatsapp(str(destino), texto, 'puntero_la_paz')
    except Exception as exc:
        logger.error('Error enviando el reporte del puntero a %s: %s', destino, exc)
        reporte.intentos += 1
        reporte.estado = 'fallido'
        reporte.destinatarios_fallidos = 1
        reporte.error_message = str(exc)
        reporte.save(update_fields=['intentos', 'estado', 'destinatarios_fallidos', 'error_message'])
        raise self.retry(exc=exc)

    reporte.mensajes_enviados = 1
    reporte.estado = 'enviado'
    reporte.save(update_fields=['mensajes_enviados', 'estado'])
    return {'estado': 'enviado', 'enviados': 1, 'reporte_id': reporte.id}


@shared_task
def dispatch_reportes_programados():
    """
    Dispatcher: se ejecuta cada 10 minutos y dispara los reportes cuya
    `ConfiguracionReporte` corresponde a la hora actual.

    Así la hora/día editable desde la UI es la fuente real de verdad, en vez
    de estar hardcodeada en CELERY_BEAT_SCHEDULE.
    """
    ahora = timezone.localtime()
    hoy = ahora.date()
    enviados = []
    omitidos = []

    try:
        configs = ConfiguracionReporte.objects.filter(activo=True)
    except Exception:
        logger.error('No se pudo leer la configuración de reportes', exc_info=True)
        return {'error': 'configuracion_ilegible'}

    for config in configs:
        try:
            if not config.corresponde_hoy(hoy):
                continue

            if config.fallos_consecutivos >= MAX_FALLOS_CONSECUTIVOS:
                logger.error(
                    'Reporte %s en pausa: %s fallos consecutivos. Revise los destinatarios '
                    'o reactívelo desde la configuración.', config.tipo, config.fallos_consecutivos,
                )
                omitidos.append(f'{config.tipo}:pausado_por_fallos')
                continue

            # Tolerancia de 10 min: el tick puede caer justo en el minuto
            if abs((ahora - ahora.replace(
                    hour=config.hora_envio.hour,
                    minute=config.hora_envio.minute,
                    second=0, microsecond=0)).total_seconds()) > 600:
                continue

            # Evita duplicados si ya se envió en esta misma hora
            if config.ultimo_envio and config.ultimo_envio >= ahora.replace(
                    hour=config.hora_envio.hour,
                    minute=config.hora_envio.minute,
                    second=0, microsecond=0) - timedelta(minutes=10):
                omitidos.append(f'{config.tipo}:ya_enviado')
                continue

            nombre_tarea = TAREAS_POR_TIPO.get(config.tipo)
            if not nombre_tarea:
                omitidos.append(f'{config.tipo}:sin_tarea')
                continue

            from celery import current_app
            current_app.send_task(nombre_tarea)
            enviados.append(config.tipo)
            config.ultimo_intento = ahora
            config.save(update_fields=['ultimo_intento'])
        except Exception:
            logger.error('Error despachando el reporte %s', config.tipo, exc_info=True)
            omitidos.append(f'{config.tipo}:error')

    return {'enviados': enviados, 'omitidos': omitidos}
