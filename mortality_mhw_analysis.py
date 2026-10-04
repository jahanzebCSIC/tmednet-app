"""
mortality_mhw_analysis.py
--------------------------
Calcula las Marine Heat Waves (Hobday et al. 2016) para cada localización
con eventos de mortalidad masiva del Mediterráneo.

Fuente de coordenadas y años: Locations_Temperature anomally.xlsx (Lucia)
Datos SST: Copernicus CMEMS - Mediterranean SST L4 multiyear (1982-presente)
Resultado: mortality_mhw_results.xlsx

Uso:
    python mortality_mhw_analysis.py

Los resultados intermedios (series SST por coordenada) se guardan en
cache/sst_cache/ para evitar re-descargas.
"""

import os
import sys
import json
import warnings

# marineHeatWaves.py vive en core/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
import datetime
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Configuración ─────────────────────────────────────────────────────────────
INPUT_XLSX   = r"C:\Users\jahan\Downloads\Locations_Temperature anomally.xlsx"
OUTPUT_XLSX  = r"C:\tmednet-app\mortality_mhw_results.xlsx"
CACHE_DIR    = r"C:\tmednet-app\cache\sst_cache"

# Dataset CMEMS mediterráneo reprocessed L4 (cubre 1982-presente)
DATASET_ID   = "cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021"
VARIABLE     = "analysed_sst"
DELTA        = 0.1   # grados alrededor del punto central para la descarga

# Meses de verano para el análisis de mortalidad
SUMMER_MONTHS = [6, 7, 8, 9]  # Junio-Septiembre

# Período de referencia para climatología MHW (Hobday 2016)
CLIM_START   = 1993
CLIM_END     = 2016

os.makedirs(CACHE_DIR, exist_ok=True)

# ── Importar librerías ─────────────────────────────────────────────────────────
try:
    import copernicusmarine
except ImportError:
    sys.exit("ERROR: instala copernicusmarine:  pip install copernicusmarine")

try:
    import marineHeatWaves as mhw
except ImportError:
    sys.exit("ERROR: instala marineHeatWaves:  pip install marineHeatWaves")


# ── 1. Leer y expandir el Excel de mortalidad ─────────────────────────────────
print("Leyendo Locations_Temperature anomally.xlsx...")
df_raw = pd.read_excel(INPUT_XLSX)

rows = []
for _, r in df_raw.iterrows():
    years_str = str(r['Years']).strip()
    years = [int(y.strip()) for y in years_str.split(',') if y.strip().isdigit()]
    for y in years:
        rows.append({
            'Country':   r['Country'],
            'Location':  r['Location'],
            'Latitude':  round(float(r['Latitude']),  4),
            'Longitude': round(float(r['Longitude']), 4),
            'Year':      y,
        })

df = pd.DataFrame(rows)
df['lat_r'] = (df['Latitude']  / 0.05).round() * 0.05
df['lon_r'] = (df['Longitude'] / 0.05).round() * 0.05

print(f"  {len(df)} eventos de mortalidad | {df[['lat_r','lon_r']].drop_duplicates().shape[0]} celdas únicas")


# ── 2. Descarga SST + detección MHW por celda ─────────────────────────────────

def cache_path(lat_r, lon_r):
    return os.path.join(CACHE_DIR, f"sst_{lat_r:.2f}_{lon_r:.2f}.csv")


def download_sst(lat_r, lon_r):
    cp = cache_path(lat_r, lon_r)
    if os.path.exists(cp):
        sst = pd.read_csv(cp, index_col=0, parse_dates=True)['sst']
        sst.index = pd.to_datetime(sst.index, errors='coerce').tz_localize(None)
        sst = sst.dropna()
        return sst if len(sst) > 365 else None

    try:
        ds = copernicusmarine.open_dataset(
            dataset_id=DATASET_ID,
            variables=[VARIABLE],
            minimum_longitude=lon_r - DELTA,
            maximum_longitude=lon_r + DELTA,
            minimum_latitude=lat_r  - DELTA,
            maximum_latitude=lat_r  + DELTA,
        )
        sst_s = (ds[VARIABLE]
                 .sel(latitude=lat_r, longitude=lon_r, method="nearest")
                 .to_series())
        if sst_s.mean() > 100:        # Kelvin → Celsius
            sst_s = sst_s - 273.15
        sst_s.index = pd.to_datetime(sst_s.index).tz_localize(None)
        sst_s = sst_s.dropna().rename("sst")
        if len(sst_s) == 0:
            return None
        sst_s.to_csv(cp, header=True)
        return sst_s
    except Exception as e:
        print(f"    ERROR descargando ({lat_r:.2f},{lon_r:.2f}): {e}")
        return None


def detect_mhws(sst_series):
    """Devuelve (mhws_dict, clim_dict) o (None, None) si datos insuficientes."""
    if sst_series is None or len(sst_series) < 365 * 5:
        return None, None
    daily = sst_series.resample('D').mean().dropna()
    if len(daily) < 365 * 5:
        return None, None

    dates = [d.date() for d in daily.index]
    t  = np.array([d.toordinal() for d in dates])
    ss = daily.values.astype(float)

    try:
        mhws, clim = mhw.detect(t, ss,
                                 climatologyPeriod=[CLIM_START, CLIM_END],
                                 pctile=90)
        return mhws, clim
    except Exception as e:
        print(f"    ERROR en MHW detect: {e}")
        return None, None


def summer_mhw_stats(mhws, year):
    """
    Extrae estadísticas de los eventos MHW que solapan con el verano
    (junio-septiembre) del año dado.
    Retorna dict con campos de resumen.
    """
    empty = {
        'MHW_detected': 'N',
        'N_events':      0,
        'Total_days':    0,
        'Max_intensity': np.nan,
        'Cum_intensity': np.nan,
        'Mean_intensity': np.nan,
        'Max_category':  np.nan,
        'Max_cat_name':  '',
    }

    if mhws is None or len(mhws['date_start']) == 0:
        return empty

    summer_start = datetime.date(year, 6, 1)
    summer_end   = datetime.date(year, 9, 30)
    cat_names    = {1: 'Moderate', 2: 'Strong', 3: 'Severe', 4: 'Extreme'}

    n_events = 0
    total_days = 0
    max_int    = -np.inf
    cum_int    = 0.0
    mean_ints  = []
    max_cat    = 0

    for i in range(len(mhws['date_start'])):
        ev_start = mhws['date_start'][i]
        ev_end   = mhws['date_end'][i]

        # Solapamiento con verano del año
        if ev_start > summer_end or ev_end < summer_start:
            continue

        # Días dentro del verano
        overlap_start = max(ev_start, summer_start)
        overlap_end   = min(ev_end,   summer_end)
        days_in_summer = (overlap_end - overlap_start).days + 1
        if days_in_summer <= 0:
            continue

        n_events    += 1
        total_days  += days_in_summer
        max_int      = max(max_int, mhws['intensity_max'][i])
        cum_int     += mhws['intensity_cumulative'][i]
        mean_ints.append(mhws['intensity_mean'][i])

        cat_str = str(mhws['category'][i])
        cat = {'Moderate': 1, 'Strong': 2, 'Severe': 3, 'Extreme': 4}.get(cat_str, 0)
        max_cat = max(max_cat, cat)

    if n_events == 0:
        return empty

    return {
        'MHW_detected':  'Y',
        'N_events':       n_events,
        'Total_days':     total_days,
        'Max_intensity':  round(max_int,  2),
        'Cum_intensity':  round(cum_int,  2),
        'Mean_intensity': round(float(np.mean(mean_ints)), 2),
        'Max_category':   max_cat,
        'Max_cat_name':   cat_names.get(max_cat, ''),
    }


# ── 3. Iterar por celdas únicas ───────────────────────────────────────────────
unique_cells = df.groupby(['lat_r', 'lon_r']).apply(lambda x: x['Year'].unique()).reset_index()
unique_cells.columns = ['lat_r', 'lon_r', 'years']

print(f"\nProcesando {len(unique_cells)} celdas únicas...\n")

# Almacenar MHW por celda para reutilizar
cell_mhws = {}   # (lat_r, lon_r) → (mhws, clim)

results = []

for idx, cell_row in unique_cells.iterrows():
    lat_r = cell_row['lat_r']
    lon_r = cell_row['lon_r']
    years = cell_row['years']

    print(f"[{idx+1:3}/{len(unique_cells)}] ({lat_r:.2f}, {lon_r:.2f})  años: {sorted(years)}")

    # Descarga/caché SST
    sst = download_sst(lat_r, lon_r)
    if sst is None:
        # Sin datos: añadir fila vacía para cada evento en esta celda
        cell_events = df[(df['lat_r'] == lat_r) & (df['lon_r'] == lon_r)]
        for _, ev in cell_events.iterrows():
            row = {**ev.to_dict(), 'Data_available': 'N',
                   'SST_years_available': 0, **{k: np.nan for k in
                   ['MHW_detected','N_events','Total_days','Max_intensity',
                    'Cum_intensity','Mean_intensity','Max_category','Max_cat_name']}}
            row['MHW_detected'] = 'N/A'
            results.append(row)
        continue

    n_years = sst.index.year.max() - sst.index.year.min() + 1
    print(f"       SST: {sst.index.min().date()} – {sst.index.max().date()}  ({n_years} años)")

    # Detección MHW (una vez por celda)
    if (lat_r, lon_r) not in cell_mhws:
        mhws_d, clim_d = detect_mhws(sst)
        cell_mhws[(lat_r, lon_r)] = (mhws_d, clim_d)
    else:
        mhws_d, clim_d = cell_mhws[(lat_r, lon_r)]

    # Estadísticas de verano para cada año de mortalidad de la celda
    cell_events = df[(df['lat_r'] == lat_r) & (df['lon_r'] == lon_r)]

    for _, ev in cell_events.iterrows():
        year = ev['Year']

        # ¿Datos SST disponibles para ese año?
        if sst.index.year.max() < year or sst.index.year.min() > year:
            stats = {'MHW_detected': 'N/A (fuera de rango)',
                     'N_events': np.nan, 'Total_days': np.nan,
                     'Max_intensity': np.nan, 'Cum_intensity': np.nan,
                     'Mean_intensity': np.nan, 'Max_category': np.nan,
                     'Max_cat_name': ''}
        else:
            stats = summer_mhw_stats(mhws_d, year)

        row = {
            'Country':   ev['Country'],
            'Location':  ev['Location'],
            'Latitude':  ev['Latitude'],
            'Longitude': ev['Longitude'],
            'Year':      year,
            'Lat_grid':  lat_r,
            'Lon_grid':  lon_r,
            'Data_available': 'Y' if sst is not None else 'N',
            'SST_start': sst.index.min().date() if sst is not None else np.nan,
            'SST_end':   sst.index.max().date() if sst is not None else np.nan,
        }
        row.update(stats)
        results.append(row)

    print(f"       MHW eventos totales: {len(mhws_d['date_start']) if mhws_d else 'N/A'}")


# ── 4. Construir y exportar tabla de resultados ───────────────────────────────
print("\nGuardando resultados...")
df_out = pd.DataFrame(results)

# Ordenar
df_out = df_out.sort_values(['Country', 'Location', 'Year']).reset_index(drop=True)

# Columnas en orden final
cols = [
    'Country', 'Location', 'Latitude', 'Longitude', 'Year',
    'Lat_grid', 'Lon_grid', 'Data_available', 'SST_start', 'SST_end',
    'MHW_detected', 'N_events', 'Total_days',
    'Max_intensity', 'Cum_intensity', 'Mean_intensity',
    'Max_category', 'Max_cat_name',
]
df_out = df_out[[c for c in cols if c in df_out.columns]]

with pd.ExcelWriter(OUTPUT_XLSX, engine='openpyxl') as writer:
    df_out.to_excel(writer, sheet_name='MHW_Mortality', index=False)

    # Hoja de resumen por país
    summary = (df_out[df_out['MHW_detected'] == 'Y']
               .groupby('Country')
               .agg(
                   Locations=('Location', 'nunique'),
                   Events_with_MHW=('MHW_detected', 'count'),
                   Avg_max_intensity=('Max_intensity', 'mean'),
                   Avg_total_days=('Total_days', 'mean'),
                   Max_category_observed=('Max_category', 'max'),
               )
               .round(2)
               .reset_index())
    summary.to_excel(writer, sheet_name='Summary_by_Country', index=False)

    # Hoja de resumen por año
    year_summary = (df_out[df_out['MHW_detected'] == 'Y']
                    .groupby('Year')
                    .agg(
                        N_locations=('Location', 'count'),
                        Avg_max_intensity=('Max_intensity', 'mean'),
                        Avg_total_days=('Total_days', 'mean'),
                        Max_category_observed=('Max_category', 'max'),
                    )
                    .round(2)
                    .reset_index())
    year_summary.to_excel(writer, sheet_name='Summary_by_Year', index=False)

print(f"\n{'='*60}")
print(f"Resultados guardados en: {OUTPUT_XLSX}")
print(f"Total filas: {len(df_out)}")
mhw_y = (df_out['MHW_detected'] == 'Y').sum()
mhw_n = (df_out['MHW_detected'] == 'N').sum()
mhw_na = df_out['MHW_detected'].str.startswith('N/A', na=False).sum()
print(f"Con MHW verano:    {mhw_y}")
print(f"Sin MHW verano:    {mhw_n}")
print(f"Sin datos SST:     {mhw_na}")
print(f"Categorías: {df_out['Max_cat_name'].value_counts().to_dict()}")
