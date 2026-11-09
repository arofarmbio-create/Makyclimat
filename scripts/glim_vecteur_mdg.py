"""Découpe la GLiM vectorielle sur l'emprise de Madagascar et calcule les surfaces par classe.

Usage : .venv/Scripts/python.exe -I scripts/glim_vecteur_mdg.py <source gdb ou /vsizip/...> <couche> <sortie.gpkg> <sortie.json>
"""
import json
import sys
from datetime import date

import geopandas as gpd
import pyogrio
from shapely.geometry import box

src, layer, out_gpkg, out_json = sys.argv[1:5]
BBOX = (43.0, -26.0, 51.0, -11.5)
# Albers équivalente centrée sur Madagascar, pour des surfaces exactes
AEA = "+proj=aea +lat_1=-14 +lat_2=-24 +lat_0=-19 +lon_0=47 +datum=WGS84 +units=m +no_defs"

info = pyogrio.read_info(src, layer=layer)
src_crs = info["crs"]
bbox_geo = gpd.GeoSeries([box(*BBOX)], crs="EPSG:4326")
bbox_src = bbox_geo.to_crs(src_crs)
gdf = pyogrio.read_dataframe(src, layer=layer, bbox=tuple(bbox_src.total_bounds))
print("lus (rectangle englobant)", len(gdf))
gdf = gdf.to_crs("EPSG:4326")
gdf = gpd.clip(gdf, bbox_geo.iloc[0])
gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
gdf["surface_km2"] = gdf.to_crs(AEA).geometry.area / 1e6
print("polygones après découpe", len(gdf))
print(gdf.drop(columns="geometry").head())

keep = [c for c in gdf.columns if c.lower() not in ("shape_length", "shape_area")]
gdf[keep].to_file(out_gpkg, driver="GPKG", layer="glim_mdg")

tot = float(gdf["surface_km2"].sum())
xx_col = next(c for c in gdf.columns if c.lower() == "xx")
lvl1 = gdf.groupby(xx_col)["surface_km2"].sum().sort_values(ascending=False)
litho_col = next((c for c in gdf.columns if c.lower() == "litho"), None)
res = {
    "n_polygones": int(len(gdf)),
    "surface_totale_km2": round(tot, 1),
    "niveau1": {k: {"km2": round(float(v), 1), "pct": round(100 * float(v) / tot, 2)} for k, v in lvl1.items()},
}
if litho_col:
    sub = gdf[gdf[xx_col] == "sc"].groupby(litho_col)["surface_km2"].agg(["sum", "count"])
    res["sc_detail_litho"] = {k: {"km2": round(float(r["sum"]), 1), "pct_du_total": round(100 * float(r["sum"]) / tot, 2),
                                  "polygones": int(r["count"])} for k, r in sub.sort_values("sum", ascending=False).iterrows()}
    allc = gdf.groupby(litho_col)["surface_km2"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    res["litho_toutes"] = {k: {"km2": round(float(r["sum"]), 1), "polygones": int(r["count"])} for k, r in allc.iterrows()}
res["champs"] = [c for c in gdf.columns if c != "geometry"]
res["crs_source"] = str(src_crs)
res["calcule_le"] = date.today().isoformat()
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(json.dumps({k: res[k] for k in ("n_polygones", "surface_totale_km2", "niveau1")}, ensure_ascii=False, indent=1))
