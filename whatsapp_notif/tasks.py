from celery import shared_task
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from .models import WhatsAppMessage

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_whatsapp_task(self, message_id, media_url=None):
    """
    Tarea de Celery para enviar un mensaje de WhatsApp
    """
    try:
        from .services import whatsapp_service
        msg = WhatsAppMessage.objects.get(pk=message_id)
        return whatsapp_service._do_send(msg, media_url=media_url).status
    except WhatsAppMessage.DoesNotExist:
        logger.error(f"Mensaje {message_id} no encontrado")
        return "not_found"
    except Exception as exc:
        logger.error(f"Error en send_whatsapp_task para mensaje {message_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def enviar_confirmacion_pago_task(self, pago_id):
    """
    Tarea para enviar confirmación de pago por WhatsApp
    """
    try:
        from tesoreria.models import Pago
        from .services import whatsapp_service
        
        # Obtener el pago
        pago = Pago.objects.select_related('afiliado', 'tipo_pago').get(pk=pago_id)
        
        # Verificar afiliado y teléfono
        if not pago.afiliado or not hasattr(pago.afiliado, 'telefono') or not pago.afiliado.telefono:
            logger.warning(f"Pago {pago_id}: Afiliado sin teléfono")
            return "no_phone"
        
        nombre = pago.afiliado.nombre_completo if hasattr(pago.afiliado, 'nombre_completo') else str(pago.afiliado)
        
        # Enviar confirmación
        whatsapp_service.send_from_template(
            template_name='payment_confirmation',
            phone=pago.afiliado.telefono,
            context={
                'nombre': nombre,
                'monto': f"{pago.monto_pagado:.2f}",
                'tipo': pago.tipo_pago.nombre if pago.tipo_pago else 'Pago',
                'fecha': pago.fecha.strftime('%d/%m/%Y'),
            },
            recipient_name=nombre,
            related_payment_id=pago.id,
            use_celery=False  # Ya estamos en Celery, enviar directo
        )
        
        logger.info(f"Confirmación de pago enviada a {nombre} por {pago.monto_pagado} Bs")
        return "sent"
        
    except Exception as exc:
        logger.error(f"Error al enviar confirmación de pago {pago_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)




@shared_task(bind=True, max_retries=3)
def enviar_notificacion_sancion_task(self, sancion_id):
    """
    Tarea para enviar notificación de sanción por WhatsApp
    """
    try:
        from sanciones.models import Sancion
        from .services import whatsapp_service
        
        # Obtener la sanción
        sancion = Sancion.objects.select_related('afiliado').get(pk=sancion_id)
        
        # Verificar afiliado y teléfono
        if not sancion.afiliado or not hasattr(sancion.afiliado, 'telefono') or not sancion.afiliado.telefono:
            logger.warning(f"Sanción {sancion_id}: Afiliado sin teléfono")
            return "no_phone"
        
        nombre = sancion.afiliado.nombre_completo if hasattr(sancion.afiliado, 'nombre_completo') else str(sancion.afiliado)
        
        # Enviar notificación
        whatsapp_service.send_from_template(
            template_name='sanction_notice',
            phone=sancion.afiliado.telefono,
            context={
                'nombre': nombre,
                'tipo': sancion.motivo if hasattr(sancion, 'motivo') else 'Sanción',
                'monto': f"{sancion.monto:.2f}",
                'fecha': sancion.fecha.strftime('%d/%m/%Y') if hasattr(sancion, 'fecha') else '',
            },
            recipient_name=nombre,
            related_sanction_id=sancion.id,
            use_celery=False  # Ya estamos en Celery
        )
        
        logger.info(f"Notificación de sanción enviada a {nombre} por {sancion.monto} Bs")
        return "sent"
        
    except Exception as exc:
        logger.error(f"Error al enviar notificación de sanción {sancion_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_shift_reminders():
    """
    Enviar recordatorios de turno para el día siguiente
    Se ejecuta diariamente a las 18:00
    """
    try:
        from hojasruta.models import HojaRuta
        from whatsapp_notif.services import whatsapp_service
        
        # Calcular fecha de mañana
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        # Obtener hojas de ruta para mañana
        hojas_manana = HojaRuta.objects.filter(
            fecha_salida=tomorrow,
            estado__in=['emitida', 'notificada']
        ).select_related('afiliado', 'ruta', 'vehiculo')
        
        count_sent = 0
        count_errors = 0
        
        for hoja in hojas_manana:
            try:
                if not hoja.afiliado:
                    continue
                
                # Verificar que el afiliado tenga teléfono
                if not hasattr(hoja.afiliado, 'telefono') or not hoja.afiliado.telefono:
                    logger.warning(f"Afiliado {hoja.afiliado} no tiene teléfono")
                    continue
                
                # Obtener información
                nombre_afiliado = hoja.afiliado.nombre_completo if hasattr(hoja.afiliado, 'nombre_completo') else str(hoja.afiliado)
                ruta_nombre = hoja.ruta.nombre if hoja.ruta else 'Sin ruta asignada'
                vehiculo_info = f"{hoja.vehiculo.placa}" if hoja.vehiculo else 'Sin vehículo'
                
                # Enviar recordatorio
                whatsapp_service.send_from_template(
                    template_name='shift_reminder',
                    phone=hoja.afiliado.telefono,
                    context={
                        'nombre': nombre_afiliado,
                        'fecha': tomorrow.strftime('%d/%m/%Y'),
                        'ruta': ruta_nombre,
                        'hora': '06:00 AM',  # Puedes hacer esto configurable
                    },
                    recipient_name=nombre_afiliado
                )
                
                # Marcar como notificada
                hoja.estado = 'notificada'
                hoja.save(update_fields=['estado'])
                
                count_sent += 1
                logger.info(f"Recordatorio enviado a {nombre_afiliado} para hoja {hoja.nro}")
                
            except Exception as e:
                count_errors += 1
                logger.error(f"Error al enviar recordatorio para hoja {hoja.nro}: {str(e)}")
        
        logger.info(f"Recordatorios enviados: {count_sent}, Errores: {count_errors}")
        return {
            'success': True,
            'sent': count_sent,
            'errors': count_errors,
            'date': tomorrow.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en send_shift_reminders: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }



@shared_task
def send_meeting_reminders():
    """
    Enviar recordatorios de reunión programada
    Se ejecuta diariamente a las 08:00
    """
    try:
        from reuniones.models import Reunion
        from asistencias.models import Asistencia
        from whatsapp_notif.services import whatsapp_service
        
        # Calcular fecha de mañana
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        
        # Obtener reuniones programadas para mañana
        reuniones_manana = Reunion.objects.filter(
            fecha=tomorrow
        )
        
        count_sent = 0
        count_errors = 0
        
        for reunion in reuniones_manana:
            try:
                # Obtener todos los afiliados activos
                from afiliados.models import Afiliado
                afiliados = Afiliado.objects.filter(estado='activo')
                
                for afiliado in afiliados:
                    try:
                        if not hasattr(afiliado, 'telefono') or not afiliado.telefono:
                            continue
                        
                        nombre_afiliado = afiliado.nombre_completo if hasattr(afiliado, 'nombre_completo') else str(afiliado)
                        
                        # Enviar recordatorio
                        whatsapp_service.send_from_template(
                            template_name='meeting_reminder',
                            phone=afiliado.telefono,
                            context={
                                'nombre': nombre_afiliado,
                                'tipo': reunion.tipo if hasattr(reunion, 'tipo') else 'Ordinaria',
                                'fecha': tomorrow.strftime('%d/%m/%Y'),
                                'hora': '09:00 AM',  # Puedes agregar campo hora al modelo
                                'lugar': 'Oficina del Sindicato',  # Configurable
                                'monto_sancion': '50',  # Desde configuración
                                'agenda': reunion.agenda if hasattr(reunion, 'agenda') else 'Por definir',
                            },
                            recipient_name=nombre_afiliado
                        )
                        
                        count_sent += 1
                        
                    except Exception as e:
                        count_errors += 1
                        logger.error(f"Error al enviar recordatorio a {afiliado}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error procesando reunión {reunion}: {str(e)}")
        
        logger.info(f"Recordatorios de reunión enviados: {count_sent}, Errores: {count_errors}")
        return {
            'success': True,
            'sent': count_sent,
            'errors': count_errors,
            'date': tomorrow.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en send_meeting_reminders: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def send_debt_reminders():
    """
    Enviar recordatorios de deuda pendiente
    Se ejecuta semanalmente los lunes a las 09:00
    """
    try:
        from afiliados.models import Afiliado
        from tesoreria.models import Pago
        from sanciones.models import Sancion
        from whatsapp_notif.services import whatsapp_service
        from django.db.models import Sum
        
        count_sent = 0
        count_errors = 0
        
        # Obtener afiliados con deudas
        afiliados = Afiliado.objects.filter(estado='activo')
        
        for afiliado in afiliados:
            try:
                if not hasattr(afiliado, 'telefono') or not afiliado.telefono:
                    continue
                
                # Calcular deuda total
                deuda_sanciones = Sancion.objects.filter(
                    afiliado=afiliado,
                    estado='pendiente'
                ).aggregate(total=Sum('monto'))['total'] or 0
                
                # Aquí puedes agregar otras deudas (cuotas, etc.)
                deuda_total = float(deuda_sanciones)
                
                # Solo enviar si tiene deuda
                if deuda_total > 0:
                    nombre_afiliado = afiliado.nombre_completo if hasattr(afiliado, 'nombre_completo') else str(afiliado)
                    
                    # Calcular días de mora (puedes mejorar esto)
                    dias_mora = 0  # Implementar lógica
                    
                    whatsapp_service.send_from_template(
                        template_name='debt_reminder',
                        phone=afiliado.telefono,
                        context={
                            'nombre': nombre_afiliado,
                            'monto': f"{deuda_total:.2f}",
                            'concepto': 'Sanciones pendientes',
                            'dias_mora': str(dias_mora),
                        },
                        recipient_name=nombre_afiliado
                    )
                    
                    count_sent += 1
                    logger.info(f"Recordatorio de deuda enviado a {nombre_afiliado}")
                    
            except Exception as e:
                count_errors += 1
                logger.error(f"Error al enviar recordatorio de deuda a {afiliado}: {str(e)}")
        
        logger.info(f"Recordatorios de deuda enviados: {count_sent}, Errores: {count_errors}")
        return {
            'success': True,
            'sent': count_sent,
            'errors': count_errors
        }
        
    except Exception as e:
        logger.error(f"Error en send_debt_reminders: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def send_monthly_debt_report():
    """
    Enviar reporte detallado de deudas el primer día de cada mes
    Se ejecuta el primer día de cada mes a las 08:00
    """
    try:
        from afiliados.models import Afiliado
        from sanciones.models import Sancion
        from cuotas.models import Cuota
        from whatsapp_notif.services import whatsapp_service
        from django.db.models import Sum
        
        count_sent = 0
        
        # Obtener afiliados activos
        afiliados = Afiliado.objects.filter(estado='activo')
        
        for afiliado in afiliados:
            # Calcular deudas
            sanciones_pendientes = Sancion.objects.filter(afiliado=afiliado, estado='pendiente').aggregate(Total=Sum('monto'))['Total'] or 0
            
            # Asumiendo que Cuota tiene un campo de estado y monto
            # cuotas_pendientes = Cuota.objects.filter(afiliado=afiliado, pagado=False).aggregate(Total=Sum('monto'))['Total'] or 0
            cuotas_pendientes = 0 # Placeholder si no hay modelo exacto
            
            total_deuda = float(sanciones_pendientes) + float(cuotas_pendientes)
            
            if total_deuda > 0:
                nombre = afiliado.nombre_completo if hasattr(afiliado, 'nombre_completo') else str(afiliado)
                
                whatsapp_service.send_from_template(
                    template_name='monthly_debt_report',
                    phone=afiliado.telefono,
                    context={
                        'nombre': nombre,
                        'total': f"{total_deuda:.2f}",
                        'mes': timezone.now().strftime('%B'),
                        'detalle': f"Sanciones: {sanciones_pendientes:.2f}"
                    },
                    recipient_name=nombre
                )
                count_sent += 1
                
        return {'success': True, 'sent': count_sent}
    except Exception as e:
        logger.error(f"Error en reporte mensual: {str(e)}")
        return {'success': False, 'error': str(e)}
