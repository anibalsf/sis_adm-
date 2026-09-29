"""Reporte de egresos por categoría.

Complementa el ReporteCategoriaView de ingresos: en lugar de medir cobertura de
afiliados, agrupa los egresos registrados (modelo ``tesoreria.Egreso``) por su
categoría (``TipoPago`` con ``tipo='egreso'``) y devuelve el detalle completo.

Los totales solo cuentan egresos con estado válido (aprobado), siguiendo la
misma regla que ArqueoCaja y query_helpers.
"""
import io
import unicodedata
from datetime import datetime

from django.db.models import Sum, Count, Max, Min
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .query_helpers import EGRESO_ESTADOS_INVALIDOS, EGRESO_ESTADOS_VALIDOS

METODOS_PAGO = {
    'efectivo': 'Efectivo',
    'qr': 'QR / Yape',
    'transferencia': 'Transferencia',
}

ESTADOS = {
    'aprobado': 'Aprobado',
    'pendiente_aprobacion': 'Pendiente de Aprobación',
    'anulado': 'Anulado',
}

TRAMITE = 'SINDICATO MIXTO "INTEGRACIÓN TAIPIPLAYA"'


def _slug(texto):
    """Normaliza un nombre de categoría para usarlo como nombre de archivo."""
    normalizado = unicodedata.normalize('NFKD', texto)
    ascii_ = normalizado.encode('ascii', 'ignore').decode('ascii')
    return '_'.join(ascii_.lower().split()) or 'categoria'


VERDE_OSCURO = colors.HexColor('#1a237e')
GRIS_TABLA = colors.HexColor('#455a64')
VERDE = colors.HexColor('#2e7d32')
AMBAR = colors.HexColor('#b45309')


def _base_queryset(fecha_inicio=None, fecha_fin=None):
    from tesoreria.models import Egreso
    qs = Egreso.objects.select_related('tipo_pago', 'aprobado_por')
    if fecha_inicio:
        qs = qs.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        qs = qs.filter(fecha__lte=fecha_fin)
    return qs


def _filtrar_egresos(tipo_pago=None, fecha_inicio=None, fecha_fin=None, estados=None):
    qs = _base_queryset(fecha_inicio, fecha_fin)
    if tipo_pago is not None:
        qs = qs.filter(tipo_pago=tipo_pago)
    if estados:
        qs = qs.filter(estado__in=estados)
    return qs


def listar_categorias():
    from tesoreria.models import TipoPago
    return list(
        TipoPago.objects.filter(tipo='egreso')
        .values('id', 'nombre', 'descripcion')
        .order_by('nombre')
    )


def _serializar(egreso):
    return {
        'id': egreso.id,
        'fecha': str(egreso.fecha),
        'categoria': egreso.tipo_pago.nombre,
        'descripcion': egreso.descripcion,
        'metodo_pago': egreso.metodo_pago,
        'metodo_pago_label': METODOS_PAGO.get(egreso.metodo_pago, egreso.metodo_pago or '-'),
        'banco': egreso.banco or '',
        'nro_operacion': egreso.nro_operacion or '',
        'monto': float(egreso.monto),
        'estado': egreso.estado,
        'estado_label': ESTADOS.get(egreso.estado, egreso.estado),
        'motivo_anulacion': egreso.motivo_anulacion or '',
        'aprobado_por': egreso.aprobado_por.get_full_name() if egreso.aprobado_por else '',
    }


def resumen_categoria(tipo_pago, fecha_inicio=None, fecha_fin=None, total_general=0):
    validos = _filtrar_egresos(tipo_pago, fecha_inicio, fecha_fin, EGRESO_ESTADOS_VALIDOS)
    pendientes = _filtrar_egresos(tipo_pago, fecha_inicio, fecha_fin, ['pendiente_aprobacion'])
    anulados = _filtrar_egresos(tipo_pago, fecha_inicio, fecha_fin, ['anulado'])

    agregado = validos.aggregate(
        total=Sum('monto'),
        promedio=Count('id'),
        maximo=Max('monto'),
        minimo=Min('monto'),
        primero=Min('fecha'),
        ultimo=Max('fecha'),
    )
    count_aprobados = agregado['promedio'] or 0
    total_aprobado = float(agregado['total'] or 0)

    return {
        'categoria': {
            'id': tipo_pago.id,
            'nombre': tipo_pago.nombre,
            'descripcion': tipo_pago.descripcion or '',
        },
        'total_egresos': total_aprobado,
        'count_egresos': count_aprobados,
        'promedio_egreso': round(total_aprobado / count_aprobados, 2) if count_aprobados else 0.0,
        'egreso_maximo': float(agregado['maximo'] or 0),
        'egreso_minimo': float(agregado['minimo'] or 0),
        'fecha_primer_egreso': str(agregado['primero']) if agregado['primero'] else None,
        'fecha_ultimo_egreso': str(agregado['ultimo']) if agregado['ultimo'] else None,
        'total_pendientes_aprobacion': float(pendientes.aggregate(total=Sum('monto'))['total'] or 0),
        'count_pendientes_aprobacion': pendientes.count(),
        'total_anulados': float(anulados.aggregate(total=Sum('monto'))['total'] or 0),
        'count_anulados': anulados.count(),
        'porcentaje_participacion': round(total_aprobado / total_general * 100, 1) if total_general > 0 else 0.0,
    }


def _resumen_global(resumenes, fecha_inicio=None, fecha_fin=None):
    validos = _filtrar_egresos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estados=EGRESO_ESTADOS_VALIDOS)
    pendientes = _filtrar_egresos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estados=['pendiente_aprobacion'])
    anulados = _filtrar_egresos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estados=['anulado'])

    total_aprobado = float(validos.aggregate(total=Sum('monto'))['total'] or 0)
    count_aprobado = validos.count()

    por_metodo = [
        {
            'metodo_pago': item['metodo_pago'] or 'efectivo',
            'metodo_pago_label': METODOS_PAGO.get(item['metodo_pago'], item['metodo_pago'] or '-'),
            'total': float(item['total'] or 0),
            'count': item['count'],
        }
        for item in validos.values('metodo_pago')
        .annotate(total=Sum('monto'), count=Count('id'))
        .order_by('-total')
    ]

    return {
        'total_egresos': total_aprobado,
        'count_egresos': count_aprobado,
        'promedio_egreso': round(total_aprobado / count_aprobado, 2) if count_aprobado else 0.0,
        'egreso_maximo': float(validos.aggregate(m=Max('monto'))['m'] or 0),
        'total_pendientes_aprobacion': float(pendientes.aggregate(total=Sum('monto'))['total'] or 0),
        'count_pendientes_aprobacion': pendientes.count(),
        'total_anulados': float(anulados.aggregate(total=Sum('monto'))['total'] or 0),
        'count_anulados': anulados.count(),
        'total_categorias': len([r for r in resumenes if r['count_egresos'] > 0]),
        'total_categorias_registradas': len(resumenes),
        'por_metodo_pago': por_metodo,
    }


def construir_reporte(tipo_pago_id=None, fecha_inicio=None, fecha_fin=None, todas=False):
    """Devuelve el payload JSON del reporte de egresos por categoría.

    Sin ``tipo_pago_id`` y sin ``todas`` devuelve únicamente el listado de
    categorías de egreso disponibles (para poblar el selector del formulario).
    """
    from tesoreria.models import TipoPago

    if not tipo_pago_id and not todas:
        return {'tipos_pago': listar_categorias()}

    filtros = {'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin}

    if todas:
        categorias = TipoPago.objects.filter(tipo='egreso').order_by('nombre')
        total_general = float(
            _filtrar_egresos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estados=EGRESO_ESTADOS_VALIDOS)
            .aggregate(total=Sum('monto'))['total'] or 0
        )
        resumenes = [resumen_categoria(tp, fecha_inicio, fecha_fin, total_general) for tp in categorias]
        resumenes.sort(key=lambda r: r['total_egresos'], reverse=True)

        egresos = [
            _serializar(e)
            for e in _filtrar_egresos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
                                      estados=EGRESO_ESTADOS_VALIDOS).order_by('-fecha', '-id')
        ]
        return {
            'modo': 'todas',
            'tipo': 'egreso',
            'filtros': filtros,
            'resumen': _resumen_global(resumenes, fecha_inicio, fecha_fin),
            'categorias': resumenes,
            'egresos': egresos,
            'egresos_revision': [
                _serializar(e)
                for e in _filtrar_egresos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
                                          estados=EGRESO_ESTADOS_INVALIDOS).order_by('estado', '-fecha')
            ],
        }

    try:
        tipo_pago = TipoPago.objects.get(id=tipo_pago_id, tipo='egreso')
    except (TipoPago.DoesNotExist, ValueError):
        return {'error': 'Categoría de egreso no encontrada'}

    validos = _filtrar_egresos(tipo_pago, fecha_inicio, fecha_fin, EGRESO_ESTADOS_VALIDOS)
    total_general = float(
        _filtrar_egresos(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, estados=EGRESO_ESTADOS_VALIDOS)
        .aggregate(total=Sum('monto'))['total'] or 0
    )
    resumen = resumen_categoria(tipo_pago, fecha_inicio, fecha_fin, total_general)
    resumen_global = _resumen_global([resumen], fecha_inicio, fecha_fin)

    return {
        'tipo': 'egreso',
        'categoria': resumen['categoria'],
        'filtros': filtros,
        'resumen': resumen,
        'resumen_global': resumen_global,
        'egresos': [_serializar(e) for e in validos.order_by('-fecha', '-id')],
        'egresos_revision': [
            _serializar(e)
            for e in _filtrar_egresos(tipo_pago, fecha_inicio, fecha_fin, EGRESO_ESTADOS_INVALIDOS)
            .order_by('estado', '-fecha')
        ],
    }


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #

def _estilos():
    styles = getSampleStyleSheet()
    return {
        'titulo': ParagraphStyle('TituloEgreso', parent=styles['Title'], fontSize=16, alignment=TA_CENTER,
                                 textColor=VERDE_OSCURO, spaceAfter=6),
        'subtitulo': ParagraphStyle('SubtituloEgreso', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER,
                                    textColor=colors.HexColor('#555'), spaceAfter=4),
        'seccion': ParagraphStyle('SeccionEgreso', parent=styles['Heading2'], fontSize=12, textColor=VERDE_OSCURO,
                                  spaceBefore=16, spaceAfter=6),
    }


def _estilo_tabla(color_header, alineacion_der=False, size=8):
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), color_header),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), size),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    if alineacion_der:
        style.append(('ALIGN', (-1, 0), (-1, -1), 'RIGHT'))
    return TableStyle(style)


def _encabezado_pdf(elements, styles, titulo, fecha_inicio, fecha_fin, lineas_extra=()):
    elements.append(Paragraph(TRAMITE, styles['titulo']))
    elements.append(Paragraph(titulo, styles['subtitulo']))
    periodo = f"Período: {fecha_inicio or 'inicio'} al {fecha_fin or 'hoy'}"
    elements.append(Paragraph(periodo, styles['subtitulo']))
    elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['subtitulo']))
    for linea in lineas_extra:
        elements.append(Paragraph(linea, styles['subtitulo']))
    elements.append(Spacer(1, 8))


def _kpi_table(resumen_global):
    data = [
        ['Total Egresos', 'N° Egresos', 'Promedio', 'Pendientes', 'Anulados'],
        [
            f"Bs. {resumen_global['total_egresos']:,.2f}",
            str(resumen_global['count_egresos']),
            f"Bs. {resumen_global['promedio_egreso']:,.2f}",
            f"{resumen_global['count_pendientes_aprobacion']} "
            f"(Bs. {resumen_global['total_pendientes_aprobacion']:,.2f})",
            f"{resumen_global['count_anulados']} (Bs. {resumen_global['total_anulados']:,.2f})",
        ],
    ]
    tabla = Table(data, colWidths=[3.4*cm, 2.2*cm, 3*cm, 4.2*cm, 4.2*cm])
    tabla.setStyle(_estilo_tabla(VERDE_OSCURO, size=9))
    return tabla


def _tabla_detalle(egresos):
    data = [['#', 'Fecha', 'Categoría', 'Descripción', 'Método', 'Banco / Nro. Op.', 'Monto (Bs)', 'Estado']]
    for i, e in enumerate(egresos, 1):
        banco_op = e['banco'] or '-'
        if e['nro_operacion']:
            banco_op = f"{e['banco']} / {e['nro_operacion']}" if e['banco'] else e['nro_operacion']
        data.append([
            str(i),
            datetime.strptime(e['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y'),
            e['categoria'],
            e['descripcion'] or '-',
            e['metodo_pago_label'],
            banco_op,
            f"{e['monto']:,.2f}",
            e['estado_label'],
        ])
    data.append(['', 'TOTAL', '', '', '', '', f"Bs. {sum(e['monto'] for e in egresos):,.2f}", ''])

    tabla = Table(data, repeatRows=1, colWidths=[0.9*cm, 1.9*cm, 3.2*cm, 5*cm, 2.3*cm, 3.3*cm, 2.4*cm, 2.6*cm])
    style = _estilo_tabla(VERDE, alineacion_der=True)
    style.add('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f1f8e9')])
    style.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9'))
    style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    tabla.setStyle(style)
    return tabla


def _tabla_revision(egresos):
    data = [['#', 'Fecha', 'Categoría', 'Descripción', 'Monto (Bs)', 'Estado', 'Motivo']]
    for i, e in enumerate(egresos, 1):
        data.append([
            str(i),
            datetime.strptime(e['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y'),
            e['categoria'],
            e['descripcion'] or '-',
            f"{e['monto']:,.2f}",
            e['estado_label'],
            e['motivo_anulacion'] or '-',
        ])
    tabla = Table(data, repeatRows=1, colWidths=[0.9*cm, 1.9*cm, 3.2*cm, 5*cm, 2.4*cm, 3.2*cm, 5*cm])
    style = _estilo_tabla(AMBAR, alineacion_der=True)
    style.add('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffbeb')])
    tabla.setStyle(style)
    return tabla


def _tabla_resumen_categorias(resumenes, total_general):
    data = [['Categoría', 'N° Egresos', 'Total (Bs)', '% Part.',
             'Promedio', 'Mayor Egreso', 'Pendientes', 'Anulados']]
    for r in resumenes:
        data.append([
            r['categoria']['nombre'],
            str(r['count_egresos']),
            f"{r['total_egresos']:,.2f}",
            f"{r['porcentaje_participacion']}%",
            f"{r['promedio_egreso']:,.2f}",
            f"{r['egreso_maximo']:,.2f}",
            str(r['count_pendientes_aprobacion']),
            str(r['count_anulados']),
        ])
    data.append(['TOTAL', '', f"Bs. {total_general:,.2f}", '100%', '', '', '', ''])

    tabla = Table(data, repeatRows=1, colWidths=[5.4*cm, 2.2*cm, 2.9*cm, 1.9*cm, 2.5*cm, 2.7*cm, 2.3*cm, 2.2*cm])
    style = _estilo_tabla(VERDE_OSCURO, alineacion_der=True)
    style.add('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f7ff')])
    style.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9'))
    style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    tabla.setStyle(style)
    return tabla


def _tabla_metodos(por_metodo, total_general):
    if not por_metodo:
        return None
    data = [['Método de Pago', 'N° Egresos', 'Total (Bs)', '% Part.']]
    for m in por_metodo:
        pct = round(m['total'] / total_general * 100, 1) if total_general > 0 else 0
        data.append([m['metodo_pago_label'], str(m['count']), f"{m['total']:,.2f}", f"{pct}%"])
    tabla = Table(data, colWidths=[5*cm, 3*cm, 4*cm, 3*cm])
    style = _estilo_tabla(GRIS_TABLA, alineacion_der=True)
    style.add('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    tabla.setStyle(style)
    return tabla


def generar_pdf(tipo_pago_id=None, fecha_inicio=None, fecha_fin=None, todas=False):
    """Devuelve (bytes_pdf, nombre_archivo) con el reporte de egresos por categoría."""
    reporte = construir_reporte(tipo_pago_id, fecha_inicio, fecha_fin, todas)
    if 'error' in reporte:
        return None, reporte['error']

    styles = _estilos()
    buffer = io.BytesIO()

    if 'tipos_pago' in reporte:
        return None, 'Se requiere tipo_pago_id'

    titulo = 'Reporte General de Egresos por Categoría' if todas else \
        f"Reporte de Egresos — {reporte['categoria']['nombre']}"

    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=1.2*cm, rightMargin=1.2*cm)
    elements = []
    _encabezado_pdf(elements, styles, titulo, fecha_inicio, fecha_fin)

    if todas:
        resumen = reporte['resumen']
        elements.append(_kpi_table(resumen))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph('📊 Resumen por Categoría de Egreso', styles['seccion']))
        elements.append(_tabla_resumen_categorias(reporte['categorias'], resumen['total_egresos']))
        elements.append(Spacer(1, 12))

        tabla_metodos = _tabla_metodos(resumen['por_metodo_pago'], resumen['total_egresos'])
        if tabla_metodos:
            elements.append(Paragraph('💳 Desglose por Método de Pago', styles['seccion']))
            elements.append(tabla_metodos)
            elements.append(Spacer(1, 12))

        elementos_detalle = reporte['egresos']
    else:
        resumen = reporte['resumen_global']
        elements.append(_kpi_table(resumen))
        elements.append(Spacer(1, 12))

        r = reporte['resumen']
        elements.append(Paragraph('📈 Indicadores de la Categoría', styles['seccion']))
        indicadores = [
            ['Indicador', 'Valor'],
            ['Total de la categoría', f"Bs. {r['total_egresos']:,.2f}"],
            ['Número de egresos', str(r['count_egresos'])],
            ['Promedio por egreso', f"Bs. {r['promedio_egreso']:,.2f}"],
            ['Egreso más alto', f"Bs. {r['egreso_maximo']:,.2f}"],
            ['Egreso más bajo', f"Bs. {r['egreso_minimo']:,.2f}"],
            ['Participación en el total', f"{r['porcentaje_participacion']}%"],
            ['Primer egreso', r['fecha_primer_egreso'] or '-'],
            ['Último egreso', r['fecha_ultimo_egreso'] or '-'],
            ['Pendientes de aprobación',
             f"{r['count_pendientes_aprobacion']} (Bs. {r['total_pendientes_aprobacion']:,.2f})"],
            ['Anulados', f"{r['count_anulados']} (Bs. {r['total_anulados']:,.2f})"],
        ]
        tabla_ind = Table(indicadores, colWidths=[7*cm, 8*cm])
        style_ind = _estilo_tabla(VERDE_OSCURO)
        style_ind.add('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f7ff')])
        style_ind.add('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold')
        tabla_ind.setStyle(style_ind)
        elements.append(tabla_ind)
        elements.append(Spacer(1, 12))

        elementos_detalle = reporte['egresos']

    elementos_detalle = sorted(elementos_detalle, key=lambda e: e['fecha'], reverse=True)
    elements.append(Paragraph(f'🧾 Detalle de Egresos Aprobados ({len(elementos_detalle)})', styles['seccion']))
    if elementos_detalle:
        elements.append(_tabla_detalle(elementos_detalle))
    else:
        elements.append(Paragraph('No hay egresos aprobados en el período seleccionado.',
                                  getSampleStyleSheet()['Normal']))

    if reporte['egresos_revision']:
        elements.append(Spacer(1, 16))
        elements.append(Paragraph(f"⚠️ Egresos Pendientes de Aprobación / Anulados "
                                  f"({len(reporte['egresos_revision'])})", styles['seccion']))
        elements.append(_tabla_revision(reporte['egresos_revision']))

    doc.build(elements)
    buffer.seek(0)

    sufijo = 'todas_las_categorias' if todas else _slug(reporte['categoria']['nombre'])
    return buffer.getvalue(), f"egresos_{sufijo}_{datetime.now().strftime('%Y%m%d')}.pdf"


# --------------------------------------------------------------------------- #
# Excel
# --------------------------------------------------------------------------- #

def _estilos_excel():
    return {
        'header_fill': PatternFill('solid', fgColor='1a237e'),
        'header_font': Font(color='FFFFFF', bold=True, size=14),
        'col_header_font': Font(color='FFFFFF', bold=True),
        'center': Alignment(horizontal='center', vertical='center'),
        'total_fill': PatternFill('solid', fgColor='e8f5e9'),
        'green_fill': PatternFill('solid', fgColor='2e7d32'),
        'amber_fill': PatternFill('solid', fgColor='b45309'),
        'gris_fill': PatternFill('solid', fgColor='455a64'),
        'bold': Font(bold=True),
    }


def _titulo_excel(ws, e, titulo, fecha_inicio, fecha_fin, columnas=8):
    from openpyxl.utils import get_column_letter
    ultimo = get_column_letter(columnas)
    ws.merge_cells(f'A1:{ultimo}1')
    ws['A1'] = titulo
    ws['A1'].font = e['header_font']
    ws['A1'].fill = e['header_fill']
    ws['A1'].alignment = e['center']

    ws.merge_cells(f'A2:{ultimo}2')
    ws['A2'] = f"Período: {fecha_inicio or 'inicio'} al {fecha_fin or 'hoy'}"
    ws['A2'].alignment = e['center']

    ws.merge_cells(f'A3:{ultimo}3')
    ws['A3'] = f"{TRAMITE} — Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws['A3'].alignment = e['center']
    ws.append([])


def _ancho_columnas(ws, anchos):
    for letra, ancho in anchos.items():
        ws.column_dimensions[letra].width = ancho


def generar_excel(tipo_pago_id=None, fecha_inicio=None, fecha_fin=None, todas=False):
    """Devuelve (bytes_xlsx, nombre_archivo) con el reporte de egresos por categoría."""
    reporte = construir_reporte(tipo_pago_id, fecha_inicio, fecha_fin, todas)
    if 'error' in reporte:
        return None, reporte['error']
    if 'tipos_pago' in reporte:
        return None, 'Se requiere tipo_pago_id'

    e = _estilos_excel()
    wb = Workbook()

    # --- Hoja 1: Resumen ---
    ws = wb.active
    ws.title = 'Resumen por Categoria' if todas else 'Resumen'
    _titulo_excel(ws, e, 'REPORTE DE EGRESOS POR CATEGORÍA' if todas
                  else f"REPORTE DE EGRESOS — {reporte['categoria']['nombre'].upper()}",
                  fecha_inicio, fecha_fin)

    if todas:
        resumen = reporte['resumen']
        ws.append(['INDICADOR', 'VALOR'])
        for celda in ws[5]:
            celda.fill = e['header_fill']
            celda.font = e['col_header_font']
            celda.alignment = e['center']

        indicadores = [
            ('Total de egresos (Bs)', float(resumen['total_egresos'])),
            ('Número de egresos', resumen['count_egresos']),
            ('Promedio por egreso (Bs)', float(resumen['promedio_egreso'])),
            ('Egreso más alto (Bs)', float(resumen['egreso_maximo'])),
            ('Pendientes de aprobación', resumen['count_pendientes_aprobacion']),
            ('Monto pendiente de aprobación (Bs)', float(resumen['total_pendientes_aprobacion'])),
            ('Egresos anulados', resumen['count_anulados']),
            ('Monto anulado (Bs)', float(resumen['total_anulados'])),
            ('Categorías con egresos', resumen['total_categorias']),
            ('Categorías de egreso registradas', resumen['total_categorias_registradas']),
        ]
        for etiqueta, valor in indicadores:
            ws.append([etiqueta, valor])
        _ancho_columnas(ws, {'A': 36, 'B': 22})
    else:
        r = reporte['resumen']
        g = reporte['resumen_global']
        ws.append(['INDICADOR', 'VALOR'])
        for celda in ws[5]:
            celda.fill = e['header_fill']
            celda.font = e['col_header_font']
            celda.alignment = e['center']

        filas = [
            ('Total de la categoría (Bs)', float(r['total_egresos'])),
            ('Número de egresos', r['count_egresos']),
            ('Promedio por egreso (Bs)', float(r['promedio_egreso'])),
            ('Egreso más alto (Bs)', float(r['egreso_maximo'])),
            ('Egreso más bajo (Bs)', float(r['egreso_minimo'])),
            ('Participación en el total general', f"{r['porcentaje_participacion']}%"),
            ('Primer egreso', r['fecha_primer_egreso'] or '-'),
            ('Último egreso', r['fecha_ultimo_egreso'] or '-'),
            ('Pendientes de aprobación', r['count_pendientes_aprobacion']),
            ('Monto pendiente de aprobación (Bs)', float(r['total_pendientes_aprobacion'])),
            ('Egresos anulados', r['count_anulados']),
            ('Monto anulado (Bs)', float(r['total_anulados'])),
            ('Total general de egresos (Bs)', float(g['total_egresos'])),
        ]
        for etiqueta, valor in filas:
            ws.append([etiqueta, valor])
        _ancho_columnas(ws, {'A': 36, 'B': 22})

    # --- Hoja 2: Desglose por categoría ---
    if todas:
        ws_cat = wb.create_sheet('Categorias')
        ws_cat.append(['Categoría', 'N° Egresos', 'Total (Bs)', '% Participación',
                       'Promedio (Bs)', 'Mayor Egreso (Bs)', 'Menor Egreso (Bs)',
                       'Pendientes', 'Monto Pendientes (Bs)', 'Anulados', 'Monto Anulado (Bs)'])
        for celda in ws_cat[1]:
            celda.fill = e['header_fill']
            celda.font = e['col_header_font']
            celda.alignment = e['center']

        total_general = reporte['resumen']['total_egresos']
        for r in reporte['categorias']:
            ws_cat.append([
                r['categoria']['nombre'],
                r['count_egresos'],
                float(r['total_egresos']),
                f"{r['porcentaje_participacion']}%",
                float(r['promedio_egreso']),
                float(r['egreso_maximo']),
                float(r['egreso_minimo']),
                r['count_pendientes_aprobacion'],
                float(r['total_pendientes_aprobacion']),
                r['count_anulados'],
                float(r['total_anulados']),
            ])

        fila_total = ws_cat.max_row + 1
        ws_cat.cell(row=fila_total, column=1, value='TOTAL GENERAL')
        ws_cat.cell(row=fila_total, column=3, value=float(total_general))
        for col in range(1, 12):
            ws_cat.cell(row=fila_total, column=col).font = e['bold']
            ws_cat.cell(row=fila_total, column=col).fill = e['total_fill']
        _ancho_columnas(ws_cat, {'A': 30, 'B': 12, 'C': 16, 'D': 14, 'E': 15, 'F': 18,
                                 'G': 18, 'H': 12, 'I': 20, 'J': 11, 'K': 18})
        ws_met = wb.create_sheet('Por Metodo de Pago')
        ws_met.append(['Método de Pago', 'N° Egresos', 'Total (Bs)', '% Participación'])
        for celda in ws_met[1]:
            celda.fill = e['gris_fill']
            celda.font = e['col_header_font']
            celda.alignment = e['center']
        for m in reporte['resumen']['por_metodo_pago']:
            pct = round(m['total'] / total_general * 100, 1) if total_general > 0 else 0
            ws_met.append([m['metodo_pago_label'], m['count'], float(m['total']), f"{pct}%"])
        _ancho_columnas(ws_met, {'A': 22, 'B': 12, 'C': 16, 'D': 15})

    # --- Hoja de detalle ---
    egresos = sorted(reporte['egresos'], key=lambda x: (x['fecha'], x['id']), reverse=True)
    ws_det = wb.create_sheet('Detalle de Egresos')
    ws_det.append(['#', 'Fecha', 'Categoría', 'Descripción', 'Método de Pago',
                   'Banco', 'Nro. Operación', 'Monto (Bs)', 'Estado'])
    for celda in ws_det[1]:
        celda.fill = e['green_fill']
        celda.font = e['col_header_font']
        celda.alignment = e['center']

    for i, egreso in enumerate(egresos, 1):
        ws_det.append([
            i,
            datetime.strptime(egreso['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y'),
            egreso['categoria'],
            egreso['descripcion'] or '',
            egreso['metodo_pago_label'],
            egreso['banco'] or '',
            egreso['nro_operacion'] or '',
            float(egreso['monto']),
            egreso['estado_label'],
        ])

    fila_total = ws_det.max_row + 1
    ws_det.cell(row=fila_total, column=1, value='TOTAL')
    ws_det.cell(row=fila_total, column=8, value=float(sum(x['monto'] for x in egresos)))
    for col in range(1, 10):
        ws_det.cell(row=fila_total, column=col).font = e['bold']
        ws_det.cell(row=fila_total, column=col).fill = e['total_fill']
    _ancho_columnas(ws_det, {'A': 6, 'B': 12, 'C': 26, 'D': 42, 'E': 16, 'F': 16, 'G': 16, 'H': 15, 'I': 22})

    # --- Hoja de revisión (pendientes / anulados) ---
    filas_revision = reporte.get('egresos_revision') or []
    if filas_revision:
        ws_rev = wb.create_sheet('Revision')
        ws_rev.append(['#', 'Fecha', 'Categoría', 'Descripción', 'Método de Pago',
                       'Monto (Bs)', 'Estado', 'Motivo'])
        for celda in ws_rev[1]:
            celda.fill = e['amber_fill']
            celda.font = e['col_header_font']
            celda.alignment = e['center']
        for i, r in enumerate(filas_revision, 1):
            ws_rev.append([
                i,
                datetime.strptime(r['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y'),
                r['categoria'],
                r['descripcion'] or '',
                r['metodo_pago_label'],
                float(r['monto']),
                r['estado_label'],
                r['motivo_anulacion'] or '',
            ])
        _ancho_columnas(ws_rev, {'A': 6, 'B': 12, 'C': 26, 'D': 42, 'E': 16, 'F': 15, 'G': 22, 'H': 40})

    buffer = io.BytesIO()
    wb.save(buffer)
    sufijo = 'todas_las_categorias' if todas else _slug(reporte['categoria']['nombre'])
    return buffer.getvalue(), f"egresos_{sufijo}_{datetime.now().strftime('%Y%m%d')}.xlsx"
