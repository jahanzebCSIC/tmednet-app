"""
generate_complete_mpa_data.py
Genera datos MHW completos para TODOS los AMPs del Mediterráneo.
- Calcula MHW para todos los años 1993-2024 (no solo años de mortalidad)
- Añade tendencia de calentamiento SST (°C/década)
- Usa cache existente, descarga lo que falte
- Output: src/data/mpas.json y src/data/mpa_years.json actualizados
"""
import os, sys, json, warnings, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
warnings.filterwarnings("ignore")

import sys, io
# Force UTF-8 stdout on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import copernicusmarine
import marineHeatWaves as mhw_lib
from scipy import stats

# ── Config ─────────────────────────────────────────────────────────────────────
CACHE_DIR    = r'c:\tmednet-app\cache\sst_cache'
MPA_JSON_IN  = r'c:\tmednet-app\mapamed_mpas.json'
OUT_MPAS     = r'c:\tmednet-app\mpa-dashboard\src\data\mpas.json'
OUT_YEARS    = r'c:\tmednet-app\mpa-dashboard\src\data\mpa_years.json'
OUT_EXCEL    = r'c:\tmednet-app\MPA_MHW_Mediterraneo_v2.xlsx'

DATASET_ID   = 'cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021'
VARIABLE     = 'analysed_sst'
DELTA        = 0.1
CLIM_START   = 1982
CLIM_END     = 2011
YEARS        = list(range(1982, 2025))   # 1982-2024
SUMMER       = [6, 7, 8, 9]
CAT_MAP      = {1:'Moderate', 2:'Strong', 3:'Severe', 4:'Extreme'}

os.makedirs(CACHE_DIR, exist_ok=True)

# ── SST helpers ────────────────────────────────────────────────────────────────
def cache_path(lat_r, lon_r):
    return os.path.join(CACHE_DIR, f"sst_{lat_r:.2f}_{lon_r:.2f}.csv")

def load_cached(lat_r, lon_r):
    cp = cache_path(lat_r, lon_r)
    if not os.path.exists(cp):
        return None
    sst = pd.read_csv(cp, index_col=0, parse_dates=True)['sst']
    sst.index = pd.to_datetime(sst.index, errors='coerce').tz_localize(None)
    return sst.dropna() if len(sst) > 365 else None

def download_sst(lat_r, lon_r, name=''):
    sst = load_cached(lat_r, lon_r)
    if sst is not None:
        return sst
    try:
        ds = copernicusmarine.open_dataset(
            dataset_id=DATASET_ID, variables=[VARIABLE],
            minimum_longitude=lon_r - DELTA, maximum_longitude=lon_r + DELTA,
            minimum_latitude=lat_r  - DELTA, maximum_latitude=lat_r  + DELTA,
        )
        s = ds[VARIABLE].sel(latitude=lat_r, longitude=lon_r, method='nearest').to_series()
        if s.mean() > 100:
            s = s - 273.15
        s.index = pd.to_datetime(s.index).tz_localize(None)
        s = s.dropna().rename('sst')
        if len(s) == 0:
            return None
        s.to_csv(cache_path(lat_r, lon_r), header=True)
        return s
    except Exception as e:
        print(f"    ERROR SST ({lat_r:.2f},{lon_r:.2f}) {name}: {e}")
        return None

def detect_mhws(sst_series):
    if sst_series is None or len(sst_series) < 365 * 5:
        return None, None
    daily = sst_series.resample('D').mean().dropna()
    if len(daily) < 365 * 5:
        return None, None
    t  = np.array([d.toordinal() for d in [x.date() for x in daily.index]])
    ss = daily.values.astype(float)
    try:
        return mhw_lib.detect(t, ss, climatologyPeriod=[CLIM_START, CLIM_END], pctile=90)
    except:
        return None, None

def summer_stats(mhws, year):
    empty = dict(MHW_detected='N', N_events=0, Total_days=0,
                 Max_intensity=None, Cum_intensity=None,
                 Mean_intensity=None, Max_category=None, Max_cat_name=None)
    if mhws is None or len(mhws['date_start']) == 0:
        return empty
    s_start = datetime.date(year, 6, 1)
    s_end   = datetime.date(year, 9, 30)
    n_ev = tot_d = cum_i = max_c = 0
    max_i = -np.inf
    mean_is = []
    for i in range(len(mhws['date_start'])):
        ev_s, ev_e = mhws['date_start'][i], mhws['date_end'][i]
        if ev_s > s_end or ev_e < s_start:
            continue
        ol_s = max(ev_s, s_start); ol_e = min(ev_e, s_end)
        days = (ol_e - ol_s).days + 1
        if days <= 0:
            continue
        n_ev  += 1
        tot_d += days
        max_i  = max(max_i, mhws['intensity_max'][i])
        cum_i += mhws['intensity_cumulative'][i]
        mean_is.append(mhws['intensity_mean'][i])
        cat_str = str(mhws['category'][i])
        cat = {'Moderate':1,'Strong':2,'Severe':3,'Extreme':4}.get(cat_str, 0)
        max_c = max(max_c, cat)
    if n_ev == 0:
        return empty
    return dict(MHW_detected='Y', N_events=n_ev, Total_days=tot_d,
                Max_intensity=round(float(max_i),2),
                Cum_intensity=round(float(cum_i),2),
                Mean_intensity=round(float(np.mean(mean_is)),2),
                Max_category=max_c,
                Max_cat_name=CAT_MAP.get(max_c,''))

def summer_mean_sst(sst_series, year):
    """Media SST de junio-septiembre para un año dado."""
    if sst_series is None:
        return None
    mask = (sst_series.index.year == year) & (sst_series.index.month.isin(SUMMER))
    vals = sst_series[mask]
    return round(float(vals.mean()), 3) if len(vals) >= 30 else None

def warming_trend(sst_series):
    """Tendencia lineal SST media estival. Retorna (slope_per_decade, r2, p_value)."""
    if sst_series is None:
        return None, None, None
    records = []
    for y in YEARS:
        v = summer_mean_sst(sst_series, y)
        if v is not None:
            records.append((y, v))
    if len(records) < 10:
        return None, None, None
    xs = np.array([r[0] for r in records])
    ys = np.array([r[1] for r in records])
    slope, intercept, r, p, se = stats.linregress(xs, ys)
    return round(slope * 10, 3), round(r**2, 3), round(p, 4)

# ── Cargar AMPs existentes ─────────────────────────────────────────────────────
print("Cargando AMPs existentes...")
with open(MPA_JSON_IN, encoding='utf-8') as f:
    mpas_in = json.load(f)

print(f"  {len(mpas_in)} AMPs cargados")

# ── Procesar cada AMP ─────────────────────────────────────────────────────────
print(f"\nCalculando MHW para {len(mpas_in)} AMPs × {len(YEARS)} años...\n")

all_year_rows = []
mpa_summaries = []

for idx, mpa in enumerate(mpas_in):
    name    = mpa['NAME']
    lat     = mpa['Lat']
    lon     = mpa['Lon']
    country = mpa['Country']
    desig   = mpa.get('DESIG_ENG', '')

    # Usar coordenada oceánica si build_ocean_mask_and_snap.py ya la calculó
    lat_r = round(mpa.get('SST_Lat') or lat, 2) if mpa.get('SST_Lat') else round(round(lat / 0.05) * 0.05, 2)
    lon_r = round(mpa.get('SST_Lon') or lon, 2) if mpa.get('SST_Lon') else round(round(lon / 0.05) * 0.05, 2)

    cached = load_cached(lat_r, lon_r)
    label  = '(cache)' if cached is not None else '(descarga)'
    safe_name = name[:50].encode('ascii', errors='replace').decode('ascii')
    print(f"[{idx+1:3}/{len(mpas_in)}] {label} {safe_name}")

    sst = download_sst(lat_r, lon_r, name)

    if sst is None:
        print(f"    Sin SST - saltando")
        mpa_summaries.append({
            'MAPAMED_ID': mpa.get('MAPAMED_ID'), 'NAME': name, 'Country': country,
            'DESIG_ENG': desig, 'DESIG_TYPE': mpa.get('DESIG_TYPE'),
            'SITE_TYPE': mpa.get('SITE_TYPE'), 'IUCN_CAT': mpa.get('IUCN_CAT'),
            'GIS_M_AREA': mpa.get('GIS_M_AREA'), 'GIS_M_PCT': mpa.get('GIS_M_PCT'),
            'STATUS_YR': mpa.get('STATUS_YR'),
            'Lat': lat, 'Lon': lon,
            'Years_with_data': 0, 'Year_min': None, 'Year_max': None,
            'Years_with_MHW': 0, 'Pct_MHW': None,
            'Max_intensity_ever': None, 'Max_category_ever': None,
            'Warming_trend_per_decade': None, 'Trend_R2': None, 'Trend_p': None,
            'SST_available': False,
        })
        continue

    mhws, clim = detect_mhws(sst)
    trend, r2, pval = warming_trend(sst)

    year_rows = []
    for y in YEARS:
        sst_mean = summer_mean_sst(sst, y)
        if sst_mean is None:
            continue
        st = summer_stats(mhws, y)
        row = {
            'NAME': name, 'Country': country, 'Year': y,
            'SST_summer_mean': sst_mean,
            **st
        }
        year_rows.append(row)

    years_with_data = [r['Year'] for r in year_rows]
    years_with_mhw  = [r['Year'] for r in year_rows if r['MHW_detected'] == 'Y']

    intensities = [r['Max_intensity'] for r in year_rows if r['Max_intensity'] is not None]
    categories  = [r['Max_category']  for r in year_rows if r['Max_category']  is not None]

    n_data = len(years_with_data)
    n_mhw  = len(years_with_mhw)
    pct    = round(100 * n_mhw / n_data) if n_data > 0 else None

    mpa_summaries.append({
        'MAPAMED_ID': mpa.get('MAPAMED_ID'), 'NAME': name, 'Country': country,
        'DESIG_ENG': desig, 'DESIG_TYPE': mpa.get('DESIG_TYPE'),
        'SITE_TYPE': mpa.get('SITE_TYPE'), 'IUCN_CAT': mpa.get('IUCN_CAT'),
        'GIS_M_AREA': mpa.get('GIS_M_AREA'), 'GIS_M_PCT': mpa.get('GIS_M_PCT'),
        'STATUS_YR': mpa.get('STATUS_YR'),
        'Lat': lat, 'Lon': lon,
        'Years_with_data': n_data,
        'Year_min': int(min(years_with_data)) if years_with_data else None,
        'Year_max': int(max(years_with_data)) if years_with_data else None,
        'Years_with_MHW': n_mhw,
        'Pct_MHW': pct,
        'Max_intensity_ever': round(float(max(intensities)), 2) if intensities else None,
        'Max_category_ever': int(max(categories)) if categories else None,
        'Warming_trend_per_decade': trend,
        'Trend_R2': r2,
        'Trend_p': pval,
        'SST_available': True,
    })

    all_year_rows.extend(year_rows)

    n_mhw_str = f"{n_mhw}/{n_data} años con MHW ({pct}%)" if n_data else "sin datos"
    trend_str  = f"trend={trend}°C/dec" if trend else "sin trend"
    print(f"    {n_mhw_str} | {trend_str}")

# ── Guardar JSONs ──────────────────────────────────────────────────────────────
print(f"\nGuardando JSONs...")

def clean(v):
    if v is None: return None
    try:
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)): return None
    except Exception: pass
    return v

def clean_dict(d):
    return {k: clean(v) for k, v in d.items()}

# mpas.json — actualizado con nuevos campos
mpa_summaries_clean = [clean_dict(m) for m in mpa_summaries]
with open(OUT_MPAS, 'w', encoding='utf-8') as f:
    json.dump(mpa_summaries_clean, f, ensure_ascii=False, indent=2)
print(f"  {OUT_MPAS}: {len(mpa_summaries)} AMPs")

# mpa_years.json — cobertura completa

year_rows_clean = [{k: clean(v) for k, v in r.items()} for r in all_year_rows]
with open(OUT_YEARS, 'w', encoding='utf-8') as f:
    json.dump(year_rows_clean, f, ensure_ascii=False, indent=2)
print(f"  {OUT_YEARS}: {len(year_rows_clean)} registros AMP×año")

# ── Excel completo ─────────────────────────────────────────────────────────────
print(f"\nGenerando Excel {OUT_EXCEL}...")
try:
    import openpyxl
    df_mpas  = pd.DataFrame(mpa_summaries)
    df_years = pd.DataFrame(year_rows_clean)

    with pd.ExcelWriter(OUT_EXCEL, engine='openpyxl') as writer:
        df_mpas.to_excel(writer, sheet_name='Resumen_AMPs', index=False)
        df_years.to_excel(writer, sheet_name='Detalle_AMP_Ano', index=False)

        ws = writer.sheets['Resumen_AMPs']
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(
                12, max(len(str(c.value or '')) for c in col))
    print(f"  Excel guardado: {OUT_EXCEL}")
except Exception as e:
    print(f"  Excel error: {e}")

# ── Resumen final ──────────────────────────────────────────────────────────────
print("\n" + "="*60)
df_s = pd.DataFrame(mpa_summaries)
print(f"AMPs procesados:        {len(df_s)}")
print(f"AMPs con SST:           {df_s['SST_available'].sum()}")
print(f"AMPs sin SST:           {(~df_s['SST_available']).sum()}")
print(f"Registros AMP×año:      {len(year_rows_clean)}")
df_ok = df_s[df_s['Pct_MHW'].notna()]
print(f"Media años con datos:   {df_ok['Years_with_data'].mean():.1f}")
print(f"Media % con MHW:        {df_ok['Pct_MHW'].mean():.1f}%")
print(f"AMPs con trend calent.: {df_s['Warming_trend_per_decade'].notna().sum()}")
if df_s['Warming_trend_per_decade'].notna().any():
    tr = df_s['Warming_trend_per_decade'].dropna()
    print(f"Trend medio:            {tr.mean():.3f} °C/década")
    print(f"Trend max:              {tr.max():.3f} °C/década")
print("="*60)
print("DONE")
