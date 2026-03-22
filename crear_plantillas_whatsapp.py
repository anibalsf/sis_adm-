"""
Script para crear plantillas iniciales de WhatsApp
Ejecutar: python crear_plantillas_whatsapp.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from whatsapp_notif.models import WhatsAppTemplate, WhatsAppConfig

def crear_plantillas():
    """Crear plantillas predefinidas de WhatsApp"""
    
    plantillas = [
        {
            'name': 'payment_confirmation',
            'message_type': 'payment_confirmation',
            'template_content': '''🎉 *PAGO RECIBIDO*

Hola {nombre},

✅ Hemos recibido tu pago de:
💰 *{monto} Bs* - {tipo}

📅 Fecha: {fecha}
🧾 Recibo: #{recibo}

Gracias por tu puntualidad! 🙏

_Sindicato Mixto Integración Taipiplaya_''',
            'is_active': True
        },
        {
            'name': 'shift_reminder',
            'message_type': 'shift_reminder',
            'template_content': '''📢 *RECORDATORIO DE TURNO*

Hola {nombre},

🚌 Tienes turno asignado:
📅 Fecha: *{fecha}*
🛣️ Ruta: *{ruta}*
⏰ Hora: {hora}

Por favor, confirma tu asistencia.

_No olvides llevar tu documentación completa._

Sindicato Mixto Integración Taipiplaya''',
            'is_active': True
        },
        {
            'name': 'sanction_notice',
            'message_type': 'sanction_notice',
            'template_content': '''⚠️ *NOTIFICACIÓN DE SANCIÓN*

Hola {nombre},

Se te ha aplicado una sanción:
📋 Motivo: *{tipo}*
💰 Monto: *{monto} Bs*
📅 Fecha: {fecha}

Por favor, regulariza esta situación en secretaría.

Para consultas, contacta a la directiva.

_Sindicato Mixto Integración Taipiplaya_''',
            'is_active': True
        },
        {
            'name': 'reservation_confirmation',
            'message_type': 'reservation_confirmation',
            'template_content': '''✅ *RESERVA CONFIRMADA*

Hola {nombre},

Tu reserva ha sido confirmada:
🎫 Código: *{codigo}*
🚌 Ruta: {ruta}
📅 Fecha: {fecha}
⏰ Hora: {hora}
💺 Asiento: *{asiento}*

📱 Presenta este código QR al abordar.

¡Buen viaje! 🚍

_Sindicato Mixto Integración Taipiplaya_''',
            'is_active': True
        },
        {
            'name': 'reservation_received',
            'message_type': 'reservation_confirmation',
            'template_content': '''⏳ *RESERVA RECIBIDA*

Hola {nombre},

Hemos registrado tu solicitud de reserva:
🎫 Código: *{codigo}*
🚌 Ruta: {ruta}
📅 Fecha: {fecha}
💺 Asiento: *{asiento}*

⚠️ *Estado: PENDIENTE*
Para confirmar tu espacio, por favor realiza el pago por QR o en oficina.

¡Gracias por elegirnos! 🚍

_Sindicato Mixto Integración Taipiplaya_''',
            'is_active': True
        },
        {
            'name': 'meeting_reminder',
            'message_type': 'meeting_reminder',
            'template_content': '''📣 *RECORDATORIO DE REUNIÓN*

Hola {nombre},

📅 Reunión {tipo}:
⏰ Fecha y hora: *{fecha}* a las *{hora}*
📍 Lugar: {lugar}

⚠️ Tu asistencia es *obligatoria*.
La falta injustificada tiene sanción de {monto_sancion} Bs.

Agenda: {agenda}

_Directiva Sindicato Taipiplaya_''',
            'is_active': True
        },
        {
            'name': 'debt_reminder',
            'message_type': 'debt_reminder',
            'template_content': '''💳 *RECORDATORIO DE DEUDA*

Hola {nombre},

Tienes una deuda pendiente:
💰 Monto total: *{monto} Bs*
📋 Concepto: {concepto}
⏰ Días de mora: {dias_mora}

Por favor, acércate a tesorería para regularizar tu situación.

_Área de Tesorería_
_Sindicato Mixto Integración Taipiplaya_''',
            'is_active': True
        },
    ]
    
    print("🔧 Creando plantillas de WhatsApp...")
    for plantilla_data in plantillas:
        plantilla, created = WhatsAppTemplate.objects.update_or_create(
            name=plantilla_data['name'],
            defaults={
                'message_type': plantilla_data['message_type'],
                'template_content': plantilla_data['template_content'],
                'is_active': plantilla_data['is_active'],
            }
        )
        status = "✅ Creada" if created else "🔄 Actualizada"
        print(f"{status}: {plantilla.name}")
    
    print("\n📊 Total de plantillas:", WhatsAppTemplate.objects.count())


def configurar_whatsapp():
    """Crear configuración inicial de WhatsApp"""
    config = WhatsAppConfig.get_config()
    config.provider = 'twilio'
    config.is_enabled = False  # Deshabilitado por defecto hasta configurar
    config.max_retries = 3
    config.retry_delay_minutes = 5
    config.daily_message_limit = 1000
    config.save()
    
    print("\n⚙️ Configuración de WhatsApp creada")
    print(f"   Proveedor: {config.get_provider_display()}")
    print(f"   Estado: {'❌ Deshabilitado' if not config.is_enabled else '✅ Habilitado'}")
    print(f"   Límite diario: {config.daily_message_limit} mensajes")


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 INICIALIZANDO MÓDULO DE WHATSAPP")
    print("=" * 60)
    
    try:
        crear_plantillas()
        configurar_whatsapp()
        
        print("\n" + "=" * 60)
        print("✅ WHATSAPP INICIALIZADO CORRECTAMENTE")
        print("=" * 60)
        print("\n📝 PRÓXIMOS PASOS:")
        print("1. Configurar variables de entorno en .env:")
        print("   TWILIO_ACCOUNT_SID=tu_account_sid")
        print("   TWILIO_AUTH_TOKEN=tu_auth_token")
        print("   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886")
        print("\n2. Activar el servicio en Django Admin:")
        print("   /admin/whatsapp_notif/whatsappconfig/")
        print("\n3. Instalar dependencias:")
        print("   pip install -r requirements.txt")
        print("\n4. Correr migraciones:")
        print("   python manage.py makemigrations whatsapp_notif")
        print("   python manage.py migrate")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
