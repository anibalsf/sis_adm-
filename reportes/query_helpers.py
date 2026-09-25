"""Helpers de consulta para reportes financieros.

Estados considerados como transacciones válidas (consistentes con el cálculo
de ArqueoCaja en tesoreria/views.py):
  - Ingresos válidos: Pago.estado == 'completado'
  - Egresos válidos:  Egreso.estado in ('aprobado', 'completado')

Los registros anulados/cancelados o pendientes NO forman parte de los totales
que se reportan a los afiliados.
"""
from django.db.models import Sum, Count

INGRESO_ESTADOS_VALIDOS = ['completado']
EGRESO_ESTADOS_VALIDOS = ['aprobado', 'completado']

INGRESO_ESTADOS_INVALIDOS = ['pendiente', 'anulado', 'cancelado']
EGRESO_ESTADOS_INVALIDOS = ['pendiente_aprobacion', 'anulado']


def pagos_validos(fecha_inicio=None, fecha_fin=None):
    from tesoreria.models import Pago
    qs = Pago.objects.select_related('afiliado', 'tipo_pago').filter(
        estado__in=INGRESO_ESTADOS_VALIDOS
    )
    if fecha_inicio:
        qs = qs.filter(fecha_pago__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(fecha_pago__lte=fecha_fin)
    return qs


def egresos_validos(fecha_inicio=None, fecha_fin=None):
    from tesoreria.models import Egreso
    qs = Egreso.objects.select_related('tipo_pago').filter(
        estado__in=EGRESO_ESTADOS_VALIDOS
    )
    if fecha_inicio:
        qs = qs.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(fecha__lte=fecha_fin)
    return qs


def pagos_excluidos(fecha_inicio=None, fecha_fin=None):
    """Pagos con estado no válido (anulado, cancelado o pendiente de revisión)."""
    from tesoreria.models import Pago
    qs = Pago.objects.select_related('afiliado', 'tipo_pago').filter(
        estado__in=INGRESO_ESTADOS_INVALIDOS
    )
    if fecha_inicio:
        qs = qs.filter(fecha_pago__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(fecha_pago__lte=fecha_fin)
    return qs


def egresos_excluidos(fecha_inicio=None, fecha_fin=None):
    """Egresos con estado no válido (pendiente de aprobación o anulado)."""
    from tesoreria.models import Egreso
    qs = Egreso.objects.select_related('tipo_pago').filter(
        estado__in=EGRESO_ESTADOS_INVALIDOS
    )
    if fecha_inicio:
        qs = qs.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(fecha__lte=fecha_fin)
    return qs


def resumen_periodo(fecha_inicio=None, fecha_fin=None):
    """Devuelve un resumen financiero del período con solo transacciones válidas."""
    pagos = pagos_validos(fecha_inicio, fecha_fin)
    egresos = egresos_validos(fecha_inicio, fecha_fin)
    ingresos_excluidos_qs = pagos_excluidos(fecha_inicio, fecha_fin)
    egresos_excluidos_qs = egresos_excluidos(fecha_inicio, fecha_fin)

    total_ingresos = pagos.aggregate(total=Sum('monto'))['total'] or 0
    total_egresos = egresos.aggregate(total=Sum('monto'))['total'] or 0
    total_ingresos_excluidos = ingresos_excluidos_qs.aggregate(total=Sum('monto'))['total'] or 0
    total_egresos_excluidos = egresos_excluidos_qs.aggregate(total=Sum('monto'))['total'] or 0

    return {
        'total_ingresos': float(total_ingresos),
        'total_egresos': float(total_egresos),
        'saldo': float(total_ingresos - total_egresos),
        'count_ingresos': pagos.count(),
        'count_egresos': egresos.count(),
        'anulados_cancelados': {
            'count_ingresos': ingresos_excluidos_qs.count(),
            'monto_ingresos': float(total_ingresos_excluidos),
            'count_egresos': egresos_excluidos_qs.count(),
            'monto_egresos': float(total_egresos_excluidos),
        },
        'ingresos_por_tipo': [
            {
                'tipo': item['tipo_pago__nombre'] or 'Otros Ingresos',
                'total': float(item['total'] or 0),
                'count': item['count'],
            }
            for item in pagos.values('tipo_pago__nombre')
            .annotate(total=Sum('monto'), count=Count('id'))
            .order_by('-total')
        ],
        'egresos_por_tipo': [
            {
                'tipo': item['tipo_pago__nombre'] or 'Otros Gastos',
                'total': float(item['total'] or 0),
                'count': item['count'],
            }
            for item in egresos.values('tipo_pago__nombre')
            .annotate(total=Sum('monto'), count=Count('id'))
            .order_by('-total')
        ],
    }