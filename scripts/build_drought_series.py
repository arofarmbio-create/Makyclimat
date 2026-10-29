"""Séries mensuelles par district pour comparer SPI et SPEI au NDVI (validation/protocole_spei_ndvi.md).

  --part et0    ERA5-Land, moyennes mensuelles (Climate Data Store, CDS_API_KEY) -> ET0 Penman-Monteith FAO-56, 1981-aujourd'hui
  --part ndvi   MODIS MOD13C2 v6.1 (AppEEARS, NASA ; EARTHDATA_USER / EARTHDATA_PASSWORD) -> NDVI mensuel, 2000-aujourd'hui,
                pixels de fiabilité 0 (bonne) ou 1 (marginale) seulement
  --part pluie  CHIRPS v2.0 mensuel (CHC, sans compte), 1981-aujourd'hui
Valeur d'un district : moyenne pondérée par la surface de ses fokontany, chacun prenant la maille valide la plus proche
de son centroïde. Sortie : data/<pays>/drought/<partie>_districts.csv (mois, adm2, valeur). Les secrets ne sont jamais affichés.
Usage : python scripts/build_drought_series.py --country mdg --part et0
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import soilwater_core as C
from common import country_data_dir, load_config, read_units

ERA5_VARS = ["2m_temperature", "2m_dewpoint_temperature", "10m_u_component_of_wind", "10m_v_component_of_wind",
             "surface_solar_radiation_downwards", "surface_pressure"]
APPEEARS = "https://appeears.earthdatacloud.nasa.gov/api"


def leaf_index(units, lat, lon, valid):
    """Pour chaque fokontany : indices (i, j) de la maille valide la plus proche ; poids = surface ; district."""
    lv = units[units.level == 4].reset_index(drop=True)
    vi, vj = np.where(valid)
    vlat, vlon = lat[vi], lon[vj]
    out_i, out_j = [], []
    for la, lo in zip(lv.lat.to_numpy(), lv.lon.to_numpy()):
        k = np.argmin((vlat - la) ** 2 + (vlon - lo) ** 2)
        out_i.append(vi[k]); out_j.append(vj[k])
    return np.array(out_i), np.array(out_j), lv.area_km2.fillna(1.0).to_numpy(), lv.adm2.to_numpy()


def district_means(field, idx):
    ii, jj, w, d = idx
    v = field[ii, jj]
    ok = np.isfinite(v)
    df = pd.DataFrame({"adm2": d, "vw": np.where(ok, v * w, 0), "w": np.where(ok, w, 0)})
    g = df.groupby("adm2").sum()
    return (g.vw / g.w.replace(0, np.nan)).to_dict()


def _era5_retrieve(c, ys, lat1, lon0, lat0, lon1, f):
    c.retrieve("reanalysis-era5-land-monthly-means", {
        "product_type": ["monthly_averaged_reanalysis"], "variable": ERA5_VARS, "year": [str(y) for y in ys],
        "month": [f"{m:02d}" for m in range(1, 13)], "time": ["00:00"], "area": [lat1, lon0, lat0, lon1],
        "data_format": "netcdf", "download_format": "unarchived"}, str(f))


def part_et0(cfg, units, years):
    import cdsapi
    import xarray as xr
    lon0, lat0, lon1, lat1 = cfg["map"]["bbox"]
    c = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=os.environ["CDS_API_KEY"], quiet=True, progress=False, timeout=1800)
    rows, idx = [], None
    for y0 in range(years[0], years[1] + 1, 5):
        ys = [y for y in range(y0, min(y0 + 5, years[1] + 1))]
        f = Path(tempfile.mkdtemp()) / "era5land.nc"
        try:
            _era5_retrieve(c, ys, lat1, lon0, lat0, lon1, f)
        except requests.HTTPError as e:                       # message du CDS (licence, requête) au lieu d'un « 400 » muet
            raise RuntimeError(f"ERA5-Land refusé : {e.response.text[:800] if e.response is not None else e}") from e
        ds = xr.open_dataset(f)
        tname = "valid_time" if "valid_time" in ds.dims else "time"
        lat, lon = ds.latitude.values, ds.longitude.values
        for t in ds[tname].values:
            d = ds.sel({tname: t})
            ts = pd.Timestamp(t)
            e = C.et0_pm_monthly(d.t2m.values, d.d2m.values, d.u10.values, d.v10.values, d.ssrd.values, d.sp.values,
                                 lat[:, None], ts.year, ts.month)
            if idx is None:
                idx = leaf_index(units, lat, lon, np.isfinite(e))
            rows += [(f"{ts.year}-{ts.month:02d}", k, v) for k, v in district_means(e, idx).items()]
        print(f"ERA5-Land {ys[0]}-{ys[-1]} : ok", flush=True)
    return rows


def part_ndvi(cfg, units, years):
    import xarray as xr
    s = requests.Session()
    tok = s.post(f"{APPEEARS}/login", auth=(os.environ["EARTHDATA_USER"], os.environ["EARTHDATA_PASSWORD"]), timeout=120).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    lon0, lat0, lon1, lat1 = cfg["map"]["bbox"]
    layers = s.get(f"{APPEEARS}/product/MOD13C2.061", headers=h, timeout=120).json()   # noms exacts des couches
    names = list(layers) if isinstance(layers, dict) else [x.get("Layer", x) if isinstance(x, dict) else x for x in layers]
    l_ndvi = next((k for k in names if "ndvi" in str(k).lower()), None)
    l_rel = next((k for k in names if "reliab" in str(k).lower()), None)
    if not l_ndvi or not l_rel:
        raise RuntimeError(f"couches MOD13C2 introuvables ; réponse AppEEARS : {str(layers)[:600]}")
    task = {"task_type": "area", "task_name": f"makyclimat_ndvi_{dt.date.today():%Y%m%d}",
            "params": {"dates": [{"startDate": f"01-01-{years[0]}", "endDate": f"12-31-{years[1]}"}],
                       "layers": [{"product": "MOD13C2.061", "layer": l_ndvi}, {"product": "MOD13C2.061", "layer": l_rel}],
                       "output": {"format": {"type": "netcdf4"}, "projection": "geographic"},
                       "geo": {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {
                           "type": "Polygon", "coordinates": [[[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]]}}]}}}
    r = s.post(f"{APPEEARS}/task", json=task, headers=h, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"AppEEARS a refusé la tâche (HTTP {r.status_code}) : {r.text[:300]}")
    tid = r.json()["task_id"]
    for _ in range(360):                                               # jusqu'à 6 h
        st = s.get(f"{APPEEARS}/task/{tid}", headers=h, timeout=120).json().get("status")
        if st == "done":
            break
        if st == "error":
            raise RuntimeError("tâche AppEEARS en erreur")
        time.sleep(60)
    files = s.get(f"{APPEEARS}/bundle/{tid}", headers=h, timeout=120).json()["files"]
    nc = next(f for f in files if f["file_name"].endswith(".nc"))
    path = Path(tempfile.mkdtemp()) / "ndvi.nc"
    with s.get(f"{APPEEARS}/bundle/{tid}/{nc['file_id']}", headers=h, stream=True, timeout=600, allow_redirects=True) as g:
        g.raise_for_status()
        with open(path, "wb") as fo:
            for chunk in g.iter_content(1 << 20):
                fo.write(chunk)
    ds = xr.open_dataset(path)
    nd = [v for v in ds.data_vars if "NDVI" in v][0]
    rel = [v for v in ds.data_vars if "reliability" in v][0]
    lat, lon = ds.lat.values, ds.lon.values
    rows, idx = [], None
    for t in ds.time.values:
        a = ds[nd].sel(time=t).values.astype("float32")
        q = ds[rel].sel(time=t).values
        a = np.where(np.isin(q, [0, 1]) & (a >= -0.2) & (a <= 1.0), a, np.nan)
        if idx is None:
            idx = leaf_index(units, lat, lon, np.isfinite(a) | np.isfinite(ds[nd].isel(time=-1).values))
        ts = pd.Timestamp(str(t)[:10])
        rows += [(f"{ts.year}-{ts.month:02d}", k, v) for k, v in district_means(a, idx).items()]
    print(f"NDVI MODIS : {len(ds.time)} mois", flush=True)
    return rows


def part_pluie(cfg, units, years):
    from chirps import fetch_array
    rows, idx = [], None
    today = dt.date.today()
    for y in range(years[0], years[1] + 1):
        for m in range(1, 13):
            if (y, m) >= (today.year, today.month):
                break
            r = fetch_array(cfg["rainfall"]["monthly_url"].format(y=y, m=m), cfg["map"]["bbox"])
            if r is None:
                continue
            a, x0, y0, res = r
            lat = y0 - res * (np.arange(a.shape[0]) + 0.5)
            lon = x0 + res * (np.arange(a.shape[1]) + 0.5)
            if idx is None:
                idx = leaf_index(units, lat, lon, np.isfinite(a))
            rows += [(f"{y}-{m:02d}", k, v) for k, v in district_means(a, idx).items()]
        print(f"CHIRPS {y} : ok", flush=True)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--part", choices=["et0", "ndvi", "pluie"], required=True)
    args = ap.parse_args()
    cfg, units = load_config(args.country), read_units(args.country)
    last = dt.date.today().year
    years = {"et0": (1981, last), "ndvi": (2000, last), "pluie": (1981, last)}[args.part]
    rows = {"et0": part_et0, "ndvi": part_ndvi, "pluie": part_pluie}[args.part](cfg, units, years)
    out = country_data_dir(args.country) / "drought"
    out.mkdir(exist_ok=True)
    pd.DataFrame(rows, columns=["mois", "adm2", "valeur"]).to_csv(out / f"{args.part}_districts.csv", index=False)
    print(f"{args.part} : {len(rows)} valeurs, {len({r[0] for r in rows})} mois")


if __name__ == "__main__":
    main()
