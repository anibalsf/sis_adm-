"""
Fase 6: Automatización de Notificaciones WhatsApp
Sistema completo de notificaciones automáticas
"""

# ========================================
# OPCIÓN 1: Sin Celery (Más Simple)
# ========================================
# Requiere configurar cron jobs del sistema o usar APScheduler

# ========================================
# INSTALACIÓN PARA OPCIÓN SIMPLE
# ========================================
"""
pip install APScheduler requests
"""

# ========================================
# ARCHIVO: notificaciones/scheduler.py (CREAR)
# ========================================
"""
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def iniciar_scheduler():
    '''
    Inicializar scheduler de tareas automáticas.
    Llamar en apps.py del módulo principal.
    '''
    scheduler = BackgroundScheduler()
    
    # Recordatorios de pagos vencidos - Ejecutar todos los lunes a las 9:00 AM
    scheduler.add_job(
        enviar_recordatorios_pagos_vencidos,
        'cron',
        day_of_week='mon',
        hour=9,
        minute=0,
        id='recordatorios_pagos'
    )
    
    # Notificaciones de sanciones nuevas - Ejecutar diariamente a las 10:00 AM
    scheduler.add_job(
        enviar_notificaciones_sanciones_nuevas,
        'cron',
        hour=10,
        minute=0,
        id='notificaciones_sanciones'
    )
    
    # Confirmaciones de hojas de ruta - Ejecutar diariamente a las 18:00 (6 PM)
    scheduler.add_job(
        enviar_confirmaciones_hojas_manana,
        'cron',
        hour=18,
        minute=0,
        id='confirmaciones_hojas'
    )
    
    scheduler.start()
    logger.info("Scheduler de notificaciones iniciado")
    
    return scheduler
"""

# ========================================
# FUNCIÓN 1: Recordatorios de Pagos Vencidos
# ========================================
"""
def enviar_recordatorios_pagos_vencidos():
    '''
    Enviar recordatorios automáticos a afiliados con pagos vencidos.
    '''
    from tesoreria.models import Pago
    from afiliados.models import Afiliado
    from datetime import datetime, timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Ejecutando envío de recordatorios de pagos vencidos...")
    
    try:
        # Obtener cuotas pendientes de hace más de 7 días
        fecha_limite = datetime.now() - timedelta(days=7)
        
        # Obtener afiliados con cuotas pendientes
        from tesoreria.models import Cuota
        cuotas_vencidas = Cuota.objects.filter(
            estado='pendiente',
            created_at__lte=fecha_limite
        ).select_related('afiliado')
        
        # Agrupar por afiliado
        afiliados_notificar = {}
        for cuota in cuotas_vencidas:
            afiliado_id = cuota.afiliado.id
            if afiliado_id not in afiliados_notificar:
                afiliados_notificar[afiliado_id] = {
                    'afiliado': cuota.afiliado,
                    'cuotas': [],
                    'total_deuda': 0
                }
            
            afiliados_notificar[afiliado_id]['cuotas'].append(cuota)
            afiliados_notificar[afiliado_id]['total_deuda'] += float(cuota.monto)
        
        # Enviar notificaciones
        enviados = 0
        for data in afiliados_notificar.values():
            afiliado = data['afiliado']
            
            if not afiliado.telefono:
                continue
            
            mensaje = f'''🔔 *RECORDATORIO DE PAGO*

Estimado(a) {afiliado.nombre_completo},

Tiene {len(data['cuotas'])} cuota(s) pendiente(s) de pago:

'''
            for cuota in data['cuotas']:
                mensaje += f"• {cuota.periodo}: Bs. {cuota.monto}\\n"
            
            mensaje += f'''
*Total Adeudado:* Bs. {data['total_deuda']:.2f}

Por favor, regularice su situación a la brevedad posible.

📍 Puede realizar el pago en nuestras oficinas o coordinar con la administración.

_Sindicato Mixto Integración Taipiplaya_
'''
            
            if enviar_whatsapp(afiliado.telefono, mensaje):
                enviados += 1
        
        logger.info(f"Recordatorios enviados: {enviados}/{len(afiliados_notificar)}")
        return {
            'success': True,
            'enviados': enviados,
            'total': len(afiliados_notificar)
        }
        
    except Exception as e:
        logger.error(f"Error en recordatorios de pagos: {e}")
        return {'success': False, 'error': str(e)}
"""

# ========================================
# FUNCIÓN 2: Notificaciones de Sanciones Nuevas
# ========================================
"""
def enviar_notificaciones_sanciones_nuevas():
    '''
    Enviar notificaciones de sanciones creadas en las últimas 24 horas.
    '''
    from sanciones.models import Sancion
    from datetime import datetime, timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Ejecutando envío de notificaciones de sanciones nuevas...")
    
    try:
        # Sanciones creadas en las últimas 24 horas que no han sido notificadas
        hace_24h = datetime.now() - timedelta(hours=24)
        
        sanciones_nuevas = Sancion.objects.filter(
            created_at__gte=hace_24h,
            estado='pendiente'
        ).select_related('afiliado')
        
        enviados = 0
        for sancion in sanciones_nuevas:
            if not sancion.afiliado.telefono:
                continue
            
            mensaje = f'''🚫 *SANCIÓN REGISTRADA*

Estimado(a) {sancion.afiliado.nombre_completo},

Se ha registrado una nueva sanción a su nombre:

📋 *Tipo:* {sancion.tipo}
💰 *Monto:* Bs. {sancion.monto}
📝 *Motivo:* {sancion.motivo or 'No especificado'}
📅 *Fecha:* {sancion.created_at.strftime('%d/%m/%Y')}

⚠️ *Estado:* PENDIENTE DE PAGO

Por favor, regularice esta situación a la brevedad posible para evitar inconvenientes futuros.

📍 Para más información, comuníquese con la administración del sindicato.

_Sindicato Mixto Integración Taipiplaya_
'''
            
            if enviar_whatsapp(sancion.afiliado.telefono, mensaje):
                # Opcional: marcar como notificada
                # sancion.estado = 'notificada'
                # sancion.save()
                enviados += 1
        
        logger.info(f"Notificaciones de sanciones enviadas: {enviados}/{sanciones_nuevas.count()}")
        return {
            'success': True,
            'enviados': enviados,
            'total': sanciones_nuevas.count()
        }
        
    except Exception as e:
        logger.error(f"Error en notificaciones de sanciones: {e}")
        return {'success': False, 'error': str(e)}
"""

# ========================================
# FUNCIÓN 3: Confirmaciones de Hojas de Ruta
# ========================================
"""
def enviar_confirmaciones_hojas_manana():
    '''
    Enviar confirmaciones de hojas de ruta asignadas para el día siguiente.
    '''
    from hojasruta.models import HojaRuta
    from datetime import datetime, timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Ejecutando envío de confirmaciones de hojas de ruta...")
    
    try:
        # Hojas de ruta para mañana
        manana = (datetime.now() + timedelta(days=1)).date()
        
        hojas_manana = HojaRuta.objects.filter(
            fecha_salida__date=manana
        ).select_related('afiliado', 'ruta', 'vehiculo')
        
        enviados = 0
        for hoja in hojas_manana:
            if not hoja.afiliado or not hoja.afiliado.telefono:
                continue
            
            ruta_nombre = hoja.ruta.nombre if hoja.ruta else 'N/A'
            vehiculo_placa = hoja.vehiculo.placa if hoja.vehiculo else 'N/A'
            hora_salida = hoja.fecha_salida.strftime('%H:%M') if hoja.fecha_salida else 'N/A'
            
            mensaje = f'''✅ *HOJA DE RUTA CONFIRMADA*

Estimado(a) {hoja.afiliado.nombre_completo},

Tiene una hoja de ruta asignada para mañana:

📋 *Nº de Hoja:* {hoja.nro or hoja.id}
📅 *Fecha:* {manana.strftime('%d/%m/%Y')}
🕐 *Hora de Salida:* {hora_salida}
🗺️ *Ruta:* {ruta_nombre}
🚐 *Vehículo:* {vehiculo_placa}
💰 *Tarifa:* Bs. {hoja.precio}

💡 *Recordatorios:*
• Llegar con 30 minutos de anticipación
• Revisar la documentación del vehículo
• Verificar el estado mecánico

¡Buen viaje! 🚐

_Sindicato Mixto Integración Taipiplaya_
'''
            
            if enviar_whatsapp(hoja.afiliado.telefono, mensaje):
                enviados += 1
        
        logger.info(f"Confirmaciones de hojas enviadas: {enviados}/{hojas_manana.count()}")
        return {
            'success': True,
            'enviados': enviados,
            'total': hojas_manana.count()
        }
        
    except Exception as e:
        logger.error(f"Error en confirmaciones de hojas: {e}")
        return {'success': False, 'error': str(e)}
"""

# ========================================
# FUNCIÓN AUXILIAR: Enviar WhatsApp
# ========================================
"""
def enviar_whatsapp(telefono, mensaje):
    '''
    Función auxiliar para enviar mensajes por WhatsApp.
    Implementar con la API de su elección (Twilio, WhatsApp Business API, etc.)
    '''
    import requests
    import logging
    
    logger = logging.getLogger(__name__)
    
    # OPCIÓN 1: Twilio (requiere cuenta y configuración)
    # from twilio.rest import Client
    # account_sid = settings.TWILIO_ACCOUNT_SID
    # auth_token = settings.TWILIO_AUTH_TOKEN
    # client = Client(account_sid, auth_token)
    # 
    # try:
    #     message = client.messages.create(
    #         from_='whatsapp:+14155238886',  # Número de Twilio
    #         body=mensaje,
    #         to=f'whatsapp:{telefono}'
    #     )
    #     logger.info(f"WhatsApp enviado a {telefono}: {message.sid}")
    #     return True
    # except Exception as e:
    #     logger.error(f"Error enviando WhatsApp a {telefono}: {e}")
    #     return False
    
    # OPCIÓN 2: API propia o servicio local (modificar según su implementación)
    # try:
    #     response = requests.post(
    #         'http://localhost:3000/send-message',  # URL de su servicio
    #         json={
    #             'phone': telefono,
    #             'message': mensaje
    #         },
    #         timeout=10
    #     )
    #     return response.status_code == 200
    # except Exception as e:
    #     logger.error(f"Error enviando WhatsApp: {e}")
    #     return False
    
    # OPCIÓN 3: Solo log (para desarrollo/testing)
    logger.info(f"[SIMULADO] WhatsApp a {telefono}:")
    logger.info(mensaje)
    logger.info("-" * 50)
    return True  # Simular éxito
"""

# ========================================
# INTEGRACIÓN EN apps.py
# ========================================
"""
# En sistema_administracion/apps.py o el app principal:

from django.apps import AppConfig

class SistemaAdministracionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sistema_administracion'
    
    def ready(self):
        # Iniciar scheduler de notificaciones
        try:
            from notificaciones.scheduler import iniciar_scheduler
            iniciar_scheduler()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al iniciar scheduler: {e}")
"""

# ========================================
# CONFIGURACIÓN EN settings.py
# ========================================
"""
# WhatsApp / Twilio Configuration
TWILIO_ACCOUNT_SID = 'your_account_sid_here'
TWILIO_AUTH_TOKEN = 'your_auth_token_here'
TWILIO_WHATSAPP_NUMBER = '+14155238886'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/notificaciones.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'notificaciones': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
"""

# ========================================
# ENDPOINTS MANUALES (OPCIONAL)
# ========================================
"""
# En notificaciones/views.py:

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

class EnviarRecordatoriosPagosView(APIView):
    '''Endpoint manual para probar recordatorios'''
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        from notificaciones.scheduler import enviar_recordatorios_pagos_vencidos
        resultado = enviar_recordatorios_pagos_vencidos()
        return Response(resultado)

class EnviarNotificacionesSancionesView(APIView):
    '''Endpoint manual para probar notificaciones de sanciones'''
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        from notificaciones.scheduler import enviar_notificaciones_sanciones_nuevas
        resultado = enviar_notificaciones_sanciones_nuevas()
        return Response(resultado)

class EnviarConfirmacionesHojasView(APIView):
    '''Endpoint manual para probar confirmaciones de hojas'''
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        from notificaciones.scheduler import enviar_confirmaciones_hojas_manana
        resultado = enviar_confirmaciones_hojas_manana()
        return Response(resultado)

# En urls.py:
from notificaciones.views import (
    EnviarRecordatoriosPagosView,
    EnviarNotificacionesSancionesView,
    EnviarConfirmacionesHojasView
)

urlpatterns = [
    path('notificaciones/recordatorios-pagos/', EnviarRecordatoriosPagosView.as_view()),
    path('notificaciones/sanciones/', EnviarNotificacionesSancionesView.as_view()),
    path('notificaciones/confirmaciones-hojas/', EnviarConfirmacionesHojasView.as_view()),
]
"""

# ========================================
# OPCIÓN 2: Con Celery (Más Robusto para Producción)
# ========================================
"""
# Instalación:
pip install celery redis

# En celery.py:
from celery import Celery
from celery.schedules import crontab

app = Celery('sistema_administracion')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'recordatorios-pagos-lunes': {
        'task': 'notificaciones.tasks.enviar_recordatorios_pagos',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
    'notificaciones-sanciones-diario': {
        'task': 'notificaciones.tasks.enviar_notificaciones_sanciones',
        'schedule': crontab(hour=10, minute=0),
    },
    'confirmaciones-hojas-tarde': {
        'task': 'notificaciones.tasks.enviar_confirmaciones_hojas',
        'schedule': crontab(hour=18, minute=0),
    },
}

# En notificaciones/tasks.py:
from celery import shared_task

@shared_task
def enviar_recordatorios_pagos():
    from notificaciones.scheduler import enviar_recordatorios_pagos_vencidos
    return enviar_recordatorios_pagos_vencidos()

# Ejecutar workers:
# celery -A sistema_administracion worker -l info
# celery -A sistema_administracion beat -l info
"""

print("Código de Automatización WhatsApp listo para integrar")
print("Ver opciones: APScheduler (simple) o Celery (robusto)")
