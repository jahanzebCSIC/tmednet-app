"""
Genera la guía del Excel de MHW — contexto, metodología y diccionario de datos.
Sin conclusiones ni interpretación de resultados.
"""
import io, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, Image, KeepTogether)
from reportlab.platypus.flowables import Flowable

W, H = A4
MARGIN = 2.1 * cm

# ── Paleta ────────────────────────────────────────────────────────────────────
NAVY    = colors.HexColor('#1A3A5C')
TEAL    = colors.HexColor('#1A7A96')
TEAL_BG = colors.HexColor('#EBF6FA')
WHITE   = colors.white
GREY_BG = colors.HexColor('#F6F9FB')
RULE    = colors.HexColor('#CDDDE8')
INK     = colors.HexColor('#1C2B38')
SOFT    = colors.HexColor('#4A6A7E')
FAINT   = colors.HexColor('#8AAABB')

PLOT_BG   = '#F6F9FB'
PLOT_GRID = '#CDDDE8'
FONT_C    = '#4A6A7E'

usable_w = W - 2 * MARGIN

# ── Estilos ───────────────────────────────────────────────────────────────────
def make_styles():
    s = {}
    s['label']    = ParagraphStyle('lb', fontSize=8, fontName='Helvetica-Bold',
                                   textColor=TEAL, leading=10, spaceAfter=4, charSpace=1.5)
    s['title']    = ParagraphStyle('ti', fontSize=21, fontName='Helvetica-Bold',
                                   textColor=NAVY, leading=26, spaceAfter=6)
    s['subtitle'] = ParagraphStyle('su', fontSize=10.5, fontName='Helvetica-Oblique',
                                   textColor=SOFT, leading=15, spaceAfter=10)
    s['abstract'] = ParagraphStyle('ab', fontSize=9.5, fontName='Helvetica-Oblique',
                                   textColor=SOFT, leading=14, alignment=TA_JUSTIFY,
                                   leftIndent=10, rightIndent=10, spaceAfter=4)
    s['h2']       = ParagraphStyle('h2', fontSize=11.5, fontName='Helvetica-Bold',
                                   textColor=NAVY, leading=14, spaceBefore=18, spaceAfter=8)
    s['h3']       = ParagraphStyle('h3', fontSize=8, fontName='Helvetica-Bold',
                                   textColor=TEAL, leading=11, spaceBefore=14, spaceAfter=6,
                                   charSpace=1.2)
    s['h4']       = ParagraphStyle('h4', fontSize=9.5, fontName='Helvetica-Bold',
                                   textColor=NAVY, leading=13, spaceBefore=10, spaceAfter=4)
    s['body']     = ParagraphStyle('bo', fontSize=9.5, fontName='Helvetica',
                                   textColor=INK, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
    s['caption']  = ParagraphStyle('ca', fontSize=7.5, fontName='Helvetica-Oblique',
                                   textColor=FAINT, leading=10, alignment=TA_CENTER, spaceAfter=6)
    s['col_name'] = ParagraphStyle('cn', fontSize=9, fontName='Helvetica-Bold',
                                   textColor=NAVY, leading=12)
    s['col_type'] = ParagraphStyle('ct', fontSize=7.5, fontName='Helvetica-Oblique',
                                   textColor=FAINT, leading=10)
    s['col_desc'] = ParagraphStyle('cd', fontSize=9, fontName='Helvetica',
                                   textColor=INK, leading=13)
    s['col_val']  = ParagraphStyle('cv', fontSize=8.5, fontName='Helvetica',
                                   textColor=SOFT, leading=12)
    s['ref']      = ParagraphStyle('re', fontSize=8, fontName='Helvetica', textColor=SOFT,
                                   leading=11, leftIndent=12, firstLineIndent=-12, spaceAfter=5)
    s['sheet_tag']= ParagraphStyle('st', fontSize=9.5, fontName='Helvetica-Bold',
                                   textColor=WHITE, leading=13)
    return s

ST = make_styles()

# ── Flowables ─────────────────────────────────────────────────────────────────
class ThinLine(Flowable):
    def __init__(self, w, color=RULE, t=0.6):
        super().__init__(); self.w = w; self.color = color; self.t = t
    def draw(self):
        self.canv.setStrokeColor(self.color); self.canv.setLineWidth(self.t)
        self.canv.line(0, 0, self.w, 0)
    def wrap(self, *a): return self.w, self.t + 2

class NavyStripe(Flowable):
    def __init__(self, w, h=3, color=NAVY):
        super().__init__(); self.w = w; self.h = h; self.color = color
    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.w, self.h, fill=1, stroke=0)
    def wrap(self, *a): return self.w, self.h

class SheetBadge(Flowable):
    """Etiqueta de hoja con fondo de color."""
    def __init__(self, text, color=NAVY, width=None):
        super().__init__()
        self.text  = text
        self.color = color
        self.w     = width or usable_w
        self.h     = 26

    def wrap(self, *a): return self.w, self.h

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.roundRect(0, 0, self.w, self.h, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 9.5)
        c.drawString(10, 8, self.text)

class ProcCards(Flowable):
    """4 tarjetas de proceso con badge numérico."""
    def __init__(self, steps, width):
        super().__init__()
        self.steps = steps
        self.width = width
        self.gap   = 6
        self.col_w = (width - 3 * self.gap) / 4
        self.h     = 96

    def wrap(self, *a): return self.width, self.h

    def draw(self):
        c   = self.canv
        n   = len(self.steps)
        r   = 11
        px  = 10

        for i, (num, title, desc) in enumerate(self.steps):
            x = i * (self.col_w + self.gap)
            c.setFillColor(GREY_BG); c.setStrokeColor(RULE); c.setLineWidth(0.5)
            c.roundRect(x, 0, self.col_w, self.h, 4, fill=1, stroke=1)

            bx = x + r + px
            by = self.h - r - 10
            c.setFillColor(NAVY); c.circle(bx, by, r, fill=1, stroke=0)
            c.setFillColor(WHITE); c.setFont('Helvetica-Bold', 10)
            c.drawCentredString(bx, by - 3.5, num)

            title_y = by - r - 14
            c.setFillColor(NAVY); c.setFont('Helvetica-Bold', 8.5)
            c.drawString(x + px, title_y, title)

            desc_y = title_y - 14
            c.setFillColor(SOFT); c.setFont('Helvetica', 7.8)
            words = desc.split()
            line, lines = '', []
            for w in words:
                test = (line + ' ' + w).strip()
                if c.stringWidth(test, 'Helvetica', 7.8) < self.col_w - px * 2:
                    line = test
                else:
                    if line: lines.append(line)
                    line = w
            if line: lines.append(line)
            for j, ln in enumerate(lines[:3]):
                c.drawString(x + px, desc_y - j * 11, ln)

            if i < n - 1:
                ax = x + self.col_w + self.gap / 2
                ay = self.h / 2
                c.setStrokeColor(FAINT); c.setLineWidth(1.2)
                c.line(ax - 2, ay, ax + 1, ay)

class CatCards(Flowable):
    """4 tarjetas de categoría con borde superior de color."""
    def __init__(self, width):
        super().__init__(); self.width = width; self.h = 80

    def wrap(self, *a): return self.width, self.h

    def draw(self):
        c = self.canv
        cats = [
            ('#C87820', 'CAT. 1', 'Moderada',
             'SST > p90 hasta\n2× la anomalía umbral'),
            ('#2176AE', 'CAT. 2', 'Fuerte',
             'Anomalía entre\n2–3× el umbral p90'),
            ('#B83030', 'CAT. 3', 'Severa',
             'Anomalía entre\n3–4× el umbral p90'),
            ('#6040A0', 'CAT. 4', 'Extrema',
             'Anomalía superior\na 4× el umbral p90'),
        ]
        gap = 7
        cw  = (self.width - 3 * gap) / 4
        for i, (col, num, name, desc) in enumerate(cats):
            x = i * (cw + gap)
            c.setFillColor(colors.HexColor('#F6F9FB'))
            c.setStrokeColor(colors.HexColor('#CDDDE8')); c.setLineWidth(0.5)
            c.roundRect(x, 0, cw, self.h, 3, fill=1, stroke=1)
            c.setFillColor(colors.HexColor(col))
            c.roundRect(x, self.h - 5, cw, 5, 2, fill=1, stroke=0)
            c.rect(x, self.h - 8, cw, 5, fill=1, stroke=0)
            c.setFillColor(colors.HexColor('#8AAABB')); c.setFont('Helvetica-Bold', 7)
            c.drawString(x + 8, self.h - 18, num)
            c.setFillColor(colors.HexColor('#1C2B38')); c.setFont('Helvetica-Bold', 10)
            c.drawString(x + 8, self.h - 30, name)
            c.setFillColor(colors.HexColor('#4A6A7E')); c.setFont('Helvetica', 8)
            for j, ln in enumerate(desc.split('\n')):
                c.drawString(x + 8, self.h - 44 - j * 12, ln)

# ── Gráfica conceptual MHW ────────────────────────────────────────────────────
def chart_concept():
    N = 122
    def clim(i): return 23.8 + 4.0 * np.sin(np.pi * (i - 8) / 104)
    def thr(i):  return clim(i) + 1.7 + 0.25 * np.sin(np.pi * i / 122)
    def sst(i):
        b = clim(i)
        a = 0.5 * np.sin(np.pi * i / 122 * 2 + 0.4)
        if 36 <= i <= 76: a += 3.0 * np.exp(-((i - 56) ** 2) / 280)
        if 86 <= i <= 97: a += 1.9 * np.exp(-((i - 91) ** 2) / 36)
        a += 0.22 * (np.sin(i * 7.1) + np.sin(i * 3.9) * 0.5)
        return b + a

    x  = np.arange(N)
    SS = np.array([sst(i)  for i in range(N)])
    TH = np.array([thr(i)  for i in range(N)])
    CL = np.array([clim(i) for i in range(N)])

    fig, ax = plt.subplots(figsize=(13, 3.2))
    fig.patch.set_facecolor(PLOT_BG); ax.set_facecolor(PLOT_BG)
    ax.fill_between(x, TH, SS, where=SS > TH, color='#1A7A96', alpha=0.18, interpolate=True)
    ax.plot(x, CL, color='#AABFCC', linewidth=1.1, linestyle='--', label='Climatología media')
    ax.plot(x, TH, color='#1A7A96', linewidth=1.6, linestyle='-.', label='Umbral p90')
    ax.plot(x, SS, color='#1A3A5C', linewidth=2.0, label='SST diaria')
    ax.annotate('Episodio MHW (~37 días)',
                xy=(56, SS[56]), xytext=(56 - 5, SS[56] + 0.8),
                ha='center', fontsize=8, color='#1A7A96', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#1A7A96', lw=1))
    months = [('Jun', 0), ('Jul', 30), ('Ago', 61), ('Sep', 92)]
    ax.set_xticks([d for _, d in months])
    ax.set_xticklabels([l for l, _ in months], fontsize=8.5, color=FONT_C)
    ax.tick_params(axis='y', labelsize=8, colors=FONT_C)
    ax.set_ylabel('SST (°C)', fontsize=8.5, color=FONT_C)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color(PLOT_GRID)
    ax.yaxis.grid(True, color=PLOT_GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False, loc='lower right', labelcolor=FONT_C)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=160, bbox_inches='tight', facecolor=PLOT_BG)
    plt.close(fig); buf.seek(0)
    return buf

# ── Pie de página (sin cabecera) ─────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFillColor(colors.HexColor('#8AAABB'))
        canvas.setFont('Helvetica', 7)
        canvas.drawCentredString(W / 2, 0.7 * cm, str(doc.page))
    canvas.restoreState()

# ── Helpers ───────────────────────────────────────────────────────────────────
def col_row(name, type_str, description, values=''):
    """Fila para la tabla de diccionario de columnas."""
    name_p   = Paragraph(name,        ST['col_name'])
    type_p   = Paragraph(type_str,    ST['col_type'])
    desc_p   = Paragraph(description, ST['col_desc'])
    vals_p   = Paragraph(values,      ST['col_val']) if values else Paragraph('', ST['col_val'])
    return [[name_p, type_p], [desc_p, vals_p]]

def col_table(rows_data, col_widths=None):
    """Construye la tabla de diccionario con filas alternadas."""
    if col_widths is None:
        col_widths = [usable_w * 0.26, usable_w * 0.74]

    tbl_rows = []
    # Cabecera
    tbl_rows.append([
        Paragraph('COLUMNA / TIPO', ParagraphStyle('ch', fontSize=7.5, fontName='Helvetica-Bold',
                                                    textColor=TEAL, charSpace=0.8, leading=10)),
        Paragraph('DESCRIPCIÓN · VALORES POSIBLES', ParagraphStyle('dh', fontSize=7.5,
                                                                     fontName='Helvetica-Bold',
                                                                     textColor=TEAL, charSpace=0.8, leading=10)),
    ])

    style_cmds = [
        ('LINEBELOW',     (0, 0), (-1, 0), 1.2, TEAL),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]

    for i, (name, type_str, desc, vals) in enumerate(rows_data):
        bg = GREY_BG if i % 2 == 0 else WHITE
        left_cell  = [Paragraph(f'<b>{name}</b>', ST['col_name']),
                      Paragraph(type_str, ST['col_type'])]
        right_cell_parts = [Paragraph(desc, ST['col_desc'])]
        if vals:
            right_cell_parts.append(Paragraph(vals, ST['col_val']))
        right_cell = right_cell_parts

        row_idx = i + 1
        tbl_rows.append([left_cell, right_cell])
        style_cmds += [
            ('BACKGROUND',    (0, row_idx), (-1, row_idx), bg),
            ('LINEBELOW',     (0, row_idx), (-1, row_idx), 0.4, RULE),
        ]

    tbl = Table(tbl_rows, colWidths=col_widths)
    tbl.setStyle(TableStyle(style_cmds))
    return tbl

# ── Helper: agrupa título + regla + primer bloque ─────────────────────────────
def sec(heading_text, style, *first_flowables):
    """Keeps section heading together with its first content block."""
    return KeepTogether([Paragraph(heading_text, style), ThinLine(usable_w),
                         Spacer(1, 0.15 * cm)] + list(first_flowables))

def subsec(heading_text, *first_flowables):
    """Keeps h3 label together with its first paragraph."""
    return KeepTogether([Paragraph(heading_text, ST['h3'])] + list(first_flowables))

# ── Documento ─────────────────────────────────────────────────────────────────
OUT = r'c:\tmednet-app\MHW_Guia_Excel.pdf'
doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=MARGIN, rightMargin=MARGIN,
                        topMargin=1.4 * cm, bottomMargin=1.6 * cm,
                        title='Guía del fichero Excel MHW', author='T-MEDNet')
story = []

# ══════════════════════════════════════════════════════════════════════════════
# PORTADA / CABECERA
# ══════════════════════════════════════════════════════════════════════════════
story.append(Spacer(1, 0.3 * cm))
story.append(ThinLine(usable_w, TEAL, 1.5))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph('T-MEDNET · GUÍA DE DATOS', ST['label']))
story.append(Paragraph(
    'Guía del fichero Excel de resultados:<br/>Olas de Calor Marinas y Mortalidad Masiva',
    ST['title']))
story.append(Paragraph(
    'Descripción del contexto científico, la metodología de obtención de datos '
    'y el significado detallado de cada hoja y columna del fichero de resultados '
    '<i>mortality_mhw_results.xlsx</i>',
    ST['subtitle']))
story.append(ThinLine(usable_w))
story.append(Spacer(1, 0.4 * cm))
story.append(Paragraph(
    'Este documento acompaña al fichero Excel entregado con los resultados del '
    'análisis de Olas de Calor Marinas (MHW) para las localizaciones de mortalidad '
    'masiva documentadas en el Mediterráneo. Su propósito es explicar de dónde '
    'provienen los datos, cómo se calculan, y qué significa cada campo del fichero, '
    'de modo que cualquier persona del grupo pueda interpretar correctamente los '
    'valores sin necesidad de acceder al código fuente.',
    ST['abstract']))
story.append(Spacer(1, 0.3 * cm))

# ══════════════════════════════════════════════════════════════════════════════
# 1. CONTEXTO: QUÉ ES UNA OLA DE CALOR MARINA
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('1. ¿Qué es una Ola de Calor Marina?', ST['h2']))
story.append(ThinLine(usable_w))
story.append(Spacer(1, 0.15 * cm))
story.append(Paragraph(
    'Una <b>Ola de Calor Marina (MHW, <i>Marine Heat Wave</i>)</b> es un período '
    'prolongado en que la temperatura superficial del mar (SST) supera de forma '
    'anómala los valores esperados para esa época del año. A diferencia de las '
    'fluctuaciones diarias normales, una MHW representa un evento extremo sostenido '
    'que puede tener consecuencias graves sobre los ecosistemas marinos.',
    ST['body']))
story.append(Paragraph(
    'La definición estándar, propuesta por <b>Hobday et al. (2016)</b>, establece '
    'tres condiciones que deben cumplirse simultáneamente:',
    ST['body']))

cond_data = [
    ['Duración mínima', '≥ 5 días consecutivos por encima del umbral'],
    ['Umbral térmico',  'Percentil 90 de la climatología local (p90)'],
    ['Climatología',    'Calculada para cada día del año con datos del período 1993–2016'],
]
cond_tbl = Table(cond_data, colWidths=[usable_w * 0.28, usable_w * 0.72])
cond_tbl.setStyle(TableStyle([
    ('BACKGROUND',    (0, 0), (0, -1), GREY_BG),
    ('BACKGROUND',    (1, 0), (1, -1), WHITE),
    ('BOX',           (0, 0), (-1, -1), 0.5, RULE),
    ('INNERGRID',     (0, 0), (-1, -1), 0.4, RULE),
    ('TOPPADDING',    (0, 0), (-1, -1), 7),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ('LEFTPADDING',   (0, 0), (-1, -1), 10),
    ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTSIZE',      (0, 0), (-1, -1), 9),
    ('TEXTCOLOR',     (0, 0), (0, -1), NAVY),
    ('TEXTCOLOR',     (1, 0), (1, -1), INK),
    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(cond_tbl)
story.append(Spacer(1, 0.2 * cm))

story.append(Paragraph(
    'El <b>percentil 90 (p90)</b> actúa como umbral dinámico: se calcula para cada '
    'día del año aplicando una ventana móvil de ±15 días, lo que produce un valor '
    'estacional suavizado que refleja las variaciones naturales a lo largo del año. '
    'El resultado es un umbral que en invierno es más bajo (cuando la SST media '
    'es más baja) y en verano es más alto, siguiendo el ciclo anual.',
    ST['body']))

# Gráfica conceptual
buf = chart_concept()
img = Image(buf, width=usable_w, height=usable_w * 3.2 / 13)
story.append(img)
story.append(Paragraph(
    'Figura 1. Representación esquemática de la detección de MHW. '
    'La línea azul oscura es la SST diaria; la línea teal discontinua, el umbral p90 climatológico. '
    'La zona sombreada corresponde al período MHW (SST > p90 durante ≥5 días). '
    'La línea gris indica la climatología media (promedio histórico).',
    ST['caption']))
story.append(Spacer(1, 0.15 * cm))

# Categorías
story.append(subsec('CATEGORÍAS DE INTENSIDAD (HOBDAY ET AL. 2018)',
    Paragraph(
        'Dentro de cada MHW, la intensidad se clasifica en cuatro categorías según '
        'cuántas veces supera el umbral p90 la anomalía observada. Se usa la diferencia '
        'entre p90 y la mediana climatológica (p50) como referencia de escala '
        '(<i>delta climatológico</i>).',
        ST['body'])))
story.append(CatCards(usable_w))
story.append(Spacer(1, 0.35 * cm))

# ══════════════════════════════════════════════════════════════════════════════
# 2. DATOS DE TEMPERATURA SATELITAL
# ══════════════════════════════════════════════════════════════════════════════
story.append(sec('2. Fuente de datos: temperatura satelital', ST['h2'],
    Paragraph(
        'Los datos de temperatura superficial del mar provienen del '
        '<b>Copernicus Marine Service (CMEMS)</b>, el programa europeo de observación '
        'oceánica que integra información de múltiples satélites y la distribuye '
        'libremente de forma estandarizada.',
        ST['body'])))
story.append(subsec('PRODUCTO UTILIZADO'))

prod_data = [
    ['Nombre del producto',   'Mediterranean Sea SST L4 Reprocessed Observations'],
    ['Identificador',         'cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021'],
    ['Cobertura geográfica',  'Mediterráneo completo (26°N–48°N, 6°W–37°E)'],
    ['Resolución espacial',   '0,05° (~5 km por celda)'],
    ['Resolución temporal',   'Diaria'],
    ['Cobertura temporal',    '1 de enero de 1982 – presente'],
    ['Nivel de procesamiento','L4 (fusión de sensores, sin huecos en la cobertura)'],
    ['Tipo de dato',          'Reprocessed (serie histórica homogénea y corregida)'],
]
prod_tbl = Table(prod_data, colWidths=[usable_w * 0.32, usable_w * 0.68])
prod_tbl.setStyle(TableStyle([
    ('BACKGROUND',    (0, 0), (0, -1), GREY_BG),
    ('BACKGROUND',    (1, 0), (1, -1), WHITE),
    ('ROWBACKGROUNDS',(0, 0), (-1, -1), [GREY_BG, WHITE]),
    ('BOX',           (0, 0), (-1, -1), 0.5, RULE),
    ('LINEBELOW',     (0, 0), (-1, -2), 0.4, RULE),
    ('TOPPADDING',    (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('LEFTPADDING',   (0, 0), (-1, -1), 10),
    ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTSIZE',      (0, 0), (-1, -1), 9),
    ('TEXTCOLOR',     (0, 0), (0, -1), NAVY),
    ('TEXTCOLOR',     (1, 0), (1, -1), INK),
    ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
]))
story.append(prod_tbl)
story.append(Spacer(1, 0.2 * cm))

story.append(Paragraph(
    'El nivel <b>L4</b> garantiza que todos los días tienen cobertura completa '
    'sobre el Mediterráneo, combinando datos de sensores infrarrojos (AVHRR, MODIS, '
    'SEVIRI, SLSTR) mediante interpolación óptima. El carácter <b>Reprocessed</b> '
    'significa que toda la serie histórica se ha tratado con los mismos algoritmos '
    'y correcciones, lo que garantiza la comparabilidad entre los años 1982 y 2026 '
    'sin artefactos de cambio instrumental.',
    ST['body']))

story.append(subsec('CORRESPONDENCIA COORDENADAS → CELDA',
    Paragraph(
        'El producto CMEMS tiene una rejilla regular de 0,05° de resolución. '
        'Las coordenadas de cada localización de mortalidad se redondean al nodo '
        'más cercano de esta rejilla antes de descargar los datos. '
        'El redondeo se hace con la fórmula:',
        ST['body'])))

formula_tbl = Table(
    [[Paragraph('<b>lat_grid</b> = round(lat / 0.05) × 0.05',
                ParagraphStyle('fm', fontSize=9, fontName='Helvetica',
                               textColor=NAVY, leading=13, alignment=TA_CENTER)),
      Paragraph('<b>lon_grid</b> = round(lon / 0.05) × 0.05',
                ParagraphStyle('fm2', fontSize=9, fontName='Helvetica',
                               textColor=NAVY, leading=13, alignment=TA_CENTER))]],
    colWidths=[usable_w / 2, usable_w / 2])
formula_tbl.setStyle(TableStyle([
    ('BACKGROUND',    (0, 0), (-1, -1), TEAL_BG),
    ('BOX',           (0, 0), (-1, -1), 0.8, TEAL),
    ('INNERGRID',     (0, 0), (-1, -1), 0.4, RULE),
    ('TOPPADDING',    (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(formula_tbl)
story.append(Spacer(1, 0.15 * cm))
story.append(Paragraph(
    'Gracias a este redondeo, varios puntos de mortalidad cercanos pueden compartir '
    'la misma celda de descarga. La serie SST se descarga y calcula una sola vez '
    'por celda y luego se reutiliza para todos los eventos de esa celda, '
    'reduciendo el tiempo de proceso.',
    ST['body']))

# ══════════════════════════════════════════════════════════════════════════════
# 3. PROCESO DE ANÁLISIS
# ══════════════════════════════════════════════════════════════════════════════
steps = [
    ('01', 'Lectura del inventario',
     'Coordenadas y año(s) de cada evento de mortalidad documentado.'),
    ('02', 'Descarga SST 1982–2026',
     'Serie diaria para cada celda de la rejilla. Se almacena en caché local.'),
    ('03', 'Detección MHW',
     'Climatología p90 + algoritmo Hobday sobre la serie histórica completa.'),
    ('04', 'Extracción estival',
     'Estadísticas de junio–septiembre del año de mortalidad concreto.'),
]
story.append(KeepTogether([
    Paragraph('3. Proceso de análisis', ST['h2']),
    ThinLine(usable_w),
    Spacer(1, 0.2 * cm),
    ProcCards(steps, usable_w),
]))
story.append(Spacer(1, 0.25 * cm))
story.append(Paragraph(
    'El análisis se ejecuta de forma automática mediante Python, utilizando el '
    'módulo <i>marineHeatWaves</i> (implementación de referencia de Hobday et al. '
    '2016). Para cada localización, se trabaja siempre con la serie SST completa '
    '(1982–2026) para calcular la climatología y el umbral p90. Posteriormente, '
    'se extraen solo los eventos MHW que se solapan con el período junio–septiembre '
    'del año de mortalidad específico.',
    ST['body']))
story.append(Paragraph(
    'El <b>período estival de análisis (junio–septiembre)</b> se escoge porque '
    'en el Mediterráneo las temperaturas máximas se alcanzan entre julio y agosto, '
    'y los eventos de mortalidad masiva bentónica documentados se asocian '
    'consistentemente con el calentamiento de verano.',
    ST['body']))

# ══════════════════════════════════════════════════════════════════════════════
# 4. ESTRUCTURA DEL FICHERO EXCEL
# ══════════════════════════════════════════════════════════════════════════════
story.append(sec('4. Estructura del fichero Excel', ST['h2'],
    Paragraph(
        'El fichero <b>mortality_mhw_results.xlsx</b> contiene tres hojas. '
        'Cada hoja tiene un propósito distinto: la hoja principal incluye todos los '
        'eventos individualmente, mientras que las dos hojas de resumen agregan '
        'la información por país y por año respectivamente.',
        ST['body'])))

sheets_data = [
    ['MHW_Mortality',      'Hoja principal', 'Un registro por evento de mortalidad (localización × año)'],
    ['Summary_by_Country', 'Resumen por país', 'Agregado estadístico por país (solo eventos con MHW)'],
    ['Summary_by_Year',    'Resumen por año',  'Agregado estadístico por año (solo eventos con MHW)'],
]
sheets_tbl = Table(sheets_data, colWidths=[usable_w * 0.28, usable_w * 0.22, usable_w * 0.50])
sheets_tbl.setStyle(TableStyle([
    ('ROWBACKGROUNDS',  (0, 0), (-1, -1), [TEAL_BG, GREY_BG, WHITE]),
    ('BOX',             (0, 0), (-1, -1), 0.5, RULE),
    ('LINEBELOW',       (0, 0), (-1, -2), 0.4, RULE),
    ('TOPPADDING',      (0, 0), (-1, -1), 7),
    ('BOTTOMPADDING',   (0, 0), (-1, -1), 7),
    ('LEFTPADDING',     (0, 0), (-1, -1), 10),
    ('RIGHTPADDING',    (0, 0), (-1, -1), 10),
    ('FONTNAME',        (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTSIZE',        (0, 0), (-1, -1), 9),
    ('TEXTCOLOR',       (0, 0), (0, -1), TEAL),
    ('TEXTCOLOR',       (1, 0), (1, -1), NAVY),
    ('TEXTCOLOR',       (2, 0), (2, -1), INK),
    ('VALIGN',          (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(sheets_tbl)
story.append(Spacer(1, 0.3 * cm))

# ══════════════════════════════════════════════════════════════════════════════
# 4.1 Hoja MHW_Mortality
# ══════════════════════════════════════════════════════════════════════════════
story.append(KeepTogether([SheetBadge('📋  Hoja 1: MHW_Mortality — Datos individuales por evento', NAVY)]))
story.append(Spacer(1, 0.15 * cm))
story.append(Paragraph(
    'Esta es la hoja principal del fichero. Contiene una fila por cada combinación '
    'única de localización × año de mortalidad. Si una localización tiene varios '
    'años documentados, aparece tantas veces como años tenga registrados.',
    ST['body']))
story.append(Spacer(1, 0.1 * cm))

story.append(subsec('BLOQUE 1 — IDENTIFICACIÓN DEL EVENTO'))
cols_id = [
    ('Country',   'Texto',
     'País donde se ubica la localización de mortalidad.',
     'Ejemplos: Spain, France, Italy, Greece, Croatia…'),
    ('Location',  'Texto',
     'Nombre del sitio o localización donde se documentó la mortalidad.',
     'Ejemplos: Marseille, Banyuls-sur-Mer, Cap de Creus, Medes…'),
    ('Latitude',  'Decimal (°N)',
     'Latitud geográfica original del evento, tal como aparece en el inventario de partida.',
     'Rango en el Mediterráneo: ~30°N – 46°N'),
    ('Longitude', 'Decimal (°E)',
     'Longitud geográfica original del evento, tal como aparece en el inventario de partida.',
     'Rango: ~-6°E (Estrecho de Gibraltar) a 37°E (Levante)'),
    ('Year',      'Entero (año)',
     'Año del evento de mortalidad documentado. Una localización puede tener más de un año si la mortalidad se registró en diferentes años.',
     'Rango del dataset: 1985–2026'),
]
story.append(col_table(cols_id))
story.append(Spacer(1, 0.2 * cm))

story.append(subsec('BLOQUE 2 — DATOS DE LA REJILLA Y SERIE SST'))
cols_grid = [
    ('Lat_grid',  'Decimal (°N)',
     'Latitud redondeada al nodo más cercano de la rejilla CMEMS (resolución 0,05°). '
     'Es la latitud efectiva que se usa para descargar y extraer los datos de temperatura.',
     'Puede diferir ligeramente de Latitude (diferencia ≤ 0,025°)'),
    ('Lon_grid',  'Decimal (°E)',
     'Longitud redondeada al nodo más cercano de la rejilla CMEMS (resolución 0,05°). '
     'Ídem para la longitud.',
     'Puede diferir ligeramente de Longitude'),
    ('Data_available', 'Y / N',
     '<b>Y</b>: se obtuvieron datos SST válidos para esta celda de la rejilla.<br/>'
     '<b>N</b>: no fue posible obtener datos (por ejemplo, el píxel más cercano cae '
     'sobre tierra o en una zona sin cobertura suficiente del satélite).',
     'Si Data_available = N, todos los campos de MHW estarán vacíos.'),
    ('SST_start', 'Fecha (AAAA-MM-DD)',
     'Primera fecha disponible en la serie histórica SST descargada para esta celda.',
     'Generalmente 1982-01-01 para todo el Mediterráneo'),
    ('SST_end',   'Fecha (AAAA-MM-DD)',
     'Última fecha disponible en la serie histórica SST. Refleja hasta dónde llega '
     'la descarga en el momento del análisis.',
     'Puede ser inferior a 2026-09-04 para datos muy recientes aún no publicados'),
]
story.append(col_table(cols_grid))
story.append(Spacer(1, 0.2 * cm))

story.append(subsec('BLOQUE 3 — DETECCIÓN DE MHW ESTIVAL',
    Paragraph(
        'Los campos de este bloque describen si se detectó una MHW durante '
        '<b>junio–septiembre del año de mortalidad</b> y, en caso afirmativo, '
        'sus características. Solo se consideran los episodios MHW que se '
        'solapan (total o parcialmente) con ese período estival.',
        ST['body'])))
cols_mhw = [
    ('MHW_detected', 'Y / N / N/A',
     '<b>Y</b>: se detectó al menos un episodio MHW durante junio–septiembre del año.<br/>'
     '<b>N</b>: no se detectó ningún episodio MHW en ese período (la SST no superó '
     'el umbral p90 de forma sostenida).<br/>'
     '<b>N/A</b>: no hay datos SST disponibles para esta celda, o el año de mortalidad '
     'queda fuera del rango temporal de la serie.',
     ''),
    ('N_events',     'Entero',
     'Número de episodios MHW distintos que se solapan con el período estival '
     '(junio–septiembre) del año de mortalidad. Un verano puede tener más de un '
     'episodio si hay varios picos de calor separados por períodos de descenso.',
     '0 si MHW_detected = N. Vacío si N/A.'),
    ('Total_days',   'Entero (días)',
     'Suma total de días dentro de episodios MHW durante junio–septiembre del año. '
     'Si un episodio comienza antes de junio o termina después de septiembre, '
     'solo se cuentan los días dentro de ese rango.',
     '0 si MHW_detected = N. Vacío si N/A.'),
    ('Max_intensity','Decimal (°C)',
     'Anomalía térmica máxima registrada en alguno de los episodios MHW del verano. '
     'Se calcula como la diferencia entre la SST observada y el umbral p90 '
     'en el día de mayor anomalía.',
     'Valores típicos en el Mediterráneo: 0,5–6 °C. Vacío si no hay MHW.'),
    ('Cum_intensity','Decimal (°C·días)',
     'Intensidad cumulativa: suma de las anomalías diarias sobre el umbral p90 '
     'a lo largo de todos los días de los episodios MHW del verano. '
     'Refleja la <i>dosis térmica</i> total acumulada durante la temporada.',
     'Depende de la duración y la intensidad. Vacío si no hay MHW.'),
    ('Mean_intensity','Decimal (°C)',
     'Intensidad media: promedio de la anomalía diaria sobre el umbral p90 '
     'durante los días de MHW. Permite comparar eventos de distinta duración '
     'en términos de intensidad media.',
     'Vacío si no hay MHW.'),
]
story.append(col_table(cols_mhw))
story.append(Spacer(1, 0.2 * cm))

story.append(subsec('BLOQUE 4 — CATEGORÍA DEL EPISODIO MÁS INTENSO'))
cols_cat = [
    ('Max_category', 'Entero (1–4)',
     'Categoría numérica del episodio MHW más intenso detectado durante el verano, '
     'según la clasificación de Hobday et al. (2018). Se asigna en función de '
     'cuántas veces supera la anomalía al delta climatológico (diferencia p90–p50):',
     '1 = Moderada · 2 = Fuerte · 3 = Severa · 4 = Extrema · Vacío si no hay MHW'),
    ('Max_cat_name', 'Texto',
     'Nombre en inglés de la categoría máxima. Corresponde directamente al valor '
     'numérico de Max_category.',
     'Moderate · Strong · Severe · Extreme · (vacío si no hay MHW)'),
]
story.append(col_table(cols_cat))
story.append(Spacer(1, 0.25 * cm))

# ══════════════════════════════════════════════════════════════════════════════
# 4.2 Hoja Summary_by_Country
# ══════════════════════════════════════════════════════════════════════════════
story.append(KeepTogether([
    SheetBadge('🌍  Hoja 2: Summary_by_Country — Resumen por país',
               colors.HexColor('#1A5C3A')),
    Spacer(1, 0.15 * cm),
    Paragraph(
        'Agrega los eventos de la hoja principal por país. <b>Solo incluye los eventos '
        'en que se detectó MHW</b> (MHW_detected = Y). Los eventos sin datos o sin MHW '
        'no participan en el cálculo de medias, aunque sí en el recuento total si '
        'el grupo de investigación lo necesita.',
        ST['body']),
    Spacer(1, 0.1 * cm),
]))

cols_country = [
    ('Country',                 'Texto',
     'Nombre del país, igual que en la hoja principal.',
     ''),
    ('Locations',               'Entero',
     'Número de localizaciones únicas dentro del país que tienen al menos un evento '
     'con MHW detectada.',
     ''),
    ('Events_with_MHW',         'Entero',
     'Total de eventos (localización × año) en ese país en los que se detectó MHW '
     'durante el verano. Es la suma de filas con MHW_detected = Y para ese país.',
     ''),
    ('Avg_max_intensity',       'Decimal (°C)',
     'Media de Max_intensity sobre todos los eventos con MHW del país. '
     'Indica cuán intensa ha sido la anomalía máxima de forma promedio.',
     ''),
    ('Avg_total_days',          'Decimal (días)',
     'Media de Total_days sobre todos los eventos con MHW del país. '
     'Indica la duración media de la exposición térmica estival.',
     ''),
    ('Max_category_observed',   'Entero (1–4)',
     'Categoría MHW más alta observada en algún evento del país. '
     'Refleja el nivel de extremo más severo registrado históricamente.',
     '1 = Moderada · 2 = Fuerte · 3 = Severa · 4 = Extrema'),
]
story.append(col_table(cols_country))
story.append(Spacer(1, 0.25 * cm))

# ══════════════════════════════════════════════════════════════════════════════
# 4.3 Hoja Summary_by_Year
# ══════════════════════════════════════════════════════════════════════════════
story.append(KeepTogether([
    SheetBadge('📅  Hoja 3: Summary_by_Year — Resumen por año',
               colors.HexColor('#6040A0')),
    Spacer(1, 0.15 * cm),
    Paragraph(
        'Agrega los eventos de la hoja principal por año. <b>Solo incluye los eventos '
        'en que se detectó MHW</b> (MHW_detected = Y). Permite analizar '
        'la evolución temporal de la frecuencia e intensidad de las MHWs en los años '
        'con mortalidad documentada.',
        ST['body']),
    Spacer(1, 0.1 * cm),
]))

cols_year = [
    ('Year',                    'Entero (año)',
     'Año del evento de mortalidad, igual que en la hoja principal.',
     ''),
    ('N_locations',             'Entero',
     'Número de eventos (localización × año) en ese año en los que se detectó MHW. '
     'Un año con muchas localizaciones afectadas indica una MHW de gran extensión geográfica.',
     ''),
    ('Avg_max_intensity',       'Decimal (°C)',
     'Media de Max_intensity sobre todos los eventos con MHW de ese año. '
     'Indica cuán intensa fue la anomalía máxima de forma promedio en ese verano.',
     ''),
    ('Avg_total_days',          'Decimal (días)',
     'Media de Total_days sobre todos los eventos con MHW de ese año. '
     'Indica la duración media de la exposición térmica estival en ese año.',
     ''),
    ('Max_category_observed',   'Entero (1–4)',
     'Categoría MHW más alta observada en algún evento de ese año. '
     'Refleja la severidad máxima del verano en términos de temperatura.',
     '1 = Moderada · 2 = Fuerte · 3 = Severa · 4 = Extrema'),
]
story.append(col_table(cols_year))
story.append(Spacer(1, 0.3 * cm))

# ══════════════════════════════════════════════════════════════════════════════
# 5. GUÍA DE LECTURA E INTERPRETACIÓN DE LOS CAMPOS
# ══════════════════════════════════════════════════════════════════════════════
story.append(sec('5. Guía de lectura de los campos', ST['h2']))
story.append(subsec('CASOS ESPECIALES Y VALORES VACÍOS'))

cases = [
    ('Data_available = N',
     'La celda de la rejilla no tiene datos SST válidos (píxel terrestre o zona '
     'sin cobertura). Todos los campos MHW estarán vacíos para ese evento. '
     'Esto ocurre principalmente en localizaciones muy costeras o en áreas con '
     'interferencia terrestre en el satélite.'),
    ('MHW_detected = N/A',
     'Hay dos situaciones posibles: (1) no hay datos SST — igual que Data_available = N —, '
     'o (2) el año de mortalidad queda fuera del rango temporal de la serie SST '
     '(antes de 1982 o después del último dato disponible). '
     'En ambos casos los campos numéricos estarán vacíos.'),
    ('MHW_detected = N,<br/>campos numéricos en 0 o vacíos',
     'La SST no superó el umbral p90 durante ≥5 días consecutivos en '
     'junio–septiembre de ese año. No se detectó MHW. '
     'N_events = 0 y Total_days = 0. Los campos de intensidad y categoría '
     'están vacíos porque no hay episodio que describir.'),
    ('N_events > 1',
     'El verano tuvo más de un episodio MHW separado. Los campos de intensidad '
     'reflejan el valor del episodio más intenso (Max_intensity, Max_category), '
     'o la suma/media de todos (Total_days, Cum_intensity, Mean_intensity).'),
    ('SST_end anterior al año de mortalidad',
     'Los datos del satélite solo llegan hasta una fecha anterior al año analizado. '
     'Puede ocurrir con años muy recientes (2025, 2026) si el dataset '
     'reprocessed aún no ha incorporado esos datos. En este caso MHW_detected '
     'aparece como N/A (fuera de rango).'),
]
for title, desc in cases:
    tbl = Table(
        [[Paragraph(title, ParagraphStyle('ct2', fontSize=8.5, fontName='Helvetica-Bold',
                                           textColor=TEAL, leading=12)),
          Paragraph(desc, ST['body'])]],
        colWidths=[usable_w * 0.30, usable_w * 0.70])
    tbl.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (0, -1), 0),
        ('LEFTPADDING',   (1, 0), (1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.4, RULE),
    ]))
    story.append(tbl)
story.append(Spacer(1, 0.25 * cm))

story.append(subsec('DIFERENCIA ENTRE Max_intensity Y Mean_intensity',
    Paragraph(
        '<b>Max_intensity</b> recoge el pico puntual: el día en que la SST fue más alta '
        'respecto al umbral p90. <b>Mean_intensity</b> es el promedio de las anomalías '
        'durante todos los días MHW del verano. Un evento breve pero muy intenso tendrá '
        'Max_intensity alto y Mean_intensity próximo a él; un evento largo con un pico '
        'moderado tendrá Max_intensity más alto que Mean_intensity. '
        '<b>Cum_intensity</b> combina ambas dimensiones (intensidad × duración) '
        'y es útil como proxy de la exposición térmica total.',
        ST['body'])))

story.append(subsec('DIFERENCIA ENTRE Latitude/Longitude Y Lat_grid/Lon_grid',
    Paragraph(
        'Las columnas <b>Latitude</b> y <b>Longitude</b> son las coordenadas originales '
        'del inventario de mortalidad. Las columnas <b>Lat_grid</b> y <b>Lon_grid</b> '
        'son las coordenadas de la celda de la rejilla satelital que se usó realmente '
        'para la descarga. La diferencia máxima es de 0,025° (~2,5 km), generalmente '
        'irrelevante para el análisis oceánico pero que conviene tener en cuenta en '
        'zonas con alta heterogeneidad costera.',
        ST['body'])))

# ══════════════════════════════════════════════════════════════════════════════
# 6. CONSIDERACIONES TÉCNICAS
# ══════════════════════════════════════════════════════════════════════════════
story.append(sec('6. Consideraciones técnicas', ST['h2']))
lims = [
    ('<b>SST de superficie vs. temperatura en profundidad.</b> El satélite mide la temperatura '
     'en los primeros metros (~0–1 m). Los organismos bentónicos viven a mayor profundidad y '
     'pueden experimentar anomalías distintas, con un desfase temporal respecto a la superficie. '
     'Los datos satelitales son una aproximación del estrés térmico, no una medida directa '
     'de la temperatura en el fondo.'),
    ('<b>Resolución espacial de ~5 km.</b> En zonas con alta variabilidad costera o fondos '
     'complejos, el píxel de la rejilla puede no representar fielmente las condiciones exactas '
     'del punto de mortalidad. Esto es especialmente relevante en fiordos, canales estrechos '
     'o zonas con corrientes locales fuertes.'),
    ('<b>Período de referencia climatológica 1993–2016.</b> El umbral p90 se calcula sobre '
     'este período estándar. Si el calentamiento de las últimas décadas ha desplazado '
     'significativamente la SST media, el umbral puede infraestimar la anomalía percibida '
     'en años muy recientes (2022–2026). Esta es una limitación conocida del método estándar.'),
    ('<b>Datos de 2025–2026 potencialmente incompletos.</b> El producto Reprocessed de '
     'CMEMS tiene un retardo de varios meses respecto al tiempo real. Los resultados para '
     'años muy recientes pueden ser parciales o no estar disponibles en el momento del análisis.'),
    ('<b>Decisión de solapamiento temporal.</b> Si un episodio MHW comienza en mayo y '
     'termina en julio, solo se cuentan los días dentro de junio–septiembre. '
     'Las métricas de intensidad (Max_intensity, Max_cat_name) corresponden '
     'al episodio completo, no solo a la fracción estival.'),
]
for l in lims:
    story.append(Paragraph(f'· {l}',
                            ParagraphStyle('lim', fontSize=9, fontName='Helvetica',
                                           textColor=SOFT, leading=13, leftIndent=10,
                                           spaceAfter=8)))
story.append(Spacer(1, 0.2 * cm))

# ══════════════════════════════════════════════════════════════════════════════
# 7. REFERENCIAS
# ══════════════════════════════════════════════════════════════════════════════
story.append(KeepTogether([Paragraph('Referencias', ST['h2']), ThinLine(usable_w)]))
story.append(Spacer(1, 0.1 * cm))
refs = [
    'Hobday, A.J., et al. (2016). A hierarchical approach to defining marine heatwaves. '
    '<i>Progress in Oceanography</i>, 141, 227–238.',
    'Hobday, A.J., et al. (2018). Categorizing and naming marine heatwaves. '
    '<i>Oceanography</i>, 31(2), 162–173.',
    'Copernicus Marine Service (2024). <i>Mediterranean Sea SST L4 Reprocessed '
    'Observations (cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021)</i>. '
    'https://doi.org/10.48670/moi-00172',
    'Garrabou, J., et al. (2009). Mass mortality in Northwestern Mediterranean rocky '
    'benthic communities: effects of the 2003 heat wave. '
    '<i>Global Change Biology</i>, 15(5), 1090–1103.',
    'Oliver, E.C.J., et al. (2018). Longer and more frequent marine heatwaves over '
    'the past century. <i>Nature Communications</i>, 9, 1324.',
]
for r in refs:
    story.append(Paragraph(r, ST['ref']))

# ── Build ─────────────────────────────────────────────────────────────────────
print('Generando PDF guía...')
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f'Guardado: {OUT}')
