import qrcode
import base64
import uuid
import json
from io import BytesIO
from datetime import datetime
from django.conf import settings
from .models import QRTransaccion

class QRService:
    @staticmethod
    def generate_qr(monto, glosa, valid_hours=24, content_object=None):
        """
        Genera una transacción QR y retorna el objeto creado.
        Simula el formato 'Simple QR' (o similar).
        """
        transaction_id = str(uuid.uuid4())
        expiration_date = datetime.now() # En un caso real sumar valid_hours
        
        # 1. Generar payload del QR (Simulado formato bancario)
        # Payload real de Simple QR es complejo, aquí usaremos uno simplificado funcional para el scanner del app.
        payload_data = {
            "id": transaction_id,
            "monto": float(monto),
            "moneda": "BOB",
            "glosa": glosa,
            "banco": "BNB", # Ejemplo
            "cuenta": "123456789",
            "vence": expiration_date.strftime("%Y-%m-%d")
        }
        qr_string = json.dumps(payload_data)
        
        # 2. Generar Imagen QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        img_buffer = BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(img_buffer, format="PNG")
        img_str = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # 3. Guardar en BD
        qr_obj = QRTransaccion(
            monto=monto,
            glosa=glosa,
            expiration_date=expiration_date, # Ojo: ajustar tiempo real
            qr_string=qr_string,
            imagen_base64=img_str,
            transaction_id=transaction_id,
            estado='pendiente'
        )
        
        if content_object:
            qr_obj.content_object = content_object
            
        qr_obj.save()
        
        return qr_obj

    @staticmethod
    def verify_payment(transaction_id):
        """
        Método para simular verificación o llamar a API del banco.
        """
        from whatsapp_notif.services import whatsapp_service
        from tesoreria.models import Pago
        import logging

        logger = logging.getLogger(__name__)

        try:
            qr = QRTransaccion.objects.get(transaction_id=transaction_id)
            if qr.estado == 'pendiente':
                # Aquí iría la lógica real de consulta al banco
                # Por ahora simulamos éxito
                qr.estado = 'pagado'
                qr.save()

                # Si el objeto vinculado es un Pago, actualizar su estado para disparar la señal
                if isinstance(qr.content_object, Pago):
                    pago = qr.content_object
                    pago.estado = 'completado'
                    pago.save(update_fields=['estado', 'updated_at'])
                    logger.info(f"Pago {pago.id} marcado como COMPLETADO tras verificación QR")

                # Si el objeto vinculado es una Reserva, enviamos confirmación de reserva
                elif qr.content_object.__class__.__name__ == 'Reserva':
                    reserva = qr.content_object
                    # Actualizar estado de la reserva
                    reserva.estado = 'confirmada'
                    reserva.save()
                    
                    if hasattr(reserva, 'telefono') and reserva.telefono:
                        try:
                            mensaje = f"✅ *PAGO DE RESERVA VERIFICADO*\n\n"
                            mensaje += f"Estimado(a) *{reserva.cliente}*,\n"
                            mensaje += f"Su pago de reserva ha sido verificado.\n\n"
                            mensaje += f"📍 *Ruta:* {reserva.ruta.nombre if reserva.ruta else 'N/A'}\n"
                            mensaje += f"📅 *Fecha de Viaje:* {reserva.fecha_viaje.strftime('%d/%m/%Y')}\n"
                            mensaje += f"🎟️ *Asientos:* {reserva.cantidad}\n"
                            mensaje += f"💰 *Monto:* {qr.monto} Bs.\n\n"
                            mensaje += f"¡Buen viaje! 🚌\n"
                            mensaje += f"_Sindicato S.M.I.T. Taipiplaya_"

                            whatsapp_service.send_message(
                                phone=reserva.telefono,
                                message=mensaje,
                                message_type='reserva_confirmation',
                                recipient_name=reserva.cliente,
                                related_reservation_id=reserva.id
                            )
                        except Exception as we:
                            logger.error(f"Error enviando WhatsApp tras pago QR de Reserva: {str(we)}")

                return True, "Pagado exitosamente"
            return False, f"Estado actual: {qr.estado}"
        except QRTransaccion.DoesNotExist:
            return False, "Transacción no encontrada"
