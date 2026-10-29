"""Prévisions saisonnières multi-modèles Copernicus C3S (pluie mensuelle), émises le 1er octobre : rétroprévisions
1993-2016 et prévision de l'année en cours, pour chaque système opérationnel (cahier des charges §5 « plusieurs
organismes et modèles indépendants », §8 approche 3).

Source : C3S `seasonal-monthly-single-levels` (Climate Data Store, compte requis, licence Copernicus : libre avec
attribution). Variable : taux de précipitation moyen mensuel (m/s), tous les membres, échéances 1 à 6 mois (octobre à
mars), maille 1°, emprise du pays (config map.bbox). Converti en mm par mois.
Sortie : data/<pays>/c3s/<centre>_<système>.npz, avec pluie[année, membre, échéance, lat, lon] (float16, NaN pour les
membres absents), années, échéances, grille. Lit CDS_API_KEY (secret GitHub), ne l'affiche jamais.
Usage : python scripts/build_c3s_seasonal.py --country mdg [--systems ecmwf:51 ukmo:610 ...] [--year 2026]
"""
from __future__ import annotations

import argparse
import calendar
import os
import tempfile
import time
from pathlib import Path

import numpy as np

from common import country_data_dir, load_config, save_grid

# systèmes opérationnels en octobre 2026, avec rétroprévisions 1993-2016 (API de contraintes du CDS, 29/10/2026)
SYSTEMS = ["ecmwf:51", "ukmo:610", "meteo_france:9", "dwd:22", "cmcc:4", "ncep:2", "jma:4", "eccc:4", "eccc:5", "bom:2"]
HINDCAST = list(range(1993, 2017))
INIT_MONTH = 10
LEADS = list(range(1, 7))


def retrieve(c, centre, system, years, area, out):
    c.retrieve("seasonal-monthly-single-levels", {
        "originating_centre": centre, "system": system, "variable": ["total_precipitation"], "product_type": ["monthly_mean"],
        "year": [str(y) for y in years], "month": [f"{INIT_MONTH:02d}"], "leadtime_month": [str(k) for k in LEADS],
        "area": area, "data_format": "grib"}, str(out))


def read(path: Path, years):
    """GRIB -> pluie en mm/mois [année, membre, échéance, lat, lon]."""
    import xarray as xr
    ds = xr.open_dataset(path, engine="cfgrib", backend_kwargs={"time_dims": ("forecastMonth", "time"), "indexpath": ""})
    v = ds[list(ds.data_vars)[0]]
    if "number" not in v.dims:
        v = v.expand_dims("number")
    v = v.transpose("time", "number", "forecastMonth", "latitude", "longitude")
    got = [int(str(t)[:4]) for t in v.time.values]
    arr = np.full((len(years), v.sizes["number"], len(LEADS), v.sizes["latitude"], v.sizes["longitude"]), np.nan, "float32")
    for i, y in enumerate(years):
        if y not in got:
            continue
        a = v.values[got.index(y)]
        for k, lead in enumerate(LEADS):
            m = (INIT_MONTH - 1 + lead - 1) % 12 + 1
            yy = y + (INIT_MONTH - 1 + lead - 1) // 12
            arr[i, :, k] = a[:, list(v.forecastMonth.values).index(lead)] * 1000 * 86400 * calendar.monthrange(yy, m)[1]
    return arr, v.latitude.values, v.longitude.values


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--systems", nargs="+", default=SYSTEMS)
    ap.add_argument("--year", type=int, default=None, help="année de la prévision opérationnelle (défaut : année en cours)")
    args = ap.parse_args()
    import datetime as dt

    import cdsapi
    cfg = load_config(args.country)
    lon0, lat0, lon1, lat1 = cfg["map"]["bbox"]
    area = [lat1 + 1, lon0 - 1, lat0 - 1, lon1 + 1]
    year = args.year or dt.date.today().year
    c = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=os.environ["CDS_API_KEY"], quiet=True, progress=False, timeout=1800)
    out_dir = country_data_dir(args.country) / "c3s"
    out_dir.mkdir(exist_ok=True)
    for cs in args.systems:
        centre, system = cs.split(":")
        out = out_dir / f"{centre}_{system}.npz"
        if out.exists():
            z = dict(np.load(out))
            if year in z["years"]:
                print(f"{out.name} : déjà à jour ({year})")
                continue
            try:                                   # rétroprévisions déjà là : seule la prévision de l'année est ajoutée
                f = Path(tempfile.mkdtemp()) / "c3s.grib"
                retrieve(c, centre, system, [year], area, f)
                fc, _, _ = read(f, [year])
            except Exception as e:  # noqa: BLE001
                print(f"::warning::{cs} : prévision {year} indisponible : {type(e).__name__} : {str(e)[:300]}")
                continue
            h = z["pluie"][: len(HINDCAST)].astype("float32")
            nm = max(h.shape[1], fc.shape[1])
            pad = lambda a: np.concatenate([a, np.full((a.shape[0], nm - a.shape[1], *a.shape[2:]), np.nan, "float32")], axis=1)
            z.update(pluie=np.concatenate([pad(h), pad(fc)]).astype("float16"), years=np.array(HINDCAST + [year]),
                     members_forecast=np.array(fc.shape[1]))
            save_grid(out, **z)
            print(f"{out.name} : prévision {year} ajoutée ({fc.shape[1]} membres)")
            continue
        t0 = time.time()
        parts = []
        try:
            for yrs in (HINDCAST, [year]):
                f = Path(tempfile.mkdtemp()) / "c3s.grib"
                retrieve(c, centre, system, yrs, area, f)
                parts.append(read(f, yrs))
        except Exception as e:  # noqa: BLE001  (un système indisponible n'empêche pas les autres)
            print(f"::warning::{cs} indisponible : {type(e).__name__} : {str(e)[:300]}")
            continue
        (h, lat, lon), (fc, _, _) = parts
        nm = max(h.shape[1], fc.shape[1])
        pad = lambda a: np.concatenate([a, np.full((a.shape[0], nm - a.shape[1], *a.shape[2:]), np.nan, "float32")], axis=1)
        arr = np.concatenate([pad(h), pad(fc)])
        save_grid(out, pluie=arr.astype("float16"), years=np.array(HINDCAST + [year]), leads=np.array(LEADS),
                  init_month=np.array(INIT_MONTH), lat=lat.astype("float32"), lon=lon.astype("float32"),
                  members_hindcast=np.array(h.shape[1]), members_forecast=np.array(fc.shape[1]))
        print(f"{out.name} : rétroprévisions {HINDCAST[0]}-{HINDCAST[-1]} ({h.shape[1]} membres), prévision {year} "
              f"({fc.shape[1]} membres), grille {len(lat)} x {len(lon)}, {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
