# Notificaciones Automáticas - Signals para Hojas de Ruta
# Archivo: hojasruta/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HojaRuta
from whatsapp_notif.services import whatsapp_service
import os


@receiver(post_save, sender=HojaRuta)
def notificar_asignacion_hoja(sender, instance, created, **kwargs):
    """
    Notifica al afiliado cuando se le asigna una nueva hoja de ruta
    """
    if created and instance.afiliado:
        try:
            telefono = instance.afiliado.telefono
            if not telefono:
                return
            
            mensaje = f"""
🚌 *Nueva Hoja de Ruta Asignada*

Estimado(a) {instance.afiliado.nombre_completo},

Se le ha asignado una nueva hoja de ruta:

📋 *Hoja #:* {instance.id}
🗺️ *Ruta:* {instance.ruta.origen} - {instance.ruta.destino}
📅 *Fecha:* {instance.fecha_emision.strftime('%d/%m/%Y')}
🕐 *Hora Salida:* {instance.hora_salida.strftime('%H:%M')}
🚗 *Vehículo:* {instance.vehiculo.placa if instance.vehiculo else 'Por asignar'}

Por favor, confirme su disponibilidad.

_Sindicato Mixto Integración Taipiplaya_
            """.strip()
            
            whatsapp_service.send_message(
                phone=telefono,
                message=mensaje,
                message_type='general'
            )
                
        except Exception as e:
            print(f"Error enviando notificación de hoja de ruta: {e}")

