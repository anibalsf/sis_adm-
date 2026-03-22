"""
Servicio principal para envío de mensajes WhatsApp
Soporta múltiples proveedores: Twilio, Baileys, WhatsApp Business API
"""
import logging
import time
from typing import Optional, Dict
from django.conf import settings
from decouple import config
from .models import WhatsAppMessage, WhatsAppConfig, WhatsAppTemplate

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Servicio centralizado para envío de mensajes WhatsApp
    """
    
    def __init__(self):
        self.config = None
        self.provider = None
        self.client = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Inicializar el servicio solo cuando se necesite (lazy initialization)"""
        if self._initialized:
            return
        
        try:
            self.config = WhatsAppConfig.get_config()
            self.provider = self.config.provider
            
            # Inicializar cliente según proveedor
            if self.provider == 'twilio':
                self._init_twilio()
            elif self.provider == 'baileys':
                self._init_baileys()
            else:
                logger.warning(f"Proveedor {self.provider} no configurado")
            
            self._initialized = True
        except Exception as e:
            # Si falla (ej: tabla no existe), solo loguear
            logger.warning(f"No se pudo inicializar WhatsApp service: {str(e)}")
            self._initialized = False
    
    def _init_twilio(self):
        """Inicializar cliente de Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = config('TWILIO_ACCOUNT_SID', default='')
            auth_token = config('TWILIO_AUTH_TOKEN', default='')
            
            if not account_sid or not auth_token:
                logger.error("Credenciales de Twilio no configuradas")
                self.client = None
                return
            
            self.client = Client(account_sid, auth_token)
            self.twilio_from = config('TWILIO_WHATSAPP_FROM', default='whatsapp:+14155238886')
            logger.info("Cliente Twilio inicializado correctamente")
            
        except ImportError:
            logger.error("twilio no está instalado. Ejecute: pip install twilio")
            self.client = None
        except Exception as e:
            logger.error(f"Error al inicializar Twilio: {str(e)}")
            self.client = None
    
    def _init_baileys(self):
        """Inicializar cliente de Baileys (placeholder)"""
        logger.warning("Baileys no implementado todavía")
        self.client = None
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalizar número de teléfono al formato WhatsApp
        
        Args:
            phone (str): Número en cualquier formato
        
        Returns:
            str: Número en formato whatsapp:+591XXXXXXXX
        """
        # Remover espacios y caracteres especiales
        phone = ''.join(filter(str.isdigit, phone))
        
        # Si no empieza con 591, agregarlo
        if not phone.startswith('591'):
            phone = '591' + phone
        
        return f"whatsapp:+{phone}"
    
    def send_message(
        self,
        phone: str,
        message: str,
        message_type: str = 'general',
        related_payment_id: Optional[int] = None,
        related_reservation_id: Optional[int] = None,
        related_sanction_id: Optional[int] = None,
        related_cuota_id: Optional[int] = None,
        related_hoja_id: Optional[int] = None,
        recipient_name: str = '',
        use_celery: bool = True,
        media_url: Optional[str] = None,
    ) -> Optional[WhatsAppMessage]:
        """
        Enviar mensaje de WhatsApp (asíncrono por defecto)
        """
        # Asegurar que el servicio esté inicializado
        self._ensure_initialized()
        
        # Verificar que esté habilitado
        if not self.config or not self.config.is_enabled:
            logger.warning("WhatsApp deshabilitado en configuración")
            return None
        
        # Normalizar teléfono
        normalized_phone = self._normalize_phone(phone)
        
        # Crear registro del mensaje con estado 'pending'
        whatsapp_msg = WhatsAppMessage.objects.create(
            recipient_phone=normalized_phone,
            recipient_name=recipient_name,
            message_type=message_type,
            message_content=message,
            related_payment_id=related_payment_id,
            related_reservation_id=related_reservation_id,
            related_sanction_id=related_sanction_id,
            related_cuota_id=related_cuota_id,
            related_hoja_id=related_hoja_id,
            status='pending'
        )
        
        if use_celery:
            from .tasks import send_whatsapp_task
            send_whatsapp_task.delay(whatsapp_msg.id, media_url=media_url)
            return whatsapp_msg
        
        # Envío síncrono (solo si use_celery=False)
        return self._do_send(whatsapp_msg, media_url=media_url)

    def _do_send(self, whatsapp_msg: WhatsAppMessage, media_url: Optional[str] = None) -> WhatsAppMessage:
        """
        Realiza el envío real del mensaje
        """
        try:
            # Enviar según proveedor
            if self.provider == 'twilio':
                result = self._send_via_twilio(
                    whatsapp_msg.recipient_phone, 
                    whatsapp_msg.message_content,
                    media_url=media_url
                )
                if result:
                    whatsapp_msg.mark_as_sent(external_id=result)
                    logger.info(f"Mensaje enviado a {whatsapp_msg.recipient_phone}: {result}")
                else:
                    whatsapp_msg.mark_as_failed("Error al enviar via Twilio")
            
            elif self.provider == 'baileys':
                whatsapp_msg.mark_as_failed("Baileys no implementado")
            
            else:
                whatsapp_msg.mark_as_failed(f"Proveedor {self.provider} no soportado")
        
        except Exception as e:
            logger.error(f"Error al enviar mensaje {whatsapp_msg.id}: {str(e)}")
            whatsapp_msg.mark_as_failed(str(e))
        
        return whatsapp_msg
    
    def _send_via_twilio(self, to: str, body: str, media_url: Optional[str] = None) -> Optional[str]:
        """
        Enviar mensaje via Twilio
        
        Returns:
            str: SID del mensaje si fue exitoso, None si falló
        """
        if not self.client:
            logger.error("Cliente Twilio no inicializado")
            return None
        
        try:
            params = {
                'from_': self.twilio_from,
                'body': body,
                'to': to
            }
            if media_url:
                params['media_url'] = [media_url]
                
            message = self.client.messages.create(**params)
            return message.sid
        
        except Exception as e:
            logger.error(f"Error Twilio: {str(e)}")
            return None
    
    def send_from_template(
        self,
        template_name: str,
        phone: str,
        context: Dict,
        **kwargs
    ) -> Optional[WhatsAppMessage]:
        """
        Enviar mensaje usando una plantilla predefinida
        
        Args:
            template_name (str): Nombre de la plantilla
            phone (str): Número de teléfono destino
            context (dict): Variables para la plantilla
            **kwargs: Argumentos adicionales para send_message
        
        Returns:
            WhatsAppMessage: Objeto con el mensaje enviado
        """
        # Asegurar que el servicio esté inicializado
        self._ensure_initialized()
        
        try:
            template = WhatsAppTemplate.objects.get(
                name=template_name,
                is_active=True
            )
        except WhatsAppTemplate.DoesNotExist:
            logger.error(f"Plantilla '{template_name}' no encontrada")
            return None
        
        # Renderizar plantilla
        message = template.render(context)
        
        # Enviar mensaje
        return self.send_message(
            phone=phone,
            message=message,
            message_type=template.message_type,
            **kwargs
        )
    
    def send_payment_confirmation(
        self,
        phone: str,
        recipient_name: str,
        amount: float,
        payment_type: str,
        payment_id: int
    ) -> Optional[WhatsAppMessage]:
        """
        Enviar confirmación de pago
        """
        return self.send_from_template(
            template_name='payment_confirmation',
            phone=phone,
            context={
                'nombre': recipient_name,
                'monto': f"{amount:.2f}",
                'tipo': payment_type,
            },
            recipient_name=recipient_name,
            related_payment_id=payment_id
        )
    
    def send_shift_reminder(
        self,
        phone: str,
        recipient_name: str,
        shift_date: str,
        shift_route: str
    ) -> Optional[WhatsAppMessage]:
        """
        Enviar recordatorio de turno
        """
        return self.send_from_template(
            template_name='shift_reminder',
            phone=phone,
            context={
                'nombre': recipient_name,
                'fecha': shift_date,
                'ruta': shift_route,
            },
            recipient_name=recipient_name
        )
    
    def send_sanction_notice(
        self,
        phone: str,
        recipient_name: str,
        sanction_type: str,
        amount: float,
        sanction_id: int
    ) -> Optional[WhatsAppMessage]:
        """
        Enviar notificación de sanción
        """
        return self.send_from_template(
            template_name='sanction_notice',
            phone=phone,
            context={
                'nombre': recipient_name,
                'tipo': sanction_type,
                'monto': f"{amount:.2f}",
            },
            recipient_name=recipient_name,
            related_sanction_id=sanction_id
        )

    def send_cuota_payment(
        self,
        phone: str,
        recipient_name: str,
        periodo: str,
        amount: float,
        cuota_id: int
    ) -> Optional[WhatsAppMessage]:
        """
        Enviar confirmación de pago de cuota
        """
        return self.send_from_template(
            template_name='cuota_payment',
            phone=phone,
            context={
                'nombre': recipient_name,
                'periodo': periodo,
                'monto': f"{amount:.2f}",
            },
            recipient_name=recipient_name,
            related_cuota_id=cuota_id
        )

    def send_hoja_ruta_notification(
        self,
        phone: str,
        recipient_name: str,
        nro_hoja: str,
        ruta: str,
        placa: str,
        precio: float,
        hoja_id: int
    ) -> Optional[WhatsAppMessage]:
        """
        Enviar notificación de emisión de hoja de ruta
        """
        return self.send_from_template(
            template_name='hoja_ruta_emitted',
            phone=phone,
            context={
                'nombre': recipient_name,
                'nro': nro_hoja,
                'ruta': ruta,
                'placa': placa,
                'precio': f"{precio:.2f}",
            },
            recipient_name=recipient_name,
            related_hoja_id=hoja_id
        )


# Instancia global del servicio
whatsapp_service = WhatsAppService()
