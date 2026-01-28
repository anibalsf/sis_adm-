from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import CambioEstado, LogAuditoria
from afiliados.models import Afiliado
from cuotas.models import Cuota
from sanciones.models import Sancion
from vehiculos.models import Vehiculo
from hojasruta.models import HojaRuta
from tesoreria.models import Pago
from sistema.middleware import get_current_user
import json

def get_cambios(instance):
    if not instance.pk:
        return None
    try:
        old_instance = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return None

    cambios = {}
    for field in instance._meta.fields:
        field_name = field.name
        old_value = getattr(old_instance, field_name)
        new_value = getattr(instance, field_name)
        if old_value != new_value:
            cambios[field_name] = {
                'antes': str(old_value),
                'despues': str(new_value)
            }
    return cambios if cambios else None

@receiver(pre_save)
def audit_log_pre_save(sender, instance, **kwargs):
    # Lista de modelos a los que aplicamos auditoría
    models_to_audit = [Afiliado, Vehiculo, HojaRuta, Pago, Cuota, Sancion]
    if sender not in models_to_audit:
        return

    if instance.pk:
        try:
            instance._old_state = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_state = None
    else:
        instance._old_state = None

@receiver(post_save)
def audit_log_post_save(sender, instance, created, **kwargs):
    models_to_audit = [Afiliado, Vehiculo, HojaRuta, Pago, Cuota, Sancion]
    if sender not in models_to_audit:
        return

    user = get_current_user()
    if user and not user.is_authenticated:
        user = None

    accion = 'crear' if created else 'editar'
    cambios = None
    
    if not created and hasattr(instance, '_old_state') and instance._old_state:
        cambios = {}
        for field in instance._meta.fields:
            name = field.name
            old_val = getattr(instance._old_state, name)
            new_val = getattr(instance, name)
            if old_val != new_val:
                cambios[name] = {
                    'antes': str(old_val),
                    'despues': str(new_val)
                }
        if not cambios:
            cambios = None

    LogAuditoria.objects.create(
        usuario=user,
        accion=accion,
        tabla=sender._meta.model_name,
        objeto_id=str(instance.pk),
        descripcion=f"{accion.capitalize()} {sender._meta.verbose_name}: {instance}",
        cambios=cambios
    )

@receiver(post_delete)
def audit_log_delete(sender, instance, **kwargs):
    models_to_audit = [Afiliado, Vehiculo, HojaRuta, Pago, Cuota, Sancion]
    if sender not in models_to_audit:
        return

    user = get_current_user()
    if user and not user.is_authenticated:
        user = None

    LogAuditoria.objects.create(
        usuario=user,
        accion='eliminar',
        tabla=sender._meta.model_name,
        objeto_id=str(instance.pk),
        descripcion=f"Eliminación {sender._meta.verbose_name}: {instance}"
    )

# Mantener compatibilidad con CambioEstado para lógica existente
@receiver(pre_save, sender=Afiliado)
@receiver(pre_save, sender=Cuota)
@receiver(pre_save, sender=Sancion)
def tracking_estado_compat(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        obj_anterior = sender.objects.get(pk=instance.pk)
        estado_anterior = getattr(obj_anterior, 'estado', None)
        estado_nuevo = getattr(instance, 'estado', None)
        
        if estado_anterior and estado_nuevo and estado_anterior != estado_nuevo:
            CambioEstado.objects.create(
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.pk,
                estado_anterior=estado_anterior,
                estado_nuevo=estado_nuevo,
                usuario=get_current_user()
            )
    except sender.DoesNotExist:
        pass
