"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import io
import sys
import traceback

import numpy as np
import pandas as pd
import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
out = []


def note(msg):
    print(msg)
    out.append(str(msg))


def raster(url, label, bbox=(46.5, -20.0, 47.5, -19.0), shape=(40, 40)):
    try:
        import rasterio
        from rasterio.windows import from_bounds
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3", GDAL_HTTP_RETRY_DELAY="2"):
            with rasterio.open(url) as src:
                win = from_bounds(*bbox, transform=src.transform)
                a = src.read(1, window=win, out_shape=shape, boundless=True).astype("float64")
                note(f"== {label} OK : crs={src.crs} res={src.res} dtype={src.dtypes[0]} nodata={src.nodata} stats min/mean/max={np.nanmin(a):.1f}/{np.nanmean(a):.1f}/{np.nanmax(a):.1f} valeurs distinctes={len(np.unique(a))}")
    except Exception as e:
        note(f"== {label} ECHEC {type(e).__name__}: {str(e)[:300]}")


# Sols (SoilGrids 2.0, ISRIC) : argile, sable, carbone organique, 0-5 cm et 30-60 cm
for var in ["clay", "sand", "soc"]:
    for layer in ["0-5cm", "30-60cm"]:
        raster(f"/vsicurl/https://files.isric.org/soilgrids/latest/data/{var}/{var}_{layer}_mean.vrt", f"SoilGrids {var} {layer}")
# Occupation du sol (ESA WorldCover 2021, tuile 3x3 degrés)
raster("/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S21E045_Map.tif", "WorldCover S21E045",
       bbox=(46.0, -20.0, 47.0, -19.0), shape=(100, 100))
# ET0 FAO-56 d'ERA5-Land (Open-Meteo, archive)
try:
    r = requests.get("https://archive-api.open-meteo.com/v1/archive", params={"latitude": "-18.9,-21.4", "longitude": "47.5,47.1", "start_date": "2015-01-01", "end_date": "2015-12-31",
                                                                           "daily": "et0_fao_evapotranspiration,precipitation_sum", "timezone": "auto"}, headers=UA, timeout=120)
    note(f"== Open-Meteo archive HTTP {r.status_code}")
    j = r.json()
    j = j if isinstance(j, list) else [j]
    for k in j:
        d = pd.DataFrame(k["daily"])
        d["m"] = d.time.str[5:7]
        note("   ET0 mensuel (mm/jour) : " + " ".join(f"{x:.1f}" for x in d.groupby("m").et0_fao_evapotranspiration.mean()))
except Exception as e:
    note(f"== Open-Meteo archive ECHEC {type(e).__name__}: {str(e)[:300]}")
# Inventaire des glissements de terrain (NASA Global Landslide Catalog)
for u in ["https://data.nasa.gov/api/views/dd9e-wu2v/rows.csv?accessType=DOWNLOAD", "https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export.csv"]:
    try:
        r = requests.get(u, headers=UA, timeout=180)
        df = pd.read_csv(io.BytesIO(r.content), low_memory=False)
        cols = [c for c in df.columns if "country" in c.lower()]
        sub = df[df[cols[0]].astype(str).str.contains("Madagascar", case=False)] if cols else df.iloc[:0]
        note(f"== GLC {u[:60]} HTTP {r.status_code} : {df.shape}, Madagascar={len(sub)}, colonnes={list(df.columns)[:14]}")
        if len(sub):
            note(sub.head(5).to_string(max_colwidth=40)[:1500])
        break
    except Exception as e:
        note(f"== GLC {u[:60]} ECHEC {type(e).__name__}: {str(e)[:200]}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
