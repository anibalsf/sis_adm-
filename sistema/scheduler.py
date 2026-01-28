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
    Reporte semanal de morosos críticos (Viernes 18:00)
    """
    from afiliados.models import Afiliado
    from comunicacion.services import WhatsAppService
    from comunicacion.whatsapp_templates import WhatsAppTemplates
    
    try:
        # Lógica simplificada de morosos (ej. más de 500Bs deuda)
        # Esto debería ser más complejo, reusando lógica de reportes
        afiliados = Afiliado.objects.filter(estado='activo')
        criticos = []
        total_deuda_sistema = 0
        
        for afi in afiliados:
            deuda_cuotas = 0 # Implementar cálculo real si props existen
            # Por ahora solo sanciones para el ejemplo rápido o lo que tenga relación
            deuda_sanciones = 0
            # deuda_sanciones = afi.sanciones.filter(estado='pendiente').aggregate(Sum('monto'))['monto__sum'] or 0
            
            # Como llamar a relaciones inversas sin importar modelos circularmente puede ser tricky si no están cargados,
            # confiamos en que sanciones.models importó Afiliado, no al revés.
            # Usamos related_name si existe.
            
            sanciones = afi.sanciones.filter(estado='pendiente')
            deuda = sanciones.aggregate(t=Sum('monto'))['t'] or 0
            
            if deuda > 200: # Umbral de ejemplo
                criticos.append((afi.nombre_completo, deuda))
                total_deuda_sistema += deuda
        
        # Top 5
        criticos.sort(key=lambda x: x[1], reverse=True)
        top_5 = criticos[:5]
        
        detalle = ""
        for nombre, monto in top_5:
            detalle += f"- {nombre}: Bs. {monto}\n"
            
        msg = WhatsAppTemplates.alerta_morosos(
            len(criticos),
            total_deuda_sistema,
            detalle or "Sin morosos críticos"
        )
        
        service = WhatsAppService()
        admin_phone = getattr(settings, 'ADMIN_PHONE_NUMBER', None)
        if admin_phone:
             service.send_message(admin_phone, msg)
        
        logger.info("✅ Reporte semanal de morosos enviado")
        return 1

    except Exception as e:
        logger.error(f"❌ Error enviando reporte semanal: {str(e)}")
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
        
        scheduler.start()
        logger.info("🚀 Scheduler iniciado con tareas de reportes y recordatorios")
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ Error iniciando scheduler: {str(e)}")
        return None
