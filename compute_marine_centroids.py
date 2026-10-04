"""
compute_marine_centroids.py
Calcula el centroide marino de cada AMP:
1. Polígono real del AMP (GeoPackage MAPAMED EPSG:3035)
2. Intersección con océano (Natural Earth 10m land mask)
3. Centroide de la parte marina → coordenada de visualización correcta
4. Guarda en mpas.json inmediatamente (MHW ya calculado, no requiere re-descarga)
"""
import os, sys, json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GPKG         = r'C:\Users\jahan\Downloads\MAPAMED\MAPAMED_2019_edition_version_2\MAPAMED_2019_v2_spatial_data_epsg3035.gpkg'
MPAS_JSON    = r'C:\tmednet-app\mpa-dashboard\src\data\mpas.json'
MAPAMED_JSON = r'C:\tmednet-app\mapamed_mpas.json'
CACHE_DIR    = r'C:\tmednet-app\cache\sst_cache'
LAND_FILE    = r'C:\tmednet-app\cache\ne_10m_land.gpkg'

os.makedirs(CACHE_DIR, exist_ok=True)

# ── 1. Máscara de tierra Natural Earth 10m ────────────────────────────────────
if os.path.exists(LAND_FILE):
    print("Cargando máscara de tierra NE10m desde cache...", flush=True)
    land_3035 = gpd.read_file(LAND_FILE)
else:
    print("Descargando Natural Earth 10m land polygons...", flush=True)
    ne_url = "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip"
    land = gpd.read_file(ne_url)
    med_bbox = box(-10, 27, 42, 50)
    land_med = land[land.geometry.intersects(med_bbox)].copy()
    land_3035 = land_med.to_crs('EPSG:3035')
    land_3035.to_file(LAND_FILE, driver='GPKG')
    print(f"  Guardada en {LAND_FILE}", flush=True)

land_union = unary_union(land_3035.geometry)
print(f"  Máscara lista ({len(land_3035)} polígonos)", flush=True)

# ── 2. Cargar GeoPackage MAPAMED ───────────────────────────────────────────────
print(f"\nCargando GeoPackage MAPAMED...", flush=True)
gdf = gpd.read_file(GPKG)
print(f"  {len(gdf)} features totales", flush=True)

print(f"\nCargando mapamed_mpas.json...", flush=True)
with open(MAPAMED_JSON, encoding='utf-8') as f:
    mapamed_base = json.load(f)
valid_ids = {int(m['MAPAMED_ID']) for m in mapamed_base}
gdf_filt = gdf[gdf['MAPAMED_ID'].isin(valid_ids)].copy()
print(f"  {len(gdf_filt)} AMPs con polígono (de {len(valid_ids)} en JSON)", flush=True)

# ── 3. Calcular centroide marino ───────────────────────────────────────────────
print(f"\nCalculando centroides marinos...", flush=True)
marine_coords = {}

for i, row in gdf_filt.iterrows():
    mid  = row['MAPAMED_ID']
    geom = row.geometry
    if geom is None or geom.is_empty:
        continue
    try:
        marine_geom = geom.difference(land_union)
        if marine_geom.is_empty:
            marine_geom = geom
        centroid_3035 = marine_geom.centroid
    except Exception:
        centroid_3035 = geom.centroid

    pt_gdf = gpd.GeoDataFrame(geometry=[centroid_3035], crs='EPSG:3035')
    pt_wgs = pt_gdf.to_crs('EPSG:4326')
    lon, lat = pt_wgs.geometry[0].x, pt_wgs.geometry[0].y
    marine_coords[str(int(mid))] = (round(lat, 5), round(lon, 5))

print(f"  {len(marine_coords)} centroides marinos calculados", flush=True)

# ── 4. Actualizar mpas.json ────────────────────────────────────────────────────
print(f"\nActualizando mpas.json...", flush=True)
with open(MPAS_JSON, encoding='utf-8') as f:
    mpas = json.load(f)

updated = unchanged = not_found = 0
for mpa in mpas:
    mid = str(mpa.get('MAPAMED_ID', ''))
    if mid in marine_coords:
        new_lat, new_lon = marine_coords[mid]
        old_lat, old_lon = mpa['Lat'], mpa['Lon']
        dist_deg = ((new_lat - old_lat)**2 + (new_lon - old_lon)**2)**0.5
        if dist_deg > 0.001:
            mpa['Lat'] = new_lat
            mpa['Lon'] = new_lon
            mpa['SST_Lat'] = round(round(new_lat / 0.05) * 0.05, 2)
            mpa['SST_Lon'] = round(round(new_lon / 0.05) * 0.05, 2)
            updated += 1
        else:
            unchanged += 1
    else:
        not_found += 1

print(f"  Actualizados (centroide movido): {updated}", flush=True)
print(f"  Sin cambio (ya estaban bien):    {unchanged}", flush=True)
print(f"  Sin polígono en GeoPackage:      {not_found}", flush=True)

# ── 5. Guardar INMEDIATAMENTE ─────────────────────────────────────────────────
print(f"\nGuardando {MPAS_JSON}...", flush=True)
with open(MPAS_JSON, 'w', encoding='utf-8') as f:
    json.dump(mpas, f, ensure_ascii=False, indent=2)
print("DONE — coordenadas marinas guardadas en mpas.json", flush=True)
print(f"\n→ {updated} AMPs tienen ahora su punto en la zona marina real del AMP", flush=True)
print(f"→ MHW data ya calculada — no requiere re-descarga SST", flush=True)

# ── 6. Mostrar ejemplos de cambios más grandes ────────────────────────────────
print(f"\nEjemplos de correcciones más grandes:", flush=True)
examples = []
with open(MAPAMED_JSON, encoding='utf-8') as f:
    mapamed_base2 = json.load(f)
base_dict = {str(m['MAPAMED_ID']): m for m in mapamed_base2}

for mpa in mpas:
    mid = str(mpa.get('MAPAMED_ID', ''))
    if mid in marine_coords and mid in base_dict:
        base = base_dict[mid]
        old_lat, old_lon = base['Lat'], base['Lon']
        new_lat, new_lon = mpa['Lat'], mpa['Lon']
        dist_km = ((new_lat-old_lat)*111)**2 + ((new_lon-old_lon)*111*0.82)**2
        dist_km = dist_km**0.5
        if dist_km > 1:
            name = mpa.get('NAME','?')[:40].encode('ascii','replace').decode('ascii')
            examples.append((dist_km, name, old_lat, old_lon, new_lat, new_lon))

examples.sort(reverse=True)
for dist, name, olat, olon, nlat, nlon in examples[:10]:
    print(f"  {dist:.1f}km: {name}", flush=True)
    print(f"    Antes: ({olat:.4f},{olon:.4f}) → Ahora: ({nlat:.4f},{nlon:.4f})", flush=True)
