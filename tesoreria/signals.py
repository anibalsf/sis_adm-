"""
Señales para enviar notificaciones automáticas de WhatsApp
cuando se crean pagos
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Pago
import logging

logger = logging.getLogger(__name__)


# @receiver(post_save, sender=Pago)
def enviar_confirmacion_pago(sender, instance, created, **kwargs):
    """
    Enviar confirmación de pago por WhatsApp automáticamente (asíncrono)
    """
    # Solo enviar si es un pago nuevo y está confirmado
    if not created or instance.estado != 'confirmado':
        return
    
    # Verificar que tenga afiliado con teléfono
    if not instance.afiliado or not hasattr(instance.afiliado, 'telefono') or not instance.afiliado.telefono:
        logger.warning(f"Pago {instance.id}: Afiliado sin teléfono")
        return
    
    try:
        # Importar la tarea de Celery
        from whatsapp_notif.tasks import enviar_confirmacion_pago_task
        
        # Ejecutar en segundo plano (no bloquea el guardado)
        enviar_confirmacion_pago_task.delay(instance.id)
        
        logger.info(f"Tarea de confirmación de pago programada para pago {instance.id}")
        
    except Exception as e:
        logger.error(f"Error al programar confirmación de pago {instance.id}: {str(e)}")
