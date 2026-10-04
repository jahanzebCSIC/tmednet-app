"""
snap_to_marine_pixel.py v2
Encuentra la celda Copernicus más marina posible para cada AMP.
"Marina" = alta cobertura SST (>8000 días válidos, ~55% del dataset 1982-2024)
indicando pixel oceánico robusto, no costera marginal.
Si no hay celda robusta en el cache, baja el umbral progresivamente.
"""
import json, os, math
import pandas as pd

MPAS_JSON = r'C:\tmednet-app\mpa-dashboard\src\data\mpas.json'
CACHE_DIR = r'C:\tmednet-app\cache\sst_cache'

def cache_path(lat_r, lon_r):
    return os.path.join(CACHE_DIR, f"sst_{lat_r:.2f}_{lon_r:.2f}.csv")

def sst_coverage(lat_r, lon_r):
    """Devuelve número de días válidos en el cache, o 0 si no existe."""
    cp = cache_path(lat_r, lon_r)
    if not os.path.exists(cp):
        return 0
    try:
        sst = pd.read_csv(cp, index_col=0, parse_dates=True)['sst']
        return len(sst.dropna())
    except Exception:
        return 0

def best_marine_cell(lat, lon, search_radius=15):
    """
    Busca en espiral hasta search_radius celdas de radio.
    Devuelve la celda con mayor cobertura SST dentro de un radio razonable,
    priorizando celdas con >8000 días (claramente oceánicas).
    Retorna (lat_r, lon_r, coverage).
    """
    step = 0.05
    lat_r0 = round(round(lat / 0.05) * 0.05, 2)
    lon_r0 = round(round(lon / 0.05) * 0.05, 2)

    best = {'lat': None, 'lon': None, 'cov': 0, 'dist': 9999}

    for r in range(0, search_radius + 1):
        ring_best = []
        if r == 0:
            candidates = [(0.0, lat_r0, lon_r0)]
        else:
            candidates = []
            for di in range(-r, r+1):
                for dj in range(-r, r+1):
                    if abs(di) != r and abs(dj) != r:
                        continue
                    lat_c = round(lat_r0 + di * step, 2)
                    lon_c = round(lon_r0 + dj * step, 2)
                    dist = math.sqrt((lat_c - lat)**2 + (lon_c - lon)**2)
                    candidates.append((dist, lat_c, lon_c))
            candidates.sort()

        for dist, lat_c, lon_c in candidates:
            cov = sst_coverage(lat_c, lon_c)
            if cov > best['cov']:
                best = {'lat': lat_c, 'lon': lon_c, 'cov': cov, 'dist': dist}

        # Si encontramos una celda robustamente oceánica en este anillo, ya es suficiente
        # (8000 días ~ >55% del dataset 1982-2024 = pixel marino robusto)
        if best['cov'] >= 8000:
            break

    if best['lat'] is None:
        return None, None, 0
    return best['lat'], best['lon'], best['cov']

# ── Procesar ───────────────────────────────────────────────────────────────────
print("Cargando mpas.json...")
with open(MPAS_JSON, encoding='utf-8') as f:
    mpas = json.load(f)
print(f"  {len(mpas)} AMPs")

robust = coastal = not_found = 0

for i, mpa in enumerate(mpas):
    lat = mpa['Lat']
    lon = mpa['Lon']

    sst_lat, sst_lon, cov = best_marine_cell(lat, lon)

    mpa['SST_Lat'] = sst_lat
    mpa['SST_Lon'] = sst_lon
    mpa['SST_coverage_days'] = cov

    if cov >= 8000:
        robust += 1
    elif cov > 0:
        coastal += 1
    else:
        not_found += 1

print(f"\nResultados:")
print(f"  Pixel oceánico robusto (>8000 dias): {robust}")
print(f"  Pixel costera marginal (<8000 dias):  {coastal}")
print(f"  Sin SST en ningún vecino:              {not_found}")

# Guardar
with open(MPAS_JSON, 'w', encoding='utf-8') as f:
    json.dump(mpas, f, ensure_ascii=False, indent=2)
print(f"\nGuardado: {MPAS_JSON}")
