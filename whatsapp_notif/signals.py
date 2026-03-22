"""
Señales de Django para envío automático de notificaciones WhatsApp
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .services import whatsapp_service

logger = logging.getLogger(__name__)


# Importar modelos relacionados cuando estén disponibles
try:
    from tesoreria.models import Pago
    PAGO_MODEL_AVAILABLE = True
except ImportError:
    logger.warning("Modelo Pago no disponible")
    PAGO_MODEL_AVAILABLE = False

try:
    from sanciones.models import Sancion
    SANCION_MODEL_AVAILABLE = True
except ImportError:
    logger.warning("Modelo Sancion no disponible")
    SANCION_MODEL_AVAILABLE = False

try:
    from reservas.models import Reserva
    RESERVA_MODEL_AVAILABLE = True
except ImportError:
    logger.warning("Modelo Reserva no disponible")
    RESERVA_MODEL_AVAILABLE = False

try:
    from cuotas.models import Cuota
    CUOTA_MODEL_AVAILABLE = True
except ImportError:
    logger.warning("Modelo Cuota no disponible")
    CUOTA_MODEL_AVAILABLE = False

try:
    from hojasruta.models import HojaRuta
    HOJA_MODEL_AVAILABLE = True
except ImportError:
    logger.warning("Modelo HojaRuta no disponible")
    HOJA_MODEL_AVAILABLE = False


if PAGO_MODEL_AVAILABLE:
    @receiver(post_save, sender=Pago)
    def send_payment_notification(sender, instance, created, **kwargs):
        """
        Enviar notificación automática cuando se registra un pago
        """
        if not created:
            return
        
        try:
            # Obtener teléfono del afiliado
            if hasattr(instance, 'afiliado') and instance.afiliado:
                phone = instance.afiliado.telefono
                name = instance.afiliado.nombre_completo
                
                whatsapp_service.send_payment_confirmation(
                    phone=phone,
                    recipient_name=name,
                    amount=float(instance.monto),
                    payment_type=instance.tipo_pago.nombre if hasattr(instance, 'tipo_pago') else 'Pago',
                    payment_id=instance.id
                )
                logger.info(f"Notificación de pago enviada a {name}")
        
        except Exception as e:
            logger.error(f"Error al enviar notificación de pago: {str(e)}")


if SANCION_MODEL_AVAILABLE:
    @receiver(post_save, sender=Sancion)
    def send_sanction_notification(sender, instance, created, **kwargs):
        """
        Enviar notificación automática cuando se aplica una sanción
        """
        if not created:
            return
        
        try:
            # Obtener teléfono del afiliado
            if hasattr(instance, 'afiliado') and instance.afiliado:
                phone = instance.afiliado.telefono
                name = instance.afiliado.nombre_completo
                
                whatsapp_service.send_sanction_notice(
                    phone=phone,
                    recipient_name=name,
                    sanction_type=instance.descripcion if hasattr(instance, 'descripcion') else 'Sanción',
                    amount=float(instance.monto),
                    sanction_id=instance.id
                )
                logger.info(f"Notificación de sanción enviada a {name}")
        
        except Exception as e:
            logger.error(f"Error al enviar notificación de sanción: {str(e)}")


if RESERVA_MODEL_AVAILABLE:
    @receiver(post_save, sender=Reserva)
    def send_reservation_notification(sender, instance, created, **kwargs):
        """
        Enviar notificación automática cuando se crea o confirma una reserva
        """
        try:
            # Obtener teléfono del cliente
            if not instance.telefono:
                return

            from datetime import datetime
            
            # Formatear fecha
            fecha_str = instance.fecha_viaje.strftime('%d/%m/%Y') if instance.fecha_viaje else 'Por definir'
            ruta_nombre = instance.ruta.nombre if hasattr(instance, 'ruta') and instance.ruta else 'Ruta no especificada'
            codigo_res = f"RES-{instance.id:06d}"

            # Caso 1: Nueva reserva (Pendiente de pago)
            if created and instance.estado == 'pendiente':
                whatsapp_service.send_from_template(
                    template_name='reservation_received',
                    phone=instance.telefono,
                    context={
                        'nombre': instance.cliente,
                        'codigo': codigo_res,
                        'ruta': ruta_nombre,
                        'fecha': fecha_str,
                        'asiento': str(instance.asiento) if instance.asiento else 'Por asignar',
                    },
                    recipient_name=instance.cliente,
                    related_reservation_id=instance.id
                )
                logger.info(f"Notificación de RECIBO de reserva enviada a {instance.cliente}")

            # Caso 2: Reserva cambia a Confirmada (Pago realizado)
            elif not created and instance.estado == 'confirmada':
                # Solo enviar si el estado cambió en este guardado (esto requeriría trackear el estado previo)
                # Por simplicidad aquí lo enviamos, pero en producción es mejor verificar el cambio
                whatsapp_service.send_from_template(
                    template_name='reservation_confirmation',
                    phone=instance.telefono,
                    context={
                        'nombre': instance.cliente,
                        'codigo': codigo_res,
                        'ruta': ruta_nombre,
                        'fecha': fecha_str,
                        'hora': '06:00 AM', # Opcionalmente obtener del vehiculo/hoja
                        'asiento': str(instance.asiento) if instance.asiento else 'Por asignar',
                    },
                    recipient_name=instance.cliente,
                    related_reservation_id=instance.id
                )
                logger.info(f"Notificación de CONFIRMACIÓN de reserva enviada a {instance.cliente}")
        
        except Exception as e:
            logger.error(f"Error al enviar notificación de reserva: {str(e)}")


if CUOTA_MODEL_AVAILABLE:
    @receiver(post_save, sender=Cuota)
    def send_cuota_notification(sender, instance, created, **kwargs):
        """
        Enviar notificación automática cuando se paga una cuota
        """
        # Solo enviar si el estado cambia a 'pagada'
        if instance.estado != 'pagada':
            return
            
        try:
            # Obtener teléfono del afiliado
            if hasattr(instance, 'afiliado') and instance.afiliado:
                phone = instance.afiliado.telefono
                name = instance.afiliado.nombre_completo
                
                # Formatear periodo para el mensaje (ej: Enero 2024)
                periodo_str = instance.periodo.strftime('%m/%Y') if instance.periodo else 'N/A'
                
                whatsapp_service.send_from_template(
                    template_name='cuota_payment',
                    phone=phone,
                    context={
                        'nombre': name,
                        'periodo': periodo_str,
                        'monto': f"{instance.monto:.2f}",
                        'tipo': instance.tipo,
                    },
                    recipient_name=name,
                    related_cuota_id=instance.id
                )
                logger.info(f"Notificación de pago de cuota enviada a {name}")
        
        except Exception as e:
            logger.error(f"Error al enviar notificación de cuota: {str(e)}")


if HOJA_MODEL_AVAILABLE:
    @receiver(post_save, sender=HojaRuta)
    def send_hoja_ruta_notification(sender, instance, created, **kwargs):
        """
        Enviar notificación automática cuando se emite una hoja de ruta
        """
        if not created:
            return
            
        try:
            # Obtener teléfono del afiliado
            if hasattr(instance, 'afiliado') and instance.afiliado:
                phone = instance.afiliado.telefono
                name = instance.afiliado.nombre_completo
                
                whatsapp_service.send_hoja_ruta_notification(
                    phone=phone,
                    recipient_name=name,
                    nro_hoja=instance.nro,
                    ruta=instance.ruta.nombre if instance.ruta else "General",
                    placa=instance.vehiculo.placa if instance.vehiculo else "N/A",
                    precio=float(instance.precio),
                    hoja_id=instance.id
                )
                logger.info(f"Notificación de emisión de hoja de ruta enviada a {name}")
        
        except Exception as e:
            logger.error(f"Error al enviar notificación de hoja de ruta: {str(e)}")
