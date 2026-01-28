"""
Señales para enviar notificaciones automáticas de WhatsApp
cuando se aplican sanciones
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Sancion
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Sancion)
def notificar_sancion(sender, instance, created, **kwargs):
    """
    Notificar al afiliado cuando se le aplica una sanción (asíncrono)
    """
    # Solo enviar si es una sanción nueva
    if not created:
        return
    
    # Verificar que tenga afiliado con teléfono
    if not instance.afiliado or not hasattr(instance.afiliado, 'telefono') or not instance.afiliado.telefono:
        logger.warning(f"Sanción {instance.id}: Afiliado sin teléfono")
        return
    
    try:
        # Importar la tarea de Celery
        from whatsapp_notif.tasks import enviar_notificacion_sancion_task
        
        # Ejecutar en segundo plano (no bloquea el guardado)
        enviar_notificacion_sancion_task.delay(instance.id)
        
        logger.info(f"Tarea de notificación de sanción programada para sanción {instance.id}")
        
    except Exception as e:
        logger.error(f"Error al programar notificación de sanción {instance.id}: {str(e)}")
