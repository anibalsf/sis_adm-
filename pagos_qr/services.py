import base64
import json
import logging
import uuid
from datetime import timedelta
from io import BytesIO

import qrcode
from django.utils import timezone

from .models import QRTransaccion

logger = logging.getLogger(__name__)


class QRService:
    @staticmethod
    def generate_qr(monto, glosa, valid_hours=24, content_object=None, metadata=None):
        """
        Genera una transacción QR y retorna el objeto creado.
        Simula el formato 'Simple QR' (o similar).
        """
        transaction_id = str(uuid.uuid4())
        expiration_date = timezone.now() + timedelta(hours=valid_hours)

        # 1. Generar payload del QR (Simulado formato bancario)
        payload_data = {
            "id": transaction_id,
            "monto": float(monto),
            "moneda": "BOB",
            "glosa": glosa,
            "banco": "BNB",
            "cuenta": "123456789",
            "vence": expiration_date.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        qr_string = json.dumps(payload_data)

        # 2. Generar Imagen QR
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
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
            expiration_date=expiration_date,
            qr_string=qr_string,
            imagen_base64=img_str,
            transaction_id=transaction_id,
            estado='pendiente',
            response_data=metadata or {},
        )

        if content_object:
            qr_obj.content_object = content_object

        qr_obj.save()

        return qr_obj

    @staticmethod
    def verify_payment(transaction_id):
        """
        Simula la verificación del banco. Marca el QR como pagado y confirma
        todas las reservas asociadas al grupo.
        """
        from whatsapp_notif.services import whatsapp_service

        try:
            qr = QRTransaccion.objects.get(transaction_id=transaction_id)
        except QRTransaccion.DoesNotExist:
            return False, "Transacción no encontrada"

        if qr.estado != 'pendiente':
            return False, f"Estado actual: {qr.estado}"

        if qr.expiration_date and qr.expiration_date < timezone.now():
            qr.estado = 'expirado'
            qr.save(update_fields=['estado', 'updated_at'])
            return False, "El código QR expiró. Genere uno nuevo."

        qr.estado = 'pagado'
        qr.save(update_fields=['estado', 'updated_at'])

        content = qr.content_object

        # Si el objeto vinculado es un Pago, actualizar su estado para disparar la señal
        try:
            from tesoreria.models import Pago
        except ImportError:
            Pago = None

        if Pago is not None and isinstance(content, Pago):
            content.estado = 'completado'
            content.save(update_fields=['estado', 'updated_at'])
            logger.info("Pago %s marcado como COMPLETADO tras verificación QR", content.id)

        # Si el objeto vinculado es una Reserva (o grupo), confirmar todas.
        elif content is not None and content.__class__.__name__ == 'Reserva':
            from reservas.models import Reserva

            ids = qr.response_data.get('reserva_ids') or [content.id]
            reservas = list(
                Reserva.objects.select_related('ruta', 'hoja_ruta')
                .filter(id__in=ids)
                .exclude(estado='cancelada')
                .order_by('id')
            )
            confirmadas = reservas
            if confirmadas:
                Reserva.objects.filter(id__in=[r.id for r in confirmadas]).update(
                    estado='confirmada', updated_at=timezone.now()
                )

            if confirmadas:
                reserva = confirmadas[0]
                if getattr(reserva, 'telefono', ''):
                    try:
                        codigos = ', '.join(f"RES-{r.id:06d}" for r in confirmadas)
                        asientos = ', '.join(
                            str(r.asiento) for r in confirmadas if r.asiento
                        ) or 'Por asignar'
                        cantidad = sum(r.cantidad for r in confirmadas)
                        mensaje = (
                            "✅ *PAGO DE RESERVA VERIFICADO*\n\n"
                            f"Estimado(a) *{reserva.cliente}*,\n"
                            "Su pago de reserva ha sido verificado.\n\n"
                            f"🎫 *Reserva(s):* {codigos}\n"
                            f"📍 *Ruta:* {reserva.ruta.nombre if reserva.ruta else 'N/A'}\n"
                            f"📅 *Fecha de Viaje:* {reserva.fecha_viaje.strftime('%d/%m/%Y')}\n"
                            f"💺 *Asiento(s):* {asientos}\n"
                            f"🎟️ *Pasajes:* {cantidad}\n"
                            f"💰 *Monto:* {qr.monto} Bs.\n\n"
                            "¡Buen viaje! 🚌\n"
                            "_Sindicato S.M.I.T. Taipiplaya_"
                        )
                        whatsapp_service.send_message(
                            phone=reserva.telefono,
                            message=mensaje,
                            message_type='reserva_confirmation',
                            recipient_name=reserva.cliente,
                            related_reservation_id=reserva.id,
                        )
                    except Exception as exc:
                        logger.error("Error enviando WhatsApp tras pago QR de Reserva: %s", exc)

        return True, "Pagado exitosamente"
