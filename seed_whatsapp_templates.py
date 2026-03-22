
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from whatsapp_notif.models import WhatsAppTemplate

templates = [
    {
        'name': 'hoja_ruta_emitted',
        'message_type': 'hoja_ruta_emitted',
        'template_content': (
            "📄 *NUEVA HOJA DE RUTA*\n\n"
            "Hola {nombre}, se ha emitido tu hoja de ruta:\n\n"
            "📌 *Nro:* {nro}\n"
            "🛣️ *Ruta:* {ruta}\n"
            "🚗 *Vehículo:* {placa}\n"
            "💰 *Precio:* Bs. {precio}\n\n"
            "¡Buen viaje y conduzca con precaución! 🚗💨"
        )
    },
    {
        'name': 'payment_confirmation',
        'message_type': 'payment_confirmation',
        'template_content': (
            "✅ *CONFIRMACIÓN DE PAGO*\n\n"
            "Hola {nombre}, hemos recibido tu pago correctamente:\n\n"
            "💰 *Monto:* Bs. {monto}\n"
            "📝 *Concepto:* {tipo}\n\n"
            "¡Gracias por estar al día! 🤝"
        )
    },
    {
        'name': 'sanction_notice',
        'message_type': 'sanction_notice',
        'template_content': (
            "⚠️ *AVISO DE SANCIÓN/MULTA*\n\n"
            "Hola {nombre}, se ha registrado una nueva sanción en el sistema:\n\n"
            "🚫 *Motivo:* {tipo}\n"
            "💰 *Monto a pagar:* Bs. {monto}\n\n"
            "Por favor, pase por las oficinas para regularizar su situación."
        )
    },
    {
        'name': 'cuota_payment',
        'message_type': 'cuota_payment',
        'template_content': (
            "💳 *PAGO DE CUOTA RECIBIDO*\n\n"
            "Hola {nombre}, se registró el pago de tu cuota:\n\n"
            "🗓️ *Periodo:* {periodo}\n"
            "💰 *Monto:* Bs. {monto}\n"
            "📋 *Tipo:* {tipo}\n\n"
            "¡Gracias por tu aporte! ✨"
        )
    }
]

for t_data in templates:
    t, created = WhatsAppTemplate.objects.get_or_create(name=t_data['name'], defaults=t_data)
    if not created:
        t.template_content = t_data['template_content']
        t.message_type = t_data['message_type']
        t.save()
    print(f"{'Creada' if created else 'Actualizada'} plantilla: {t.name}")

# Habilitar WhatsApp si no está configurado
from whatsapp_notif.models import WhatsAppConfig
config = WhatsAppConfig.get_config()
if not config.is_enabled:
    config.is_enabled = True
    config.save()
    print("WhatsApp habilitado globalmente.")
