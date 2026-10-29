"""Essai des reprévisions GloFAS v4 (Copernicus EWDS) sur Madagascar : taille, durée, dates et membres disponibles.

Prépare la vérification des prévisions d'ensemble de crue par l'impact (thèse, cahier des charges §8, §13) : avant de
télécharger 20 ans, on mesure ce que coûte un mois. Lit CDS_API_KEY (secret GitHub), ne l'affiche jamais.
Usage : python scripts/probe_glofas_reforecast.py --year 2018 --month 1
"""
from __future__ import annotations

import argparse
import os
import tempfile
import time
from pathlib import Path

import cdsapi

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2018)
    ap.add_argument("--month", type=int, default=1)
    ap.add_argument("--days", type=int, default=15, help="échéances de 1 à N jours")
    args = ap.parse_args()
    c = cdsapi.Client(url="https://ewds.climate.copernicus.eu/api", key=os.environ["CDS_API_KEY"], quiet=True, progress=False,
                      timeout=900)
    out = Path(tempfile.mkdtemp()) / "refc.grib"
    req = {"system_version": ["version_4_0"], "hydrological_model": ["lisflood"],
           "product_type": ["control_reforecast", "ensemble_perturbed_reforecasts"],
           "variable": "river_discharge_in_the_last_24_hours", "hyear": [str(args.year)], "hmonth": [MONTHS[args.month - 1]],
           "hday": [f"{d:02d}" for d in range(1, 32)], "leadtime_hour": [str(24 * k) for k in range(1, args.days + 1)],
           "area": [-11.5, 43.0, -26.0, 51.0], "data_format": "grib2", "download_format": "unarchived"}
    t0 = time.time()
    c.retrieve("cems-glofas-reforecast", req, str(out))
    print(f"Téléchargé : {out.stat().st_size / 1e6:.1f} Mo en {time.time() - t0:.0f} s", flush=True)
    import xarray as xr
    for pt in ("cf", "pf"):
        try:
            ds = xr.open_dataset(out, engine="cfgrib", backend_kwargs={"filter_by_keys": {"dataType": pt}, "indexpath": ""})
        except Exception as e:  # noqa: BLE001
            print(f"{pt} : illisible ({type(e).__name__} : {str(e)[:200]})")
            continue
        v = ds[list(ds.data_vars)[0]]
        print(f"{pt} : {dict(v.sizes)}")
        print(f"   dates : {[str(x)[:10] for x in ds.time.values[:12]]}")
        print(f"   grille : lat {float(ds.latitude[0]):.4f}..{float(ds.latitude[-1]):.4f}, lon {float(ds.longitude[0]):.4f}..{float(ds.longitude[-1]):.4f}")
        print(f"   maille Mananjary-Analamanga (-18.875, 47.575) : {v.sel(latitude=-18.875, longitude=47.575, method='nearest').isel(step=0).values.ravel()[:11]}")


if __name__ == "__main__":
    main()
