"""
Generador de reportes automáticos.

Cada método devuelve un dict con:
  - `texto`:  resumen para WhatsApp
  - `datos`:  estructura {titulo, subtitulo, secciones, tabla} usada para
              renderizar el PDF/Excel y la vista de detalle del frontend.
"""
import logging
from datetime import timedelta

from django.db.models import Sum, Count, Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

DIAS_ES = [
    'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'
]
MESES_ES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]
MESES_ES_ABREV = [
    'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
    'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
]


def _bs(monto):
    """Formatea un monto con separador de miles estilo Bolivia."""
    try:
        valor = float(monto or 0)
    except (TypeError, ValueError):
        valor = 0.0
    return f"{valor:,.2f}"


def _kpis_financieros(fecha_inicio, fecha_fin):
    """KPIs del período reusando query_helpers (respeta estados válidos)."""
    from reportes.query_helpers import resumen_periodo
    return resumen_periodo(fecha_inicio, fecha_fin)


def _nombre(row):
    nombres = (row.get('afiliado__nombres') or '').strip()
    apellidos = (row.get('afiliado__apellidos') or '').strip()
    if nombres or apellidos:
        return f"{nombres} {apellidos}".strip()
    return row.get('afiliado__nombre_completo') or 'Sin nombre'


class ReportGenerator:
    """
    Genera el contenido de los reportes automáticos y su estructura de datos.
    """

    # ------------------------------------------------------------------ diario
    @staticmethod
    def get_daily_summary():
        """
        Resumen de ayer: hojas de ruta, pagos, egresos y sanciones.
        """
        from hojasruta.models import HojaRuta
        from tesoreria.models import Pago
        from sanciones.models import Sancion

        ayer = timezone.localdate() - timedelta(days=1)

        hojas = HojaRuta.objects.filter(fecha_emision=ayer)
        total_hojas = hojas.count()
        ingresos_hojas = hojas.aggregate(total=Sum('precio'))['total'] or 0

        pagos = Pago.objects.filter(fecha_pago=ayer, estado='completado')
        total_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0
        count_pagos = pagos.count()

        from reportes.query_helpers import egresos_validos
        egresos = egresos_validos(ayer, ayer)
        total_egresos = egresos.aggregate(total=Sum('monto'))['total'] or 0

        sanciones = Sancion.objects.filter(estado='pendiente')
        monto_sanciones = sanciones.aggregate(total=Sum('monto'))['total'] or 0

        texto = (
            f"📊 *RESUMEN DIARIO - {ayer.strftime('%d/%m/%Y')}*\n\n"
            f"🚗 *Hojas de Ruta:* {total_hojas} emitidas ({_bs(ingresos_hojas)} Bs)\n"
            f"💰 *Pagos recibidos:* {count_pagos} por {_bs(total_pagos)} Bs\n"
            f"💸 *Egresos:* {_bs(total_egresos)} Bs\n"
            f"📉 *Saldo del día:* {_bs(total_pagos - total_egresos)} Bs\n"
            f"⚠️ *Sanciones pendientes:* {sanciones.count()} ({_bs(monto_sanciones)} Bs)\n\n"
            f"_Sindicato Mixto Taipiplaya_"
        )

        datos = {
            'titulo': 'Resumen Diario',
            'subtitulo': ayer.strftime('%d/%m/%Y'),
            'kpis': [
                {'etiqueta': 'Hojas de ruta', 'valor': total_hojas},
                {'etiqueta': 'Ingresos hojas', 'valor': _bs(ingresos_hojas), 'sufijo': ' Bs'},
                {'etiqueta': 'Pagos recibidos', 'valor': _bs(total_pagos), 'sufijo': ' Bs'},
                {'etiqueta': 'Egresos', 'valor': _bs(total_egresos), 'sufijo': ' Bs'},
                {'etiqueta': 'Saldo del día', 'valor': _bs(total_pagos - total_egresos), 'sufijo': ' Bs'},
                {'etiqueta': 'Sanciones pendientes', 'valor': _bs(monto_sanciones), 'sufijo': ' Bs'},
            ],
            'secciones': [
                {
                    'titulo': 'Detalle por tipo de pago',
                    'tabla': {
                        'columnas': ['Concepto', 'Cantidad', 'Monto (Bs)'],
                        'filas': [
                            [row['tipo_pago__nombre'] or 'Otros', row['count'], _bs(row['total'])]
                            for row in pagos.values('tipo_pago__nombre')
                            .annotate(total=Sum('monto'), count=Count('id'))
                            .order_by('-total')
                        ],
                    },
                }
            ],
        }

        return texto, datos

    # ----------------------------------------------------------------- semanal
    @staticmethod
    def get_weekly_financial_summary():
        """
        Resumen financiero de los últimos 7 días.
        """
        from hojasruta.models import HojaRuta
        from tesoreria.models import Pago
        from cuotas.models import Cuota
        from sanciones.models import Sancion
        from dateutil.relativedelta import relativedelta

        fin = timezone.localdate()
        inicio = fin - timedelta(days=6)

        hojas = HojaRuta.objects.filter(fecha_emision__gte=inicio, fecha_emision__lte=fin)
        total_hojas = hojas.count()
        ingresos_hojas = hojas.aggregate(total=Sum('precio'))['total'] or 0

        pagos = Pago.objects.filter(
            fecha_pago__gte=inicio, fecha_pago__lte=fin, estado='completado'
        )
        total_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0

        from reportes.query_helpers import egresos_validos
        egresos = egresos_validos(inicio, fin)
        total_egresos = egresos.aggregate(total=Sum('monto'))['total'] or 0

        # Deuda real: cuotas + sanciones pendientes de afiliados activos.
        # Reusa el módulo de morosidad para que el número coincida con el del
        # reporte de morosos y con el KPI de morosos.
        from reportes_auto.morosidad import contar_morosos
        morosos = contar_morosos()

        top_afiliados = list(
            hojas.values('afiliado_id', 'afiliado__nombres', 'afiliado__apellidos')
            .annotate(viajes=Count('id'))
            .order_by('-viajes')[:10]
        )
        nombres = [f"{_nombre(row)}" for row in top_afiliados]

        detalle_top = "\n".join(
            f"{i}. {nombre}: {row['viajes']} viajes"
            for i, (row, nombre) in enumerate(zip(top_afiliados, nombres), 1)
        ) or "Sin viajes registrados"

        texto = (
            f"📊 *RESUMEN SEMANAL*\n"
            f"📅 {inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}\n\n"
            f"🚗 *Hojas de Ruta:* {total_hojas} ({_bs(ingresos_hojas)} Bs)\n"
            f"💰 *Pagos recibidos:* {_bs(total_pagos)} Bs\n"
            f"💸 *Egresos:* {_bs(total_egresos)} Bs\n"
            f"📉 *Saldo semanal:* {_bs(total_pagos - total_egresos)} Bs\n"
            f"⚠️ *Afiliados con deuda:* {morosos}\n\n"
            f"🏆 *Top 10 por viajes:*\n{detalle_top}\n\n"
            f"_Sindicato Mixto Taipiplaya_"
        )

        datos = {
            'titulo': 'Resumen Semanal',
            'subtitulo': f"{inicio.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}",
            'kpis': [
                {'etiqueta': 'Hojas de ruta', 'valor': total_hojas},
                {'etiqueta': 'Pagos recibidos', 'valor': _bs(total_pagos), 'sufijo': ' Bs'},
                {'etiqueta': 'Egresos', 'valor': _bs(total_egresos), 'sufijo': ' Bs'},
                {'etiqueta': 'Saldo semanal', 'valor': _bs(total_pagos - total_egresos), 'sufijo': ' Bs'},
                {'etiqueta': 'Afiliados con deuda', 'valor': morosos},
            ],
            'secciones': [
                {
                    'titulo': 'Top 10 afiliados por viajes',
                    'tabla': {
                        'columnas': ['#', 'Afiliado', 'Viajes'],
                        'filas': [
                            [i, nombre, row['viajes']]
                            for i, (row, nombre) in enumerate(zip(top_afiliados, nombres), 1)
                        ],
                    },
                },
                {
                    'titulo': 'Egresos por tipo',
                    'tabla': {
                        'columnas': ['Concepto', 'Monto (Bs)'],
                        'filas': [
                            [row['tipo_pago__nombre'] or 'Otros', _bs(row['total'])]
                            for row in egresos.values('tipo_pago__nombre')
                            .annotate(total=Sum('monto')).order_by('-total')
                        ],
                    },
                },
            ],
        }

        return texto, datos

    # ----------------------------------------------------------------- mensual
    @staticmethod
    def get_monthly_summary():
        """
        Cierre del mes calendario anterior.
        """
        from hojasruta.models import HojaRuta
        from tesoreria.models import Pago
        from cuotas.models import Cuota
        from sanciones.models import Sancion
        from afiliados.models import Afiliado

        hoy = timezone.localdate()
        inicio = (hoy.replace(day=1) - relativedelta(months=1)).replace(day=1)
        fin = inicio + relativedelta(months=1) - timedelta(days=1)
        nombre_mes = f"{MESES_ES[inicio.month - 1]} {inicio.year}"

        hojas = HojaRuta.objects.filter(fecha_emision__gte=inicio, fecha_emision__lte=fin)
        total_hojas = hojas.count()
        ingresos_hojas = hojas.aggregate(total=Sum('precio'))['total'] or 0

        pagos = Pago.objects.filter(
            fecha_pago__gte=inicio, fecha_pago__lte=fin, estado='completado'
        )
        total_pagos = pagos.aggregate(total=Sum('monto'))['total'] or 0

        from reportes.query_helpers import egresos_validos
        egresos = egresos_validos(inicio, fin)
        total_egresos = egresos.aggregate(total=Sum('monto'))['total'] or 0

        # Deuda real: cuotas + sanciones pendientes de afiliados activos.
        from reportes_auto.morosidad import contar_morosos
        morosos = contar_morosos()

        sanciones_mes = Sancion.objects.filter(
            created_at__date__gte=inicio, created_at__date__lte=fin
        )
        monto_sanciones = sanciones_mes.aggregate(total=Sum('monto'))['total'] or 0

        nuevos_afiliados = Afiliado.objects.filter(
            fecha_ingreso__gte=inicio, fecha_ingreso__lte=fin
        ).count()

        saldo = total_pagos - total_egresos
        texto = (
            f"📊 *CIERRE MENSUAL - {nombre_mes.upper()}*\n\n"
            f"🚗 *Hojas de Ruta:* {total_hojas} ({_bs(ingresos_hojas)} Bs)\n"
            f"💰 *Ingresos totales:* {_bs(total_pagos)} Bs\n"
            f"💸 *Egresos totales:* {_bs(total_egresos)} Bs\n"
            f"{'✅' if saldo >= 0 else '🔴'} *Saldo del mes:* {_bs(saldo)} Bs\n"
            f"⚠️ *Sanciones aplicadas:* {sanciones_mes.count()} ({_bs(monto_sanciones)} Bs)\n"
            f"📉 *Afiliados con deuda:* {morosos}\n"
            f"🆕 *Afiliados nuevos:* {nuevos_afiliados}\n\n"
            f"_Sindicato Mixto Taipiplaya_"
        )

        datos = {
            'titulo': 'Cierre Mensual',
            'subtitulo': nombre_mes,
            'kpis': [
                {'etiqueta': 'Ingresos', 'valor': _bs(total_pagos), 'sufijo': ' Bs'},
                {'etiqueta': 'Egresos', 'valor': _bs(total_egresos), 'sufijo': ' Bs'},
                {'etiqueta': 'Saldo', 'valor': _bs(saldo), 'sufijo': ' Bs'},
                {'etiqueta': 'Hojas de ruta', 'valor': total_hojas},
                {'etiqueta': 'Sanciones aplicadas', 'valor': sanciones_mes.count()},
                {'etiqueta': 'Afiliados con deuda', 'valor': morosos},
                {'etiqueta': 'Afiliados nuevos', 'valor': nuevos_afiliados},
            ],
            'secciones': [
                {
                    'titulo': 'Ingresos por concepto',
                    'tabla': {
                        'columnas': ['Concepto', 'Cantidad', 'Monto (Bs)'],
                        'filas': [
                            [row['tipo_pago__nombre'] or 'Otros', row['count'], _bs(row['total'])]
                            for row in pagos.values('tipo_pago__nombre')
                            .annotate(total=Sum('monto'), count=Count('id'))
                            .order_by('-total')
                        ],
                    },
                },
                {
                    'titulo': 'Egresos por concepto',
                    'tabla': {
                        'columnas': ['Concepto', 'Cantidad', 'Monto (Bs)'],
                        'filas': [
                            [row['tipo_pago__nombre'] or 'Otros', row['count'], _bs(row['total'])]
                            for row in egresos.values('tipo_pago__nombre')
                            .annotate(total=Sum('monto'), count=Count('id'))
                            .order_by('-total')
                        ],
                    },
                },
            ],
        }

        return texto, datos

    # ------------------------------------------------------- control de lunes
    @staticmethod
    def get_monday_hojas_pagadas_report():
        """
        Lista de control: quién pagó sus hojas de ruta y quién no.
        """
        from hojasruta.models import HojaRuta

        hoy = timezone.localdate()
        hojas = HojaRuta.objects.filter(
            fecha_emision=hoy
        ).select_related('afiliado', 'ruta')

        pagadas = list(hojas.filter(estado='pagada').order_by('nro'))
        pendientes = list(hojas.exclude(estado='pagada').order_by('nro'))
        monto_total = sum(float(h.precio or 0) for h in pagadas)

        lineas_pagadas = "\n".join(
            f"✅ {h.nro} - {h.afiliado.nombre_completo if h.afiliado else 'Sin nombre'}: {float(h.precio or 0):.2f} Bs"
            for h in pagadas
        ) or "_Ninguna hoja pagada._"

        lineas_pendientes = "\n".join(
            f"❌ {h.nro} - {h.afiliado.nombre_completo if h.afiliado else 'Sin nombre'}: PENDIENTE"
            for h in pendientes
        )
        if lineas_pendientes:
            lineas_pendientes = f"\n*SANCIONES / PENDIENTES:*\n{lineas_pendientes}"

        texto = (
            f"📋 *LISTA OFICIAL DE CONTROL*\n"
            f"📅 *Día:* {DIAS_ES[hoy.weekday()]} {hoy.strftime('%d/%m/%Y')}\n\n"
            f"*DETALLE DE PAGOS:*\n{lineas_pagadas}{lineas_pendientes}\n\n"
            f"---\n✅ Pagadas: {len(pagadas)}\n"
            f"❌ Pendientes: {len(pendientes)}\n"
            f"💰 Recaudación: {float(monto_total):.2f} Bs\n\n"
            f"_Sindicato S.M.I.T. Taipiplaya_"
        )

        def _fila(h, pagado):
            return [
                h.nro,
                h.afiliado.nombre_completo if h.afiliado else 'Sin nombre',
                h.ruta.nombre if h.ruta else '-',
                f"{float(h.precio):.2f}",
                'Pagada' if pagado else h.estado,
            ]

        datos = {
            'titulo': 'Lista de Control - Hojas de Ruta',
            'subtitulo': f"{DIAS_ES[hoy.weekday()]} {hoy.strftime('%d/%m/%Y')}",
            'kpis': [
                {'etiqueta': 'Hojas pagadas', 'valor': len(pagadas)},
                {'etiqueta': 'Hojas pendientes', 'valor': len(pendientes)},
                {'etiqueta': 'Recaudación', 'valor': _bs(monto_total), 'sufijo': ' Bs'},
            ],
            'secciones': [
                {
                    'titulo': 'Detalle',
                    'tabla': {
                        'columnas': ['Nro', 'Afiliado', 'Ruta', 'Precio', 'Estado'],
                        'filas': (
                            [_fila(h, True) for h in pagadas]
                            + [_fila(h, False) for h in pendientes]
                        ),
                    },
                }
            ],
        }

        return texto, datos

    # --------------------------------------------------------- puntero La Paz
    @staticmethod
    def get_daily_puntero_la_paz_report():
        """
        Control diario de salidas por el puntero de La Paz.
        """
        from hojasruta.models import TurnoSalida

        hoy = timezone.localdate()
        dia_nombre = DIAS_ES[hoy.weekday()]

        turnos = list(
            TurnoSalida.objects.filter(
                fecha=hoy, ruta__destino__iexact='la paz'
            ).select_related('afiliado', 'ruta').order_by('orden')
        )

        filas = []
        detalle = ""
        for t in turnos:
            af = t.afiliado
            if not af:
                continue
            vehiculos = list(af.vehiculos.all())
            placa = vehiculos[0].placa if vehiculos else 'Sin placa reg.'
            tipo = vehiculos[0].tipo if vehiculos else 'N/A'
            filas.append([t.orden, af.nombre_completo, tipo, placa, af.telefono or 'N/A'])
            detalle += (
                f"✅ *{t.orden}º Salida:*\n"
                f"👤 *Socio:* {af.nombre_completo}\n"
                f"🚗 *Vehículo:* {str(tipo).upper()} - {placa}\n"
                f"📞 *Tel:* {af.telefono or 'N/A'}\n\n"
            )

        if hoy.weekday() in (1, 3):
            cuerpo = "ℹ️ *AVISO:* Hoy no hay turno de Taipiplaya. Salen integración Caranavi (Convenio).\n"
        elif not filas:
            cuerpo = "⚠️ *ATENCIÓN:* No se encontró programación para hoy en el sistema.\n"
        else:
            cuerpo = f"*PROGRAMACIÓN DE SALIDA (PUNTERO):*\n{detalle}"

        texto = (
            f"🚌 *CONTROL DIARIO - RUTA LA PAZ*\n"
            f"📅 *Día:* {dia_nombre} {hoy.strftime('%d/%m/%Y')}\n\n"
            f"{cuerpo}"
            f"Favor realizar el control respectivo.\n"
            f"_Sindicato S.M.I.T. Taipiplaya_"
        )

        datos = {
            'titulo': 'Control Diario - Ruta La Paz',
            'subtitulo': f"{dia_nombre} {hoy.strftime('%d/%m/%Y')}",
            'kpis': [{'etiqueta': 'Salidas programadas', 'valor': len(filas)}],
            'secciones': [
                {
                    'titulo': 'Programación de salida',
                    'tabla': {
                        'columnas': ['Orden', 'Socio', 'Vehículo', 'Placa', 'Teléfono'],
                        'filas': filas,
                    },
                }
            ],
        }

        return texto, datos
