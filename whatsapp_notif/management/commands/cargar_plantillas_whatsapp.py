"""
Management command para cargar las plantillas de WhatsApp predeterminadas
Ejecutar: python manage.py cargar_plantillas_whatsapp
"""
from django.core.management.base import BaseCommand
from whatsapp_notif.models import WhatsAppTemplate, WhatsAppConfig

PLANTILLAS_DEFAULT = [
    {
        'name': 'payment_confirmation',
        'message_type': 'payment_confirmation',
        'template_content': (
            "✅ *PAGO REGISTRADO*\n\n"
            "Hola {nombre},\n\n"
            "Tu pago ha sido registrado exitosamente:\n"
            "• Concepto: *{tipo}*\n"
            "• Monto: *Bs. {monto}*\n\n"
            "Gracias por mantener tus pagos al día.\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
    {
        'name': 'cuota_payment',
        'message_type': 'cuota_payment',
        'template_content': (
            "✅ *CUOTA MENSUAL PAGADA*\n\n"
            "Hola {nombre},\n\n"
            "Tu cuota mensual ha sido registrada:\n"
            "• Período: *{periodo}*\n"
            "• Monto: *Bs. {monto}*\n\n"
            "¡Perfecto, estás al día! 👍\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
    {
        'name': 'sanction_notice',
        'message_type': 'sanction_notice',
        'template_content': (
            "⚠️ *NOTIFICACIÓN DE SANCIÓN*\n\n"
            "Estimado/a {nombre},\n\n"
            "Se ha registrado una sanción en su cuenta:\n"
            "• Tipo: *{tipo}*\n"
            "• Monto: *Bs. {monto}*\n\n"
            "Por favor acérquese a la secretaría para regularizar su situación.\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
    {
        'name': 'shift_reminder',
        'message_type': 'shift_reminder',
        'template_content': (
            "🕐 *RECORDATORIO DE TURNO*\n\n"
            "Hola {nombre},\n\n"
            "Le recordamos que tiene turno mañana:\n"
            "• Fecha: *{fecha}*\n"
            "• Ruta/Parada: *{ruta}*\n\n"
            "Recuerde presentarse a tiempo. 🚌\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
    {
        'name': 'meeting_reminder',
        'message_type': 'meeting_reminder',
        'template_content': (
            "📅 *RECORDATORIO DE REUNIÓN*\n\n"
            "Hola {nombre},\n\n"
            "Le convocamos a la reunión:\n"
            "• Fecha: *{fecha}*\n"
            "• Hora: *{hora}*\n"
            "• Lugar: *{lugar}*\n"
            "• Agenda: *{agenda}*\n\n"
            "Su asistencia es obligatoria. ✅\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
    {
        'name': 'debt_reminder',
        'message_type': 'debt_reminder',
        'template_content': (
            "💸 *AVISO DE DEUDA PENDIENTE*\n\n"
            "Estimado/a {nombre},\n\n"
            "Tiene una deuda pendiente:\n"
            "• Cuotas: *Bs. {deuda_cuotas}*\n"
            "• Multas: *Bs. {deuda_sanciones}*\n"
            "• *TOTAL: Bs. {total}*\n\n"
            "Por favor regularice su situación a la brevedad posible.\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
    {
        'name': 'reservation_received',
        'message_type': 'reservation_confirmation',
        'template_content': (
            "📋 *RESERVA RECIBIDA*\n\n"
            "Hola {nombre},\n\n"
            "Tu reserva fue registrada:\n"
            "• Código: *{codigo}*\n"
            "• Ruta: *{ruta}*\n"
            "• Fecha: *{fecha}*\n"
            "• Asiento: *{asiento}*\n\n"
            "Pasa por la oficina para confirmar y pagar tu pasaje.\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
    {
        'name': 'reservation_confirmation',
        'message_type': 'reservation_confirmation',
        'template_content': (
            "✅ *¡RESERVA CONFIRMADA!*\n\n"
            "Hola {nombre},\n\n"
            "Tu pasaje está confirmado:\n"
            "• Código: *{codigo}*\n"
            "• Ruta: *{ruta}*\n"
            "• Fecha: *{fecha}*\n"
            "• Hora: *{hora}*\n"
            "• Asiento: *{asiento}*\n\n"
            "¡Buen viaje! 🛣️\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
    {
        'name': 'hoja_ruta_emitted',
        'message_type': 'hoja_ruta_emitted',
        'template_content': (
            "📄 *HOJA DE RUTA EMITIDA*\n\n"
            "Hola {nombre},\n\n"
            "Se ha emitido tu hoja de ruta:\n"
            "• N°: *{nro}*\n"
            "• Ruta: *{ruta}*\n"
            "• Placa: *{placa}*\n"
            "• Precio: *Bs. {precio}*\n\n"
            "¡Buen viaje! 🚌\n\n"
            "_Sindicato Integración Taipiplaya_"
        ),
    },
]


class Command(BaseCommand):
    help = 'Carga las plantillas de WhatsApp predeterminadas en la base de datos'

    def handle(self, *args, **options):
        creadas = 0
        actualizadas = 0

        for data in PLANTILLAS_DEFAULT:
            obj, created = WhatsAppTemplate.objects.update_or_create(
                name=data['name'],
                defaults={
                    'message_type': data['message_type'],
                    'template_content': data['template_content'],
                    'is_active': True,
                }
            )
            if created:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ Creada: {obj.name}'))
            else:
                actualizadas += 1
                self.stdout.write(self.style.WARNING(f'  🔄 Actualizada: {obj.name}'))

        # Asegurar que existe la configuración
        config, _ = WhatsAppConfig.objects.get_or_create(pk=1)
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Completado: {creadas} creadas, {actualizadas} actualizadas.'
        ))
        self.stdout.write(
            f'\n⚙️  Configuración actual: Proveedor={config.get_provider_display()}, '
            f'Habilitado={"Sí" if config.is_enabled else "No"}'
        )
        self.stdout.write(
            '\n👉 Para activar WhatsApp, configura TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en el .env\n'
            '   Luego actívalo desde el panel de administración o desde el módulo WhatsApp del sistema.'
        )
