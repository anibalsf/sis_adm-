from django.apps import apps
from django.db.models.signals import post_delete, post_save, pre_save

from sistema.middleware import get_client_ip, get_current_user

from .models import CambioEstado, LogAuditoria

# Módulos que no se auditan: ruido técnico, tablas de infraestructura o riesgo
# de recursión (historial se audita a sí mismo si se incluye).
EXCLUIDOS_APP_LABELS = {
    'historial',
    'admin',
    'contenttypes',
    'sessions',
    'authtoken',
    'whatsapp_notif',
    'reportes_auto',
    'django_apscheduler',
    'token_blacklist',
}

# Excepciones puntuales dentro de apps que sí se auditan.
# 'auth' se audita a propósito: es el módulo de Usuarios (User y Group).
EXCLUIDOS_MODELOS = {
    ('auth', 'permission'),
}

# Campos que cambian solos o en cada operación y solo generarían ruido
CAMPOS_IGNORADOS = {'last_login'}

# Campos cuyo valor nunca debe quedar escrito en la bitácora
CAMPOS_SENSIBLES = ('password', 'contrasena', 'contraseña', 'token', 'secret')
VALOR_OCULTO = '(oculto)'

# Estos modelos ya registran CambioEstado a mano en sus vistas (cuotas/views.py,
# hojasruta/views.py, sanciones/views.py). incluirlos aquí duplicaría cada cambio.
ESTADO_YA_REGISTRADO = {
    ('cuotas', 'cuota'),
    ('hojasruta', 'hojaruta'),
    ('sanciones', 'sancion'),
}

AUDITADOS = []


def get_modelos_auditados():
    """Todos los modelos de negocio de todos los módulos instalables."""
    return [
        model
        for model in apps.get_models()
        if model._meta.app_label not in EXCLUIDOS_APP_LABELS
        and (model._meta.app_label, model._meta.model_name) not in EXCLUIDOS_MODELOS
        and not model._meta.abstract
        and not model._meta.proxy
        and model._meta.managed
    ]


def _texto(valor):
    return '' if valor is None else str(valor)


def _valor_legible(field, instance, valor_crudo):
    """Convierte el valor a texto; en ForeignKey recupera el nombre del registro."""
    if valor_crudo is None or valor_crudo == '':
        return ''
    if field.is_relation and field.many_to_one:
        relacionado = getattr(instance, field.name, None)
        if relacionado is not None:
            return str(relacionado)[:200]
    return _texto(valor_crudo)[:200]


def _normalizar(field, valor):
    """Convierte al tipo real del campo.

    Necesario porque al asignar, por ejemplo, fecha='2026-09-25' el atributo del
    objeto sigue siendo texto y la base de datos lo devuelve como date: sin
    normalizar, cada guardado parecería un cambio.
    """
    if valor is None:
        return None
    try:
        return field.to_python(valor)
    except Exception:
        return valor


def _es_automatico(field):
    return bool(getattr(field, 'auto_now', False) or getattr(field, 'auto_now_add', False))


def _es_sensible(field):
    nombre = field.name.lower()
    return any(patron in nombre for patron in CAMPOS_SENSIBLES)


def _describir_cambios(instance, anterior):
    """Compara el registro guardado con el que había en base de datos."""
    if anterior is None:
        return None, None

    cambios = {}
    labels = {}
    for field in instance._meta.fields:
        if field.primary_key or _es_automatico(field) or field.name in CAMPOS_IGNORADOS:
            continue

        attname = field.attname
        valor_antes = _normalizar(field, getattr(anterior, attname, None))
        valor_despues = _normalizar(field, getattr(instance, attname, None))
        if valor_antes == valor_despues:
            continue

        if _es_sensible(field):
            # Se registra que cambió, nunca su valor (hash de contraseña, tokens...)
            cambios[field.name] = {'antes': VALOR_OCULTO, 'despues': VALOR_OCULTO}
        else:
            cambios[field.name] = {
                'antes': _valor_legible(field, anterior, valor_antes),
                'despues': _valor_legible(field, instance, valor_despues),
            }
        labels[field.name] = str(field.verbose_name)

    return (cambios, labels) if cambios else (None, None)


def pre_save_auditoria(sender, instance, **kwargs):
    instance._estado_anterior = None
    if not instance.pk:
        return
    try:
        instance._estado_anterior = sender.objects.filter(pk=instance.pk).first()
    except sender.DoesNotExist:
        instance._estado_anterior = None


def post_save_auditoria(sender, instance, created, **kwargs):
    accion = 'crear' if created else 'editar'
    cambios = labels = None

    if not created:
        cambios, labels = _describir_cambios(instance, getattr(instance, '_estado_anterior', None))
        if cambios is None:
            # Guardado sin ningún cambio real: no ensuciar la bitácora
            return

    try:
        descripcion_objeto = str(instance)[:250]
    except Exception:
        descripcion_objeto = f'#{instance.pk}'

    LogAuditoria.objects.create(
        usuario=get_current_user(),
        accion=accion,
        app_label=sender._meta.app_label,
        tabla=sender._meta.model_name,
        objeto_id=str(instance.pk),
        descripcion=f"{accion.capitalize()} {sender._meta.verbose_name}: {descripcion_objeto}",
        cambios=cambios,
        cambios_labels=labels,
        ip_address=get_client_ip(),
    )


def post_delete_auditoria(sender, instance, **kwargs):
    try:
        descripcion_objeto = str(instance)[:250]
    except Exception:
        descripcion_objeto = f'#{instance.pk}'

    LogAuditoria.objects.create(
        usuario=get_current_user(),
        accion='eliminar',
        app_label=sender._meta.app_label,
        tabla=sender._meta.model_name,
        objeto_id=str(instance.pk),
        descripcion=f"Eliminación {sender._meta.verbose_name}: {descripcion_objeto}",
        ip_address=get_client_ip(),
    )


def pre_save_cambio_estado(sender, instance, **kwargs):
    """Registra el histórico de estados de cualquier modelo con campo 'estado'."""
    if not instance.pk:
        return

    anterior = getattr(instance, '_estado_anterior', None)
    if anterior is None:
        try:
            anterior = sender.objects.filter(pk=instance.pk).first()
        except sender.DoesNotExist:
            return

    if anterior is None:
        return

    estado_anterior = getattr(anterior, 'estado', None)
    estado_nuevo = getattr(instance, 'estado', None)
    if not estado_anterior or not estado_nuevo or estado_anterior == estado_nuevo:
        return

    from django.contrib.contenttypes.models import ContentType

    try:
        CambioEstado.objects.create(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk,
            estado_anterior=str(estado_anterior)[:30],
            estado_nuevo=str(estado_nuevo)[:30],
            usuario=get_current_user(),
        )
    except Exception:
        # El histórico de estados nunca debe impedir la operación principal
        pass


def conectar_signals():
    """Conecta la auditoría a todos los modelos de todos los módulos."""
    global AUDITADOS
    AUDITADOS = get_modelos_auditados()

    for model in AUDITADOS:
        post_save.connect(post_save_auditoria, sender=model, dispatch_uid=f'bitacora_save_{model._meta.label_lower}')
        post_delete.connect(post_delete_auditoria, sender=model, dispatch_uid=f'bitacora_delete_{model._meta.label_lower}')
        pre_save.connect(pre_save_auditoria, sender=model, dispatch_uid=f'bitacora_pre_{model._meta.label_lower}')

        tiene_estado = any(f.name == 'estado' for f in model._meta.fields)
        if tiene_estado and (model._meta.app_label, model._meta.model_name) not in ESTADO_YA_REGISTRADO:
            pre_save.connect(
                pre_save_cambio_estado,
                sender=model,
                dispatch_uid=f'bitacora_estado_{model._meta.label_lower}',
            )

    return len(AUDITADOS)
