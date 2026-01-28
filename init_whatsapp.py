
import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

from whatsapp_notif.models import WhatsAppConfig, WhatsAppTemplate

def init_whatsapp():
    print("Iniciando configuración de WhatsApp...")
    
    # 1. Configuración global (deshabilitada por defecto para evitar envíos accidentales)
    config, created = WhatsAppConfig.objects.get_or_create(pk=1)
    if created or not config.is_enabled:
        config.is_enabled = True
        config.provider = 'twilio'
        config.save()
        print("- Configuración global habilitada")
    else:
        print("- Configuración global ya existe y está habilitada")

    # 2. Plantillas base
    templates = [
        {
            'name': 'shift_reminder',
            'message_type': 'shift_reminder',
            'template_content': 'Hola {nombre}, le recordamos que mañana {fecha} tiene un turno programado en la ruta {ruta} a las {hora}. Por favor, sea puntual.'
        },
        {
            'name': 'payment_confirmation',
            'message_type': 'payment_confirmation',
            'template_content': 'Hola {nombre}, su pago de {monto} Bs por concepto de {tipo} ha sido registrado exitosamente. Gracias.'
        },
        {
            'name': 'sanction_notice',
            'message_type': 'sanction_notice',
            'template_content': 'Hola {nombre}, se le ha aplicado una sanción por: {tipo}. El monto a pagar es de {monto} Bs. Por favor, regularice su situación en secretaría.'
        },
        {
            'name': 'cuota_payment',
            'message_type': 'cuota_payment',
            'template_content': 'Hola {nombre}, agradecemos el pago de su cuota {tipo} del periodo {periodo} por un monto de {monto} Bs. Su estado ha sido actualizado a AL DÍA.'
        },
        {
            'name': 'reservation_confirmation',
            'message_type': 'reservation_confirmation',
            'template_content': 'Hola {nombre}, su reserva {codigo} para la ruta {ruta} el día {fecha} a las {hora} ha sido CONFIRMADA. Asiento: {asiento}. ¡Buen viaje!'
        },
        {
            'name': 'meeting_reminder',
            'message_type': 'meeting_reminder',
            'template_content': 'Hola {nombre}, tenemos una reunión {tipo} mañana {fecha} a las {hora} en {lugar}. Su asistencia es obligatoria. Agenda: {agenda}.'
        },
        {
            'name': 'debt_reminder',
            'message_type': 'debt_reminder',
            'template_content': 'Hola {nombre}, le recordamos que tiene una deuda pendiente de {monto} Bs por concepto de {concepto}. Por favor, evite sanciones adicionales.'
        }
    ]

    for t_data in templates:
        t, created = WhatsAppTemplate.objects.get_or_create(
            name=t_data['name'],
            defaults={
                'message_type': t_data['message_type'],
                'template_content': t_data['template_content'],
                'is_active': True
            }
        )
        if created:
            print(f"- Plantilla '{t_data['name']}' creada")
        else:
            # Actualizar contenido si ya existe para asegurar que coincida con lo esperado
            t.template_content = t_data['template_content']
            t.message_type = t_data['message_type']
            t.save()
            print(f"- Plantilla '{t_data['name']}' actualizada")

    print("\n¡Configuración completada exitosamente!")
    print("RECUERDA: Debes habilitar WhatsApp en el panel de administración y configurar las credenciales de Twilio en el archivo .env")

if __name__ == "__main__":
    init_whatsapp()
