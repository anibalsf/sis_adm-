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
        self._last_error = None
        # Twilio
        self.twilio_from = None
        # Meta WhatsApp Cloud API
        self.cloud_token = None
        self.cloud_phone_id = None
        self.cloud_api_version = None
        # Baileys vía WAHA
        self.waha_url = None
        self.waha_api_key = None
        self.waha_session = None
    
    def _ensure_initialized(self):
        """Inicializar el servicio solo cuando se necesite (lazy initialization)"""
        if self._initialized and (self.provider != 'twilio' or self.client is not None):
            return
        
        try:
            self.config = WhatsAppConfig.get_config()
            self.provider = self.config.provider
            
            # Inicializar cliente según proveedor
            if self.provider == 'twilio':
                self._init_twilio()
            elif self.provider == 'whatsapp_business':
                self._init_cloud_api()
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
            tw_from = config('TWILIO_WHATSAPP_FROM', default='') or config('TWILIO_PHONE_NUMBER', default='')
            if not tw_from:
                tw_from = 'whatsapp:+14155238886'
            elif not tw_from.startswith('whatsapp:'):
                tw_from = 'whatsapp:' + tw_from
            self.twilio_from = tw_from
            logger.info("Cliente Twilio inicializado correctamente")
            
        except ImportError:
            logger.error("twilio no está instalado. Ejecute: pip install twilio")
            self.client = None
        except Exception as e:
            logger.error(f"Error al inicializar Twilio: {str(e)}")
            self.client = None
    
    def _init_baileys(self):
        """
        Inicializar Baileys vía WAHA (WhatsApp HTTP API).
        Requiere un servidor WAHA corriendo (Docker): https://waha.devlike.pro
        Variables: WAHA_URL, WAHA_API_KEY (opcional), WAHA_SESSION (opcional)
        """
        self.waha_url = (config('WAHA_URL', default='') or config('BAILEYS_URL', default='')).rstrip('/')
        self.waha_api_key = config('WAHA_API_KEY', default='')
        self.waha_session = config('WAHA_SESSION', default='default')
        if not self.waha_url:
            self._last_error = ('WAHA no configurado. Define WAHA_URL en el .env '
                                '(ej: http://localhost:3000) y ejecuta el servidor WAHA.')
            logger.error(self._last_error)
        else:
            logger.info(f"Baileys/WAHA configurado en {self.waha_url} (sesión: {self.waha_session})")

    def _init_cloud_api(self):
        """
        Inicializar Meta WhatsApp Cloud API (oficial).
        Variables: WHATSAPP_CLOUD_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_API_VERSION
        """
        self.cloud_token = config('WHATSAPP_CLOUD_TOKEN', default='')
        self.cloud_phone_id = config('WHATSAPP_PHONE_NUMBER_ID', default='')
        self.cloud_api_version = config('WHATSAPP_API_VERSION', default='v21.0')
        if not self.cloud_token or not self.cloud_phone_id:
            self._last_error = ('Cloud API no configurada. Define WHATSAPP_CLOUD_TOKEN y '
                                'WHATSAPP_PHONE_NUMBER_ID en el .env.')
            logger.error(self._last_error)
        else:
            logger.info("Meta WhatsApp Cloud API inicializada correctamente")

    def _digits(self, phone: str) -> str:
        """
        Devuelve solo dígitos del número, agregando el código de país 591 si falta.
        """
        digits = ''.join(filter(str.isdigit, phone))
        if digits and not digits.startswith('591'):
            digits = '591' + digits
        return digits
    
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
            recipient = whatsapp_msg.recipient_phone
            body = whatsapp_msg.message_content

            if self.provider == 'twilio':
                result = self._send_via_twilio(recipient, body, media_url=media_url)
            elif self.provider == 'whatsapp_business':
                result = self._send_via_cloud_api(recipient, body, media_url=media_url)
            elif self.provider == 'baileys':
                result = self._send_via_baileys(recipient, body, media_url=media_url)
            else:
                self._last_error = f"Proveedor {self.provider} no soportado"
                result = None

            if result:
                whatsapp_msg.mark_as_sent(external_id=result)
                logger.info(f"Mensaje enviado a {recipient}: {result}")
            else:
                whatsapp_msg.mark_as_failed(self._last_error or "Error al enviar el mensaje")

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
            self._last_error = ('Credenciales de Twilio no configuradas. Define '
                                'TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en el archivo .env '
                                'de la raíz del proyecto y reinicia el backend.')
            logger.error(self._last_error)
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
            self._last_error = f"Twilio: {str(e)}"
            logger.error(f"Error Twilio: {str(e)}")
            return None
    
    def _send_via_cloud_api(self, to: str, body: str, media_url: Optional[str] = None) -> Optional[str]:
        """
        Enviar mensaje vía Meta WhatsApp Cloud API (Graph API).

        Returns:
            str: ID del mensaje si fue exitoso, None si falló
        """
        import json
        import requests

        if not self.cloud_token or not self.cloud_phone_id:
            self._last_error = ('Cloud API no configurada. Define WHATSAPP_CLOUD_TOKEN y '
                                'WHATSAPP_PHONE_NUMBER_ID en el .env.')
            logger.error(self._last_error)
            return None

        url = f"https://graph.facebook.com/{self.cloud_api_version}/{self.cloud_phone_id}/messages"
        headers = {
            'Authorization': f'Bearer {self.cloud_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': self._digits(to),
        }
        if media_url:
            payload['type'] = 'image'
            payload['image'] = {'link': media_url}
        else:
            payload['type'] = 'text'
            payload['text'] = {'preview_url': False, 'body': body}

        try:
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=20)
            data = resp.json() if resp.content else {}
            if resp.status_code in (200, 201) and isinstance(data, dict) and data.get('messages'):
                return data['messages'][0].get('id')
            err = data.get('error', {}) if isinstance(data, dict) else {}
            self._last_error = f"Cloud API: {err.get('message') or resp.text[:300]}"
            logger.error(self._last_error)
            return None
        except Exception as e:
            self._last_error = f"Cloud API: {e}"
            logger.error(self._last_error)
            return None

    def _send_via_baileys(self, to: str, body: str, media_url: Optional[str] = None) -> Optional[str]:
        """
        Enviar mensaje vía Baileys usando un servidor WAHA (WhatsApp HTTP API).
        Docs: https://waha.devlike.pro
        Returns: ID del mensaje si fue exitoso, None si falló.
        """
        import json
        import requests

        if not self.waha_url:
            self._last_error = ('WAHA no configurado. Define WAHA_URL en el .env '
                                '(ej: http://localhost:3000) y ejecuta el servidor WAHA.')
            logger.error(self._last_error)
            return None

        chat_id = f"{self._digits(to)}@c.us"
        headers = {'Content-Type': 'application/json'}
        if self.waha_api_key:
            headers['X-Api-Key'] = self.waha_api_key

        if media_url:
            endpoint = f"{self.waha_url}/api/sendImage"
            payload = {
                'session': self.waha_session,
                'chatId': chat_id,
                'file': {'url': media_url},
                'caption': body,
            }
        else:
            endpoint = f"{self.waha_url}/api/sendText"
            payload = {
                'session': self.waha_session,
                'chatId': chat_id,
                'text': body,
            }

        try:
            resp = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=30)
            if resp.status_code in (200, 201):
                data = resp.json() if resp.content else {}
                return (data.get('id') or (data.get('_data') or {}).get('id')
                        or data.get('messageId') or 'waha-ok')
            self._last_error = f"WAHA ({resp.status_code}): {resp.text[:300]}"
            logger.error(self._last_error)
            return None
        except Exception as e:
            self._last_error = f"WAHA: {e}"
            logger.error(self._last_error)
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
