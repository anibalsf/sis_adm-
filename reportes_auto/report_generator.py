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
        pagos = Pago.objects.filter(fecha_pago=yesterday)
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
        pagos = Pago.objects.filter(fecha_pago__range=[start_date, end_date])
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
            fecha_pago__range=[first_day_last_month, last_day_last_month]
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
