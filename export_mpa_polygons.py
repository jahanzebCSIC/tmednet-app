"""
export_mpa_polygons.py
Exporta los polígonos MAPAMED simplificados como GeoJSON para el mapa web.
Incluye las propiedades MHW necesarias para colorear y mostrar en sidebar.
"""
import json, os, sys
import geopandas as gpd
import warnings
warnings.filterwarnings('ignore')

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GPKG      = r'C:\Users\jahan\Downloads\MAPAMED\MAPAMED_2019_edition_version_2\MAPAMED_2019_v2_spatial_data_epsg3035.gpkg'
MPAS_JSON = r'C:\tmednet-app\mpa-dashboard\src\data\mpas.json'
OUT_JSON  = r'C:\tmednet-app\mpa-dashboard\src\data\mpa_polygons.json'

# ── Cargar datos MHW ───────────────────────────────────────────────────────────
print("Cargando mpas.json...")
with open(MPAS_JSON, encoding='utf-8') as f:
    mpas = json.load(f)
mpa_dict = {str(m['MAPAMED_ID']): m for m in mpas}
valid_ids = {int(k) for k in mpa_dict}
print(f"  {len(mpa_dict)} AMPs")

# ── Cargar GeoPackage ─────────────────────────────────────────────────────────
print("Cargando GeoPackage MAPAMED...")
gdf = gpd.read_file(GPKG)
print(f"  {len(gdf)} features")

# Filtrar a nuestros 1050 AMPs y deduplicar por MAPAMED_ID
gdf_filt = gdf[gdf['MAPAMED_ID'].isin(valid_ids)].copy()
gdf_filt = gdf_filt.drop_duplicates(subset='MAPAMED_ID')
print(f"  {len(gdf_filt)} AMPs tras filtro y deduplicación")

# ── Reproyectar a WGS84 ───────────────────────────────────────────────────────
print("Reproyectando a WGS84...")
gdf_wgs = gdf_filt.to_crs('EPSG:4326')

# ── Simplificar geometrías ─────────────────────────────────────────────────────
# tolerance 0.005° ≈ 400m: buen equilibrio calidad/tamaño para zoom 5-12
print("Simplificando geometrías (tolerance=0.005°)...")
gdf_wgs['geometry'] = gdf_wgs['geometry'].simplify(tolerance=0.005, preserve_topology=True)

# ── Añadir propiedades MHW ─────────────────────────────────────────────────────
print("Añadiendo propiedades MHW...")
fields = [
    'NAME','Country','DESIG_ENG','DESIG_TYPE','IUCN_CAT','GIS_M_AREA','GIS_M_PCT',
    'STATUS_YR','Lat','Lon','Years_with_data','Year_min','Year_max',
    'Years_with_MHW','Pct_MHW','Max_intensity_ever','Max_category_ever',
    'Warming_trend_per_decade','Trend_R2','Trend_p','SST_available'
]
for field in fields:
    gdf_wgs[field] = gdf_wgs['MAPAMED_ID'].apply(
        lambda mid: mpa_dict.get(str(mid), {}).get(field)
    )

# ── Exportar GeoJSON ───────────────────────────────────────────────────────────
export_cols = ['MAPAMED_ID', 'geometry'] + fields
gdf_export = gdf_wgs[export_cols].copy()

print(f"Exportando GeoJSON a {OUT_JSON}...")
gdf_export.to_file(OUT_JSON, driver='GeoJSON')

# Comprobar tamaño
size_mb = os.path.getsize(OUT_JSON) / 1_000_000
print(f"  Tamaño: {size_mb:.1f} MB")

if size_mb > 8:
    print("  AVISO: archivo grande, aplicando simplificación extra...")
    gdf_wgs['geometry'] = gdf_wgs['geometry'].simplify(tolerance=0.01, preserve_topology=True)
    gdf_export = gdf_wgs[export_cols].copy()
    gdf_export.to_file(OUT_JSON, driver='GeoJSON')
    size_mb2 = os.path.getsize(OUT_JSON) / 1_000_000
    print(f"  Nuevo tamaño: {size_mb2:.1f} MB")

print(f"\nDONE — {len(gdf_export)} polígonos exportados ({size_mb:.1f} MB)")
