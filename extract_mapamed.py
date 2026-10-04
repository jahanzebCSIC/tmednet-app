"""
extract_mapamed.py
Extrae AMPs marinos del GeoPackage de MAPAMED 2019.
Reproyecta de EPSG:3035 a WGS84 y calcula centroides.
Filtra solo AMPs con componente marina real.
Output: mapamed_mpas.json con NAME, Country, DESIG_ENG, Lat, Lon, MAPAMED_ID, etc.
"""
import geopandas as gpd
import pandas as pd
import json, re

GPKG = r'C:\Users\jahan\Downloads\MAPAMED\MAPAMED_2019_edition_version_2\MAPAMED_2019_v2_spatial_data_epsg3035.gpkg'
TSV  = r'C:\Users\jahan\Downloads\MAPAMED\MAPAMED_2019_edition_version_2\mapamed_2019_v2_attribute_data.tsv'
OUT  = r'C:\tmednet-app\mapamed_mpas.json'

# ISO3 → Country name map (Mediterranean countries)
ISO3_COUNTRY = {
    'ALB':'Albania','DZA':'Algeria','BIH':'Bosnia and Herzegovina',
    'HRV':'Croatia','CYP':'Cyprus','EGY':'Egypt','FRA':'France',
    'GRC':'Greece','ISR':'Israel','ITA':'Italy','LBN':'Lebanon',
    'LBY':'Libya','MLT':'Malta','MNE':'Montenegro','MAR':'Morocco',
    'MCO':'Monaco','MKD':'North Macedonia','SLV':'Slovenia',
    'SVN':'Slovenia','ESP':'Spain','SYR':'Syria','TUN':'Tunisia',
    'TUR':'Turkey',
}

MED_ISO3 = set(ISO3_COUNTRY.keys())

print("Leyendo GeoPackage...")
# List layers using geopandas/pyogrio
import pyogrio
layers = pyogrio.list_layers(GPKG)
print(f"  Capas disponibles: {layers}")
layer_name = layers[0][0]

gdf = gpd.read_file(GPKG, layer=layer_name)
print(f"  {len(gdf)} geometrías cargadas, CRS: {gdf.crs}")

# Reproject to WGS84
# Compute centroids BEFORE reprojecting (LAEA is a projected CRS, safe for centroid)
gdf['centroid_proj'] = gdf.geometry.centroid

# Reproject to WGS84
print("Reproyectando a WGS84...")
gdf_wgs = gdf.to_crs(epsg=4326)
centroids_wgs = gdf['centroid_proj'].set_crs(epsg=3035).to_crs(epsg=4326)
gdf_wgs['Lon'] = centroids_wgs.x
gdf_wgs['Lat'] = centroids_wgs.y

# GeoPackage already has all attributes - no merge needed
merged = gdf_wgs.copy()
id_col = 'MAPAMED_ID'

print(f"\nColumnas en GeoPackage: {[c for c in merged.columns if c not in ['geometry','centroid_proj']]}")
print(f"Total filas: {len(merged)}")

# ── Filter marine MPAs ──────────────────────────────────────────────────────────
def is_marine(row):
    # Has marine component
    m_pct = pd.to_numeric(row.get('GIS_M_PCT','0') or '0', errors='coerce') or 0
    m_area = pd.to_numeric(row.get('GIS_M_AREA','0') or '0', errors='coerce') or 0
    site_type = str(row.get('SITE_TYPE_ENG','') or '')
    desig = str(row.get('DESIG_ENG','') or '')
    if m_pct >= 10 or m_area >= 0.5:
        return True
    if 'Marine' in site_type or 'marine' in desig.lower() or 'SPAMI' in desig:
        return True
    return False

def get_iso3(row):
    iso = row.get('ISO3','') or ''
    # Remove set notation {ALB} → ALB
    iso = re.sub(r'[{}\s]','', str(iso)).split(',')[0].strip()
    return iso

def get_country(row):
    iso = get_iso3(row)
    return ISO3_COUNTRY.get(iso, iso)

# Filter for Mediterranean countries
merged['_iso3'] = merged.apply(get_iso3, axis=1)
merged['_country'] = merged.apply(get_country, axis=1)

med_mask = merged['_iso3'].isin(MED_ISO3)
print(f"\nAMPs en países mediterráneos: {med_mask.sum()} / {len(merged)}")

med = merged[med_mask].copy()

# Filter marine
med['_marine'] = med.apply(is_marine, axis=1)
print(f"AMPs con componente marina: {med['_marine'].sum()} / {len(med)}")
marine = med[med['_marine']].copy()

# Filter designated (not proposed)
if 'STATUS_ENG' in marine.columns:
    status_ok = marine['STATUS_ENG'].isin(['Designated','Adopted','Established','Inscribed'])
    print(f"AMPs con status oficial: {status_ok.sum()} / {len(marine)}")
    marine = marine[status_ok]

# Exclude Secondary and Zone entries — these are overlapping sub-designations
# of the same physical area (e.g. SPAMI + National Park on same footprint).
# Keep 'Main' (top-level of a multi-designation group) and 'Not reported' (standalone AMPs).
if 'PARENT_TYPE_ENG' in marine.columns:
    before = len(marine)
    marine = marine[~marine['PARENT_TYPE_ENG'].isin(['Secondary', 'Zone'])]
    print(f"Excluidas Secondary/Zone: {before} -> {len(marine)} AMPs")

# Drop rows with invalid coords
marine = marine.dropna(subset=['Lat','Lon'])
marine = marine[(marine['Lat'].between(-90,90)) & (marine['Lon'].between(-180,180))]

# Deduplicate by MAPAMED_ID if possible
id_field = 'MAPAMED_ID' if 'MAPAMED_ID' in marine.columns else id_col
if id_field and id_field in marine.columns:
    before = len(marine)
    marine = marine.drop_duplicates(subset=[id_field])
    print(f"Deduplicados por {id_field}: {before} -> {len(marine)}")

print(f"\nAMPs finales: {len(marine)}")
print(f"Países: {sorted(marine['_country'].unique())}")

# ── Build output JSON ──────────────────────────────────────────────────────────
def safe(v):
    if pd.isna(v) if not isinstance(v, (list,dict)) else False:
        return None
    return str(v).strip() if v else None

records = []
for _, row in marine.iterrows():
    name = safe(row.get('NAME') or row.get('name') or '')
    if not name:
        continue
    rec = {
        'MAPAMED_ID': safe(row.get('MAPAMED_ID') or row.get(id_col)),
        'NAME':       name,
        'Country':    row['_country'],
        'ISO3':       row['_iso3'],
        'DESIG_ENG':  safe(row.get('DESIG_ENG')),
        'DESIG_TYPE': safe(row.get('DESIG_TYPE')),
        'SITE_TYPE':  safe(row.get('SITE_TYPE_ENG')),
        'IUCN_CAT':   safe(row.get('IUCN_CAT_ENG')),
        'GIS_M_AREA': float(pd.to_numeric(row.get('GIS_M_AREA',0) or 0, errors='coerce') or 0),
        'GIS_M_PCT':  float(pd.to_numeric(row.get('GIS_M_PCT',0) or 0, errors='coerce') or 0),
        'STATUS_YR':  safe(row.get('STATUS_YR')),
        'Lat':        round(float(row['Lat']), 4),
        'Lon':        round(float(row['Lon']), 4),
    }
    records.append(rec)

records.sort(key=lambda r: (r['Country'], r['NAME']))

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"\nGuardado: {OUT}")
print(f"  Total AMPs: {len(records)}")
# Summary by country
from collections import Counter
cc = Counter(r['Country'] for r in records)
for country, n in sorted(cc.items(), key=lambda x: -x[1]):
    print(f"  {country}: {n}")
