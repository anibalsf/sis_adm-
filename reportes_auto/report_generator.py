"""
Generador de reportes en PDF y Excel para envío automático
"""
import logging
import os
from datetime import datetime, timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Sum, Count, Q

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Clase para generar contenido de reportes (Texto, PDF, etc.)
    """
    
    @staticmethod
    def get_daily_summary():
        """
        Genera un resumen de las últimas 24 horas
        """
        from hojasruta.models import HojaRuta
        from tesoreria.models import Pago
        from sanciones.models import Sancion
        
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Estadísticas de Hojas de Ruta
        hojas = HojaRuta.objects.filter(created_at__date=yesterday)
        total_hojas = hojas.count()
        ingresos_hojas = hojas.aggregate(total=Sum('precio'))['total'] or 0
        
        # Estadísticas de Pagos recibidos
        pagos = Pago.objects.filter(fecha_pago=yesterday, estado='completado')
        total_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0
        
        # Sanciones aplicadas
        sanciones = Sancion.objects.filter(created_at__date=yesterday)
        total_sanciones = sanciones.count()
        monto_sanciones = sanciones.aggregate(total=Sum('monto'))['total'] or 0
        
        summary = (
            f"📊 *RESUMEN DIARIO - {yesterday.strftime('%d/%m/%Y')}*\n\n"
            f"🚗 *Hojas de Ruta:* {total_hojas} emitidas\n"
            f"💰 *Ingresos Hojas:* {ingresos_hojas:.2f} Bs\n"
            f"💸 *Total Pagos Recibidos:* {total_pagos:.2f} Bs\n"
            f"⚠️ *Sanciones:* {total_sanciones} aplicadas ({monto_sanciones:.2f} Bs)\n\n"
            f"Sindicato Mixto Taipiplaya"
        )
        
        return summary

    @staticmethod
    def get_weekly_financial_summary():
        """
        Genera resumen financiero semanal
        """
        from hojasruta.models import HojaRuta
        from tesoreria.models import Pago
        from afiliados.models import Afiliado
        from sanciones.models import Sancion
        
        # Última semana (7 días)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Hojas de ruta
        hojas = HojaRuta.objects.filter(created_at__date__range=[start_date, end_date])
        total_hojas = hojas.count()
        ingresos_hojas = hojas.aggregate(total=Sum('precio'))['total'] or 0
        
        # Top 10 afiliados por viajes
        top_afiliados = hojas.values('afiliado__nombres', 'afiliado__apellidos').annotate(
            viajes=Count('id')
        ).order_by('-viajes')[:10]
        
        # Pagos recibidos
        pagos = Pago.objects.filter(fecha_pago__range=[start_date, end_date], estado='completado')
        total_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0
        
        # Afiliados con deuda
        afiliados_con_deuda = Sancion.objects.filter(
            estado='pendiente'
        ).values('afiliado').distinct().count()
        
        # Construir reporte
        summary = (
            f"📊 *RESUMEN SEMANAL*\n"
            f"📅 {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}\n\n"
            f"🚗 *Hojas de Ruta:* {total_hojas}\n"
            f"💰 *Ingresos Hojas:* {ingresos_hojas:.2f} Bs\n"
            f"💸 *Pagos Recibidos:* {total_pagos:.2f} Bs\n"
            f"⚠️ *Afiliados con Deuda:* {afiliados_con_deuda}\n\n"
            f"🏆 *Top 10 Afiliados por Viajes:*\n"
        )
        
        for i, afiliado in enumerate(top_afiliados, 1):
            nombre = f"{afiliado.get('afiliado__nombres', '')} {afiliado.get('afiliado__apellidos', '')}"
            summary += f"{i}. {nombre}: {afiliado['viajes']} viajes\n"
        
        summary += f"\nSindicato Mixto Taipiplaya"
        
        return summary

    @staticmethod
    def get_monthly_summary():
        """
        Genera resumen mensual completo
        """
        from hojasruta.models import HojaRuta
        from tesoreria.models import Pago
        from sanciones.models import Sancion
        from afiliados.models import Afiliado
        
        # Mes anterior
        today = timezone.now().date()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        
        # Hojas de ruta
        hojas = HojaRuta.objects.filter(
            created_at__date__range=[first_day_last_month, last_day_last_month]
        )
        total_hojas = hojas.count()
        ingresos_hojas = hojas.aggregate(total=Sum('precio'))['total'] or 0
        
        # Pagos
        pagos = Pago.objects.filter(
            fecha_pago__range=[first_day_last_month, last_day_last_month],
            estado='completado'
        )
        total_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0
        
        # Sanciones
        sanciones = Sancion.objects.filter(
            created_at__date__range=[first_day_last_month, last_day_last_month]
        )
        total_sanciones_aplicadas = sanciones.count()
        monto_sanciones = sanciones.aggregate(total=Sum('monto'))['total'] or 0
        
        # Morosos
        morosos = Sancion.objects.filter(estado='pendiente').values('afiliado').distinct().count()
        
        summary = (
            f"📊 *RESUMEN MENSUAL*\n"
            f"📅 {first_day_last_month.strftime('%B %Y').upper()}\n\n"
            f"🚗 *Hojas de Ruta:* {total_hojas}\n"
            f"💰 *Ingresos Hojas:* {ingresos_hojas:.2f} Bs\n"
            f"💸 *Pagos Recibidos:* {total_pagos:.2f} Bs\n"
            f"⚠️ *Sanciones Aplicadas:* {total_sanciones_aplicadas} ({monto_sanciones:.2f} Bs)\n"
            f"📉 *Afiliados Morosos:* {morosos}\n\n"
            f"Sindicato Mixto Taipiplaya"
        )
        
        return summary
    @staticmethod
    def get_monday_hojas_pagadas_report():
        """
        Genera una lista detallada de los afiliados que pagaron sus hojas de ruta
        el día lunes para el control de la directiva.
        """
        from hojasruta.models import HojaRuta
        
        today = timezone.now().date()
        # Obtener hojas de ruta del día (Lunes)
        hojas = HojaRuta.objects.filter(fecha_emision=today).select_related('afiliado', 'ruta')
        
        total_pagadas = hojas.filter(estado='pagada').count()
        monto_total = hojas.filter(estado='pagada').aggregate(total=Sum('precio'))['total'] or 0
        total_pendientes = hojas.filter(estado__in=['emitida', 'notificada']).count()
        
        summary = (
            f"📋 *LISTA OFICIAL DE CONTROL*\n"
            f"📅 *Día:* Lunes {today.strftime('%d/%m/%Y')}\n"
            f"📍 *Hojas de Ruta Pagadas*\n\n"
        )
        
        if not hojas.exists():
            summary += "_No se registraron hojas de ruta hoy._\n"
        else:
            summary += "*DETALLE DE PAGOS:*\n"
            # Listar pagadas primero
            for h in hojas.filter(estado='pagada').order_by('nro'):
                nombre = h.afiliado.nombre_completo if hasattr(h.afiliado, 'nombre_completo') else str(h.afiliado)
                summary += f"✅ {h.nro} - {nombre}: {h.precio:.2f} Bs\n"
            
            # Listar pendientes
            pendientes = hojas.exclude(estado='pagada')
            if pendientes.exists():
                summary += "\n*SANCIONES / PENDIENTES:*\n"
                for h in pendientes.order_by('nro'):
                    nombre = h.afiliado.nombre_completo if hasattr(h.afiliado, 'nombre_completo') else str(h.afiliado)
                    summary += f"❌ {h.nro} - {nombre}: PENDIENTE\n"

        summary += (
            f"\n--- *RESUMEN FINAL* ---\n"
            f"✅ Pagadas: {total_pagadas}\n"
            f"❌ Pendientes: {total_pendientes}\n"
            f"💰 Recaudación: {monto_total:.2f} Bs\n\n"
            f"Sindicato S.M.I.T. Taipiplaya"
        )
        
        return summary

    @staticmethod
    def get_daily_puntero_la_paz_report():
        """
        Genera el reporte de quién sale hoy en el puntero de La Paz.
        """
        from hojasruta.models import TurnoSalida
        from datetime import date
        
        today = date.today()
        # Buscar el turno programado para hoy en la ruta La Paz
        turnos = TurnoSalida.objects.filter(
            fecha=today, 
            ruta__destino__iexact='la paz'
        ).select_related('afiliado', 'ruta')
        
        # Dial de la semana
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_nombre = dias[today.weekday()]
        
        summary = (
            f"🚌 *CONTROL DIARIO - RUTA LA PAZ*\n"
            f"📅 *Día:* {dia_nombre} {today.strftime('%d/%m/%Y')}\n\n"
        )
        
        if today.weekday() in [1, 3]: # Martes o Jueves
            summary += "ℹ️ *AVISO:* Hoy no hay turno de Taipiplaya. Salen integración Caranavi (Convenio).\n"
        elif not turnos.exists():
            summary += "⚠️ *ATENCIÓN:* No se encontró programación para hoy en el sistema.\n"
        else:
            summary += "*PROGRAMACIÓN DE SALIDA (PUNTERO):*\n"
            for t in turnos:
                af = t.afiliado
                vehiculos = af.vehiculos.all()
                placa = vehiculos[0].placa if vehiculos.exists() else "Sin placa reg."
                tipo = vehiculos[0].tipo if vehiculos.exists() else "N/A"
                
                summary += (
                    f"✅ *{t.orden}º Salida:*\n"
                    f"👤 *Socio:* {af.nombre_completo}\n"
                    f"🚗 *Vehículo:* {tipo.upper()} - {placa}\n"
                    f"📞 *Tel:* {af.telefono or 'N/A'}\n\n"
                )
        
        summary += (
            f"Favor realizar el control respectivo.\n"
            f"_Sindicato S.M.I.T. Taipiplaya_"
        )
        
        return summary
