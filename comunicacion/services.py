import logging
from django.conf import settings
from twilio.rest import Client
from .models import Notificacion
from .whatsapp_templates import WhatsAppTemplates

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)
        self.client = None
        
        if self.account_sid and self.auth_token and self.from_number:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                logger.error(f"Error initializing Twilio client: {e}")

    def send_message(self, to_number, body):
        """
        Send a WhatsApp message to a specific number.
        to_number: Number in format '7XXXXXXX' or '5917XXXXXXX'.
        """
        # Create log entry
        notificacion = Notificacion.objects.create(
            canal='whatsapp',
            destinatario=str(to_number),
            mensaje=body,
            estado='procesando'
        )

        if not self.client:
            # SIMULATION MODE
            logger.info(f"[SIMULACION] WhatsApp para {to_number}: {body}")
            notificacion.estado = 'enviado_simulado'
            notificacion.response_body = "Modo simulación: Credenciales no configuradas"
            notificacion.status_code = 200
            notificacion.save()
            return True, "Simulado"

        try:
            # Format number for Twilio (whatsapp:+591XXXXXXXX)
            clean_number = str(to_number).replace('+', '').replace('whatsapp:', '').strip()
            
            # If number doesn't start with 591, add it (assuming Bolivia)
            if len(clean_number) == 8: 
                clean_number = f"591{clean_number}"
                
            to_whatsapp = f"whatsapp:+{clean_number}"
            
            message = self.client.messages.create(
                body=body,
                from_=self.from_number,
                to=to_whatsapp
            )
            
            notificacion.estado = 'enviado'
            notificacion.status_code = 200 
            notificacion.response_body = f"SID: {message.sid}, Status: {message.status}"
            notificacion.save()
            
            return True, message.sid
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp to {to_number}: {e}")
            notificacion.estado = 'error'
            notificacion.response_body = str(e)
            notificacion.save()
            return False, str(e)

    def send_reserva_confirmation(self, reserva):
        if not reserva.telefono:
            return False, "Sin teléfono"
            
        msg = WhatsAppTemplates.reserva_confirmada(
            nombre=reserva.cliente,
            ruta=str(reserva.ruta),
            fecha=str(reserva.fecha_viaje),
            asiento=reserva.asiento,
            codigo_reserva=reserva.id
        )
        return self.send_message(reserva.telefono, msg)

    def send_pago_receipt(self, pago):
        # Asumiendo que Pago tiene relación con Afiliado y este tiene teléfono
        if not pago.afiliado or not pago.afiliado.telefono:
            return False, "Sin teléfono de afiliado"
            
        # Determinar el concepto del pago
        concepto = "Pago general"
        if hasattr(pago, 'tipo_pago') and pago.tipo_pago:
            concepto = pago.tipo_pago.nombre
        elif hasattr(pago, 'tipo') and pago.tipo:
            concepto = pago.tipo
            
        msg = WhatsAppTemplates.pago_recibido(
            nombre=f"{pago.afiliado.nombres} {pago.afiliado.apellidos}",
            concepto=concepto,
            monto=pago.monto,
            fecha=str(pago.fecha_pago),
            nro_recibo=pago.id
        )
        return self.send_message(pago.afiliado.telefono, msg)

    def send_notificacion_nueva_reserva_afiliado(self, reserva):
        """Notificar al conductor o a la secretaria sobre una nueva reserva"""
        # Buscamos a quién notificar (prioridad: conductor asignado, si no, un número por defecto de la secretaria)
        telefono_destino = None
        if reserva.afiliado and reserva.afiliado.telefono:
            telefono_destino = reserva.afiliado.telefono
            
        if not telefono_destino:
            # Puedes configurar el número de la secretaria en settings o .env
            telefono_destino = getattr(settings, 'TELEFONO_SECRETARIA', '70000000') # Placeholder

        msg = (
            f"🔔 *NUEVA RESERVA (Pizarra Pública)*\n\n"
            f"👤 Cliente: {reserva.cliente}\n"
            f"📱 Celular: {reserva.telefono}\n"
            f"🛣️ Ruta: {reserva.ruta}\n"
            f"📅 Fecha: {reserva.fecha_viaje}\n"
            f"💺 Asiento: {reserva.asiento}\n"
            f"🎟️ Código: {reserva.id}\n\n"
            f"_Notificación automática del Sistema_"
        )
        return self.send_message(telefono_destino, msg)

