from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Max, Sum

from .models import MiembroDirectorio


def resumen_caja_periodo(desde, hasta):
    """Ingresos, egresos y saldo de un período por fechas de los movimientos.

    No requiere FK al directorio: los pagos/egresos se asocian a la gestión
    vigente por su fecha. Solo se cuentan movimientos efectivos.
    """
    from tesoreria.models import Pago, Egreso

    ingresos = (
        Pago.objects.filter(fecha_pago__gte=desde, fecha_pago__lte=hasta)
        .exclude(estado__in=['anulado', 'cancelado'])
        .aggregate(t=Sum('monto'))['t'] or Decimal('0.00')
    )
    egresos = (
        Egreso.objects.filter(fecha__gte=desde, fecha__lte=hasta)
        .exclude(estado='anulado')
        .aggregate(t=Sum('monto'))['t'] or Decimal('0.00')
    )
    nro_recibo_actual = (
        Pago.objects.filter(nro_recibo__isnull=False).aggregate(m=Max('nro_recibo'))['m'] or 0
    )
    return {
        'desde': desde,
        'hasta': hasta,
        'total_ingresos': ingresos,
        'total_egresos': egresos,
        'saldo': ingresos - egresos,
        'nro_recibo_actual': nro_recibo_actual,
    }


@transaction.atomic
def cambio_gestion(nuevos_miembros, fecha_inicio=None, user=None):
    """Cierra el directorio vencido e inaugura el entrante en una transacción.

    - Concluye los miembros activos vencidos (fecha_fin = fin de vigencia).
    - Crea los miembros electos del nuevo directorio como activos.
    - Devuelve el resumen de transferencia de caja de la gestión saliente.
    - La numeración de recibos (nro_recibo) NO se reinicia: continúa global.
    """
    from tesoreria.models import Pago

    if not nuevos_miembros:
        raise ValueError('Debe indicar al menos un miembro del nuevo directorio')

    hoy = date.today()
    fecha_inicio = fecha_inicio or hoy

    cargos = [str(m.get('cargo', '')).strip().lower() for m in nuevos_miembros]
    if len(cargos) != len(set(cargos)):
        raise ValueError('No puede haber dos miembros con el mismo cargo en el nuevo directorio')

    # 1. Cerrar el directorio saliente (vencidos y, si sobreviven, cualquier
    #    activo que se reemplace para forzar un único directorio vigente)
    salientes = list(MiembroDirectorio.objects.filter(estado='activo'))
    for m in salientes:
        m.estado = 'concluido'
        m.fecha_fin = m.fecha_fin or min(m.vigencia_hasta, fecha_inicio)
        m.save(update_fields=['estado', 'fecha_fin', 'updated_at'])

    # 2. Crear el nuevo directorio electo
    entrantes = []
    for item in nuevos_miembros:
        entrantes.append(MiembroDirectorio.objects.create(
            afiliado_id=item['afiliado'],
            cargo=str(item['cargo']).strip().lower(),
            fecha_inicio=item.get('fecha_inicio') or fecha_inicio,
            estado='activo',
        ))

    # 3. Transferencia de caja de la gestión saliente (por fechas, sin migrar datos)
    if salientes:
        desde = min(m.fecha_inicio for m in salientes)
        hasta = max((m.fecha_fin or m.vigencia_hasta) for m in salientes)
        transferencia = resumen_caja_periodo(desde, hasta)
        # Asociación directorio saliente -> entrante en el resumen
        transferencia['directorio_saliente'] = salientes
        transferencia['directorio_entrante'] = entrantes
    else:
        ultimo = Pago.objects.filter(nro_recibo__isnull=False).aggregate(m=Max('nro_recibo'))['m'] or 0
        transferencia = {
            'desde': None, 'hasta': None,
            'total_ingresos': Decimal('0.00'),
            'total_egresos': Decimal('0.00'),
            'saldo': Decimal('0.00'),
            'nro_recibo_actual': ultimo,
            'directorio_saliente': [],
            'directorio_entrante': entrantes,
        }

    return {
        'saliente': salientes,
        'entrante': entrantes,
        'transferencia': transferencia,
        'realizado_por': user,
        'fecha_cambio': hoy,
    }
