"""
Cálculo de morosidad compartido entre el reporte de estado de cuentas
(`/api/reportes/afiliados-morosos/`), el KPI de morosos y la alerta
semanal por WhatsApp.

Definición de deuda: cuotas pendientes + sanciones pendientes.
Antes cada consumidor calculaba algo distinto (el KPI usaba
`estado='pasivo'`, la alerta solo sanciones con umbral 200 Bs), lo que
hacía que los tres mostraran números diferentes.
"""
import logging
from decimal import Decimal

from django.db.models import Count, DecimalField, IntegerField, Max, Subquery, Sum
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)

# Umbrales en días desde el último pago válido
NIVELES = (
    ('CRÍTICO', 90),
    ('ALTO', 60),
    ('MODERADO', 30),
)
NIVEL_SIN_PAGOS = 'CRÍTICO'

CEROS = {'deuda_cuotas': Decimal('0'), 'deuda_sanciones': Decimal('0')}


def nivel_morosidad(dias_sin_pagar):
    """Clasifica por días sin pagar. `None` = nunca pagó → nivel máximo."""
    if dias_sin_pagar is None:
        return NIVEL_SIN_PAGOS
    for nombre, limite in NIVELES:
        if dias_sin_pagar > limite:
            return nombre
    return 'BAJO'


def _deuda_queryset(periodo_limite=None):
    """
    Queryset de afiliados activos anotado con su deuda y último pago.
    `periodo_limite` acota las cuotas consideradas (ej. solo vencidas).
    """
    from afiliados.models import Afiliado
    from asistencias.models import Asistencia
    from cuotas.models import Cuota
    from sanciones.models import Sancion
    from reportes.query_helpers import INGRESO_ESTADOS_VALIDOS
    from tesoreria.models import Pago

    from django.db.models import OuterRef

    activos = Afiliado.objects.filter(estado='activo', is_active=True)

    cuotas = Cuota.objects.filter(estado='pendiente')
    if periodo_limite is not None:
        cuotas = cuotas.filter(periodo__lt=periodo_limite)

    cuotas_agg = (
        cuotas.values('afiliado_id')
        .annotate(
            deuda_cuotas=Sum('monto'),
            cantidad_cuotas_pendientes=Count('id'),
        )
    )
    sanciones_agg = (
        Sancion.objects.filter(estado='pendiente')
        .values('afiliado_id')
        .annotate(
            deuda_sanciones=Sum('monto'),
            cantidad_sanciones_pendientes=Count('id'),
        )
    )
    faltas_agg = (
        Asistencia.objects.filter(estado='falta')
        .values('afiliado_id')
        .annotate(cantidad_faltas=Count('id'))
    )
    ultimo_pago_agg = (
        Pago.objects.filter(estado__in=INGRESO_ESTADOS_VALIDOS)
        .values('afiliado_id')
        .annotate(ultimo_pago=Max('fecha_pago'))
    )

    qs = activos.annotate(
        deuda_cuotas=Subquery(cuotas_agg.filter(afiliado_id=OuterRef('pk')).values('deuda_cuotas'),
                              output_field=DecimalField(max_digits=12, decimal_places=2)),
        cantidad_cuotas_pendientes=Subquery(cuotas_agg.filter(afiliado_id=OuterRef('pk')).values('cantidad_cuotas_pendientes'),
                                            output_field=IntegerField()),
        deuda_sanciones=Subquery(sanciones_agg.filter(afiliado_id=OuterRef('pk')).values('deuda_sanciones'),
                                 output_field=DecimalField(max_digits=12, decimal_places=2)),
        cantidad_sanciones_pendientes=Subquery(sanciones_agg.filter(afiliado_id=OuterRef('pk')).values('cantidad_sanciones_pendientes'),
                                              output_field=IntegerField()),
        cantidad_faltas=Subquery(faltas_agg.filter(afiliado_id=OuterRef('pk')).values('cantidad_faltas'),
                                output_field=IntegerField()),
        ultimo_pago=Subquery(ultimo_pago_agg.filter(afiliado_id=OuterRef('pk')).values('ultimo_pago')),
    ).annotate(
        deuda_total=Coalesce('deuda_cuotas', CEROS['deuda_cuotas'])
        + Coalesce('deuda_sanciones', CEROS['deuda_sanciones'])
    ).filter(
        Q_deuda()
    )

    return qs


def Q_deuda():
    from django.db.models import Q
    return Q(deuda_cuotas__gt=0) | Q(deuda_sanciones__gt=0)


CAMPOS_MOROSO = (
    'id', 'nombres', 'apellidos', 'ci', 'telefono',
    'deuda_cuotas', 'deuda_sanciones', 'deuda_total',
    'cantidad_cuotas_pendientes', 'cantidad_sanciones_pendientes',
    'cantidad_faltas', 'ultimo_pago',
)


def serializar_filas(filas, hoy):
    """
    Convierte filas (queryset o .values()) al formato de la API.
    Se separa de _serializar para poder serializar solo la página pedida.
    """
    for fila in filas:
        ultimo_pago = fila['ultimo_pago']
        dias = (hoy - ultimo_pago).days if ultimo_pago else None
        nombres = (fila.get('nombres') or '').strip()
        apellidos = (fila.get('apellidos') or '').strip()
        yield {
            'afiliado_id': fila['id'],
            'nombre_completo': f"{nombres} {apellidos}".strip(),
            'ci': fila['ci'],
            'telefono': fila['telefono'],
            'deuda_cuotas': float(fila['deuda_cuotas'] or 0),
            'deuda_sanciones': float(fila['deuda_sanciones'] or 0),
            'deuda_total': float(fila['deuda_total'] or 0),
            'cantidad_cuotas_pendientes': fila['cantidad_cuotas_pendientes'] or 0,
            'cantidad_sanciones_pendientes': fila['cantidad_sanciones_pendientes'] or 0,
            'cantidad_faltas': fila['cantidad_faltas'] or 0,
            'ultimo_pago': str(ultimo_pago) if ultimo_pago else 'Nunca',
            'dias_sin_pagar': dias,
            'nivel_morosidad': nivel_morosidad(dias),
        }


def _serializar(qs, hoy):
    return serializar_filas(qs.values(*CAMPOS_MOROSO), hoy)


def contar_morosos(periodo_limite=None):
    """
    Número de afiliados activos con deuda, sin materializar filas.
    Única definición usada por KPIs, reportes y alertas.
    """
    return _deuda_queryset(periodo_limite=periodo_limite).count()


def resumen_morosidad(periodo_limite=None, umbral_critico=0, top=5):
    """
    Resumen agregado de morosidad, sin materializar toda la lista.

    Devuelve: {con_deuda, deuda_total, por_nivel, top_deudores, sin_pago}
    """
    from django.utils import timezone

    hoy = timezone.localdate()
    qs = _deuda_queryset(periodo_limite=periodo_limite)

    totales = qs.aggregate(
        con_deuda=Count('id'),
        deuda_total=Sum('deuda_total'),
    )
    con_deuda = totales['con_deuda'] or 0
    deuda_total = float(totales['deuda_total'] or 0)

    por_nivel = {'critico': 0, 'alto': 0, 'moderado': 0, 'bajo': 0}
    top_deudores = []
    sin_pago = 0

    if con_deuda:
        # Solo se materializan los deudores: son unos cientos, no millones.
        for item in _serializar(qs, hoy):
            clave = item['nivel_morosidad'].lower()
            if clave in por_nivel:
                por_nivel[clave] += 1
            if item['ultimo_pago'] == 'Nunca':
                sin_pago += 1
            if umbral_critico and item['deuda_total'] >= umbral_critico:
                top_deudores.append(item)

        top_deudores.sort(key=lambda x: x['deuda_total'], reverse=True)
        top_deudores = top_deudores[:top]

    return {
        'con_deuda': con_deuda,
        'deuda_total': deuda_total,
        'por_nivel': por_nivel,
        'top_deudores': top_deudores,
        'sin_pago': sin_pago,
    }
