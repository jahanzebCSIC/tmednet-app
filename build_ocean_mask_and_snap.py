"""
build_ocean_mask_and_snap.py
Solución definitiva para snap de coordenadas a píxel marino:
1. Descarga un día de SST de todo el Mediterráneo → máscara oceánica exacta
   (misma definición tierra/mar que usa nuestro cálculo MHW)
2. Construye KD-tree de todos los píxeles oceánicos válidos
3. Para cada AMP, encuentra el píxel oceánico más cercano
4. Si ese píxel no está en cache, lo descarga de Copernicus
5. Actualiza SST_Lat / SST_Lon en mpas.json
"""
import json, os, sys
import numpy as np
import pandas as pd
import copernicusmarine
from scipy.spatial import cKDTree

MPAS_JSON  = r'C:\tmednet-app\mpa-dashboard\src\data\mpas.json'
CACHE_DIR  = r'C:\tmednet-app\cache\sst_cache'
MASK_FILE  = r'C:\tmednet-app\cache\med_ocean_mask.npz'
DATASET_ID = 'cmems_SST_MED_SST_L4_REP_OBSERVATIONS_010_021'
VARIABLE   = 'analysed_sst'
DELTA      = 0.1

os.makedirs(CACHE_DIR, exist_ok=True)

# ── 1. Obtener máscara oceánica ────────────────────────────────────────────────
if os.path.exists(MASK_FILE):
    print("Cargando máscara oceánica existente...")
    data = np.load(MASK_FILE)
    ocean_lats = data['lats']
    ocean_lons = data['lons']
    print(f"  {len(ocean_lats)} píxeles oceánicos")
else:
    print("Descargando máscara oceánica del Mediterráneo (1 día)...")
    ds = copernicusmarine.open_dataset(
        dataset_id=DATASET_ID,
        variables=[VARIABLE],
        minimum_longitude=-6.0, maximum_longitude=37.0,
        minimum_latitude=30.0,  maximum_latitude=47.0,
        start_datetime='2010-07-15T00:00:00',
        end_datetime='2010-07-15T00:00:00',
    )
    sst_day = ds[VARIABLE].isel(time=0)
    lats_all = sst_day.latitude.values
    lons_all = sst_day.longitude.values
    sst_vals = sst_day.values  # shape: (lat, lon)

    # Píxeles válidos = no NaN = océano
    lat_grid, lon_grid = np.meshgrid(lats_all, lons_all, indexing='ij')
    valid = ~np.isnan(sst_vals)
    ocean_lats = lat_grid[valid].astype(np.float32)
    ocean_lons = lon_grid[valid].astype(np.float32)

    np.savez(MASK_FILE, lats=ocean_lats, lons=ocean_lons)
    print(f"  {len(ocean_lats)} píxeles oceánicos guardados en {MASK_FILE}")

# ── 2. Construir KD-tree ───────────────────────────────────────────────────────
print("Construyendo KD-tree...")
# Convertir a radianes para distancia esférica aproximada
# A escala mediterránea (distancias <200km) la aproximación plana es suficiente
tree = cKDTree(np.column_stack([ocean_lats, ocean_lons]))
print("  OK")

# ── 3. Cargar AMPs ────────────────────────────────────────────────────────────
print(f"\nCargando {MPAS_JSON}...")
with open(MPAS_JSON, encoding='utf-8') as f:
    mpas = json.load(f)
print(f"  {len(mpas)} AMPs")

# ── 4. Snap cada AMP al píxel oceánico más cercano ────────────────────────────
def cache_path(lat_r, lon_r):
    return os.path.join(CACHE_DIR, f"sst_{lat_r:.2f}_{lon_r:.2f}.csv")

def load_cached(lat_r, lon_r):
    cp = cache_path(lat_r, lon_r)
    if not os.path.exists(cp):
        return None
    try:
        sst = pd.read_csv(cp, index_col=0, parse_dates=True)['sst']
        sst.index = pd.to_datetime(sst.index, errors='coerce').tz_localize(None)
        return sst.dropna() if len(sst) > 365 else None
    except Exception:
        return None

def download_sst(lat_r, lon_r):
    sst = load_cached(lat_r, lon_r)
    if sst is not None:
        return True
    try:
        ds = copernicusmarine.open_dataset(
            dataset_id=DATASET_ID, variables=[VARIABLE],
            minimum_longitude=lon_r-DELTA, maximum_longitude=lon_r+DELTA,
            minimum_latitude=lat_r-DELTA,  maximum_latitude=lat_r+DELTA,
        )
        s = ds[VARIABLE].sel(latitude=lat_r, longitude=lon_r, method='nearest').to_series()
        if s.mean() > 100: s = s - 273.15
        s.index = pd.to_datetime(s.index).tz_localize(None)
        s = s.dropna().rename('sst')
        if len(s) < 365: return False
        s.to_csv(cache_path(lat_r, lon_r), header=True)
        return True
    except Exception as e:
        print(f"    ERROR descarga ({lat_r:.2f},{lon_r:.2f}): {e}")
        return False

downloads_needed = []
snapped = same = no_sst = 0

for mpa in mpas:
    lat = mpa['Lat']
    lon = mpa['Lon']

    # Encontrar píxel oceánico más cercano en el KD-tree
    _, idx = tree.query([lat, lon])
    sst_lat = round(float(ocean_lats[idx]), 2)
    sst_lon = round(float(ocean_lons[idx]), 2)

    mpa['SST_Lat'] = sst_lat
    mpa['SST_Lon'] = sst_lon

    lat_r0 = round(round(lat / 0.05) * 0.05, 2)
    lon_r0 = round(round(lon / 0.05) * 0.05, 2)

    if sst_lat == lat_r0 and sst_lon == lon_r0:
        same += 1
    else:
        snapped += 1

    # ¿Necesita descarga?
    if load_cached(sst_lat, sst_lon) is None:
        downloads_needed.append((sst_lat, sst_lon, mpa.get('NAME','?')))

print(f"\nSnap completado:")
print(f"  Centroide ya era oceánico: {same}")
print(f"  Snapped a píxel oceánico:  {snapped}")
print(f"  Necesitan descarga SST:    {len(downloads_needed)}")

# ── 5. Descargar SST para celdas nuevas ───────────────────────────────────────
if downloads_needed:
    # Deduplicar por coordenada
    unique = list({(lat_r, lon_r): name for lat_r, lon_r, name in downloads_needed}.items())
    print(f"\nDescargando {len(unique)} celdas nuevas...")
    ok = fail = 0
    for i, ((lat_r, lon_r), name) in enumerate(unique):
        safe_name = name[:40].encode('ascii','replace').decode('ascii')
        print(f"  [{i+1}/{len(unique)}] ({lat_r:.2f},{lon_r:.2f}) {safe_name}")
        if download_sst(lat_r, lon_r):
            ok += 1
        else:
            # Celda fallida: buscar siguiente más cercana
            for k in range(2, 20):
                _, idxs = tree.query([float(lat_r), float(lon_r)], k=k)
                idx_next = idxs[-1]
                alt_lat = round(float(ocean_lats[idx_next]), 2)
                alt_lon = round(float(ocean_lons[idx_next]), 2)
                if download_sst(alt_lat, alt_lon):
                    # Actualizar AMPs que usaban esta celda
                    for mpa in mpas:
                        if mpa.get('SST_Lat') == lat_r and mpa.get('SST_Lon') == lon_r:
                            mpa['SST_Lat'] = alt_lat
                            mpa['SST_Lon'] = alt_lon
                    ok += 1
                    break
            else:
                fail += 1
    print(f"  OK: {ok} | Fallidas: {fail}")

# ── 6. Guardar ────────────────────────────────────────────────────────────────
print(f"\nGuardando {MPAS_JSON}...")
with open(MPAS_JSON, 'w', encoding='utf-8') as f:
    json.dump(mpas, f, ensure_ascii=False, indent=2)
print("DONE")
