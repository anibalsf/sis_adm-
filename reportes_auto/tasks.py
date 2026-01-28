"""
Tareas de reporte automático via Celery
"""
from celery import shared_task
import logging
from datetime import timedelta
from django.utils import timezone
from .report_generator import ReportGenerator
from .models import ReporteGenerado, ConfiguracionReporte
from whatsapp_notif.services import whatsapp_service
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def send_daily_report_task():
    """
    Tarea para enviar el reporte diario a la directiva
    """
    try:
        # Generar contenido
        summary = ReportGenerator.get_daily_summary()
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Obtener configuración
        try:
            config = ConfiguracionReporte.objects.get(tipo='diario', activo=True)
            recipients = config.destinatarios_whatsapp.split(',') if config.destinatarios_whatsapp else []
        except ConfiguracionReporte.DoesNotExist:
            # Fallback a settings
            recipients = getattr(settings, 'REPORT_RECIPIENTS_WHATSAPP', '').split(',') if hasattr(settings, 'REPORT_RECIPIENTS_WHATSAPP') else []
        
        if not recipients:
            admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
            if admin_phone:
                recipients = [admin_phone]
        
        # Crear registro del reporte
        reporte = ReporteGenerado.objects.create(
            tipo='diario',
            fecha_periodo=yesterday,
            contenido=summary,
            destinatarios_whatsapp=','.join(recipients),
            estado='generado'
        )
        
        # Enviar mensajes
        sent_count = 0
        for phone in recipients:
            try:
                whatsapp_service.send_message(
                    phone=phone.strip(),
                    message=summary,
                    message_type='general',
                    recipient_name='Directivo'
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Error enviando reporte diario a {phone}: {e}")
                reporte.error_message += f"\nError en {phone}: {str(e)}"
        
        # Actualizar estado
        reporte.mensajes_enviados = sent_count
        reporte.estado = 'enviado' if sent_count > 0 else 'fallido'
        reporte.save()
        
        return f"Reportes enviados: {sent_count}"
    
    except Exception as e:
        logger.error(f"Error en send_daily_report_task: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_weekly_report_task():
    """
    Tarea para enviar el reporte semanal
    """
    try:
        summary = ReportGenerator.get_weekly_financial_summary()
        today = timezone.now().date()
        
        # Obtener configuración
        try:
            config = ConfiguracionReporte.objects.get(tipo='semanal', activo=True)
            recipients = config.destinatarios_whatsapp.split(',') if config.destinatarios_whatsapp else []
        except ConfiguracionReporte.DoesNotExist:
            recipients = getattr(settings, 'REPORT_RECIPIENTS_WHATSAPP', '').split(',') if hasattr(settings, 'REPORT_RECIPIENTS_WHATSAPP') else []
        
        # Crear registro
        reporte = ReporteGenerado.objects.create(
            tipo='semanal',
            fecha_periodo=today,
            contenido=summary,
            destinatarios_whatsapp=','.join(recipients),
            estado='generado'
        )
        
        # Enviar
        sent_count = 0
        for phone in recipients:
            try:
                whatsapp_service.send_message(
                    phone=phone.strip(),
                    message=summary,
                    message_type='general',
                    recipient_name='Directivo'
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Error enviando reporte semanal a {phone}: {e}")
        
        reporte.mensajes_enviados = sent_count
        reporte.estado = 'enviado' if sent_count > 0 else 'fallido'
        reporte.save()
        
        return f"Reportes semanales enviados: {sent_count}"
    
    except Exception as e:
        logger.error(f"Error en send_weekly_report_task: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_monthly_report_task():
    """
    Tarea para enviar el reporte mensual
    """
    try:
        summary = ReportGenerator.get_monthly_summary()
        today = timezone.now().date()
        
        # Obtener configuración
        try:
            config = ConfiguracionReporte.objects.get(tipo='mensual', activo=True)
            recipients = config.destinatarios_whatsapp.split(',') if config.destinatarios_whatsapp else []
        except ConfiguracionReporte.DoesNotExist:
            recipients = getattr(settings, 'REPORT_RECIPIENTS_WHATSAPP', '').split(',') if hasattr(settings, 'REPORT_RECIPIENTS_WHATSAPP') else []
        
        # Crear registro
        reporte = ReporteGenerado.objects.create(
            tipo='mensual',
            fecha_periodo=today,
            contenido=summary,
            destinatarios_whatsapp=','.join(recipients),
            estado='generado'
        )
        
        # Enviar
        sent_count = 0
        for phone in recipients:
            try:
                whatsapp_service.send_message(
                    phone=phone.strip(),
                    message=summary,
                    message_type='general',
                    recipient_name='Directivo'
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Error enviando reporte mensual a {phone}: {e}")
        
        reporte.mensajes_enviados = sent_count
        reporte.estado = 'enviado' if sent_count > 0 else 'fallido'
        reporte.save()
        
        return f"Reportes mensuales enviados: {sent_count}"
    
    except Exception as e:
        logger.error(f"Error en send_monthly_report_task: {e}")
        return f"Error: {str(e)}"
