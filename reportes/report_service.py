import logging
from datetime import datetime, timedelta
from django.db.models import Sum, Count
from django.utils import timezone
from tesoreria.models import Pago, Egreso
from hojasruta.models import HojaRuta
from sanciones.models import Sancion
from afiliados.models import Afiliado

logger = logging.getLogger(__name__)

class ReportService:
    @staticmethod
    def get_daily_summary():
        """Genera resumen del día anterior"""
        ayer = timezone.now().date() - timedelta(days=1)
        
        ingresos = Pago.objects.filter(fecha_pago=ayer).aggregate(total=Sum('monto'))['total'] or 0
        egresos = Egreso.objects.filter(fecha=ayer).aggregate(total=Sum('monto'))['total'] or 0
        viajes = HojaRuta.objects.filter(fecha_emision=ayer).count()
        sanciones = Sancion.objects.filter(fecha__date=ayer).count()
        
        resumen = f"📊 *REPORTE DIARIO - {ayer.strftime('%d/%m/%Y')}*\n\n"
        resumen += f"💰 *Ingresos:* Bs. {ingresos:.2f}\n"
        resumen += f"💸 *Egresos:* Bs. {egresos:.2f}\n"
        resumen += f"🚐 *Viajes realizados:* {viajes}\n"
        resumen += f"⚠️ *Sanciones:* {sanciones}\n\n"
        resumen += "_Generado automáticamente por el Sistema S.M.I.T._"
        
        return resumen

    @staticmethod
    def get_weekly_summary():
        """Genera resumen de la última semana"""
        hoy = timezone.now().date()
        hace_una_semana = hoy - timedelta(days=7)
        
        ingresos = Pago.objects.filter(fecha_pago__gte=hace_una_semana).aggregate(total=Sum('monto'))['total'] or 0
        egresos = Egreso.objects.filter(fecha__gte=hace_una_semana).aggregate(total=Sum('monto'))['total'] or 0
        morosos_count = Afiliado.objects.filter(estado='sancionado').count()
        
        resumen = f"📈 *RESUMEN SEMANAL S.M.I.T.*\n"
        resumen += f"Semana: {hace_una_semana.strftime('%d/%m')} al {hoy.strftime('%d/%m')}\n\n"
        resumen += f"💵 *Total Ingresos:* Bs. {ingresos:.2f}\n"
        resumen += f"📉 *Total Egresos:* Bs. {egresos:.2f}\n"
        resumen += f"⚖️ *Saldo Semanal:* Bs. {(ingresos - egresos):.2f}\n"
        resumen += f"👤 *Afiliados Sancionados:* {morosos_count}\n\n"
        resumen += "¡Buen inicio de semana directiva! 🚀"
        
        return resumen

    @staticmethod
    def get_monthly_summary():
        """Genera resumen del mes"""
        hoy = timezone.now().date()
        mes_nombre = hoy.strftime('%B %Y')
        inicio_mes = hoy.replace(day=1)
        
        ingresos = Pago.objects.filter(fecha_pago__gte=inicio_mes).aggregate(total=Sum('monto'))['total'] or 0
        egresos = Egreso.objects.filter(fecha__gte=inicio_mes).aggregate(total=Sum('monto'))['total'] or 0
        
        resumen = f"🏛️ *BALANCE MENSUAL - {mes_nombre.upper()}*\n\n"
        resumen += f"💰 *Ingresos Totales:* Bs. {ingresos:.2f}\n"
        resumen += f"💸 *Egresos Totales:* Bs. {egresos:.2f}\n"
        resumen += f"🏦 *Cierre de Caja:* Bs. {(ingresos - egresos):.2f}\n\n"
        resumen += "Para más detalle, consulte el Balance en el sistema."
        
        return resumen
