"""Indice de circulation du canal de Mozambique (protocole H-N7, attribution seulement) : ERA5, niveau 850 hPa,
moyennes mensuelles de décembre, janvier et février, 1981 à l'année précédente.

Jeu Copernicus : reanalysis-era5-pressure-levels-monthly-means (ERA5, pas ERA5-Land), variables tourbillon relatif
(vorticity), vent zonal u et méridien v, sur 30-50°E, 30-10°S. Moyenne pondérée par le cosinus de la latitude.
Une seule demande, passée dans la file Copernicus après ERA5-Land (une demande à la fois pour tout le compte).
Sortie : data/enso/mct_era5.csv (annee, mois, vort850_1e5_s, u850_ms, v850_ms). Le tourbillon est donné en
1e-5 s-1 ; dans l'hémisphère sud, un tourbillon négatif est cyclonique.
Usage : python scripts/build_mct_era5.py [--last-year 2025]
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import tempfile
from pathlib import Path

import numpy as np

from common import ROOT, cds_retrieve

AREA = [-10, 30, -30, 50]                       # N, O, S, E
MONTHS = (12, 1, 2)
OUT = ROOT / "data" / "enso" / "mct_era5.csv"


def area_mean(field: np.ndarray, lats: np.ndarray) -> float:
    """Moyenne d'un champ (lat, lon) pondérée par cos(latitude), NaN ignorés."""
    w = np.cos(np.deg2rad(np.asarray(lats, float)))[:, None] * np.ones(field.shape[1])[None, :]
    ok = np.isfinite(field)
    return float(np.sum(np.where(ok, field * w, 0.0)) / np.sum(np.where(ok, w, 0.0)))


def rows_from_dataset(ds) -> list[tuple[int, int, float, float, float]]:
    """Dataset xarray (temps, latitude, longitude[, niveau]) -> lignes (année, mois, vort, u, v)."""
    tname = "valid_time" if "valid_time" in ds.dims else "time"
    sq = ds.squeeze(drop=True)
    lats = sq.latitude.values
    out = []
    for i, t in enumerate(sq[tname].values):
        d = dt.date.fromisoformat(str(t)[:10])
        if d.month not in MONTHS:
            continue
        vo, u, v = (sq[k].isel({tname: i}).values.astype(float) for k in ("vo", "u", "v"))
        out.append((d.year, d.month, round(area_mean(vo, lats) * 1e5, 4), round(area_mean(u, lats), 3), round(area_mean(v, lats), 3)))
    return sorted(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first-year", type=int, default=1981)
    ap.add_argument("--last-year", type=int, default=dt.date.today().year - 1)
    args = ap.parse_args()
    import cdsapi
    import xarray as xr
    c = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=os.environ["CDS_API_KEY"], quiet=False,
                      progress=False, timeout=1800)
    f = Path(tempfile.mkdtemp()) / "mct.nc"
    cds_retrieve(c, "reanalysis-era5-pressure-levels-monthly-means", {
        "product_type": ["monthly_averaged_reanalysis"], "variable": ["vorticity", "u_component_of_wind", "v_component_of_wind"],
        "pressure_level": ["850"], "year": [str(y) for y in range(args.first_year, args.last_year + 1)],
        "month": [f"{m:02d}" for m in MONTHS], "time": ["00:00"], "area": AREA,
        "data_format": "netcdf", "download_format": "unarchived"}, f)
    rows = rows_from_dataset(xr.open_dataset(f))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fo:
        fo.write("annee,mois,vort850_1e5_s,u850_ms,v850_ms\n")
        for r in rows:
            fo.write(",".join(str(x) for x in r) + "\n")
    print(f"{OUT.name} : {len(rows)} mois ({rows[0][0]}-{rows[-1][0]})")


if __name__ == "__main__":
    main()
