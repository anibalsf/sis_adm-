"""
Generación de documentos (PDF / Excel) para los reportes automáticos.

Toma la estructura produced por `ReportGenerator`:
    {titulo, subtitulo, kpis: [{etiqueta, valor, sufijo}], secciones: [{titulo, tabla}]}
y la renderiza sin depender de parsear el texto de WhatsApp.
"""
import logging
from io import BytesIO

from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

logger = logging.getLogger(__name__)

AZUL = colors.HexColor('#1e40af')
AZUL_CLARO = colors.HexColor('#eff6ff')
GRIS = colors.HexColor('#64748b')
BORDE = colors.HexColor('#cbd5e1')
VERDE = colors.HexColor('#047857')


def _estilos():
    base = getSampleStyleSheet()
    return {
        'titulo': ParagraphStyle(
            'titulo', parent=base['Title'], fontSize=18, leading=22,
            textColor=AZUL, spaceAfter=2,
        ),
        'subtitulo': ParagraphStyle(
            'subtitulo', parent=base['Normal'], fontSize=10, leading=13,
            textColor=GRIS, alignment=TA_CENTER, spaceAfter=14,
        ),
        'seccion': ParagraphStyle(
            'seccion', parent=base['Heading2'], fontSize=12, leading=15,
            textColor=colors.HexColor('#0f172a'), spaceBefore=14, spaceAfter=6,
        ),
        'kpi_label': ParagraphStyle(
            'kpi_label', parent=base['Normal'], fontSize=7.5, leading=9,
            textColor=GRIS, alignment=TA_CENTER,
        ),
        'kpi_valor': ParagraphStyle(
            'kpi_valor', parent=base['Normal'], fontSize=12, leading=14,
            textColor=colors.HexColor('#0f172a'), alignment=TA_CENTER,
        ),
        'celda': ParagraphStyle(
            'celda', parent=base['Normal'], fontSize=8, leading=10, alignment=TA_LEFT,
        ),
        'pie': ParagraphStyle(
            'pie', parent=base['Normal'], fontSize=7.5, leading=9,
            textColor=GRIS, alignment=TA_CENTER,
        ),
    }


def _tabla_kpis(kpis, estilos):
    """Tarjetas de KPIs en una grilla de 4 columnas."""
    if not kpis:
        return None
    cols = 4
    filas = []
    for i in range(0, len(kpis), cols):
        fila = []
        for kpi in kpis[i:i + cols]:
            valor = f"{kpi.get('valor', '')}{kpi.get('sufijo') or ''}"
            fila.append(
                Paragraph(
                    f'<b>{_esc(valor)}</b><br/>{_esc(kpi.get("etiqueta", ""))}',
                    estilos['kpi_valor'],
                )
            )
        # completa la última fila para que la grilla quede rectangular
        while len(fila) < cols:
            fila.append('')
        filas.append(fila)

    ancho = (A4[0] - 4 * cm) / cols
    tabla = Table(filas, colWidths=[ancho] * cols)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_CLARO),
        ('BOX', (0, 0), (-1, -1), 0.6, BORDE),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return tabla


def _tabla_datos(seccion, estilos):
    tabla = seccion.get('tabla')
    if not tabla or not tabla.get('filas'):
        return None

    columnas = tabla.get('columnas') or []
    filas = tabla['filas']
    # Normaliza anchos de columna según la longitud del encabezado
    n = len(columnas) or (len(filas[0]) if filas else 0)
    if not n:
        return None

    # Ajuste de anchos: 2.6cm para la primera columna, resto se reparte
    if len(columnas) and len(columnas) <= 4:
        anchos = [6.4 * cm] + [(A4[0] - 4 * cm - 6.4 * cm) / (n - 1)] * (n - 1)
    else:
        anchos = [(A4[0] - 4 * cm) / n] * n

    datos = [columnas] + filas
    tabla_pdf = Table(datos, colWidths=anchos, repeatRows=1)
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDE),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return tabla_pdf


def generar_pdf(datos, titulo_archivo='reporte'):
    """Devuelve los bytes de un PDF A4 con el reporte."""
    estilos = _estilos()
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=1.6 * cm,
        title=datos.get('titulo', 'Reporte'),
        author='Sindicato Mixto Taipiplaya',
    )

    story = [
        Paragraph(_esc(datos.get('titulo', 'Reporte')), estilos['titulo']),
        Paragraph(_esc(datos.get('subtitulo', '')), estilos['subtitulo']),
    ]

    kpis = _tabla_kpis(datos.get('kpis'), estilos)
    if kpis:
        story += [kpis, Spacer(1, 10)]

    for seccion in datos.get('secciones', []):
        bloque = []
        if seccion.get('titulo'):
            bloque.append(Paragraph(_esc(seccion['titulo']), estilos['seccion']))
        tabla = _tabla_datos(seccion, estilos)
        if tabla is not None:
            bloque.append(tabla)
        if not bloque:
            continue
        # Un título solo no puede partirse: se mantiene junto al contenido.
        if len(bloque) == 1:
            story.append(KeepTogether(bloque))
        else:
            # El título no se separa de la tabla, pero una tabla larga sí puede
            # empezar en la página siguiente (KeepTogether la dejaría en blanco).
            story.extend([KeepTogether([bloque[0]]), *bloque[1:]])

    generado = timezone.localtime().strftime('%d/%m/%Y %H:%M')
    story += [
        Spacer(1, 16),
        Paragraph(
            f"Generado automáticamente el {generado} - {_PIE}",
            estilos['pie'],
        ),
    ]

    doc.build(story)
    return buffer.getvalue()


_PIE = 'Sindicato Mixto Taipiplaya'


def _esc(texto):
    """Escapa el texto antes de pasarlo a Paragraph (reportlab usa XML)."""
    from xml.sax.saxutils import escape
    return escape(str(texto or ''))


def guardar_adjuntos(datos, tipo, fecha_periodo, formatos=('pdf',), sufijo=''):
    """
    Genera y persiste los adjuntos en MEDIA_ROOT/reportes_auto/<año>/<mes>/.
    Devuelve la lista de dicts {nombre, ruta, url, mime, peso}.

    `url` es absoluta solo si hay MEDIA_BASE_URL configurada; sin ella Twilio
    no puede descargar el archivo y el envío cae a texto plano.
    """
    import os

    from django.conf import settings

    guardados = []
    ahora = timezone.now()
    subdir = os.path.join('reportes_auto', str(ahora.year), f'{ahora.month:02d}')
    destino_dir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(destino_dir, exist_ok=True)

    base = f"{tipo}_{fecha_periodo.strftime('%Y%m%d')}{sufijo}"

    if 'pdf' in formatos:
        nombre = f'{base}.pdf'
        contenido = generar_pdf(datos)
        with open(os.path.join(destino_dir, nombre), 'wb') as fh:
            fh.write(contenido)
        guardados.append(_registro(subdir, nombre, len(contenido), 'application/pdf'))

    if 'excel' in formatos:
        nombre = f'{base}.xlsx'
        contenido = generar_excel(datos)
        with open(os.path.join(destino_dir, nombre), 'wb') as fh:
            fh.write(contenido)
        guardados.append(_registro(
            subdir, nombre, len(contenido),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ))

    return guardados


def _registro(subdir, nombre, peso, mime):
    from django.conf import settings

    relativa = f'{subdir}/{nombre}'.replace('\\', '/')
    url_relativa = f"{settings.MEDIA_URL.rstrip('/')}/{relativa}"
    base_publica = getattr(settings, 'MEDIA_BASE_URL', '') or ''
    return {
        'nombre': nombre,
        'ruta': relativa,
        # Twilio exige una URL absoluta y accesible desde internet.
        'url': f"{base_publica}{url_relativa}" if base_publica else url_relativa,
        'mime': mime,
        'peso': peso,
    }


def generar_excel(datos):
    """Devuelve los bytes de un XLSX con KPIs y tablas."""
    wb = Workbook()

    # --- Hoja resumen
    ws = wb.active
    ws.title = 'Resumen'
    ws['A1'] = datos.get('titulo', 'Reporte')
    ws['A1'].font = Font(size=16, bold=True, color='1E40AF')
    ws.merge_cells('A1:C1')

    ws['A2'] = datos.get('subtitulo', '')
    ws['A2'].font = Font(size=10, color='64748B')
    ws.merge_cells('A2:C2')

    fila = 4
    ws.cell(row=fila, column=1, value='Indicador').font = Font(bold=True, color='FFFFFF')
    ws.cell(row=fila, column=2, value='Valor').font = Font(bold=True, color='FFFFFF')
    ws.cell(row=fila, column=3, value='Unidad').font = Font(bold=True, color='FFFFFF')
    for col in range(1, 4):
        ws.cell(row=fila, column=col).fill = PatternFill('solid', fgColor='1E40AF')

    for kpi in datos.get('kpis', []):
        fila += 1
        ws.cell(row=fila, column=1, value=kpi.get('etiqueta', ''))
        ws.cell(row=fila, column=2, value=kpi.get('valor', ''))
        ws.cell(row=fila, column=3, value=str(kpi.get('sufijo') or '').strip())

    ws.column_dimensions['A'].width = 32
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 10

    # --- Una hoja por sección con tabla
    borde = Border(*[Side(style='thin', color='CBD5E1')] * 4)

    for idx, seccion in enumerate(datos.get('secciones', []), start=1):
        tabla = seccion.get('tabla')
        if not tabla or not tabla.get('filas'):
            continue
        columnas = tabla.get('columnas') or []
        filas = tabla['filas']

        hoja = wb.create_sheet(
            title=(seccion.get('titulo') or f'Seccion {idx}')[:31]
        )
        hoja['A1'] = seccion.get('titulo', '')
        hoja['A1'].font = Font(size=12, bold=True, color='0F172A')

        for c, encabezado in enumerate(columnas, start=1):
            celda = hoja.cell(row=3, column=c, value=encabezado)
            celda.font = Font(bold=True, color='FFFFFF')
            celda.fill = PatternFill('solid', fgColor='1E40AF')
            celda.alignment = Alignment(horizontal='center', vertical='center')
            celda.border = borde
            ancho = max(len(str(encabezado)) + 4, 14)
            hoja.column_dimensions[get_column_letter(c)].width = min(ancho, 40)

        for r, fila_datos in enumerate(filas, start=4):
            for c, valor in enumerate(fila_datos, start=1):
                celda = hoja.cell(row=r, column=c, value=valor)
                celda.border = borde
                if r % 2 == 0:
                    celda.fill = PatternFill('solid', fgColor='F8FAFC')
            # ensancha la columna con el dato más largo
            for c in range(1, len(columnas) + 1):
                largo = max(
                    [len(str(columnas[c - 1]))]
                    + [len(str(f[c - 1])) for f in filas if len(f) >= c]
                )
                actual = hoja.column_dimensions[get_column_letter(c)].width or 14
                hoja.column_dimensions[get_column_letter(c)].width = min(max(actual, largo + 4), 40)

        hoja.freeze_panes = 'A4'

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
