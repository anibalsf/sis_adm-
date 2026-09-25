import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .report_service import ReportService
from whatsapp_notif.services import whatsapp_service

logger = logging.getLogger(__name__)

def send_daily_report():
    try:
        report = ReportService.get_daily_summary()
        admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
        if admin_phone:
            whatsapp_service.send_message(
                phone=admin_phone,
                message=report,
                message_type='general'
            )
            logger.info("Reporte diario enviado exitosamente.")
    except Exception as e:
        logger.error(f"Error al enviar reporte diario: {str(e)}")

def send_weekly_report():
    try:
        report = ReportService.get_weekly_summary()
        admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
        if admin_phone:
            whatsapp_service.send_message(
                phone=admin_phone,
                message=report,
                message_type='general'
            )
            logger.info("Reporte semanal enviado exitosamente.")
    except Exception as e:
        logger.error(f"Error al enviar reporte semanal: {str(e)}")

def send_monthly_report():
    try:
        report = ReportService.get_monthly_summary()
        admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
        if admin_phone:
            whatsapp_service.send_message(
                phone=admin_phone,
                message=report,
                message_type='general'
            )
            logger.info("Reporte mensual enviado exitosamente.")
    except Exception as e:
        logger.error(f"Error al enviar reporte mensual: {str(e)}")


# ============ NUEVAS NOTIFICACIONES AUTOMÁTICAS ============

def notify_overdue_payments():
    """
    Notifica a afiliados con pagos vencidos (más de 7 días)
    """
    try:
        from afiliados.models import Afiliado
        from cuotas.models import Cuota
        
        fecha_limite = timezone.now().date() - timedelta(days=7)
        
        # Obtener cuotas vencidas
        cuotas_vencidas = Cuota.objects.filter(
            estado='pendiente',
            fecha_vencimiento__lt=fecha_limite
        ).select_related('afiliado')
        
        afiliados_notificados = set()
        
        for cuota in cuotas_vencidas:
            if cuota.afiliado and cuota.afiliado.id not in afiliados_notificados:
                telefono = cuota.afiliado.telefono
                if telefono:
                    # Calcular total de deuda del afiliado
                    deuda_total = Cuota.objects.filter(
                        afiliado=cuota.afiliado,
                        estado='pendiente'
                    ).aggregate(total=models.Sum('monto'))['total'] or 0
                    
                    mensaje = f"""
⚠️ *Recordatorio de Pago Vencido*

Estimado(a) {cuota.afiliado.nombre_completo},

Tiene pagos pendientes con más de 7 días de vencimiento.

💰 *Deuda Total:* Bs. {deuda_total}
📅 *Cuotas Vencidas:* {Cuota.objects.filter(afiliado=cuota.afiliado, estado='pendiente').count()}

Por favor, regularice su situación a la brevedad para evitar sanciones.

_Sindicato Mixto Integración Taipiplaya_
                    """.strip()
                    
                    whatsapp_service.send_message(
                        phone=telefono,
                        message=mensaje,
                        message_type='general'
                    )
                    afiliados_notificados.add(cuota.afiliado.id)
        
        logger.info(f"Notificaciones de pagos vencidos enviadas a {len(afiliados_notificados)} afiliados.")
    except Exception as e:
        logger.error(f"Error notificando pagos vencidos: {str(e)}")


def notify_upcoming_meetings():
    """
    Notifica reuniones programadas para mañana (24h antes)
    """
    try:
        from reuniones.models import Reunion
        from afiliados.models import Afiliado
        
        manana = timezone.now().date() + timedelta(days=1)
        
        reuniones = Reunion.objects.filter(
            fecha=manana,
            estado='programada'
        )
        
        for reunion in reuniones:
            # Notificar a todos los afiliados activos
            afiliados = Afiliado.objects.filter(estado='activo', is_active=True)
            
            for afiliado in afiliados:
                if afiliado.telefono:
                    mensaje = f"""
📅 *Recordatorio de Reunión*

Estimado(a) {afiliado.nombre_completo},

Le recordamos que mañana hay reunión:

📋 *Asunto:* {reunion.asunto}
📅 *Fecha:* {reunion.fecha.strftime('%d/%m/%Y')}
🕐 *Hora:* {reunion.hora.strftime('%H:%M')}
📍 *Lugar:* {reunion.lugar}

Su asistencia es obligatoria. La inasistencia sin justificación genera sanción.

_Sindicato Mixto Integración Taipiplaya_
                    """.strip()
                    
                    whatsapp_service.send_message(
                        phone=afiliado.telefono,
                        message=mensaje,
                        message_type='general'
                    )
        
        logger.info(f"Recordatorios de reunión enviados para {reuniones.count()} reuniones.")
    except Exception as e:
        logger.error(f"Error notificando reuniones: {str(e)}")


def notify_low_balance():
    """
    Alerta a la directiva si el balance está por debajo del umbral
    """
    try:
        from tesoreria.models import Pago, Egreso
        from django.db.models import Sum
        
        # Calcular balance del mes
        inicio_mes = timezone.now().date().replace(day=1)
        
        from reportes.query_helpers import INGRESO_ESTADOS_VALIDOS, EGRESO_ESTADOS_VALIDOS
        ingresos = Pago.objects.filter(
            fecha_pago__gte=inicio_mes,
            estado__in=INGRESO_ESTADOS_VALIDOS
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        egresos = Egreso.objects.filter(
            fecha__gte=inicio_mes,
            estado__in=EGRESO_ESTADOS_VALIDOS
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        balance = ingresos - egresos
        umbral = 5000  # Bs. 5000 como umbral mínimo
        
        if balance < umbral:
            admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
            if admin_phone:
                mensaje = f"""
🚨 *Alerta de Balance Bajo*

El balance financiero del mes está por debajo del umbral establecido:

💰 *Balance Actual:* Bs. {balance:,.2f}
⚠️ *Umbral Mínimo:* Bs. {umbral:,.2f}
📊 *Ingresos del Mes:* Bs. {ingresos:,.2f}
📉 *Egresos del Mes:* Bs. {egresos:,.2f}

Se recomienda revisar la situación financiera.

_Sistema Administrativo Taipiplaya_
                """.strip()
                
                whatsapp_service.send_message(
                    phone=admin_phone,
                    message=mensaje,
                    message_type='general'
                )
                logger.info("Alerta de balance bajo enviada.")
    except Exception as e:
        logger.error(f"Error notificando balance bajo: {str(e)}")


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Reporte Diario: 8:00 AM todos los días
    scheduler.add_job(
        send_daily_report,
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_report",
        max_instances=1,
        replace_existing=True,
    )
    
    # Reporte Semanal: Lunes 8:15 AM
    scheduler.add_job(
        send_weekly_report,
        trigger=CronTrigger(day_of_week='mon', hour=8, minute=15),
        id="weekly_report",
        max_instances=1,
        replace_existing=True,
    )
    
    # Reporte Mensual: Día 1 de cada mes 8:30 AM
    scheduler.add_job(
        send_monthly_report,
        trigger=CronTrigger(day=1, hour=8, minute=30),
        id="monthly_report",
        max_instances=1,
        replace_existing=True,
    )
    
    # ============ NUEVAS NOTIFICACIONES ============
    
    # Pagos Vencidos: Todos los días a las 9:00 AM
    scheduler.add_job(
        notify_overdue_payments,
        trigger=CronTrigger(hour=9, minute=0),
        id="overdue_payments",
        max_instances=1,
        replace_existing=True,
    )
    
    # Recordatorios de Reuniones: Todos los días a las 18:00 (6 PM)
    scheduler.add_job(
        notify_upcoming_meetings,
        trigger=CronTrigger(hour=18, minute=0),
        id="meeting_reminders",
        max_instances=1,
        replace_existing=True,
    )
    
    # Alerta de Balance Bajo: Todos los lunes a las 10:00 AM
    scheduler.add_job(
        notify_low_balance,
        trigger=CronTrigger(day_of_week='mon', hour=10, minute=0),
        id="low_balance_alert",
        max_instances=1,
        replace_existing=True,
    )
    
    register_events(scheduler)
    scheduler.start()
    logger.info("APScheduler para reportes y notificaciones automáticas iniciado.")

