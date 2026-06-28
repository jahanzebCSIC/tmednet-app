"""
T-MEDNet — Generador genérico de gráficas y ficheros de salida
==============================================================
Configura la sección de CONFIGURACIÓN y ejecuta:

    python generate_tmednet_plots.py

Genera por año en Desktop/{SITE_NAME}_{year}/:
  • Stratification (Hovmöller)              — siempre
  • Annual Temperature Cycle                — siempre
  • Summer Thresholds 23–27 °C (JAS)        — requiere datos de verano completo (jul–sep)
  • Anomaly                                 — requiere datos históricos de años anteriores

Genera en Desktop/:
  • {SITE_CODE}_Database_T_{...}.txt        — matriu de dades (tab-separado)
  • Database_T_{SITE_CODE}_{...}.zip        — listo para subir a t-outputs
  • {SITE_CODE}_Stat_Report_{...}.xlsx      — informe estadístico (listo para t-outputs)
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from scipy.ndimage import uniform_filter1d
from pandas import ExcelWriter as _ExcelWriter
import zipfile

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                           CONFIGURACIÓN                                    ║
# ║  ← Edita únicamente esta sección antes de ejecutar el script               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

SITE_NAME     = "Cap de Creus-S"    # Nombre del sitio (aparece en títulos y nombres de fichero)
SITE_CODE     = 5                   # ID numérico del proyecto en T-MEDNet (project_id de la URL)

# Carpeta con los ficheros .txt exportados por HOBOware
TXT_DIR       = r"C:\Users\jahan\AppData\Local\Temp\hobo_export_creus"

# Carpeta base de salida (se crearán subcarpetas por año)
OUTPUT_BASE   = os.path.join(os.path.expanduser("~"), "Desktop")

# Coordenadas del sitio (para descargar SST de Copernicus, profundidad 0 m)
LAT           = 42.23698
LON           = 3.26141

# Ruta a un fichero Database_T histórico existente (.txt) para calcular anomalías.
# Si no existe ninguno, déjalo como None — el script avisará que no puede generarla.
HISTORICAL_DB = r"C:\Users\jahan\AppData\Local\Temp\hobo_export_creus\Database_T_05_Cap de Creus-S_200705-202505.txt"

DPI           = 150   # Resolución de las imágenes PNG (150 = web, 300 = publicación)

# ══════════════════════════════════════════════════════════════════════════════

plt.rc('legend', fontsize='medium')

# ── Carga de datos ────────────────────────────────────────────────────────────
from data_manager import DataManager

class _Console:
    def __call__(self, msg, mode='info', *a):
        if mode != 'info':
            print(f"  [{mode}] {msg}")

class _TextBox:
    def insert(self, *a): pass
    def delete(self, *a): pass
    def get(self, *a): return ""

class _Lister:
    def __init__(self): self._items = []
    def size(self): return len(self._items)
    def insert(self, i, item): self._items.append(item)

dm = DataManager(_Console(), [])
import re as _re
_HOBO_PAT = _re.compile(r'^\d+_\d{8}-\d{2}_\d{8}-\d{2}_\d+\.txt$')
txts = sorted([
    os.path.join(TXT_DIR, f).replace("\\", "/")
    for f in os.listdir(TXT_DIR) if f.endswith(".txt") and _HOBO_PAT.match(f)
])
if not txts:
    raise FileNotFoundError(f"No se encontraron ficheros .txt en: {TXT_DIR}")

print(f"\n{'='*60}")
print(f"  T-MEDNet Plot Generator — {SITE_NAME} (ID: {SITE_CODE})")
print(f"{'='*60}")
print(f"Cargando {len(txts)} fichero(s)...")

lister = _Lister()
dm.openfile(tuple(txts), _TextBox(), lister)
dm.files = lister._items
dm.newfiles = len(dm.files)
dm.load_data()
print(f"  {len(dm.mdata)} profundidades cargadas")

# Recortar cada profundidad a la ventana datainici–datafin del nombre del fichero
for dat in dm.mdata:
    t0, t1 = dat['datainici'], dat['datafin']
    before = len(dat['df'])
    dat['df'] = dat['df'].loc[(dat['df'].index >= t0) & (dat['df'].index <= t1)]
    trimmed = before - len(dat['df'])
    if trimmed:
        print(f"  Profundidad {dat['depth']}m: {trimmed} filas recortadas fuera de [{t0} – {t1}]")

df_all, depths_int, _ = dm.list_to_df()
depths_insitu = np.array(depths_int, dtype=float)
depth_strs_insitu = [str(int(d)) for d in depths_insitu]
df_all.columns = depth_strs_insitu
df_all.index = pd.to_datetime(df_all.index)
df_all = df_all.sort_index()

# ── Copernicus SST (profundidad 0 m) ──────────────────────────────────────────
SST_CSV = os.path.join(TXT_DIR, f"{SITE_NAME.lower().replace(' ','_')}_sst_copernicus.csv")
sst_ok  = False

if os.path.exists(SST_CSV):
    try:
        sst_daily = pd.read_csv(SST_CSV, index_col=0, parse_dates=True)
        sst_daily.index = pd.to_datetime(sst_daily.index).tz_localize(None)
        sst_daily.columns = ['0']
        sst_hourly  = sst_daily.resample('h').interpolate(method='linear')
        sst_aligned = sst_hourly.reindex(df_all.index, method='nearest',
                                         tolerance=pd.Timedelta('2h'))
        df_all.insert(0, '0', sst_aligned['0'])
        print(f"  SST Copernicus cargada: {sst_aligned['0'].notna().sum()} valores horarios (0 m)")
        sst_ok = True
    except Exception as e:
        print(f"  Aviso: no se pudo cargar SST Copernicus — {e}")
else:
    # Intentar descargar
    try:
        import copernicusmarine
        t0_dl = df_all.index[0].strftime('%Y-%m-%d')
        t1_dl = df_all.index[-1].strftime('%Y-%m-%d')
        print(f"  Descargando SST Copernicus ({LAT}N, {LON}E) {t0_dl} – {t1_dl}...")
        ds = copernicusmarine.open_dataset(
            dataset_id="SST_MED_SST_L4_NRT_OBSERVATIONS_010_004_c_V2",
            variables=["analysed_sst"],
            minimum_longitude=LON - 0.1, maximum_longitude=LON + 0.1,
            minimum_latitude=LAT - 0.1,  maximum_latitude=LAT + 0.1,
            start_datetime=t0_dl, end_datetime=t1_dl,
        )
        sst_s = ds["analysed_sst"].sel(latitude=LAT, longitude=LON, method="nearest").to_series()
        if sst_s.mean() > 100:
            sst_s = sst_s - 273.15
        sst_s.index = pd.to_datetime(sst_s.index).tz_localize(None)
        sst_s = sst_s.dropna()
        sst_s.to_csv(SST_CSV, header=True)
        sst_daily   = pd.DataFrame({'0': sst_s})
        sst_hourly  = sst_daily.resample('h').interpolate(method='linear')
        sst_aligned = sst_hourly.reindex(df_all.index, method='nearest',
                                          tolerance=pd.Timedelta('2h'))
        df_all.insert(0, '0', sst_aligned['0'])
        print(f"  SST Copernicus descargada y guardada: {SST_CSV}")
        sst_ok = True
    except Exception as e:
        print(f"  Aviso: descarga Copernicus no disponible — {e}")
        print(f"         El gráfico de Stratification no mostrará la capa de 0 m.")

depth_strs = list(df_all.columns)
depths     = np.array([float(d) for d in depth_strs])
insitu_cols = [c for c in depth_strs if c != '0']

print(f"\n  Rango total: {df_all.index[0]} -- {df_all.index[-1]}")
print(f"  Profundidades: {depth_strs}")

# ── Histórico para multi-year mean del T-Cycle ────────────────────────────────
hist_df = None
if HISTORICAL_DB and os.path.exists(HISTORICAL_DB):
    try:
        _h = pd.read_csv(HISTORICAL_DB, sep='\t', dtype={'Date': str, 'Time': str})
        _dt = pd.to_datetime(_h['Date'] + ' ' + _h['Time'],
                             format='%d/%m/%Y %H:%M:%S', errors='coerce')
        _h['datetime'] = _dt
        _h = _h.dropna(subset=['datetime']).set_index('datetime').sort_index()
        _dc = [c for c in _h.columns if c not in ('Date','Time') and c.strip().lstrip('-').isdigit()]
        _h = _h[_dc]
        _h.columns = [str(int(float(c))) for c in _dc]
        hist_df = _h
        print(f"  Historico cargado para T-Cycle: {hist_df.index.year.min()}–{hist_df.index.year.max()}")
    except Exception as e:
        print(f"  Aviso: no se pudo cargar historico para T-Cycle — {e}")

# ═════════════════════════════════════════════════════════════════════════════
# Funciones de plot
# ═════════════════════════════════════════════════════════════════════════════

COLOR_DICT = {
    '0':  '#000000',
    '5':  '#d4261d', '10': '#f58e6e', '15': '#fca95a', '20': '#fde5a3',
    '25': '#e4f4f8', '30': '#a7d6e7', '35': '#9ec6de', '40': '#3a6daf',
}

def _out(out_dir, name):
    return os.path.join(out_dir, name)

# ── Stratification ────────────────────────────────────────────────────────────
def plot_stratification(df, year, out_dir):
    from datetime import datetime as dt
    yr   = int(year)
    t0_w = dt(yr, 5, 1)
    t1_w = dt(yr, 12, 1)
    df_w = df[(df.index >= pd.Timestamp(t0_w)) & (df.index < pd.Timestamp(t1_w))]

    fig = plt.figure(figsize=(10, 5))
    ax  = fig.add_subplot(111)
    max_depth = depths[-1]
    ax.set_ylim(0, -40 if max_depth < 40 else -max_depth)
    ax.invert_yaxis()
    ax.set_yticks([-d for d in depths if d == int(d)])
    ax.set_xlim(t0_w, t1_w)

    if not df_w.empty:
        hmin = np.nanmin(df_w.values)
        hmax = np.nanmax(df_w.values)
        lv2  = np.arange(np.floor(hmin), hmax, 0.1)
        lv1  = np.arange(np.floor(hmin), hmax, 1)
        cf = ax.contourf(df_w.index.to_pydatetime(), -depths,
                         df_w.values.T, 256, extend='both',
                         cmap='RdYlBu_r', levels=lv2)
        plt.colorbar(cf, ax=ax, label='Temperature (ºC)', ticks=lv1)

    ax.set(ylabel='Depth (m)', title=f'{SITE_NAME} {year}')
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.tick_top()

    t0, t1 = df.index[0], df.index[-1]
    fname = f"{SITE_NAME.lower().replace(' ','_')}_{SITE_CODE}_stratification_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png"
    fig.savefig(_out(out_dir, fname), dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [stratification]  {fname}  ({os.path.getsize(_out(out_dir, fname))//1024} KB)")

# ── Annual T Cycle ────────────────────────────────────────────────────────────
def plot_annual_T_cycle(df, year, out_dir, hist_df=None):
    fig = plt.figure(figsize=(10, 5))
    ax  = fig.add_subplot(111)
    yr  = int(year)

    # Multi-year mean: grey lines + lightgrey fill between consecutive depths
    if hist_df is not None and not hist_df.empty:
        clim_raw = hist_df[hist_df.index.year < yr].copy()
        avail = [c for c in insitu_cols if c in clim_raw.columns]
        if not clim_raw.empty and avail:
            clim_raw = clim_raw[avail]
            clim_raw['_m'] = clim_raw.index.month
            clim_raw['_d'] = clim_raw.index.day
            daily_clim = clim_raw.groupby(['_m', '_d'])[avail].mean()
            dates, rows = [], []
            for (month, day), row in daily_clim.iterrows():
                try:
                    dates.append(pd.Timestamp(f'{yr}-{int(month):02d}-{int(day):02d}'))
                    rows.append(row)
                except Exception:
                    pass
            if dates:
                ord_df = pd.DataFrame(rows, index=dates).sort_index()
                for col in avail:
                    if col in ord_df.columns:
                        s = ord_df[col].interpolate(limit_direction='both')
                        ord_df[col] = uniform_filter1d(s.values, size=min(30, len(ord_df)))
                # Grey line per depth
                for col in avail:
                    if col in ord_df.columns:
                        ax.plot(ord_df.index, ord_df[col], color='#e9e8e8',
                                label='_nolegend_', zorder=5)
                # Fill between consecutive depths
                prev_col = None
                for col in avail:
                    if col not in ord_df.columns:
                        continue
                    if prev_col is not None:
                        ax.fill_between(ord_df.index, ord_df[prev_col], ord_df[col],
                                        facecolor='lightgrey', zorder=0)
                    prev_col = col
                ax.text(0.1, 0.1, "multi-year mean", backgroundcolor='grey',
                        transform=ax.transAxes, color='white', fontsize=9)

    # Current year colored lines (360-h running smooth; reindex preserva NaN en huecos)
    for col in insitu_cols:
        col_full = df[col] if col in df.columns else pd.Series(dtype=float)
        nona = col_full.dropna()
        if nona.empty:
            continue
        color = COLOR_DICT.get(col, '#333333')
        smoothed_vals = uniform_filter1d(nona.values, size=min(360, len(nona)))
        smoothed_series = pd.Series(smoothed_vals, index=nona.index).reindex(col_full.index)
        ax.plot(smoothed_series.index, smoothed_series.values, color=color, label=col, zorder=10)

    if not df.empty:
        vals = df[insitu_cols].values.flatten() if all(c in df.columns for c in insitu_cols) else df.values.flatten()
        vals = vals[~np.isnan(vals)]
        if len(vals):
            hmax = np.nanmax(vals)
            ax.set_yticks(np.arange(10, int(hmax) + 1, 2))

    xlim_start = pd.Timestamp(f'{yr}-01-01')
    xlim_end   = pd.Timestamp(f'{yr+1}-01-01')
    ax.set_xlim([xlim_start, xlim_end])
    ax.legend(title='Depth (m)')
    ax.set(ylabel='Temperature (ºC) smoothed',
           title=f'{SITE_NAME}  year {year}')
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    t0, t1 = df.index[0], df.index[-1]
    fname = f"{SITE_NAME.lower().replace(' ','_')}_{SITE_CODE}_annual_T_cycle_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png"
    fig.savefig(_out(out_dir, fname), dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [T cycle]         {fname}  ({os.path.getsize(_out(out_dir, fname))//1024} KB)")

# ── Thresholds (JAS) ──────────────────────────────────────────────────────────
def plot_thresholds(df, year, out_dir):
    df_jas = df[(df.index.month >= 7) & (df.index.month <= 9)][insitu_cols].copy()

    if df_jas.empty:
        print(f"  [thresholds]      OMITIDO — sin datos JAS (jul–sep) en {year}.")
        print(f"                    Causa: los sensores se desplegaron después de julio.")
        print(f"                    Disponible a partir del siguiente verano completo.")
        return

    months_with_data = df_jas.index.month.unique()
    missing = [m for m in [7, 8, 9] if m not in months_with_data]
    if missing:
        names = {7: 'julio', 8: 'agosto', 9: 'septiembre'}
        missing_names = ', '.join(names[m] for m in missing)
        print(f"  [thresholds]      OMITIDO — faltan datos de {missing_names} en {year}.")
        print(f"                    Los conteos JAS serían incorrectos y engañosos.")
        return

    df_jas['year'] = df_jas.index.year.astype(str)
    years   = sorted(df_jas['year'].unique())
    markers = ['+', 'o', 'x', 's', 'd', '^', 'v', 'p', 'h', '*']
    colors  = ['b', 'b', 'k', 'k']
    lines   = ['solid', 'dotted', 'solid', 'dotted']
    maxdepth = int(max([float(c) for c in insitu_cols]))

    year_dict = {}
    for yr in years:
        yr_daily = df_jas[df_jas['year'] == yr][insitu_cols].resample('D').max()
        year_dict[yr] = {}
        for thr in range(23, 28):
            ndays   = np.array([(yr_daily[d] >= thr).sum() for d in insitu_cols])
            dep_arr = np.array([int(d) for d in insitu_cols])
            year_dict[yr][thr] = np.column_stack((ndays, dep_arr))

    t0, t1 = df.index[0], df.index[-1]
    for thr in range(23, 28):
        maxdays = max(int(np.max(year_dict[yr][thr][:, 0])) for yr in years)
        fig = plt.figure(figsize=(10, 6))
        ax  = fig.add_subplot(111)
        ax.set(ylim=(0, maxdepth + 2))
        ticks = 10 if maxdays >= 30 else (5 if maxdays >= 20 else 2)
        ax.set(xlim=(-2, max(maxdays + 2, 5)),
               xticks=np.arange(0, max(maxdays + 2, 5), ticks))

        for i, yr in enumerate(years):
            int_yr = int(yr)
            color  = 'tab:orange' if yr == years[-1] else colors[min(i, len(colors)-1)]
            ls     = lines[min(i, len(lines)-1)]
            mk     = markers[min(int_yr % 10, len(markers)-1)]
            arr    = year_dict[yr][thr]
            ax.plot(arr[:, 0], arr[:, 1], marker=mk, color=color, linestyle=ls)

        ax.invert_yaxis()
        ax.xaxis.tick_top()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(years, title='Year', loc='center left', bbox_to_anchor=(1, 0.5))
        ax.set(ylabel='Depth (m)',
               title=f'{SITE_NAME}  Summer (JAS) days >= {thr}C  {year}')
        ax.xaxis.grid(True, linestyle='dashed')

        fname = f"{SITE_NAME.lower().replace(' ','_')}_{SITE_CODE}_thresholds_{thr}C_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png"
        fig.savefig(_out(out_dir, fname), dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        print(f"  [thresh {thr}C]       {fname}  ({os.path.getsize(_out(out_dir, fname))//1024} KB)")

# ── Anomaly ───────────────────────────────────────────────────────────────────
def _anom_filter(col):
    """uniform_filter1d(360) sobre valores no nulos, devuelve serie con mismo indice."""
    seg = col.dropna()
    if len(seg) == 0:
        return pd.Series(dtype=float)
    return pd.Series(uniform_filter1d(seg.values, size=min(360, len(seg))), index=seg.index)

def _anom_df_setter(filtered_col, legend, target_year, years='old'):
    """Agrupa por dia+mes, media, indice fecha 2020."""
    df = filtered_col.to_frame(name='val')
    df['day']   = df.index.day
    df['month'] = df.index.month
    df['year']  = df.index.year
    loc = df['year'] < target_year if years == 'old' else df['year'] == target_year
    result = (df.loc[loc]
               .groupby(['day','month'], as_index=False)
               .mean(numeric_only=True)
               .rename(columns={'val': legend}))
    result.sort_values(['month','day'], inplace=True)
    result['date'] = pd.to_datetime(
        '2020/' + result['month'].astype(int).astype(str) + '/' + result['day'].astype(int).astype(str))
    return result.set_index('date')[[legend]]

def plot_anomaly(df, year, out_dir):
    from labellines import labelLine as _labelLine
    target_year = int(year)
    depths_anom = [d for d in insitu_cols if d in ['10', '25', '40']]
    if not depths_anom:
        depths_anom = [insitu_cols[0], insitu_cols[len(insitu_cols)//2], insitu_cols[-1]]

    # Datos históricos para la climatología
    if HISTORICAL_DB and os.path.exists(HISTORICAL_DB):
        hist = pd.read_csv(HISTORICAL_DB, sep='\t', dtype={'Date': str, 'Time': str})
        dt_series = pd.to_datetime(hist['Date'] + ' ' + hist['Time'],
                                   format='%d/%m/%Y %H:%M:%S', errors='coerce')
        hist['datetime'] = dt_series
        hist = hist.dropna(subset=['datetime'])
        hist = hist.set_index('datetime')
        hist.columns = [str(int(float(c))) if c not in ('Date','Time') else c
                        for c in hist.columns]
        first_year = hist.index.year.min()
        print(f"  [anomaly]         Usando historico {first_year}--{target_year-1}")
        use_hist = True
    else:
        use_hist = False
        first_year = target_year
        print(f"  [anomaly]         AVISO -- sin datos historicos previos a {year}.")

    last_legend_dict = {}
    this_legend_dict = {}
    concated = None

    for depth in depths_anom:
        last_lbl = f"{first_year}-{target_year-1} Climatology ({depth}m)" if first_year < target_year else f"Mean ({depth}m)"
        this_lbl = f"{target_year} ({depth}m)"
        last_legend_dict[depth] = last_lbl
        this_legend_dict[depth] = this_lbl

        # Climatología: del histórico si existe, si no del df actual
        if use_hist and depth in hist.columns:
            clim_filt = _anom_filter(hist[depth])
        else:
            clim_filt = _anom_filter(df[depth]) if depth in df.columns else pd.Series(dtype=float)
        clim_means = _anom_df_setter(clim_filt, last_lbl, target_year, years='old')

        # Año actual: datos crudos sin filtrar (igual que la app original)
        curr_raw   = df[depth].dropna() if depth in df.columns else pd.Series(dtype=float)
        curr_means = _anom_df_setter(curr_raw, this_lbl, target_year, years='new')

        if concated is None:
            concated = pd.concat([clim_means, curr_means], axis=1)
            prop = concated.index.strftime('%b')
        else:
            concated = pd.concat([concated, clim_means, curr_means], axis=1)

    # Reindexar al año 2020 completo
    full_idx = pd.date_range('2020-01-01', '2020-12-31', freq='D')
    concated = concated.reindex(full_idx)
    prop = concated.index.strftime('%b')
    concated.index = concated.index.strftime('%m-%d')

    _x_idx    = np.arange(len(concated))
    _idx_list = list(concated.index)

    fig = plt.figure(figsize=(10, 5))
    ax  = plt.axes()
    _line_colors   = ['black', '#444444', '#777777']
    _plotted_lines = []

    for i, depth in enumerate(depths_anom):
        clim_col = last_legend_dict[depth]
        curr_col = this_legend_dict[depth]
        _color   = _line_colors[min(i, len(_line_colors)-1)]
        _y_clim  = concated[clim_col].values
        _y_curr  = concated[curr_col].values

        _lc, = ax.plot(_x_idx, _y_clim, color=_color, linewidth=0.7, alpha=1.0)
        ax.plot(_x_idx, _y_curr, color=_color, linewidth=0.7, alpha=0.7)
        _plotted_lines.append(_lc)

        ax.fill_between(_x_idx, _y_clim, _y_curr, where=(_y_curr > _y_clim), color='#fa5a5a')
        ax.fill_between(_x_idx, _y_clim, _y_curr, where=(_y_curr < _y_clim), color='#5aaaff')

        try:
            _labelLine(_lc, 200 + int(depth), label=depth, fontsize=9,
                       ha='left', va='center', color=_color)
        except Exception:
            pass

    _month_codes  = ['01-01','02-01','03-01','04-01','05-01','06-01',
                     '07-01','08-01','09-01','10-01','11-01','12-01']
    _month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    _tick_pos    = [_idx_list.index(c) for c in _month_codes if c in _idx_list]
    _tick_labels = [_month_labels[i] for i, c in enumerate(_month_codes) if c in _idx_list]
    ax.set_xticks(_tick_pos)
    ax.set_xticklabels(_tick_labels)
    ax.set_xlim(0, len(concated) - 1)
    plt.xlabel('')
    plt.title(f'Anomalies in {SITE_NAME} in {target_year}')
    red_patch  = mpatches.Patch(color='#fa5a5a', label='[+] anomaly')
    blue_patch = mpatches.Patch(color='#5aaaff', label='[-] anomaly')
    ax.legend(handles=[_plotted_lines[0], red_patch, blue_patch],
              labels=['Multi-Year Mean', '[+] anomaly', '[-] anomaly'])

    t0, t1 = df.index[0], df.index[-1]
    fname = f"{SITE_NAME.lower().replace(' ','_')}_{SITE_CODE}_anomaly_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png"
    fig.savefig(_out(out_dir, fname), dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [anomaly]         {fname}  ({os.path.getsize(_out(out_dir, fname))//1024} KB)")

# ═════════════════════════════════════════════════════════════════════════════
# Bucle principal por año
# ═════════════════════════════════════════════════════════════════════════════

years_in_data = sorted(df_all.index.year.unique())
print(f"\nAños con datos: {years_in_data}")

for year in years_in_data:
    df_year = df_all[df_all.index.year == year][depth_strs].copy()
    if df_year.empty:
        continue

    t0y, t1y = df_year.index[0], df_year.index[-1]
    print(f"\n{'-'*60}")
    print(f"  Anio {year}: {t0y.strftime('%d %b %Y')} -- {t1y.strftime('%d %b %Y')}  ({len(df_year)} filas)")

    out_dir = os.path.join(OUTPUT_BASE, f"{SITE_NAME}_{year}")
    os.makedirs(out_dir, exist_ok=True)

    plot_stratification(df_year, str(year), out_dir)
    plot_annual_T_cycle(df_year, str(year), out_dir, hist_df=hist_df)
    plot_thresholds(df_year, str(year), out_dir)
    plot_anomaly(df_year, str(year), out_dir)

# ═════════════════════════════════════════════════════════════════════════════
# Database_T (matriu de dades)
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'-'*60}")
df_insitu = df_all[insitu_cols].copy()
t0_all, t1_all = df_insitu.index[0], df_insitu.index[-1]
date_range = f"{t0_all.strftime('%Y%m')}-{t1_all.strftime('%Y%m')}"
today_str  = pd.Timestamp.now().strftime('%Y-%m-%d')

# .txt
txt_name = f"{SITE_CODE}_Database_T_{SITE_NAME}_{date_range}_{today_str}.txt"
txt_path = os.path.join(OUTPUT_BASE, txt_name)
df_db = df_insitu.copy()
df_db.insert(0, 'Date', df_insitu.index.strftime('%d/%m/%Y'))
df_db.insert(1, 'Time', df_insitu.index.strftime('%H:%M:%S'))
df_db.to_csv(txt_path, sep='\t', index=False, float_format='%.3f')
print(f"  [Database_T .txt] {txt_name}  ({os.path.getsize(txt_path)//1024} KB)")

# .zip (listo para subir a t-outputs)
zip_name = f"Database_T_{SITE_CODE}_{SITE_NAME}_{date_range}_{today_str}.zip"
zip_path = os.path.join(OUTPUT_BASE, zip_name)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    internal_name = f"Database_T_{SITE_CODE}_{SITE_NAME}_{date_range}_{today_str}.txt"
    zf.write(txt_path, arcname=internal_name)
print(f"  [Database_T .zip] {zip_name}  ({os.path.getsize(zip_path)//1024} KB)  <- subir a t-outputs")

# ═════════════════════════════════════════════════════════════════════════════
# Excel Stat Report
# ═════════════════════════════════════════════════════════════════════════════

df_ex       = df_insitu.copy()
df_ex_date  = pd.to_datetime(df_insitu.index.strftime('%Y-%m-%d'))
ex_month    = df_insitu.index.month
ex_year     = df_insitu.index.year
df_season   = df_insitu[df_insitu.index.month.isin([7, 8, 9])]
s_month     = df_season.index.month
s_year      = df_season.index.year

daily_p, monthly_p, seasonal_p = [], [], []

for col in insitu_cols:
    depth = int(col)

    agg_d = df_insitu.groupby(df_ex_date)[col].agg(['count','mean','std','max','min']).round(3)
    agg_d.columns = ['N','mean','std','max','min']
    agg_d = agg_d.reset_index().rename(columns={'index':'date'})
    agg_d['depth(m)'] = depth
    daily_p.append(agg_d[['date','depth(m)','N','mean','std','max','min']])

    agg_m = df_insitu.groupby([ex_year, ex_month])[col].agg(['count','mean','std','max','min']).round(3)
    agg_m.columns = ['N','mean','std','max','min']
    agg_m = agg_m.reset_index(); agg_m.columns = ['year','month','N','mean','std','max','min']
    agg_m['depth(m)'] = depth
    for thr in [24, 25, 26]:
        agg_m[f'Ndays>={thr}'] = np.round(
            (df_insitu[col] >= thr).astype(int)
            .groupby([ex_year, ex_month]).sum().values / 24)
    monthly_p.append(agg_m[['year','month','depth(m)','N','mean','std','max','min',
                              'Ndays>=24','Ndays>=25','Ndays>=26']])

    agg_s = df_season.groupby(s_year)[col].agg(['count','mean','std','max','min']).round(3)
    agg_s.columns = ['N','mean','std','max','min']
    agg_s = agg_s.reset_index(); agg_s.columns = ['year','N','mean','std','max','min']
    agg_s['season'] = 3; agg_s['depth(m)'] = depth
    for thr in [23, 24, 25, 26, 27, 28]:
        vals = (df_season[col] >= thr).astype(int).groupby(s_year).sum()
        agg_s[f'Ndays>={thr}'] = np.round(vals.reindex(agg_s['year']).fillna(0).values / 24)
    seasonal_p.append(agg_s[['year','season','depth(m)','N','mean','std','max','min',
                               'Ndays>=23','Ndays>=24','Ndays>=25','Ndays>=26','Ndays>=27','Ndays>=28']])

dfexcel    = pd.concat(daily_p,    ignore_index=True).sort_values(['date','depth(m)'])
dfmonthly  = pd.concat(monthly_p,  ignore_index=True).sort_values(['year','month','depth(m)'])
dfseasonal = pd.concat(seasonal_p, ignore_index=True).sort_values(['year','depth(m)'])

dfexcel['year']  = pd.DatetimeIndex(dfexcel['date']).year
dfexcel['month'] = pd.DatetimeIndex(dfexcel['date']).month
dfexcel['date']  = dfexcel['date'].apply(lambda d: d.date())

_nona        = dfexcel.dropna(subset=['max'])
dfmaxes      = dfexcel.loc[_nona.groupby('year')['max'].idxmax()][['year','date','max']].sort_values('max', ascending=False)
dfmaxes_dep  = dfexcel.loc[_nona.groupby(['year','depth(m)'])['max'].idxmax()][['year','depth(m)','date','max']].sort_values(['depth(m)','max'], ascending=False)
dfmaxes_mon  = dfexcel.loc[_nona.groupby(['year','month'])['max'].idxmax()][['year','month','date','max']].sort_values('max', ascending=False)
dfmaxes_dm   = dfexcel.loc[_nona.groupby(['year','month','depth(m)'])['max'].idxmax()][['year','month','depth(m)','date','max']].sort_values(['depth(m)','max'], ascending=False)
df30         = dfexcel.groupby('year')['mean'].apply(lambda g: round(float(g.nlargest(30).mean()), 2)).reset_index()
df30.columns = ['year','30tmax']

xl_name = f"{SITE_CODE}_Stat_Report_{SITE_NAME}_{date_range}_{today_str}.xlsx"
xl_path = os.path.join(OUTPUT_BASE, xl_name)
with _ExcelWriter(xl_path, engine='openpyxl') as writer:
    dfexcel.to_excel(writer,      sheet_name='Daily',            index=False)
    dfmonthly.to_excel(writer,    sheet_name='Monthly',          index=False)
    dfseasonal.to_excel(writer,   sheet_name='Seasonal',         index=False)
    dfmaxes.to_excel(writer,      sheet_name='Maxes',            index=False)
    dfmaxes_dep.to_excel(writer,  sheet_name='Maxes depth',      index=False)
    dfmaxes_mon.to_excel(writer,  sheet_name='Maxes month',      index=False)
    dfmaxes_dm.to_excel(writer,   sheet_name='Maxes depth month',index=False)
    df30.to_excel(writer,         sheet_name='30Tmax',           index=False)
print(f"  [Excel]           {xl_name}  ({os.path.getsize(xl_path)//1024} KB)  <- subir a t-outputs")

# ═════════════════════════════════════════════════════════════════════════════
# Resumen final
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print(f"  Completado. Ficheros en: {OUTPUT_BASE}")
print(f"  Carpetas de graficas:    {SITE_NAME}_{{year}}/")
print(f"  Subir a t-outputs:       {zip_name}")
print(f"                           {xl_name}")
print(f"{'='*60}\n")
