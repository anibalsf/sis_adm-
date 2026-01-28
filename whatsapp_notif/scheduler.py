"""
Configuración del scheduler para tareas programadas de WhatsApp
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util
import logging

logger = logging.getLogger(__name__)

# Crear scheduler
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    Eliminar ejecuciones antiguas de jobs (más de 7 días por defecto)
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start_scheduler():
    """
    Iniciar el scheduler con todas las tareas programadas
    """
    if scheduler.running:
        logger.info("Scheduler ya está corriendo")
        return
    
    try:
        from .tasks import (
            send_shift_reminders,
            send_meeting_reminders,
            send_debt_reminders
        )
        
        # Recordatorios de turno - Diario a las 18:00
        scheduler.add_job(
            send_shift_reminders,
            trigger=CronTrigger(hour=18, minute=0),
            id='shift_reminders',
            max_instances=1,
            replace_existing=True,
            name='Recordatorios de Turno (18:00)'
        )
        logger.info("Job programado: Recordatorios de turno (18:00 diario)")
        
        # Recordatorios de reunión - Diario a las 08:00
        scheduler.add_job(
            send_meeting_reminders,
            trigger=CronTrigger(hour=8, minute=0),
            id='meeting_reminders',
            max_instances=1,
            replace_existing=True,
            name='Recordatorios de Reunión (08:00)'
        )
        logger.info("Job programado: Recordatorios de reunión (08:00 diario)")
        
        # Recordatorios de deuda - Lunes a las 09:00
        scheduler.add_job(
            send_debt_reminders,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='debt_reminders',
            max_instances=1,
            replace_existing=True,
            name='Recordatorios de Deuda (Lunes 09:00)'
        )
        logger.info("Job programado: Recordatorios de deudas semanales (Lunes 09:00)")
        
        # Reporte Mensual de Deuda - Primer día del mes a las 08:00
        from .tasks import send_monthly_debt_report
        scheduler.add_job(
            send_monthly_debt_report,
            trigger=CronTrigger(day=1, hour=8, minute=0),
            id='monthly_debt_report',
            max_instances=1,
            replace_existing=True,
            name='Reporte Mensual de Deuda (Día 1 08:00)'
        )
        logger.info("Job programado: Reporte mensual de deuda (Día 1 08:00)")
        
        # Limpiar ejecuciones antiguas - Diario a las 02:00
        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(hour=2, minute=0),
            id='delete_old_job_executions',
            max_instances=1,
            replace_existing=True,
            name='Limpiar logs antiguos (02:00)'
        )
        logger.info("Job programado: Limpieza de logs (02:00 diario)")
        
        # Iniciar scheduler
        scheduler.start()
        logger.info("Scheduler de WhatsApp iniciado correctamente")
        
    except Exception as e:
        logger.error(f"Error al iniciar scheduler: {str(e)}")


def stop_scheduler():
    """
    Detener el scheduler
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler detenido")


def get_scheduled_jobs():
    """
    Obtener lista de jobs programados
    """
    jobs= []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    return jobs
