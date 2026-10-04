"""
merge_lucia_mhw.py
Combina MME_TAnomally_MPAs.xlsx (Lucia) con el análisis MHW.
Para las celdas ya en caché reutiliza los datos; descarga las 38 nuevas.
"""
import os, sys, datetime, warnings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import copernicusmarine
import marineHeatWaves as mhw_lib

LUCIA_FILE  = r'C:\Users\jahan\Downloads\Copia de MME_MHW_merged_Lucia (1).xlsx'
MHW_FILE    = r'c:\tmednet-app\mortality_mhw_results.xlsx'
CACHE_DIR   = r'c:\tmednet-app\cache\sst_cache'
OUT_FILE    = r'c:\tmednet-app\MME_MHW_merged_v3.xlsx'
MASK_FILE   = r'c:\tmednet-app\cache\med_ocean_mask.npz'

DATASET_ID  = 'cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021'
VARIABLE    = 'analysed_sst'
DELTA       = 0.1
CLIM_START  = 1982
CLIM_END    = 2011
SUMMER      = [6, 7, 8, 9]

os.makedirs(CACHE_DIR, exist_ok=True)

# ── 0. Cargar máscara oceánica para snap marino ───────────────────────────────
_ocean_tree = None
_ocean_lats = None
_ocean_lons = None

def _load_ocean_tree():
    global _ocean_tree, _ocean_lats, _ocean_lons
    if _ocean_tree is not None:
        return
    if not os.path.exists(MASK_FILE):
        print("  Máscara oceánica no encontrada — snap marino no disponible")
        return
    import numpy as np
    from scipy.spatial import cKDTree
    data = np.load(MASK_FILE)
    _ocean_lats = data['lats']
    _ocean_lons = data['lons']
    _ocean_tree = cKDTree(np.column_stack([_ocean_lats, _ocean_lons]))
    print(f"  Máscara oceánica cargada ({len(_ocean_lats)} píxeles)")

def snap_to_ocean(lat, lon):
    """Devuelve el píxel oceánico más cercano usando la máscara. Fallback al grid simple."""
    _load_ocean_tree()
    if _ocean_tree is None:
        return round(round(lat / 0.05) * 0.05, 2), round(round(lon / 0.05) * 0.05, 2)
    _, idx = _ocean_tree.query([lat, lon])
    return round(float(_ocean_lats[idx]), 2), round(float(_ocean_lons[idx]), 2)

# ── 1. Leer fichero de Lucia ───────────────────────────────────────────────────
print("Leyendo fichero de Lucia (versión corregida)...")
lucia_raw = pd.read_excel(LUCIA_FILE)
# Si el fichero ya tiene columnas MHW, usar solo las columnas originales
mhw_drop = ['Data_available','SST_start','SST_end','MHW_detected','N_events',
            'Total_days','Max_intensity','Cum_intensity','Mean_intensity',
            'Max_category','Max_cat_name','Lat_grid','Lon_grid']
lucia = lucia_raw.drop(columns=[c for c in mhw_drop if c in lucia_raw.columns])

# Snap al píxel oceánico más cercano
snap_results = [snap_to_ocean(row['Latitude'], row['Longitude'])
                for _, row in lucia.iterrows()]
lucia['Lat_grid'] = [r[0] for r in snap_results]
lucia['Lon_grid'] = [r[1] for r in snap_results]
print(f"  {len(lucia)} filas, {lucia[['Lat_grid','Lon_grid']].drop_duplicates().shape[0]} celdas únicas")

# ── 2. SST cache helpers ───────────────────────────────────────────────────────
def cache_path(lat_r, lon_r):
    return os.path.join(CACHE_DIR, f"sst_{lat_r:.2f}_{lon_r:.2f}.csv")

def load_cached(lat_r, lon_r):
    cp = cache_path(lat_r, lon_r)
    if not os.path.exists(cp):
        return None
    sst = pd.read_csv(cp, index_col=0, parse_dates=True)['sst']
    sst.index = pd.to_datetime(sst.index, errors='coerce').tz_localize(None)
    sst = sst.dropna()
    return sst if len(sst) > 365 else None

def download_sst(lat_r, lon_r):
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
        print(f"    ERROR ({lat_r:.2f},{lon_r:.2f}): {e}")
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
                 Max_intensity=np.nan, Cum_intensity=np.nan,
                 Mean_intensity=np.nan, Max_category=np.nan, Max_cat_name='')
    if mhws is None or len(mhws['date_start']) == 0:
        return empty
    s_start = datetime.date(year, 6, 1)
    s_end   = datetime.date(year, 9, 30)
    cat_map = {1:'Moderate', 2:'Strong', 3:'Severe', 4:'Extreme'}
    n_ev = tot_d = max_i = cum_i = max_c = 0
    mean_is = []
    max_i = -np.inf
    for i in range(len(mhws['date_start'])):
        ev_s, ev_e = mhws['date_start'][i], mhws['date_end'][i]
        if ev_s > s_end or ev_e < s_start:
            continue
        ol_s = max(ev_s, s_start); ol_e = min(ev_e, s_end)
        days = (ol_e - ol_s).days + 1
        if days <= 0:
            continue
        n_ev   += 1
        tot_d  += days
        max_i   = max(max_i, mhws['intensity_max'][i])
        cum_i  += mhws['intensity_cumulative'][i]
        mean_is.append(mhws['intensity_mean'][i])
        cat_str = str(mhws['category'][i])
        cat = {'Moderate':1,'Strong':2,'Severe':3,'Extreme':4}.get(cat_str, 0)
        max_c = max(max_c, cat)
    if n_ev == 0:
        return empty
    return dict(MHW_detected='Y', N_events=n_ev, Total_days=tot_d,
                Max_intensity=round(max_i,2), Cum_intensity=round(cum_i,2),
                Mean_intensity=round(float(np.mean(mean_is)),2),
                Max_category=max_c, Max_cat_name=cat_map.get(max_c,''))

# ── 3. Procesar todas las celdas únicas ──────────────────────────────────────
unique_cells = lucia.groupby(['Lat_grid','Lon_grid'])['Year'].unique().reset_index()
print(f"\nProcesando {len(unique_cells)} celdas únicas...\n")

cell_results = {}  # (lat_r, lon_r, year) → stats dict

for idx, row in unique_cells.iterrows():
    lat_r, lon_r, years = row['Lat_grid'], row['Lon_grid'], row['Year']
    cached = load_cached(lat_r, lon_r)
    label  = '(caché)' if cached is not None else '(descarga)'
    print(f"[{idx+1:3}/{len(unique_cells)}] ({lat_r:.2f},{lon_r:.2f}) {label} años={sorted(years)}")

    sst = download_sst(lat_r, lon_r)
    if sst is None:
        for y in years:
            cell_results[(round(lat_r, 2), round(lon_r, 2), int(y))] = dict(
                Data_available='N', SST_start=np.nan, SST_end=np.nan,
                MHW_detected='Sin_SST', N_events=np.nan, Total_days=np.nan,
                Max_intensity=np.nan, Cum_intensity=np.nan,
                Mean_intensity=np.nan, Max_category=np.nan, Max_cat_name='')
        continue

    mhws, _ = detect_mhws(sst)
    sst_start = sst.index.min().date()
    sst_end   = sst.index.max().date()

    for y in years:
        if sst.index.year.max() < y or sst.index.year.min() > y:
            stats = dict(MHW_detected='Fuera_rango',
                         N_events=np.nan, Total_days=np.nan,
                         Max_intensity=np.nan, Cum_intensity=np.nan,
                         Mean_intensity=np.nan, Max_category=np.nan, Max_cat_name='')
        else:
            stats = summer_stats(mhws, y)
        cell_results[(round(lat_r, 2), round(lon_r, 2), int(y))] = dict(
            Data_available='Y', SST_start=sst_start, SST_end=sst_end, **stats)

# ── 4. Añadir columnas MHW a fichero de Lucia ─────────────────────────────────
print("\nGenerando fichero fusionado...")
mhw_cols = ['Data_available','SST_start','SST_end','MHW_detected',
            'N_events','Total_days','Max_intensity','Cum_intensity',
            'Mean_intensity','Max_category','Max_cat_name']

def get_mhw(row):
    key = (round(row['Lat_grid'],2), round(row['Lon_grid'],2), int(row['Year']))
    return pd.Series(cell_results.get(key, {c: np.nan for c in mhw_cols}))

lucia[mhw_cols] = lucia.apply(get_mhw, axis=1)

# Reordenar columnas
front = ['Country','Location','Year','Season','Latitude','Longitude',
         'Lat_grid','Lon_grid','Taxa','Species','Mortality_rate (%)',
         'Damaged qualitative','Lower Depth','Upper Depth',
         'Within_MPA','NAME','DESIG_ENG','SITE_TYPE_ENG']
mhw_c = ['Data_available','SST_start','SST_end','MHW_detected',
         'N_events','Total_days','Max_intensity','Cum_intensity',
         'Mean_intensity','Max_category','Max_cat_name']
final_cols = [c for c in front if c in lucia.columns] + mhw_c
lucia_out = lucia[final_cols]

# ── 5. Exportar ───────────────────────────────────────────────────────────────
with pd.ExcelWriter(OUT_FILE, engine='openpyxl') as writer:
    lucia_out.to_excel(writer, sheet_name='MME_MHW', index=False)

    # Resumen rápido
    sum_data = lucia_out[lucia_out['MHW_detected'].isin(['Y','N'])]
    by_country = sum_data.groupby('Country').agg(
        Filas=('MHW_detected','count'),
        Con_MHW=('MHW_detected', lambda x: (x=='Y').sum()),
    ).reset_index()
    by_country['Pct_MHW'] = (by_country['Con_MHW']/by_country['Filas']*100).round(1)
    by_country.to_excel(writer, sheet_name='Resumen_pais', index=False)

print(f"\nFichero guardado: {OUT_FILE}")
print(f"Total filas: {len(lucia_out)}")
mhw_y = (lucia_out['MHW_detected']=='Y').sum()
mhw_n = (lucia_out['MHW_detected']=='N').sum()
mhw_na= lucia_out['MHW_detected'].isna().sum()
print(f"Con MHW estival: {mhw_y}")
print(f"Sin MHW estival: {mhw_n}")
print(f"Sin datos / N/A: {mhw_na}")
