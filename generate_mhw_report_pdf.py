"""
Genera el informe PDF de MHW — tema claro, diseño visual.
"""
import io, os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, Image, KeepTogether)
from reportlab.platypus.flowables import Flowable

W, H = A4
MARGIN = 2.1 * cm

# ── Paleta clara ──────────────────────────────────────────────────────────────
NAVY    = colors.HexColor('#1A3A5C')
TEAL    = colors.HexColor('#1A7A96')
TEAL_BG = colors.HexColor('#EBF6FA')
TEAL_MID= colors.HexColor('#C5E4EE')
WHITE   = colors.white
GREY_BG = colors.HexColor('#F6F9FB')
RULE    = colors.HexColor('#CDDDE8')
INK     = colors.HexColor('#1C2B38')
SOFT    = colors.HexColor('#4A6A7E')
FAINT   = colors.HexColor('#8AAABB')
CAT1_C  = colors.HexColor('#C87820')
CAT2_C  = colors.HexColor('#2176AE')
CAT3_C  = colors.HexColor('#B83030')
CAT4_C  = colors.HexColor('#6040A0')

# ── Datos ─────────────────────────────────────────────────────────────────────
df      = pd.read_excel(r'c:\tmednet-app\mortality_mhw_results.xlsx', sheet_name='MHW_Mortality')
df_y    = df[df['MHW_detected'] == 'Y']
df_n    = df[df['MHW_detected'] == 'N']
total   = len(df)
n_mhw   = len(df_y); n_no    = len(df_n); n_nd = total - n_mhw - n_no
pct     = n_mhw / (n_mhw + n_no) * 100
avg_int = df_y['Max_intensity'].mean(); avg_days = df_y['Total_days'].mean()
n_mod   = (df_y['Max_cat_name']=='Moderate').sum()
n_str   = (df_y['Max_cat_name']=='Strong').sum()
n_sev   = (df_y['Max_cat_name']=='Severe').sum()

by_year = df[df['MHW_detected'].isin(['Y','N'])].groupby('Year').apply(
    lambda x: pd.Series({'n_mhw':(x['MHW_detected']=='Y').sum(),'total':len(x),
        'avg_int':x.loc[x['MHW_detected']=='Y','Max_intensity'].mean(),
        'avg_days':x.loc[x['MHW_detected']=='Y','Total_days'].mean()})).reset_index()
by_year['pct'] = by_year['n_mhw'] / by_year['total'] * 100

by_country = df[df['MHW_detected'].isin(['Y','N'])].groupby('Country').apply(
    lambda x: pd.Series({'n_mhw':(x['MHW_detected']=='Y').sum(),'total':len(x),
        'pct':(x['MHW_detected']=='Y').sum()/len(x)*100})).reset_index()
by_country = by_country[by_country['total']>=3].sort_values('pct',ascending=False)

# ── Estilos ───────────────────────────────────────────────────────────────────
def S():
    s = {}
    s['doc_label'] = ParagraphStyle('dl', fontSize=8, fontName='Helvetica-Bold',
                                     textColor=TEAL, leading=10, spaceAfter=4,
                                     charSpace=1.5)
    s['title'] = ParagraphStyle('ti', fontSize=21, fontName='Helvetica-Bold',
                                 textColor=NAVY, leading=26, spaceAfter=6)
    s['subtitle'] = ParagraphStyle('su', fontSize=10.5, fontName='Helvetica-Oblique',
                                    textColor=SOFT, leading=15, spaceAfter=10)
    s['abstract'] = ParagraphStyle('ab', fontSize=9.5, fontName='Helvetica-Oblique',
                                    textColor=SOFT, leading=14, alignment=TA_JUSTIFY,
                                    leftIndent=10, rightIndent=10, spaceAfter=4)
    s['h2'] = ParagraphStyle('h2', fontSize=11.5, fontName='Helvetica-Bold',
                              textColor=NAVY, leading=14, spaceBefore=18, spaceAfter=8)
    s['h3'] = ParagraphStyle('h3', fontSize=8, fontName='Helvetica-Bold',
                              textColor=TEAL, leading=11, spaceBefore=12, spaceAfter=5,
                              charSpace=1.2)
    s['body'] = ParagraphStyle('bo', fontSize=9.5, fontName='Helvetica',
                                textColor=INK, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
    s['small'] = ParagraphStyle('sm', fontSize=8.5, fontName='Helvetica',
                                 textColor=SOFT, leading=12, alignment=TA_JUSTIFY)
    s['caption'] = ParagraphStyle('ca', fontSize=7.5, fontName='Helvetica-Oblique',
                                   textColor=FAINT, leading=10, alignment=TA_CENTER, spaceAfter=6)
    s['stat_n'] = ParagraphStyle('sn', fontSize=24, fontName='Helvetica-Bold',
                                  textColor=TEAL, leading=26)
    s['stat_l'] = ParagraphStyle('sl', fontSize=7.5, fontName='Helvetica',
                                  textColor=FAINT, leading=10, charSpace=0.8)
    s['ref'] = ParagraphStyle('re', fontSize=8, fontName='Helvetica', textColor=SOFT,
                               leading=11, leftIndent=12, firstLineIndent=-12, spaceAfter=5)
    s['conc'] = ParagraphStyle('co', fontSize=9.5, fontName='Helvetica', textColor=INK,
                                leading=14, alignment=TA_JUSTIFY, leftIndent=12, spaceAfter=8)
    s['lim'] = ParagraphStyle('li', fontSize=9, fontName='Helvetica', textColor=SOFT,
                               leading=13, leftIndent=12, spaceAfter=5)
    s['proc_num'] = ParagraphStyle('pn', fontSize=13, fontName='Helvetica-Bold',
                                    textColor=WHITE, leading=16, alignment=TA_CENTER)
    s['proc_t'] = ParagraphStyle('pt', fontSize=8.5, fontName='Helvetica-Bold',
                                  textColor=NAVY, leading=11, spaceAfter=3)
    s['proc_d'] = ParagraphStyle('pd', fontSize=8, fontName='Helvetica',
                                  textColor=SOFT, leading=11)
    s['cat_n'] = ParagraphStyle('cn', fontSize=7.5, fontName='Helvetica-Bold',
                                  textColor=FAINT, leading=9, charSpace=0.8)
    s['cat_t'] = ParagraphStyle('ct', fontSize=10, fontName='Helvetica-Bold',
                                  textColor=INK, leading=12, spaceAfter=3)
    s['cat_d'] = ParagraphStyle('cd', fontSize=8, fontName='Helvetica',
                                  textColor=SOFT, leading=11)
    return s

ST = S()
usable_w = W - 2*MARGIN

# ── Flowables custom ──────────────────────────────────────────────────────────
class ThinLine(Flowable):
    def __init__(self, w, color=RULE, thickness=0.6):
        super().__init__(); self.w=w; self.color=color; self.t=thickness
    def draw(self):
        self.canv.setStrokeColor(self.color); self.canv.setLineWidth(self.t)
        self.canv.line(0,0,self.w,0)
    def wrap(self,*a): return self.w, self.t+2

class NavyTop(Flowable):
    """Franja de color encima de un bloque."""
    def __init__(self, w, h=3, color=NAVY):
        super().__init__(); self.w=w; self.h=h; self.color=color
    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0,0,self.w,self.h,fill=1,stroke=0)
    def wrap(self,*a): return self.w, self.h

# ── Gráficas ──────────────────────────────────────────────────────────────────
PLOT_BG = '#F6F9FB'
PLOT_GRID = '#CDDDE8'
FONT_C  = '#4A6A7E'

def chart_years():
    yr = by_year[by_year['total']>=3].sort_values('Year')
    fig, ax = plt.subplots(figsize=(13,3.6)); fig.patch.set_facecolor(PLOT_BG); ax.set_facecolor(PLOT_BG)
    x = np.arange(len(yr))
    ax.bar(x, yr['n_mhw'],                      color='#1A7A96', alpha=0.82, width=0.62, label='Con MHW')
    ax.bar(x, yr['total']-yr['n_mhw'], bottom=yr['n_mhw'], color='#CDDDE8', width=0.62, label='Sin MHW')
    ax.set_xticks(x); ax.set_xticklabels(yr['Year'].values, rotation=45, ha='right', fontsize=7.5, color=FONT_C)
    ax.tick_params(axis='y', labelsize=7.5, colors=FONT_C); ax.set_ylabel('N.º eventos', fontsize=8.5, color=FONT_C)
    ax.spines[['top','right','left']].set_visible(False); ax.spines['bottom'].set_color(PLOT_GRID)
    ax.yaxis.grid(True, color=PLOT_GRID, linewidth=0.6); ax.set_axisbelow(True)
    for yr_k, lbl in [(2003,'2003'),(2017,'2017'),(2024,'2024')]:
        mask = yr['Year']==yr_k
        if mask.any():
            xi = np.where(yr['Year'].values==yr_k)[0][0]
            ax.annotate(lbl, xy=(xi, yr[mask]['total'].values[0]+0.25),
                        ha='center', fontsize=7.5, color='#1A3A5C', fontweight='bold')
    ax.legend(fontsize=8, frameon=False, loc='upper left', labelcolor=FONT_C)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=160, bbox_inches='tight', facecolor=PLOT_BG)
    plt.close(fig); buf.seek(0); return buf

def chart_intensity():
    yr = by_year[by_year['n_mhw']>=5].sort_values('Year')
    fig, ax = plt.subplots(figsize=(13,3.4)); fig.patch.set_facecolor(PLOT_BG); ax.set_facecolor(PLOT_BG)
    x = np.arange(len(yr))
    sc = ax.scatter(x, yr['avg_int'], c=yr['avg_int'], cmap='YlOrRd',
                    s=yr['avg_days']*2.8+18, alpha=0.85, edgecolors='white',
                    linewidths=0.8, zorder=3, vmin=1.5, vmax=5.5)
    ax.plot(x, yr['avg_int'], color='#8AAABB', linewidth=1.2, zorder=2)
    ax.set_xticks(x); ax.set_xticklabels(yr['Year'].values, rotation=45, ha='right', fontsize=7.5, color=FONT_C)
    ax.tick_params(axis='y', labelsize=7.5, colors=FONT_C); ax.set_ylabel('Anomalía (°C)', fontsize=8.5, color=FONT_C)
    ax.spines[['top','right','left']].set_visible(False); ax.spines['bottom'].set_color(PLOT_GRID)
    ax.yaxis.grid(True, color=PLOT_GRID, linewidth=0.6); ax.set_axisbelow(True)
    for sz, lbl in [(18,'8 días'),(90,'28 días'),(190,'63 días')]:
        ax.scatter([],[], s=sz, color='#8AAABB', alpha=0.65, label=lbl)
    ax.legend(title='Duración media', title_fontsize=7, fontsize=7.5, frameon=False, loc='upper left', labelcolor=FONT_C)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=160, bbox_inches='tight', facecolor=PLOT_BG)
    plt.close(fig); buf.seek(0); return buf

def chart_country():
    bc = by_country.copy()
    fig, ax = plt.subplots(figsize=(13,3.0)); fig.patch.set_facecolor(PLOT_BG); ax.set_facecolor(PLOT_BG)
    x = np.arange(len(bc))
    bar_colors = ['#1A7A96' if p>=70 else '#6BAFC4' if p>=50 else '#CDDDE8' for p in bc['pct']]
    ax.bar(x, bc['pct'], color=bar_colors, width=0.55)
    ax.axhline(pct, color='#B83030', linewidth=1.1, linestyle='--', alpha=0.75)
    ax.text(len(x)-0.4, pct+2, f'Media {pct:.0f}%', fontsize=7.5, color='#B83030', ha='right')
    ax.set_xticks(x); ax.set_xticklabels(bc['Country'].values, rotation=32, ha='right', fontsize=8.5, color='#1C2B38')
    ax.set_ylabel('% con MHW', fontsize=8.5, color=FONT_C); ax.set_ylim(0,112)
    ax.tick_params(axis='y', labelsize=7.5, colors=FONT_C)
    ax.spines[['top','right','left']].set_visible(False); ax.spines['bottom'].set_color(PLOT_GRID)
    ax.yaxis.grid(True, color=PLOT_GRID, linewidth=0.6); ax.set_axisbelow(True)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=160, bbox_inches='tight', facecolor=PLOT_BG)
    plt.close(fig); buf.seek(0); return buf

# ── Cabecera de página ────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    # Header — texto gris, sin barra de color
    canvas.setStrokeColor(colors.HexColor('#CDDDE8')); canvas.setLineWidth(0.5)
    canvas.line(MARGIN, H-0.9*cm, W-MARGIN, H-0.9*cm)
    canvas.setFillColor(colors.HexColor('#8AAABB')); canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(MARGIN, H-0.65*cm, 'T-MEDNet')
    canvas.setFont('Helvetica', 7)
    canvas.drawString(MARGIN+1.3*cm, H-0.65*cm, '— Olas de Calor Marinas · Mortalidad masiva Mediterráneo')
    canvas.drawRightString(W-MARGIN, H-0.65*cm, 'Septiembre 2026')
    # Footer — número de página
    if doc.page > 1:
        canvas.setFillColor(colors.HexColor('#8AAABB')); canvas.setFont('Helvetica', 7)
        canvas.drawCentredString(W/2, 0.7*cm, str(doc.page))
    canvas.restoreState()

# ── Documento ─────────────────────────────────────────────────────────────────
OUT = r'c:\tmednet-app\MHW_Mortalidad_Mediterraneo.pdf'
doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                        topMargin=1.9*cm, bottomMargin=1.8*cm,
                        title='MHW Mortalidad Mediterráneo', author='T-MEDNet')
story = []

# ── CABECERA DOCUMENTO ────────────────────────────────────────────────────────
story.append(Spacer(1, 0.3*cm))
story.append(ThinLine(usable_w, TEAL, 1.5))
story.append(Spacer(1, 0.45*cm))
story.append(Paragraph('T-MEDNET · NOTA TÉCNICA', ST['doc_label']))
story.append(Paragraph(
    'Evaluación de Olas de Calor Marinas en localizaciones<br/>de mortalidad masiva del Mediterráneo',
    ST['title']))
story.append(Paragraph(
    'Análisis de temperatura superficial del mar mediante datos satelitales históricos '
    '(Copernicus Marine Service, 1982–2026) y detección de eventos extremos '
    'según el estándar Hobday et al. (2016)',
    ST['subtitle']))
story.append(ThinLine(usable_w, RULE))
story.append(Spacer(1, 0.4*cm))

# Estadísticas — 4 celdas sin fondo oscuro
def stat_cell(num, label):
    return [Paragraph(num, ST['stat_n']), Paragraph(label.upper(), ST['stat_l'])]

stat_tbl = Table(
    [[Paragraph('753', ST['stat_n']),
      Paragraph('304', ST['stat_n']),
      Paragraph('15', ST['stat_n']),
      Paragraph('1982–2026', ParagraphStyle('s2', fontSize=18, fontName='Helvetica-Bold',
                                             textColor=TEAL, leading=22))],
     [Paragraph('EVENTOS ANALIZADOS', ST['stat_l']),
      Paragraph('LOCALIZACIONES', ST['stat_l']),
      Paragraph('PAÍSES', ST['stat_l']),
      Paragraph('COBERTURA TEMPORAL', ST['stat_l'])]],
    colWidths=[usable_w/4]*4)
stat_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), GREY_BG),
    ('BOX',        (0,0), (-1,-1), 0.5, RULE),
    ('INNERGRID',  (0,0), (-1,-1), 0.5, RULE),
    ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
    ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,-1), 10),
    ('BOTTOMPADDING',(0,0),(-1,-1), 8),
]))
story.append(stat_tbl)
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph(
    'Este informe presenta los resultados del análisis de Olas de Calor Marinas (MHW) '
    'para 753 eventos de mortalidad masiva de organismos bentónicos documentados en '
    'el Mediterráneo entre 1985 y 2026. Para cada evento se descargó la serie diaria '
    'de temperatura superficial del mar (SST) desde satélite y se detectaron los '
    'episodios MHW presentes durante el período estival (junio–septiembre) del año '
    'de mortalidad correspondiente.', ST['abstract']))
story.append(Spacer(1, 0.3*cm))

# ── 1. DATOS ──────────────────────────────────────────────────────────────────
story.append(Paragraph('1. Fuente de datos', ST['h2']))
story.append(ThinLine(usable_w))
story.append(Spacer(1, 0.15*cm))
story.append(Paragraph(
    'Los datos de temperatura proceden del <b>Copernicus Marine Service (CMEMS)</b>, '
    'el programa europeo de observación del océano por satélite. Se utiliza el producto '
    '<i>Mediterranean SST L4 Reprocessed</i> '
    '(<b>cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021</b>), '
    'con resolución espacial de 0,05° (~5 km) y cobertura temporal diaria desde 1982.',
    ST['body']))
story.append(Paragraph(
    'El nivel <b>L4</b> garantiza cobertura completa sin huecos (fusión de sensores '
    'AVHRR, MODIS, SEVIRI, SLSTR). El carácter <b>Reprocessed</b> asegura la '
    'homogeneidad temporal de toda la serie histórica, condición indispensable '
    'para el cálculo riguroso de climatologías y umbrales de percentil.',
    ST['body']))

# ── 2. METODOLOGÍA ────────────────────────────────────────────────────────────
story.append(Paragraph('2. Metodología', ST['h2']))
story.append(ThinLine(usable_w))
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph('PROCESO DE ANÁLISIS', ST['h3']))

# Pasos — estilo visual con número en círculo azul
steps = [
    ('01', 'Coordenadas y años', 'Lectura del inventario de mortalidad: localización, lat/lon y año(s) documentados.'),
    ('02', 'Descarga SST 1982–2026', 'Serie diaria de temperatura completa para cada celda de la rejilla (~5 km).'),
    ('03', 'Detección MHW', 'Climatología p90 y algoritmo Hobday sobre la serie histórica completa.'),
    ('04', 'Extracción estival', 'Estadísticas de junio–septiembre del año de mortalidad.'),
]
proc_cells = []
for num, title, desc in steps:
    proc_cells.append(
        Table([[Paragraph(num, ST['proc_num'])],
               [Paragraph(title, ST['proc_t'])],
               [Paragraph(desc,  ST['proc_d'])]],
              colWidths=[(usable_w-3*0.4*cm)/4])
    )
proc_row_data = [[c] for c in proc_cells]
proc_tbl = Table(
    [[c for c in proc_cells]],
    colWidths=[(usable_w-3*0.4*cm)/4]*4,
    hAlign='LEFT',
)
proc_tbl.setStyle(TableStyle([
    ('BACKGROUND',    (0,0), (-1,-1), GREY_BG),
    ('BOX',           (0,0), (-1,-1), 0.5, RULE),
    ('INNERGRID',     (0,0), (-1,-1), 0.5, RULE),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING',    (0,0), (-1,-1), 10),
    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ('RIGHTPADDING',  (0,0), (-1,-1), 8),
]))

# Number badge — draw azul marino encima
class ProcTable(Flowable):
    """Tarjetas de proceso con badge numérico claramente separado del texto."""
    def __init__(self, steps_data, width):
        super().__init__()
        self.steps = steps_data
        self.width = width
        self.gap = 6
        self.col_w = (width - 3 * self.gap) / 4
        self.row_h = 96  # altura suficiente para badge + título + descripción

    def wrap(self, *a):
        return self.width, self.row_h

    def draw(self):
        c = self.canv
        n = len(self.steps)
        badge_r = 11
        pad_x = 10

        for i, (num, title, desc) in enumerate(self.steps):
            x = i * (self.col_w + self.gap)

            # Card background
            c.setFillColor(GREY_BG); c.setStrokeColor(RULE); c.setLineWidth(0.5)
            c.roundRect(x, 0, self.col_w, self.row_h, 4, fill=1, stroke=1)

            # Badge — centrado horizontalmente en la parte superior
            bx = x + badge_r + pad_x
            by = self.row_h - badge_r - 10   # cerca de la parte superior
            c.setFillColor(NAVY); c.circle(bx, by, badge_r, fill=1, stroke=0)
            c.setFillColor(WHITE); c.setFont('Helvetica-Bold', 10)
            c.drawCentredString(bx, by - 3.5, num)

            # Title — 14pt por debajo del borde inferior del badge
            title_y = by - badge_r - 14
            c.setFillColor(NAVY); c.setFont('Helvetica-Bold', 8.5)
            c.drawString(x + pad_x, title_y, title)

            # Description — 14pt por debajo del título, con word-wrap
            desc_y_start = title_y - 14
            c.setFillColor(SOFT); c.setFont('Helvetica', 7.8)
            words = desc.split(' ')
            line, lines = '', []
            for w in words:
                test = (line + ' ' + w).strip()
                if c.stringWidth(test, 'Helvetica', 7.8) < self.col_w - pad_x * 2:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = w
            if line:
                lines.append(line)
            for j, ln in enumerate(lines[:3]):
                c.drawString(x + pad_x, desc_y_start - j * 11, ln)

            # Arrow between cards
            if i < n - 1:
                ax = x + self.col_w + self.gap / 2
                ay = self.row_h / 2
                c.setStrokeColor(FAINT); c.setLineWidth(1.2)
                c.line(ax - 2, ay, ax + 1, ay)

story.append(ProcTable(steps, usable_w))
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph('DEFINICIÓN ESTÁNDAR DE MHW (HOBDAY ET AL. 2016)', ST['h3']))
story.append(Paragraph(
    'Se define una Ola de Calor Marina como un período en que la SST supera el '
    '<b>percentil 90 de la climatología local</b> durante <b>al menos 5 días consecutivos</b>. '
    'El umbral se calcula para cada día del año aplicando una ventana móvil de ±15 días '
    'sobre el período de referencia <b>1993–2016</b>, produciendo un umbral estacional '
    'suavizado y específico para cada localización.', ST['body']))

# Gráfica MHW conceptual
def chart_mhw_concept():
    N = 122
    def clim(i): return 23.8 + 4.0*np.sin(np.pi*(i-8)/104)
    def thr(i):  return clim(i) + 1.7 + 0.25*np.sin(np.pi*i/122)
    def sst(i):
        b = clim(i); a = 0.5*np.sin(np.pi*i/122*2+0.4)
        if 36<=i<=76: a += 3.0*np.exp(-((i-56)**2)/280)
        if 86<=i<=97: a += 1.9*np.exp(-((i-91)**2)/36)
        a += 0.22*(np.sin(i*7.1)+np.sin(i*3.9)*0.5)
        return b+a
    SS = np.array([sst(i) for i in range(N)])
    TH = np.array([thr(i) for i in range(N)])
    CL = np.array([clim(i) for i in range(N)])
    mn = min(SS.min(),TH.min(),CL.min())-0.4; mx = max(SS.max(),TH.max(),CL.max())+0.4

    fig, ax = plt.subplots(figsize=(13, 3.2))
    fig.patch.set_facecolor(PLOT_BG); ax.set_facecolor(PLOT_BG)
    x = np.arange(N)
    # MHW fill
    above = SS > TH
    ax.fill_between(x, TH, SS, where=above, color='#1A7A96', alpha=0.18, interpolate=True)
    # Lines
    ax.plot(x, CL, color='#AABFCC', linewidth=1.1, linestyle='--', label='Climatología media')
    ax.plot(x, TH, color='#1A7A96', linewidth=1.6, linestyle='-.', label='Umbral p90')
    ax.plot(x, SS, color='#1A3A5C', linewidth=2.0, label='SST diaria')
    # Annotation
    peak = 56
    ax.annotate('Episodio MHW principal (~37 días)',
                xy=(peak, SS[peak]), xytext=(peak-5, SS[peak]+0.8),
                ha='center', fontsize=8, color='#1A7A96', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#1A7A96', lw=1))
    # Axes
    months = [('Jun',0),('Jul',30),('Ago',61),('Sep',92)]
    ax.set_xticks([d for _,d in months]); ax.set_xticklabels([l for l,_ in months], fontsize=8.5, color=FONT_C)
    ax.tick_params(axis='y', labelsize=8, colors=FONT_C); ax.set_ylabel('SST (°C)', fontsize=8.5, color=FONT_C)
    ax.spines[['top','right','left']].set_visible(False); ax.spines['bottom'].set_color(PLOT_GRID)
    ax.yaxis.grid(True, color=PLOT_GRID, linewidth=0.6); ax.set_axisbelow(True)
    ax.legend(fontsize=8, frameon=False, loc='lower right', labelcolor=FONT_C)
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=160, bbox_inches='tight', facecolor=PLOT_BG)
    plt.close(fig); buf.seek(0); return buf

concept_buf = chart_mhw_concept()
concept_img = Image(concept_buf, width=usable_w, height=usable_w*3.2/13)
story.append(concept_img)
story.append(Paragraph(
    'Figura 1. Representación de la detección de MHW: SST diaria (azul oscuro), '
    'umbral p90 climatológico (teal) y zona sombreada correspondiente al episodio MHW. '
    'Solo se analiza el período junio–septiembre del año de mortalidad.',
    ST['caption']))
story.append(Spacer(1, 0.2*cm))

# Categorías — cards con borde de color superior
story.append(Paragraph('CATEGORÍAS DE INTENSIDAD (HOBDAY ET AL. 2018)', ST['h3']))

class CatCards(Flowable):
    def __init__(self, width):
        super().__init__(); self.width = width; self.h = 68
    def wrap(self, *a): return self.width, self.h
    def draw(self):
        c = self.canv
        cats = [
            ('#C87820','CAT. 1','Moderada','SST entre p90 y\n2× la anomalía umbral'),
            ('#2176AE','CAT. 2','Fuerte','Anomalía entre\n2–3× el umbral p90'),
            ('#B83030','CAT. 3','Severa','Anomalía entre\n3–4× el umbral p90'),
            ('#6040A0','CAT. 4','Extrema','Anomalía superior\na 4× el umbral p90'),
        ]
        cw = (self.width - 3*8) / 4
        for i, (col, num, name, desc) in enumerate(cats):
            x = i*(cw+8)
            # Card
            c.setFillColor(colors.HexColor('#F6F9FB'))
            c.setStrokeColor(colors.HexColor('#CDDDE8')); c.setLineWidth(0.5)
            c.roundRect(x, 0, cw, self.h, 3, fill=1, stroke=1)
            # Top bar
            c.setFillColor(colors.HexColor(col))
            c.roundRect(x, self.h-5, cw, 5, 2, fill=1, stroke=0)
            c.rect(x, self.h-8, cw, 5, fill=1, stroke=0)
            # Text
            c.setFillColor(colors.HexColor('#8AAABB')); c.setFont('Helvetica-Bold', 7)
            c.drawString(x+8, self.h-18, num)
            c.setFillColor(colors.HexColor('#1C2B38')); c.setFont('Helvetica-Bold', 10)
            c.drawString(x+8, self.h-30, name)
            c.setFillColor(colors.HexColor('#4A6A7E')); c.setFont('Helvetica', 7.8)
            for j, ln in enumerate(desc.split('\n')):
                c.drawString(x+8, self.h-44-j*11, ln)

story.append(CatCards(usable_w))
story.append(Spacer(1, 0.5*cm))

# ── 3. RESULTADOS ─────────────────────────────────────────────────────────────
story.append(Paragraph('3. Resultados', ST['h2']))
story.append(ThinLine(usable_w))
story.append(Spacer(1, 0.15*cm))

# Tabla resumen
res_data = [
    [Paragraph('Resultado', ParagraphStyle('rh', fontSize=7.5, fontName='Helvetica-Bold',
                                            textColor=TEAL, charSpace=0.8)),
     Paragraph('N', ParagraphStyle('rh2', fontSize=7.5, fontName='Helvetica-Bold',
                                    textColor=TEAL, alignment=TA_CENTER, charSpace=0.8)),
     Paragraph('%', ParagraphStyle('rh3', fontSize=7.5, fontName='Helvetica-Bold',
                                    textColor=TEAL, alignment=TA_CENTER, charSpace=0.8))],
    [Paragraph('<b>Con MHW estival detectada</b>', ST['body']),
     Paragraph(f'<b>{n_mhw}</b>', ParagraphStyle('nb',fontSize=9.5,fontName='Helvetica-Bold',textColor=INK,alignment=TA_CENTER,leading=14)),
     Paragraph(f'<b>{n_mhw/(n_mhw+n_no)*100:.1f}%</b>', ParagraphStyle('pb',fontSize=9.5,fontName='Helvetica-Bold',textColor=TEAL,alignment=TA_CENTER,leading=14))],
    [Paragraph('Sin MHW estival', ST['body']),
     Paragraph(str(n_no), ParagraphStyle('nc',fontSize=9.5,fontName='Helvetica',textColor=INK,alignment=TA_CENTER,leading=14)),
     Paragraph(f'{n_no/(n_mhw+n_no)*100:.1f}%', ParagraphStyle('pc',fontSize=9.5,fontName='Helvetica',textColor=SOFT,alignment=TA_CENTER,leading=14))],
    [Paragraph('Sin datos SST disponibles', ST['body']),
     Paragraph(str(n_nd), ParagraphStyle('nd2',fontSize=9.5,fontName='Helvetica',textColor=INK,alignment=TA_CENTER,leading=14)),
     Paragraph('—', ParagraphStyle('pd2',fontSize=9.5,fontName='Helvetica',textColor=SOFT,alignment=TA_CENTER,leading=14))],
    [Paragraph('<b>Total</b>', ST['body']),
     Paragraph(f'<b>{total}</b>', ParagraphStyle('nt',fontSize=9.5,fontName='Helvetica-Bold',textColor=INK,alignment=TA_CENTER,leading=14)),
     Paragraph('', ST['body'])],
]
res_tbl = Table(res_data, colWidths=[usable_w*0.62, usable_w*0.19, usable_w*0.19])
res_tbl.setStyle(TableStyle([
    ('TOPPADDING',    (0,0),(-1,-1), 7),
    ('BOTTOMPADDING', (0,0),(-1,-1), 7),
    ('LEFTPADDING',   (0,0),(-1,-1), 10),
    ('RIGHTPADDING',  (0,0),(-1,-1), 10),
    ('LINEBELOW',     (0,0),(-1,0), 1.2, TEAL),
    ('LINEBELOW',     (0,1),(-1,-2), 0.4, RULE),
    ('LINEBELOW',     (0,-1),(-1,-1), 0.5, RULE),
    ('BACKGROUND',    (0,1),(2,1), TEAL_BG),
    ('ROWBACKGROUNDS',(0,2),(-1,-1), [WHITE, GREY_BG, WHITE]),
    ('ALIGN',         (1,0),(-1,-1), 'CENTER'),
    ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
]))
story.append(res_tbl)
story.append(Spacer(1, 0.2*cm))
story.append(Paragraph(
    f'De los {n_mhw+n_no} eventos con datos SST disponibles, el <b>{pct:.1f}%</b> '
    f'presentó al menos un episodio MHW durante junio–septiembre del año de mortalidad. '
    f'La intensidad media de la anomalía máxima fue de <b>{avg_int:.2f}°C</b> '
    f'sobre el umbral p90, con una duración media de <b>{avg_days:.0f} días</b>. '
    f'El {n_str/n_mhw*100:.0f}% de los eventos con MHW registró categoría Fuerte '
    f'y el {n_mod/n_mhw*100:.0f}% categoría Moderada; solo {n_sev} casos alcanzaron '
    f'categoría Severa.', ST['body']))

# Gráficas
story.append(Paragraph('EVENTOS DE MORTALIDAD CON MHW POR AÑO', ST['h3']))
y1 = chart_years()
story.append(Image(y1, width=usable_w, height=usable_w*3.6/13))
story.append(Paragraph(
    'Figura 2. Eventos de mortalidad con MHW detectada (azul) y sin MHW (gris) por año '
    '(años con ≥3 eventos con datos). Se destacan los años de mayor relevancia.',
    ST['caption']))

story.append(Paragraph('INTENSIDAD Y DURACIÓN MEDIA POR AÑO', ST['h3']))
y2 = chart_intensity()
story.append(Image(y2, width=usable_w, height=usable_w*3.4/13))
story.append(Paragraph(
    'Figura 3. Anomalía máxima media (°C sobre p90) por año. '
    'El tamaño del punto refleja la duración media de los episodios MHW (días). '
    'Solo se incluyen años con ≥5 eventos con MHW detectada.',
    ST['caption']))

story.append(Paragraph('PROPORCIÓN DE EVENTOS CON MHW POR PAÍS', ST['h3']))
y3 = chart_country()
story.append(Image(y3, width=usable_w, height=usable_w*3.0/13))
story.append(Paragraph(
    'Figura 4. Porcentaje de eventos de mortalidad con MHW estival por país '
    '(países con ≥3 eventos con datos). La línea discontinua roja es la media global.',
    ST['caption']))
story.append(Spacer(1, 0.2*cm))

# ── 4. CONCLUSIONES ───────────────────────────────────────────────────────────
story.append(KeepTogether([Paragraph('4. Conclusiones', ST['h2']), ThinLine(usable_w)]))
story.append(Spacer(1, 0.15*cm))

conclusiones = [
    (f'<b>Alta asociación entre MHW y mortalidad.</b> El {pct:.1f}% de los eventos '
     f'con datos disponibles se produce en veranos con Ola de Calor Marina detectada, '
     f'lo que evidencia una relación sistemática entre el estrés térmico superficial '
     f'y la mortalidad masiva de organismos bentónicos en el Mediterráneo.'),
    (f'<b>Predominan las categorías Moderada y Fuerte.</b> De los {n_mhw} eventos con MHW, '
     f'el {n_mod/n_mhw*100:.0f}% registró categoría Moderada y el {n_str/n_mhw*100:.0f}% '
     f'categoría Fuerte. Solo {n_sev} eventos ({n_sev/n_mhw*100:.1f}%) alcanzaron '
     f'categoría Severa, concentrados en Chipre e Italia (2024) y en Baleares (2003). '
     f'No se registró ningún evento de categoría Extrema en los años con mortalidad documentada.'),
    ('<b>2024, el año de mayor intensidad y duración.</b> Con una anomalía media de '
     '4,55°C sobre p90 y una duración media de 70,8 días por localización, 2024 '
     'representa el verano de mayor estrés térmico del análisis, superando incluso '
     'los valores del emblemático verano de 2003.'),
    ('<b>2017, el año con mayor extensión espacial.</b> Con 85 localizaciones '
     'con MHW estival (81% del total con datos), 2017 fue el año con mayor '
     'cobertura geográfica de MHWs coincidentes con mortalidad documentada, '
     'aunque con intensidades medias inferiores a 2003 o 2024.'),
    ('<b>2003, episodio de referencia confirmado.</b> Cobertura del 90,2%, '
     'intensidad media de 4,30°C y duración media de 53,7 días. Los únicos '
     'eventos de categoría Severa de ese año se localizan en las Islas Baleares, '
     'consistente con la bibliografía sobre la gran mortalidad del Mediterráneo '
     'noroccidental.'),
    ('<b>Diferencias geográficas marcadas.</b> Francia (90,9%), Chipre (89,5%) '
     'e Italia (85,1%) presentan la mayor tasa de eventos asociados a MHW. '
     'Grecia muestra la tasa más baja (28,6%), lo que podría reflejar variabilidad '
     'oceanográfica regional y diferencias en la profundidad de las comunidades '
     'bentónicas documentadas.'),
    (f'<b>Intensidad y duración como indicadores complementarios.</b> La dosis '
     f'térmica acumulada media ({df_y["Cum_intensity"].mean():.0f} °C·días) y '
     f'la duración media ({avg_days:.0f} días) indican que la mortalidad se '
     f'asocia no solo a picos puntuales sino a exposición térmica prolongada. '
     f'Ambas métricas deberían incorporarse a futuros modelos de predicción de riesgo.'),
]

for c in conclusiones:
    tbl = Table([[Paragraph('—', ParagraphStyle('dash', fontSize=9.5, fontName='Helvetica-Bold',
                                                 textColor=TEAL, leading=14)),
                  Paragraph(c, ST['conc'])]],
                colWidths=[0.45*cm, usable_w-0.45*cm])
    tbl.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),0),
        ('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(0,-1),0),
        ('LEFTPADDING',(1,0),(1,-1),4),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(tbl)
story.append(Spacer(1, 0.2*cm))

# ── 5. LIMITACIONES ───────────────────────────────────────────────────────────
story.append(KeepTogether([Paragraph('5. Consideraciones sobre la interpretación', ST['h2']), ThinLine(usable_w)]))
story.append(Spacer(1, 0.15*cm))
lims = [
    '<b>SST vs. temperatura en profundidad.</b> El satélite mide la temperatura en los primeros metros. Los organismos bentónicos pueden experimentar anomalías distintas, con desfase temporal respecto a la superficie.',
    '<b>Resolución espacial de 5 km.</b> En zonas costeras con alta variabilidad, el píxel más próximo puede no representar fielmente las condiciones en el punto exacto de mortalidad.',
    '<b>Correlación no implica causalidad.</b> La asociación estadística no descarta otros factores causales (anoxia, patógenos, contaminación). El análisis es de carácter exploratorio.',
    '<b>Período de referencia 1993–2016.</b> El uso de este estándar puede infraestimar la anomalía en años recientes si el calentamiento de base es significativo.',
    '<b>Datos de 2026 incompletos.</b> El dataset REP tiene un retardo de varios meses; los resultados para 2026 son parciales.',
]
for l in lims:
    story.append(Paragraph(f'· {l}', ST['lim']))
story.append(Spacer(1, 0.3*cm))

# ── 6. REFERENCIAS ────────────────────────────────────────────────────────────
story.append(KeepTogether([Paragraph('Referencias', ST['h2']), ThinLine(usable_w)]))
story.append(Spacer(1, 0.1*cm))
for r in [
    'Hobday, A.J., et al. (2016). A hierarchical approach to defining marine heatwaves. <i>Progress in Oceanography</i>, 141, 227–238.',
    'Hobday, A.J., et al. (2018). Categorizing and naming marine heatwaves. <i>Oceanography</i>, 31(2), 162–173.',
    'Copernicus Marine Service (2024). <i>Mediterranean Sea SST L4 Reprocessed Observations (010_021)</i>. https://doi.org/10.48670/moi-00172',
    'Garrabou, J., et al. (2009). Mass mortality in Northwestern Mediterranean rocky benthic communities: effects of the 2003 heat wave. <i>Global Change Biology</i>, 15(5), 1090–1103.',
    'Oliver, E.C.J., et al. (2018). Longer and more frequent marine heatwaves over the past century. <i>Nature Communications</i>, 9, 1324.',
]:
    story.append(Paragraph(r, ST['ref']))

# ── Build ─────────────────────────────────────────────────────────────────────
print('Generando PDF...')
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f'PDF guardado: {OUT}')
