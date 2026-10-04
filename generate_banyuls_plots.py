"""
Generates all T-MEDNet plots for Banyuls / Park-buoy (site 8):
  T-Cycle, Anomaly, Stratification, Thresholds 23-27°C  (per year)
  Database_T .zip  +  Stat_Report .xlsx  (merged full history)

Data sources:
  Historical DB:   Banyuls_(Park-buoy)/Database_T_08_Banyuls_200603-202505_...zip
  HOBO campaign:   Banyuls_(Park-buoy)/Procesados  (Dec 2025 – Jul 2026, depths 5-40 m)

Note: 7-month gap between hist end (May 7, 2025) and HOBO start (Dec 8, 2025).

Output:  Desktop/temperatures t-mednet/Banyuls/
           2025/  -->  T-Cycle, anomaly, stratification, thresholds 23-27°C
           2026/  -->  T-Cycle, anomaly, stratification, thresholds 23-27°C
           Database_T_8_Banyuls_..._<date>.zip
           8_Stat_Report_Banyuls_..._<date>.xlsx
"""

import os, sys, zipfile, shutil, unicodedata
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from scipy.ndimage import uniform_filter1d
from pandas import ExcelWriter
from data_manager import DataManager
import re as _re

# ── Config ────────────────────────────────────────────────────────────────────
SITE_NAME   = "Banyuls"
SITE_CODE   = 8
MHW_CLIM_START = 2007
MHW_CLIM_END   = 2022
HIST_ZIP    = r"C:\Users\jahan\Desktop\Tmednet datos\Banyuls_(Park-buoy)\Database_T_08_Banyuls_200603-202505_2025-06-30.zip"
HOBO_DIR    = r"C:\Users\jahan\Desktop\Tmednet datos\Banyuls_(Park-buoy)\Procesados"
LAT, LON    = 42.475, 3.130
OUTPUT_BASE = os.path.join(os.path.expanduser("~"),
                           "Desktop", "temperatures t-mednet", "Banyuls")
SST_CSV     = os.path.join(OUTPUT_BASE, "banyuls_sst_copernicus.csv")
DPI         = 150

def _ascii(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

SITE_NAME_FILE = _ascii(SITE_NAME).replace(' ', '_').replace('-', '_')  # Banyuls

COLOR_DICT = {
    '5':  '#e8504a', '10': '#f58e6e', '15': '#fca95a', '20': '#fde5a3',
    '25': '#e4f4f8', '30': '#a7d6e7', '35': '#9ec6de', '40': '#3a6daf',
}
plt.rc('legend', fontsize='medium')

# ── DataManager helpers ───────────────────────────────────────────────────────
class _C:
    def __call__(self, msg, mode='info', *a): pass
class _TB:
    def insert(self, *a): pass
    def delete(self, *a): pass
    def get(self, *a): return ''
class _L:
    def __init__(self): self._i = []
    def size(self): return len(self._i)
    def insert(self, i, item): self._i.append(item)

_HOBO_PAT = _re.compile(r'^\d+_\d{8}-\d{2}_\d{8}-\d{2}_\d+\.txt$')

def _parse_hobo_direct(path):
    """Parse a HOBO .txt file by finding the 'Temp' column header directly.
    Handles files that have extra columns (e.g., pressure) before the temperature.
    Masks rows where sensor status events indicate the sensor was out of water."""
    df_raw = pd.read_csv(path, sep='\t', header=0, dtype=str)
    # Find the temperature column (header contains 'Temp')
    temp_cols = [c for c in df_raw.columns if 'Temp' in c and '°C' in c]
    if not temp_cols:
        return pd.Series(dtype=float)
    temp_col = temp_cols[0]
    # Find date and time columns
    fecha_cols = [c for c in df_raw.columns if 'Fecha' in c or 'Date' in c]
    tiempo_cols = [c for c in df_raw.columns if 'Tiempo' in c or 'Time' in c]
    if not fecha_cols or not tiempo_cols:
        return pd.Series(dtype=float)
    fecha_col  = fecha_cols[0]
    tiempo_col = tiempo_cols[0]
    # Parse datetime — handle both 2-digit and 4-digit year
    dt_str = df_raw[fecha_col].str.strip() + ' ' + df_raw[tiempo_col].str.strip()
    dt = pd.to_datetime(dt_str, dayfirst=True, errors='coerce')
    vals = pd.to_numeric(df_raw[temp_col], errors='coerce')
    s = pd.Series(vals.values, index=dt, name='T')
    s = s[s.index.notna()]

    # Mask rows where any HOBO event column is non-empty (sensor out of water:
    # "Acoplador separado", "Acoplador adjunto", "Host conectado", "Parado", etc.)
    event_cols = [c for c in df_raw.columns
                  if any(kw in c for kw in ('Acoplador', 'Host', 'Parado', 'Final'))]
    if event_cols:
        event_mask = df_raw[event_cols].apply(
            lambda col: col.str.strip().fillna('').astype(bool).where(
                col.str.strip().fillna('') != '', other=False)
        ).any(axis=1)
        # Expand mask ±1 row to catch transition readings
        event_mask_exp = event_mask | event_mask.shift(1, fill_value=False) | \
                         event_mask.shift(-1, fill_value=False)
        s[event_mask_exp.values[:len(s)]] = np.nan

    # Basic temperature range filter
    s[s < -5]  = np.nan
    s[s > 40]  = np.nan

    # Rolling median spike filter: flag values more than 2°C from 24-hour rolling median
    if s.notna().sum() > 48:
        roll_med = s.rolling(window=24, center=True, min_periods=6).median()
        spike = (s - roll_med).abs() > 2.0
        s[spike] = np.nan

    return s.sort_index()

def load_hobo_dir(folder):
    dm = DataManager(_C(), [])
    all_files = sorted([
        f for f in os.listdir(folder) if f.endswith('.txt') and _HOBO_PAT.match(f)
    ])
    txts = tuple([os.path.join(folder, f).replace('\\', '/') for f in all_files])
    if not txts:
        return pd.DataFrame()
    lister = _L()
    dm.openfile(txts, _TB(), lister)
    dm.files = lister._i; dm.newfiles = len(dm.files); dm.load_data()
    for dat in dm.mdata:
        t0, t1 = dat['datainici'], dat['datafin']
        dat['df'] = dat['df'].loc[(dat['df'].index >= t0) & (dat['df'].index <= t1)]
    df_all, depths_int, _ = dm.list_to_df()
    df_all.columns = [str(int(d)) for d in depths_int]
    df_all.index = pd.to_datetime(df_all.index)
    df_all = df_all.sort_index()

    # Fix columns that DataManager loaded but are all-NaN (e.g., pressure-logger files
    # where the temperature column is not in the expected position)
    for fname in all_files:
        m = _re.search(r'_(\d+)\.txt$', fname)
        if not m:
            continue
        depth_key = str(int(m.group(1)))  # '05' -> '5'
        if depth_key not in df_all.columns:
            continue
        if df_all[depth_key].notna().any():
            continue  # DataManager read it correctly
        # Fall back to direct header-based parsing
        print(f"  [direct parse] {fname} (depth {depth_key}m)")
        s = _parse_hobo_direct(os.path.join(folder, fname))
        if s.empty:
            continue
        s_h = s.resample('h').mean()
        df_all[depth_key] = s_h.reindex(df_all.index)

    return df_all

def read_database_t_zip(zip_path):
    tmp = os.path.join(os.environ['TEMP'], '_banyuls_hist_extract')
    os.makedirs(tmp, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(tmp)
        txt_name = [f for f in zf.namelist() if f.endswith('.txt')][0]
    df = pd.read_csv(os.path.join(tmp, txt_name), sep='\t',
                     dtype={'Date': str, 'Time': str})
    dt = pd.to_datetime(df['Date'] + ' ' + df['Time'],
                        format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df['datetime'] = dt
    df = df.dropna(subset=['datetime']).set_index('datetime').sort_index()
    dcols = [c for c in df.columns if c not in ('Date', 'Time')
             and c.strip().lstrip('-').isdigit()]
    df = df[dcols]
    df.columns = [str(int(float(c))) for c in dcols]
    shutil.rmtree(tmp, ignore_errors=True)
    return df

# ── 1. Load data ──────────────────────────────────────────────────────────────
print("Cargando Database_T historico...")
df_hist = read_database_t_zip(HIST_ZIP)
HIST_START_YEAR = df_hist.index.year.min()
print(f"  {df_hist.index[0]} --> {df_hist.index[-1]}  ({len(df_hist)} filas)")
print(f"  Profundidades: {list(df_hist.columns)}")

print("\nCargando HOBO campaña actual...")
df_hobo = load_hobo_dir(HOBO_DIR)
if not df_hobo.empty:
    print(f"  {df_hobo.index[0]} --> {df_hobo.index[-1]}  ({len(df_hobo)} filas)")
    print(f"  Profundidades: {sorted(df_hobo.columns.tolist(), key=int)}")
else:
    print("  (sin archivos HOBO)")

# ── 2. Merge historico + HOBO ─────────────────────────────────────────────────
all_depth_cols = sorted(
    {c for src in [df_hist, df_hobo] for c in src.columns if not src.empty},
    key=int)
df_full = pd.concat(
    [src[[c for c in all_depth_cols if c in src.columns]]
     for src in [df_hist, df_hobo] if not src.empty],
    axis=0).sort_index()
df_full = df_full[~df_full.index.duplicated(keep='last')].sort_index()
df_full = df_full[all_depth_cols]
print(f"\nDataset completo: {df_full.index[0]} --> {df_full.index[-1]}  "
      f"({len(df_full)} filas, profundidades {all_depth_cols})")

os.makedirs(OUTPUT_BASE, exist_ok=True)

# ── 3. Copernicus SST (0 m) for stratification ────────────────────────────────
sst_series = None
if os.path.exists(SST_CSV):
    try:
        _s = pd.read_csv(SST_CSV, index_col=0, parse_dates=True)
        _s.index = pd.to_datetime(_s.index).tz_localize(None)
        sst_series = _s.iloc[:, 0]
        print(f"\nSST Copernicus cargada desde CSV: {len(sst_series)} días")
    except Exception as e:
        print(f"\nAviso: no se pudo leer SST CSV — {e}")

if sst_series is None:
    print("\nDescargando SST Copernicus...")
    try:
        import copernicusmarine
        ds = copernicusmarine.open_dataset(
            dataset_id="SST_MED_SST_L4_NRT_OBSERVATIONS_010_004_c_V2",
            variables=["analysed_sst"],
            minimum_longitude=LON - 0.4, maximum_longitude=LON + 0.4,
            minimum_latitude=LAT - 0.4,  maximum_latitude=LAT + 0.4,
            start_datetime="2025-01-01", end_datetime="2026-10-01",
        )
        sst_grid = ds["analysed_sst"]
        sst_mean = sst_grid.mean(dim='time')
        lats = ds.latitude.values
        lons = ds.longitude.values
        lat_g, lon_g = np.meshgrid(lats, lons, indexing='ij')
        dist = np.sqrt((lat_g - LAT)**2 + (lon_g - LON)**2)
        valid_mask = ~np.isnan(sst_mean.values)
        dist[~valid_mask] = np.inf
        idx = np.unravel_index(dist.argmin(), dist.shape)
        best_lat, best_lon = float(lats[idx[0]]), float(lons[idx[1]])
        print(f"  Pixel SST más cercano válido: ({best_lat:.4f}°N, {best_lon:.4f}°E)")
        sst_series = sst_grid.sel(latitude=best_lat, longitude=best_lon).to_series()
        if sst_series.mean() > 100:
            sst_series = sst_series - 273.15
        sst_series.index = pd.to_datetime(sst_series.index).tz_localize(None)
        sst_series = sst_series.dropna()
        sst_series.to_csv(SST_CSV, header=True)
        print(f"  Descargada y guardada: {len(sst_series)} días")
    except Exception as e:
        print(f"  SST no disponible: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# Plot helpers
# ══════════════════════════════════════════════════════════════════════════════

def _save(fig, path, **kw):
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
    fig.savefig(path, **kw)


def _add_sst(df, depths_in_df):
    """Insert Copernicus SST as column '0' aligned to df index."""
    if sst_series is None or sst_series.empty:
        return df, depths_in_df
    sst_h = sst_series.resample('h').interpolate(method='linear')
    sst_a = sst_h.reindex(df.index, method='nearest', tolerance=pd.Timedelta('2h'))
    df = df.copy()
    df.insert(0, '0', sst_a)
    return df, ['0'] + list(depths_in_df)


def _correct_5m_winter(df):
    """5m HOBO pressure+temp sensor sometimes reads warm anomalies vs 10m in winter.
    In Oct-Apr, 5m > 10m + 1.5°C is physically implausible (well-mixed column) →
    replace those hours with the 10m value before smoothing/plotting."""
    if '5' not in df.columns or '10' not in df.columns:
        return df
    df = df.copy()
    is_winter = df.index.month.isin([10, 11, 12, 1, 2, 3, 4])
    warm_inv = (df['5'] > df['10'] + 1.5) & is_winter
    df.loc[warm_inv, '5'] = df.loc[warm_inv, '10']
    return df


def plot_annual_T_cycle(df_year, year, out_dir, hist_df=None):
    df_year = _correct_5m_winter(df_year)
    yr = int(year)
    fig = plt.figure(figsize=(10, 5))
    ax  = fig.add_subplot(111)

    if hist_df is not None and not hist_df.empty:
        clim_raw = hist_df[hist_df.index.year < yr]
        avail = [c for c in all_depth_cols if c in clim_raw.columns]
        if not clim_raw.empty and avail:
            clim_raw2 = clim_raw[avail].copy()
            clim_raw2['_m'] = clim_raw2.index.month
            clim_raw2['_d'] = clim_raw2.index.day
            daily_clim = clim_raw2.groupby(['_m', '_d'])[avail].mean()
            dates, rows = [], []
            for (m, d), row in daily_clim.iterrows():
                try:
                    dates.append(pd.Timestamp(f'{yr}-{int(m):02d}-{int(d):02d}'))
                    rows.append(row)
                except Exception:
                    pass
            if dates:
                ord_df = pd.DataFrame(rows, index=dates).sort_index()
                for col in avail:
                    if col in ord_df.columns:
                        s = ord_df[col].interpolate(limit_direction='both')
                        ord_df[col] = uniform_filter1d(s.values, size=min(30, len(ord_df)))
                for col in avail:
                    if col in ord_df.columns:
                        ax.plot(ord_df.index, ord_df[col], color='#e9e8e8',
                                label='_nolegend_', zorder=5)
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

    plot_cols = [c for c in all_depth_cols if c in df_year.columns]
    for col in plot_cols:
        col_full = df_year[col] if col in df_year.columns else pd.Series(dtype=float)
        if col_full.dropna().empty:
            continue
        color = COLOR_DICT.get(col, '#333333')
        smoothed = col_full.rolling(window=360, center=True, min_periods=30).mean()
        ax.plot(smoothed.index, smoothed.values, color=color, label=col, zorder=10)

    vals = df_year[plot_cols].values.flatten()
    vals = vals[~np.isnan(vals)]
    if len(vals):
        ax.set_yticks(np.arange(10, int(np.nanmax(vals)) + 2, 2))
    ax.set_xlim([pd.Timestamp(f'{yr}-01-01'), pd.Timestamp(f'{yr+1}-01-01')])
    ax.legend(title='Depth (m)')
    ax.set(ylabel='Temperature (ºC) smoothed',
           title=f'{SITE_NAME}  year {year}')
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    t0, t1 = df_year.index[0], df_year.index[-1]
    slug = _ascii(SITE_NAME).lower().replace(' ', '_')
    out = os.path.join(out_dir,
        f"{slug}_{SITE_CODE}_annual_T_cycle"
        f"_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png")
    _save(fig, out, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [T-Cycle]  {os.path.basename(out)}  ({os.path.getsize(out)//1024} KB)")


def plot_anomaly(df_year, year, out_dir, hist_df=None):
    df_year = _correct_5m_winter(df_year)
    target_year = int(year)
    candidate = ['5', '20', '40']
    avail_hist = list(hist_df.columns) if hist_df is not None and not hist_df.empty else []
    avail_yr   = [c for c in df_year.columns if df_year[c].notna().any()]
    depths_anom = [d for d in candidate
                   if d in avail_yr and (d in avail_hist or hist_df is None)]
    if not depths_anom:
        depths_anom = [c for c in avail_yr if c in avail_hist][:3]
    if not depths_anom:
        print(f"  [anomaly]  Sin profundidades comunes — omitido")
        return

    full_idx = pd.date_range('2020-01-01', '2020-12-31', freq='D').strftime('%m-%d').tolist()
    last_legend_dict, this_legend_dict = {}, {}
    concated = None

    for depth in depths_anom:
        clim_lbl = f"{HIST_START_YEAR}-{target_year-1} Climatology ({depth}m)"
        curr_lbl = f"{target_year} ({depth}m)"
        last_legend_dict[depth] = clim_lbl
        this_legend_dict[depth] = curr_lbl

        if hist_df is not None and not hist_df.empty and depth in hist_df.columns:
            col_hist = hist_df[depth].dropna()
            col_hist = col_hist[col_hist.index.year < target_year]
            if not col_hist.empty:
                smoothed_vals = uniform_filter1d(col_hist.values, size=min(360, len(col_hist)))
                col_hist_sm = pd.Series(smoothed_vals, index=col_hist.index)
                tmp = pd.DataFrame({'val': col_hist_sm.values,
                                    'month': col_hist_sm.index.month,
                                    'day': col_hist_sm.index.day})
                grp = tmp.groupby(['month', 'day'])['val'].mean()
                clim_s = pd.Series(np.nan, index=full_idx, name=clim_lbl)
                for (m, d), v in grp.items():
                    k = f'{int(m):02d}-{int(d):02d}'
                    if k in clim_s.index: clim_s[k] = v
            else:
                clim_s = pd.Series(np.nan, index=full_idx, name=clim_lbl)
        else:
            clim_s = pd.Series(np.nan, index=full_idx, name=clim_lbl)

        if depth in df_year.columns:
            col_yr = df_year[depth].dropna()
            col_yr = col_yr[col_yr.index.year == target_year]
            tmp2 = pd.DataFrame({'val': col_yr.values,
                                 'month': col_yr.index.month,
                                 'day': col_yr.index.day})
            grp2 = tmp2.groupby(['month', 'day'])['val'].mean()
            curr_s = pd.Series(np.nan, index=full_idx, name=curr_lbl)
            for (m, d), v in grp2.items():
                k = f'{int(m):02d}-{int(d):02d}'
                if k in curr_s.index: curr_s[k] = v
        else:
            curr_s = pd.Series(np.nan, index=full_idx, name=curr_lbl)

        pair = pd.concat([clim_s, curr_s], axis=1)
        concated = pair if concated is None else pd.concat([concated, pair], axis=1)

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
        ax.fill_between(_x_idx, _y_clim, _y_curr, where=(_y_curr > _y_clim),
                        color='#fa5a5a')
        ax.fill_between(_x_idx, _y_clim, _y_curr, where=(_y_curr < _y_clim),
                        color='#5aaaff')
        try:
            from labellines import labelLine as _labelLine
            _labelLine(_lc, 200 + int(depth), label=depth, fontsize=9,
                       ha='left', va='center', color=_color)
        except Exception:
            pass

    _month_codes  = ['01-01','02-01','03-01','04-01','05-01','06-01',
                     '07-01','08-01','09-01','10-01','11-01','12-01']
    _month_labels = ['Jan','Feb','Mar','Apr','May','Jun',
                     'Jul','Aug','Sep','Oct','Nov','Dec']
    _tick_pos    = [_idx_list.index(c) for c in _month_codes if c in _idx_list]
    _tick_labels = [_month_labels[i] for i, c in enumerate(_month_codes)
                    if c in _idx_list]
    ax.set_xticks(_tick_pos); ax.set_xticklabels(_tick_labels)
    ax.set_xlim(0, len(concated) - 1)
    plt.xlabel('')
    plt.title(f'Anomalies in {SITE_NAME} in {target_year}')
    red_patch  = mpatches.Patch(color='#fa5a5a', label='[+] anomaly')
    blue_patch = mpatches.Patch(color='#5aaaff', label='[-] anomaly')
    ax.legend(handles=[_plotted_lines[0], red_patch, blue_patch],
              labels=['Multi-Year Mean', '[+] anomaly', '[-] anomaly'])

    t0, t1 = df_year.index[0], df_year.index[-1]
    slug = _ascii(SITE_NAME).lower().replace(' ', '_')
    out = os.path.join(out_dir,
        f"{slug}_{SITE_CODE}_anomaly"
        f"_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png")
    _save(fig, out, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [anomaly]  {os.path.basename(out)}  ({os.path.getsize(out)//1024} KB)")


def plot_stratification(df_year, year, out_dir):
    yr = int(year)
    t_may = pd.Timestamp(f'{yr}-05-01')
    t_dec = pd.Timestamp(f'{yr}-12-01')

    in_situ_dcols = [c for c in df_year.columns
                     if c.strip().lstrip('-').isdigit()]
    df_sst, depth_cols_with_sst = _add_sst(df_year, in_situ_dcols)
    df_window = df_sst[(df_sst.index >= t_may) & (df_sst.index < t_dec)]

    plot_dcols = [c for c in depth_cols_with_sst if df_window[c].notna().any()] \
                 if not df_window.empty else []
    depths_num = np.array([float(c) for c in plot_dcols]) if plot_dcols else np.array([])

    fig = plt.figure(figsize=(10, 5))
    ax  = fig.add_subplot(111)
    max_depth = float(depths_num[-1]) if len(depths_num) else 40.0
    ax.set_ylim(0, -max_depth)
    ax.invert_yaxis()
    if len(depths_num):
        ax.set_yticks([-d for d in depths_num if d == int(d)])
    ax.set_xlim(t_may, t_dec)

    if not df_window.empty and plot_dcols:
        df_plot = df_window[plot_dcols].copy()
        df_plot[df_plot > 32] = np.nan

        # Where the 5 m sensor creates a temperature inversion (colder than both the
        # surface SST by >2°C AND colder than 10 m), infer the 5 m value by linear
        # interpolation between 0 m (SST) and 10 m.  This smooths away brief cold
        # pockets that break the expected surface-to-depth gradient.
        if '0' in df_plot.columns and '5' in df_plot.columns and '10' in df_plot.columns:
            cold_inv = (
                (df_plot['5'] < df_plot['0'] - 2.0) &
                (df_plot['5'] < df_plot['10'])
            )
            warm_inv = (
                (df_plot['5'] > df_plot['0'] + 2.0) &
                (df_plot['5'] > df_plot['10'])
            )
            inversion = cold_inv | warm_inv
            df_plot.loc[inversion, '5'] = (
                df_plot.loc[inversion, '0'] + df_plot.loc[inversion, '10']
            ) / 2.0

        df_plot = df_plot.interpolate(method='linear', axis=1)
        df_plot = df_plot.interpolate(method='linear', axis=0, limit=72)
        hmin, hmax = np.nanmin(df_plot.values), np.nanmax(df_plot.values)
        lv2 = np.arange(np.floor(hmin), hmax, 0.1)
        lv1 = np.arange(np.floor(hmin), hmax, 1)
        data_masked = np.ma.masked_invalid(df_plot.values.T)
        cf = ax.contourf(df_plot.index.to_pydatetime(), -depths_num,
                         data_masked, 256, extend='both',
                         cmap='RdYlBu_r', levels=lv2)
        plt.colorbar(cf, ax=ax, label='Temperature (ºC)', ticks=lv1)

    ax.set(ylabel='Depth (m)', title=f'{SITE_NAME} {year}')
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.tick_top()

    t0, t1 = df_year.index[0], df_year.index[-1]
    slug = _ascii(SITE_NAME).lower().replace(' ', '_')
    out = os.path.join(out_dir,
        f"{slug}_{SITE_CODE}_stratification"
        f"_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png")
    _save(fig, out, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"  [strat]    {os.path.basename(out)}  ({os.path.getsize(out)//1024} KB)")


def plot_thresholds(df_year, year, out_dir, hist_df=None):
    target_year = int(year)

    jas_yr = df_year[(df_year.index.month >= 7) & (df_year.index.month <= 9)]
    if hist_df is not None and not hist_df.empty:
        jas_hist = hist_df[(hist_df.index.month >= 7) & (hist_df.index.month <= 9) &
                           (hist_df.index.year < target_year)]
        all_depths_t = sorted(
            set(jas_hist.columns.tolist()) | set(jas_yr.columns.tolist()), key=int)
    else:
        jas_hist = pd.DataFrame()
        all_depths_t = sorted(jas_yr.columns.tolist(), key=int)

    if jas_yr.empty:
        print(f"  [thresh]   Sin datos JAS {target_year} — omitido")
        return

    all_depths_t = [d for d in all_depths_t if d.strip().lstrip('-').isdigit()]
    depths_int_t = np.array([int(d) for d in all_depths_t])
    maxdepth_t   = int(depths_int_t.max())

    def compute_thresh_year(df_jas):
        N_rec = {d: int(df_jas[d].dropna().__len__()) if d in df_jas.columns else 0
                 for d in all_depths_t}
        max_N = max(N_rec.values()) if N_rec else 0
        result = {}
        for thr in range(23, 28):
            row = {}
            for d in all_depths_t:
                n = N_rec.get(d, 0)
                if n < 720 or (max_N - n) > 240:
                    row[d] = np.nan
                else:
                    col = df_jas[d] if d in df_jas.columns else pd.Series(dtype=float)
                    row[d] = round((col >= thr).sum() / 24)
            result[thr] = row
        return result

    year_data = {}
    if not jas_hist.empty:
        for yr in sorted(jas_hist.index.year.unique()):
            year_data[str(yr)] = compute_thresh_year(
                jas_hist[jas_hist.index.year == yr])
    year_data[str(target_year)] = compute_thresh_year(jas_yr)
    all_years_t = sorted(year_data.keys())

    has_data = any(
        not np.isnan(year_data[yr][thr_check].get(d, np.nan))
        for yr in all_years_t
        for thr_check in range(23, 28)
        for d in all_depths_t
    )
    if not has_data:
        print(f"  [thresh]   Sin suficientes datos JAS {target_year} — omitido")
        return

    markers_list = ['+', 'o', 'x', 's', 'd', '^', 'v', 'p', 'h', '*']
    colors_dec   = ['b', 'b', 'k', 'k']
    lines_dec    = ['solid', 'dotted', 'solid', 'dotted']

    def style_for_year(yr_str, last_yr):
        yr = int(yr_str)
        if yr < 2000:   c, ls, mk = colors_dec[0], lines_dec[0], markers_list[(yr-1990) % 10]
        elif yr < 2010: c, ls, mk = colors_dec[1], lines_dec[1], markers_list[(yr-2000) % 10]
        elif yr < 2020: c, ls, mk = colors_dec[2], lines_dec[2], markers_list[(yr-2010) % 10]
        else:           c, ls, mk = colors_dec[3], lines_dec[3], markers_list[(yr-2020) % 10]
        if yr_str == last_yr: c = 'tab:orange'
        return c, ls, mk

    last_yr = all_years_t[-1]

    for thr in range(23, 28):
        maxdays = max(
            (v for yr in all_years_t for d in all_depths_t
             if not np.isnan(v := year_data[yr][thr].get(d, np.nan))),
            default=5)
        ticks = 10 if maxdays >= 30 else (5 if maxdays >= 20 else 2)

        fig = plt.figure(figsize=(10, 6))
        ax  = fig.add_subplot(111)
        ax.set_ylim(0, maxdepth_t + 2)
        ax.set_xlim(-2, max(int(maxdays) + 2, 5))
        ax.set_xticks(np.arange(0, max(int(maxdays) + 2, 5), ticks))
        ax.invert_yaxis()
        ax.xaxis.tick_top()
        ax.xaxis.grid(True, linestyle='dashed')

        for yr in all_years_t:
            c, ls, mk = style_for_year(yr, last_yr)
            ndays_arr = np.array([year_data[yr][thr].get(d, np.nan)
                                  for d in all_depths_t], dtype=float)
            dep_arr   = depths_int_t.astype(float)
            mask = ~np.isnan(ndays_arr)
            if mask.any():
                ax.plot(ndays_arr[mask], dep_arr[mask],
                        marker=mk, color=c, linestyle=ls)

        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(all_years_t, title='Year', loc='center left',
                  bbox_to_anchor=(1, 0.5), fontsize=7)
        ax.set(ylabel='Depth (m)',
               title=f'{SITE_NAME}  Summer (JAS) days >= {thr}C  {target_year}')

        t0, t1 = df_year.index[0], df_year.index[-1]
        slug = _ascii(SITE_NAME).lower().replace(' ', '_')
        out = os.path.join(out_dir,
            f"{slug}_{SITE_CODE}_thresholds_{thr}C"
            f"_{t0.strftime('%Y%m%d')}_{t1.strftime('%Y%m%d')}.png")
        _save(fig, out, dpi=DPI, bbox_inches='tight')
        plt.close(fig)
        print(f"  [thresh {thr}C]  {os.path.basename(out)}  ({os.path.getsize(out)//1024} KB)")


# ══════════════════════════════════════════════════════════════════════════════
# Generate plots per year
# ══════════════════════════════════════════════════════════════════════════════

for year in [2025, 2026]:
    df_year = df_full[df_full.index.year == year].copy()
    if df_year.empty:
        print(f"\nYear {year}: sin datos — omitido")
        continue
    raw_gaps = df_year.index.to_series().diff()
    big_gaps = raw_gaps[raw_gaps > pd.Timedelta('7D')]
    if not big_gaps.empty:
        for gap_end, dur in big_gaps.items():
            gap_start = gap_end - dur
            print(f"  AVISO — Sin datos: {gap_start.strftime('%d %b')} → "
                  f"{gap_end.strftime('%d %b %Y')} ({int(dur.days)} días) — se mostrará en blanco")
    df_year = df_year.resample('h').mean()
    t0y, t1y = df_year.dropna(how='all').index[0], df_year.dropna(how='all').index[-1]
    print(f"\n{'='*60}\nYear {year}: {t0y.strftime('%d %b %Y')} "
          f"--> {t1y.strftime('%d %b %Y')}  ({len(df_year)} filas)")

    out_dir = os.path.join(OUTPUT_BASE, str(year))
    os.makedirs(out_dir, exist_ok=True)

    plot_annual_T_cycle(df_year, str(year), out_dir, hist_df=df_hist)
    plot_anomaly(df_year, str(year), out_dir, hist_df=df_hist)
    plot_stratification(df_year, str(year), out_dir)
    plot_thresholds(df_year, str(year), out_dir, hist_df=df_hist)

    # ── Rename to T-MEDNet convention ─────────────────────────────────────────
    today_rename = pd.Timestamp.now().strftime('%Y-%m-%d')
    site_tag     = f"{SITE_CODE:02d}"
    _rename_map  = {
        'annual_T_cycle':  f"{site_tag}_2_{year}_{SITE_NAME_FILE}_{today_rename}.png",
        'anomaly':         f"{site_tag}_4_{year}_{SITE_NAME_FILE}_{today_rename}.png",
        'stratification':  f"{site_tag}_1_{year}_{SITE_NAME_FILE}_{today_rename}.png",
    }
    for thr in range(23, 28):
        _rename_map[f'thresholds_{thr}C'] = \
            f"{site_tag}_3_{thr}_{year}_{SITE_NAME_FILE}_{today_rename}.png"

    print()
    for fname in os.listdir(out_dir):
        if not fname.endswith('.png'):
            continue
        for key, new_name in _rename_map.items():
            if key in fname:
                src = os.path.join(out_dir, fname)
                dst = os.path.join(out_dir, new_name)
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(src, dst)
                print(f"  [rename]  {fname}  →  {new_name}")
                break


# ══════════════════════════════════════════════════════════════════════════════
# Database_T merged  (historical + HOBO)
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("Generando Database_T y Stat_Report completos...")

insitu_cols = [c for c in all_depth_cols if c != '0']
t0_all = df_full.index[0]; t1_all = df_full.index[-1]
date_range = f"{t0_all.strftime('%Y%m')}-{t1_all.strftime('%Y%m')}"
today_str  = pd.Timestamp.now().strftime('%Y-%m-%d')

txt_name = f"{SITE_CODE}_Database_T_{SITE_NAME}_{date_range}_{today_str}.txt"
txt_path = os.path.join(OUTPUT_BASE, txt_name)
df_db = df_full[insitu_cols].copy()
df_db.insert(0, 'Date', df_full.index.strftime('%d/%m/%Y'))
df_db.insert(1, 'Time', df_full.index.strftime('%H:%M:%S'))
df_db.to_csv(txt_path, sep='\t', index=False, float_format='%.3f')
print(f"\n  [Database_T .txt]  {txt_name}  ({os.path.getsize(txt_path)//1024} KB)")

zip_name = f"Database_T_{SITE_CODE}_{SITE_NAME}_{date_range}_{today_str}.zip"
zip_path = os.path.join(OUTPUT_BASE, zip_name)
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    internal = f"Database_T_{SITE_CODE}_{SITE_NAME}_{date_range}_{today_str}.txt"
    zf.write(txt_path, arcname=internal)
print(f"  [Database_T .zip]  {zip_name}  ({os.path.getsize(zip_path)//1024} KB)  <- t-outputs")

# ══════════════════════════════════════════════════════════════════════════════
# Stat_Report Excel
# ══════════════════════════════════════════════════════════════════════════════

df_ex_date = pd.to_datetime(df_full.index.strftime('%Y-%m-%d'))
ex_month   = df_full.index.month
ex_year    = df_full.index.year
df_season  = df_full[df_full.index.month.isin([7, 8, 9])]
s_year     = df_season.index.year

daily_p, monthly_p, seasonal_p = [], [], []

for col in insitu_cols:
    depth = int(col)
    sys.stdout.write(f"  depth {col}m... "); sys.stdout.flush()

    agg_d = df_full.groupby(df_ex_date)[col].agg(['count','mean','std','max','min']).round(3)
    agg_d.columns = ['N','mean','std','max','min']
    agg_d = agg_d.reset_index().rename(columns={'index':'date'})
    agg_d['depth(m)'] = depth
    daily_p.append(agg_d[['date','depth(m)','N','mean','std','max','min']])

    agg_m = df_full.groupby([ex_year, ex_month])[col].agg(['count','mean','std','max','min']).round(3)
    agg_m.columns = ['N','mean','std','max','min']
    agg_m = agg_m.reset_index(); agg_m.columns = ['year','month','N','mean','std','max','min']
    agg_m['depth(m)'] = depth
    for thr in [24, 25, 26]:
        agg_m[f'Ndays>={thr}'] = np.round(
            (df_full[col] >= thr).astype(int).groupby([ex_year, ex_month]).sum().values / 24)
    monthly_p.append(agg_m[['year','month','depth(m)','N','mean','std','max','min',
                              'Ndays>=24','Ndays>=25','Ndays>=26']])

    if not df_season.empty and col in df_season.columns:
        agg_s = df_season.groupby(s_year)[col].agg(['count','mean','std','max','min']).round(3)
        agg_s.columns = ['N','mean','std','max','min']
        agg_s = agg_s.reset_index(); agg_s.columns = ['year','N','mean','std','max','min']
        agg_s['season'] = 3; agg_s['depth(m)'] = depth
        for thr in [23, 24, 25, 26, 27, 28]:
            vals = (df_season[col] >= thr).astype(int).groupby(s_year).sum()
            agg_s[f'Ndays>={thr}'] = np.round(
                vals.reindex(agg_s['year']).fillna(0).values / 24)
        seasonal_p.append(agg_s[['year','season','depth(m)','N','mean','std','max','min',
                                   'Ndays>=23','Ndays>=24','Ndays>=25',
                                   'Ndays>=26','Ndays>=27','Ndays>=28']])
    print("ok")

dfexcel   = pd.concat(daily_p,   ignore_index=True).sort_values(['date','depth(m)'])
dfmonthly = pd.concat(monthly_p, ignore_index=True).sort_values(['year','month','depth(m)'])
dfseasonal= pd.concat(seasonal_p,ignore_index=True).sort_values(['year','depth(m)']) \
            if seasonal_p else pd.DataFrame()

dfexcel['year']  = pd.DatetimeIndex(dfexcel['date']).year
dfexcel['month'] = pd.DatetimeIndex(dfexcel['date']).month
dfexcel['date']  = dfexcel['date'].apply(lambda d: d.date())

_nona        = dfexcel.dropna(subset=['max'])
dfmaxes      = dfexcel.loc[_nona.groupby('year')['max'].idxmax()]\
                        [['year','date','max']].sort_values('max', ascending=False)
dfmaxes_dep  = dfexcel.loc[_nona.groupby(['year','depth(m)'])['max'].idxmax()]\
                        [['year','depth(m)','date','max']]\
                        .sort_values(['depth(m)','max'], ascending=False)
dfmaxes_mon  = dfexcel.loc[_nona.groupby(['year','month'])['max'].idxmax()]\
                        [['year','month','date','max']].sort_values('max', ascending=False)
dfmaxes_dm   = dfexcel.loc[_nona.groupby(['year','month','depth(m)'])['max'].idxmax()]\
                        [['year','month','depth(m)','date','max']]\
                        .sort_values(['depth(m)','max'], ascending=False)
df30 = dfexcel.groupby('year')['mean']\
              .apply(lambda g: round(float(g.nlargest(30).mean()), 2))\
              .reset_index()
df30.columns = ['year','30tmax']

def _compute_mhw_sheets(dfexcel, clim_start, clim_end):
    """Detect MHW events per depth (Hobday et al. 2016) using core/marineHeatWaves.py."""
    try:
        import marineHeatWaves as _mhw
    except ImportError:
        return pd.DataFrame(), pd.DataFrame()
    _cn = {'Moderate': 'Moderat', 'Strong': 'Fort', 'Severe': 'Sever', 'Extreme': 'Extrem'}
    all_ev = []
    for depth in sorted(dfexcel['depth(m)'].unique()):
        sub = dfexcel[dfexcel['depth(m)'] == depth][['date', 'mean']].copy()
        sub['date'] = pd.to_datetime(sub['date'])
        sub = sub.dropna(subset=['mean']).sort_values('date')
        if sub.empty:
            continue
        fy, ly = int(sub['date'].dt.year.min()), int(sub['date'].dt.year.max())
        es, ee = max(clim_start, fy), min(clim_end, ly)
        if ((sub['date'].dt.year >= es) & (sub['date'].dt.year <= ee)).sum() < 365 or es >= ee:
            continue
        t    = np.array([d.toordinal() for d in sub['date'].dt.date])
        temp = sub['mean'].values
        try:
            mhws, _ = _mhw.detect(t, temp, climatologyPeriod=[es, ee], maxPadLength=10)
        except Exception:
            continue
        for i in range(mhws.get('n_events', 0)):
            all_ev.append({
                'year': mhws['date_start'][i].year, 'depth(m)': depth,
                'start': mhws['date_start'][i], 'end': mhws['date_end'][i],
                'peak_date': mhws['date_peak'][i],
                'duration_days': int(mhws['duration'][i]),
                'max_temp(ºC)':          round(float(mhws['intensity_max_abs'][i]),  2),
                'max_intensity(ºC)':     round(float(mhws['intensity_max'][i]),       2),
                'mean_intensity(ºC)':    round(float(mhws['intensity_mean'][i]),      2),
                'cum_intensity(ºC·day)': round(float(mhws['intensity_cumulative'][i]),2),
                'category': _cn.get(mhws['category'][i], str(mhws['category'][i])),
                'clim_period': f'{es}-{ee}',
            })
    if not all_ev:
        return pd.DataFrame(), pd.DataFrame()
    df_mhw = pd.DataFrame(all_ev).sort_values(['depth(m)', 'start'])
    _co = {'Moderat': 1, 'Fort': 2, 'Sever': 3, 'Extrem': 4}
    smr = []
    for (yr, dep), g in df_mhw.groupby(['year', 'depth(m)']):
        wc = max(g['category'], key=lambda c: _co.get(c, 0))
        smr.append({
            'year': yr, 'depth(m)': dep, 'n_events': len(g),
            'total_days': int(g['duration_days'].sum()),
            'max_temp(ºC)':          round(float(g['max_temp(ºC)'].max()),        2),
            'max_intensity(ºC)':     round(float(g['max_intensity(ºC)'].max()),   2),
            'max_duration_days':     int(g['duration_days'].max()),
            'cum_intensity(ºC·day)': round(float(g['cum_intensity(ºC·day)'].sum()), 2),
            'worst_category': wc, 'clim_period': g['clim_period'].iloc[0],
        })
    return df_mhw, pd.DataFrame(smr).sort_values(['depth(m)', 'year'])


df_mhw, df_mhw_max = _compute_mhw_sheets(dfexcel, MHW_CLIM_START, MHW_CLIM_END)
print(f"  MHW events: {len(df_mhw)}")

xl_name = f"{SITE_CODE}_Stat_Report_{SITE_NAME}_{date_range}_{today_str}.xlsx"
xl_path = os.path.join(OUTPUT_BASE, xl_name)
with ExcelWriter(xl_path, engine='openpyxl') as writer:
    dfexcel.to_excel(writer,     sheet_name='Daily',             index=False)
    dfmonthly.to_excel(writer,   sheet_name='Monthly',           index=False)
    if not dfseasonal.empty:
        dfseasonal.to_excel(writer, sheet_name='Seasonal',       index=False)
    dfmaxes.to_excel(writer,     sheet_name='Maxes',             index=False)
    dfmaxes_dep.to_excel(writer, sheet_name='Maxes depth',       index=False)
    dfmaxes_mon.to_excel(writer, sheet_name='Maxes month',       index=False)
    dfmaxes_dm.to_excel(writer,  sheet_name='Maxes depth month', index=False)
    df30.to_excel(writer,        sheet_name='30Tmax',            index=False)
    df_mhw.to_excel(writer,      sheet_name='MHW',               index=False)
    df_mhw_max.to_excel(writer,  sheet_name='MHW_MAX',           index=False)

print(f"  [Excel]  {xl_name}  ({os.path.getsize(xl_path)//1024} KB)  <- t-outputs")
print(f"\nHecho. Todo en: {OUTPUT_BASE}")
