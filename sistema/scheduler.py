"""
Scheduler para notificaciones automáticas por WhatsApp
Ejecuta tareas programadas para recordatorios de pagos, sanciones y reportes administrativos
"""
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.db.models import Sum
from datetime import date, timedelta, datetime
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def enviar_recordatorios_pagos():
    """
    Envía recordatorios de cuotas pendientes cada lunes a las 9:00 AM
    """
    from cuotas.models import Cuota
    from comunicacion.services import WhatsAppService
    
    try:
        # Buscar cuotas vencidas (periodo anterior al actual)
        # Asumiendo que se debe pagar en el mes corriente. Si estamos en Dic, la de Nov ya venció.
        today = date.today()
        first_of_month = date(today.year, today.month, 1)
        
        # Cuotas pendientes con periodo menor al actual
        cuotas_vencidas = Cuota.objects.filter(
            estado='pendiente',
            periodo__lt=first_of_month
        ).select_related('afiliado')
        
        contador = 0
        service = WhatsAppService()
        
        # Agrupar por afiliado
        deudas_por_afiliado = {}
        
        for cuota in cuotas_vencidas:
            if not cuota.afiliado:
                continue
            if cuota.afiliado.id not in deudas_por_afiliado:
                 deudas_por_afiliado[cuota.afiliado.id] = {
                     'afiliado': cuota.afiliado,
                     'total': 0,
                     'meses': []
                 }
            deudas_por_afiliado[cuota.afiliado.id]['total'] += float(cuota.monto)
            deudas_por_afiliado[cuota.afiliado.id]['meses'].append(cuota.periodo.strftime('%b'))

        for data in deudas_por_afiliado.values():
            afiliado = data['afiliado']
            if afiliado.telefono:
                 meses_str = ", ".join(data['meses'])
                 mensaje = (f"📢 RECORDATORIO DE CUOTAS\n\n"
                            f"Estimado {afiliado.nombres},\n"
                            f"Tiene cuotas vencidas ({meses_str}) por un total de Bs. {data['total']}.\n"
                            f"Por favor regularice su situación.")
                 service.send_message(afiliado.telefono, mensaje)
                 contador += 1
        
        logger.info(f"✅ Enviados {contador} recordatorios de cuotas")
        return contador
        
    except Exception as e:
        logger.error(f"❌ Error enviando recordatorios de cuotas: {str(e)}")
        return 0


def enviar_recordatorios_sanciones():
    """
    Envía recordatorios de sanciones pendientes diariamente a las 10:00 AM
    """
    from sanciones.models import Sancion
    from comunicacion.services import WhatsAppService
    from comunicacion.whatsapp_templates import WhatsAppTemplates
    
    try:
        # Buscar sanciones pendientes antiguas (más de 15 días)
        fecha_limite = date.today() - timedelta(days=15)
        
        # Agrupar por afiliado para no spammear? 
        # Por ahora simple: iterar
        sanciones_antiguas = Sancion.objects.filter(
            estado='pendiente',
            created_at__lt=fecha_limite
        ).select_related('afiliado')
        
        contador = 0
        service = WhatsAppService()
        
        # Para evitar spam, podríamos agrupar, pero enviaremos individual por ahora
        # Idealmente: Agrupar por afiliado y mandar deuda total.
        
        afiliados_procesados = set()
        
        for sancion in sanciones_antiguas:
            if sancion.afiliado_id in afiliados_procesados:
                continue
                
            if sancion.afiliado and sancion.afiliado.telefono:
                # Calcular total de este afiliado
                pendientes = Sancion.objects.filter(afiliado=sancion.afiliado, estado='pendiente')
                total = sum(float(s.monto) for s in pendientes)
                count = pendientes.count()
                
                msg = WhatsAppTemplates.alerta_deuda(
                    sancion.afiliado.nombre_completo,
                    total,
                    count
                )
                service.send_message(sancion.afiliado.telefono, msg)
                afiliados_procesados.add(sancion.afiliado_id)
                contador += 1
        
        logger.info(f"✅ Enviados {contador} recordatorios de sanciones (agrupados por afiliado)")
        return contador
        
    except Exception as e:
        logger.error(f"❌ Error enviando recordatorios de sanciones: {str(e)}")
        return 0


def enviar_reporte_diario_ingresos():
    """
    Envía reporte de caja diario a la directiva (20:00 PM)
    """
    from tesoreria.models import Pago
    from comunicacion.services import WhatsAppService
    from comunicacion.whatsapp_templates import WhatsAppTemplates
    from django.contrib.auth.models import User
    
    try:
        hoy = date.today()
        pagos_hoy = Pago.objects.filter(fecha_pago=hoy)
        
        total_ingresos = pagos_hoy.aggregate(total=Sum('monto'))['total'] or 0
        cantidad = pagos_hoy.count()
        
        # Top 3 conceptos
        top_conceptos = pagos_hoy.values('tipo_pago__nombre').annotate(
            total=Sum('monto')
        ).order_by('-total')[:3]
        
        detalle = ""
        for item in top_conceptos:
            nombre = item['tipo_pago__nombre'] or "Varios"
            detalle += f"- {nombre}: Bs. {item['total']}\n"
            
        msg = WhatsAppTemplates.reporte_diario(
            str(hoy),
            total_ingresos,
            cantidad,
            detalle or "Sin movimientos hoy"
        )
        
        # Enviar a admins/directiva
        # Buscamos usuarios staff o superusers (o un grupo específico)
        destinatarios = User.objects.filter(is_staff=True)
        service = WhatsAppService()
        count = 0
        
        # Hardcode fallback si no hay usuarios con telefono en perfil (User default no tiene telefono)
        # Asumiremos que el admin quiere recibirlo en el número configurado en settings si existe
        # O mejor, usamos users extendidos si tuvieran perfil. 
        # Como User es default django, no tiene telefono. 
        # Usaremos una variable de entorno ADMIN_PHONE o similar, o enviaremos al 'afiliado' asociado al usuario si existe.
        
        admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
        if admin_phone:
             service.send_message(admin_phone, msg)
             count += 1
        
        logger.info(f"✅ Reporte diario enviado a {count} administradores")
        return count

    except Exception as e:
        logger.error(f"❌ Error enviando reporte diario: {str(e)}")
        return 0


def enviar_alertas_morosos_semanal():
    """
    Reporte semanal de morosos (Viernes 18:00)

    Usa la misma definición de deuda que el reporte de estado de cuentas
    (cuotas + sanciones pendientes) en vez de un umbral fijo de 200 Bs
    sobre sanciones solamente.
    """
    from comunicacion.services import WhatsAppService
    from comunicacion.whatsapp_templates import WhatsAppTemplates

    try:
        from reportes_auto.morosidad import resumen_morosidad

        resumen = resumen_morosidad(umbral_critico=settings.MOROSIDAD_UMBRAL_CRITICO)

        detalle = "\n".join(
            f"- {item['nombre_completo']}: Bs. {item['deuda_total']:.2f} "
            f"({item['nivel_morosidad']})"
            for item in resumen['top_deudores']
        )

        msg = WhatsAppTemplates.alerta_morosos(
            resumen['con_deuda'],
            resumen['deuda_total'],
            detalle or "Sin afiliados con deuda",
        )

        service = WhatsAppService()
        admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
        if admin_phone:
            service.send_message(admin_phone, msg)

        logger.info(
            f"✅ Reporte semanal de morosos enviado: {resumen['con_deuda']} con deuda, "
            f"Bs. {resumen['deuda_total']:.2f}"
        )
        return 1

    except Exception as e:
        logger.error(f"❌ Error enviando reporte semanal: {str(e)}")
        return 0


def enviar_notificacion_puntero_diario():
    """
    Envía notificación diaria del puntero La Paz al administrador (07:00 AM)
    """
    from reportes_auto.report_generator import ReportGenerator
    from comunicacion.services import WhatsAppService

    try:
        summary, _datos = ReportGenerator.get_daily_puntero_la_paz_report()
        admin_phone = (
            getattr(settings, 'PUNTERO_LA_PAZ_PHONE_NUMBER', None)
            or getattr(settings, 'ADMIN_PHONE_NUMBER', None)
        )
        if not admin_phone:
            logger.warning(
                "Notificación del puntero omitida: configure PUNTERO_LA_PAZ_PHONE_NUMBER "
                "o ADMIN_PHONE_NUMBER"
            )
            return 0

        service = WhatsAppService()
        service.send_message(admin_phone, summary)

        logger.info(f"✅ Notificación diaria de puntero enviada a {admin_phone}")
        return 1
    except Exception as e:
        logger.error(f"❌ Error enviando notificación diaria de puntero: {str(e)}")
        return 0

def start_scheduler():
    """
    Inicia el scheduler con las tareas programadas
    """
    global scheduler
    
    try:
        scheduler = BackgroundScheduler()
        
        # Pagos: Lunes 9:00
        scheduler.add_job(enviar_recordatorios_pagos, 'cron', day_of_week='mon', hour=9, minute=0, id='pagos', replace_existing=True)
        
        # Sanciones: Diario 10:00
        scheduler.add_job(enviar_recordatorios_sanciones, 'cron', hour=10, minute=0, id='sanciones', replace_existing=True)
        
        # Reporte Diario: Diario 20:00
        scheduler.add_job(enviar_reporte_diario_ingresos, 'cron', hour=20, minute=0, id='reporte_diario', replace_existing=True)
        
        # Reporte Morosos: Viernes 18:00
        scheduler.add_job(enviar_alertas_morosos_semanal, 'cron', day_of_week='fri', hour=18, minute=0, id='morosos', replace_existing=True)
        
        # Notificación Puntero La Paz: Diario 07:00
        scheduler.add_job(enviar_notificacion_puntero_diario, 'cron', hour=7, minute=0, id='puntero_diario', replace_existing=True)
        
        scheduler.start()
        logger.info("🚀 Scheduler iniciado con tareas de reportes y recordatorios")
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ Error iniciando scheduler: {str(e)}")
        return None
