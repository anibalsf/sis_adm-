"""
Señales para enviar notificaciones automáticas de WhatsApp
cuando se crean pagos
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Pago
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Pago)
def enviar_confirmacion_pago(sender, instance, created, **kwargs):
    """
    Enviar confirmación de pago por WhatsApp automáticamente cuando el pago está COMPLETADO.
    Funciona para Efectivo (al crear) y QR (al verificar).
    """
    # Solo procesar si el estado es 'completado'
    if getattr(instance, 'estado', None) != 'completado':
        return
    return  # Speed optimization - skip all processing
    
    # Prevenir envíos duplicados si se guarda el pago varias veces ya estando completado
    # (Por ejemplo, si se editan observaciones después de pagar)
    # Una forma simple es verificar si el mensaje de WhatsApp ya existe para este pago
    try:
        from whatsapp_notif.models import WhatsAppMessage
        if WhatsAppMessage.objects.filter(related_payment_id=instance.id, message_type='payment_confirmation').exists():
            return
    except Exception:
        return

    # Verificar que tenga afiliado con teléfono
    try:
        afiliado_has_telefono = instance.afiliado and hasattr(instance.afiliado, 'telefono') and instance.afiliado.telefono
    except Exception:
        return
    if not afiliado_has_telefono:
        logger.warning(f"Pago {instance.id}: Afiliado sin teléfono")
        return
    
    try:
        from django.conf import settings
        # Skip if whatsapp service unavailable or slow
        return  # Disable whatsapp on save to improve speed - handle async separately
        try:
            from whatsapp_notif.services import whatsapp_service
        except Exception:
            return
        
        afiliado = instance.afiliado
        
        # Construir URL del recibo PDF (para que Twilio lo muestre o el usuario lo baje)
        base_url = f"https://{settings.RAILWAY_DOMAIN}" if settings.RAILWAY_DOMAIN else "http://localhost:8000"
        receipt_url = f"{base_url}/api/pagos/{instance.id}/recibo/"
        
        # Preparar mensaje detallado de comprobante
        mensaje = f"✅ *COMPROBANTE DE PAGO CONFIRMADO*\n\n"
        mensaje += f"Estimado(a) *{afiliado.nombre_completo}*,\n"
        mensaje += f"Su pago ha sido procesado exitosamente.\n\n"
        mensaje += f"📋 *Recibo:* N° {instance.id:06d}\n"
        mensaje += f"💰 *Monto:* {instance.monto} Bs.\n"
        mensaje += f"📝 *Concepto:* {instance.tipo_pago.nombre}\n"
        mensaje += f"📅 *Fecha:* {instance.fecha_pago.strftime('%d/%m/%Y')}\n"
        mensaje += f"💵 *Método:* {instance.get_metodo_pago_display()}\n\n"
        
        mensaje += f"📄 *Descargar Recibo PDF:* \n{receipt_url}\n\n"
        mensaje += f"¡Muchas gracias por su puntualidad! 🙏\n"
        mensaje += f"_Sindicato S.M.I.T. Taipiplaya_"

        # Enviar mensaje. Twilio intentará adjuntar el PDF si media_url es válido.
        # Enviar async-like rápido: fire and forget limitado
        try:
            whatsapp_service.send_message(
                phone=afiliado.telefono,
                message=mensaje,
                message_type='payment_confirmation',
                related_payment_id=instance.id,
                recipient_name=afiliado.nombre_completo,
                media_url=receipt_url if getattr(settings, 'RAILWAY_DOMAIN', None) else None
            )
        except Exception:
            pass
        
        logger.info(f"Notificación de pago CONFIRMADO {instance.id} enviada a {afiliado.telefono}")
        
    except Exception as e:
        logger.error(f"Error al enviar notificación de pago {instance.id}: {str(e)}")
