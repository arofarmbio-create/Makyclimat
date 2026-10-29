"""Reprévisions GloFAS v4 (Copernicus EWDS) réduites pour la vérification par l'impact (validation/protocole_verification_impact.md).

Un fichier par mois : pour chaque date d'initialisation (lundi et jeudi), chaque membre (contrôle + 10 perturbés) et
chaque fenêtre d'échéance (1-3, 4-7, 8-15 jours), le débit journalier maximal de chaque maille de rivière.
Réduction sans perte pour l'usage prévu : seules les mailles dont un membre au moins atteint q_keep (5 m³/s, le
min_q2 de l'alerte) dans le mois sont gardées ; une maille absente ne peut donc dépasser aucun seuil ≥ q_keep ce mois-là.
Un mois brut fait ~100 Mo (Madagascar, 15 échéances) ; le fichier réduit est stocké hors du dépôt git (release GitHub).
Lit CDS_API_KEY (secret GitHub), ne l'affiche jamais.
Usage : python scripts/build_glofas_reforecast.py --country mdg --year 2018 --months 1 2 3 4 11 12
"""
from __future__ import annotations

import argparse
import os
import tempfile
import time
from pathlib import Path

import numpy as np

from common import country_data_dir, load_config, save_grid

WINDOWS = ((1, 3), (4, 7), (8, 15))      # jours d'échéance, bornes incluses
Q_KEEP = 5.0                             # m³/s


def request(cfg, year: int, month: int) -> dict:
    lon0, lat0, lon1, lat1 = cfg["map"]["bbox"]
    return {"system_version": ["version_4_0"], "hydrological_model": ["lisflood"],
            "product_type": ["control_reforecast", "ensemble_perturbed_reforecast"],
            "variable": "river_discharge_in_the_last_24_hours", "hyear": [str(year)], "hmonth": [f"{month:02d}"],
            "hday": [f"{d:02d}" for d in range(1, 32)], "leadtime_hour": [str(24 * k) for k in range(1, WINDOWS[-1][1] + 1)],
            "area": [lat1, lon0, lat0, lon1], "data_format": "grib2", "download_format": "unarchived"}


def reduce(path: Path) -> dict:
    """GRIB -> q[init, membre, fenêtre, maille] (float16) pour les mailles gardées, + coordonnées."""
    import xarray as xr
    kw = {"engine": "cfgrib", "backend_kwargs": {"indexpath": ""}}
    cf = xr.open_dataset(path, **{**kw, "backend_kwargs": {"indexpath": "", "filter_by_keys": {"dataType": "cf"}}})
    pf = xr.open_dataset(path, **{**kw, "backend_kwargs": {"indexpath": "", "filter_by_keys": {"dataType": "pf"}}})
    a, b = cf[list(cf.data_vars)[0]], pf[list(pf.data_vars)[0]]
    if not np.array_equal(a.time.values, b.time.values):
        raise ValueError("dates d'initialisation différentes entre contrôle et membres perturbés")
    q = np.concatenate([a.transpose("time", "step", "latitude", "longitude").values[:, None],
                        b.transpose("time", "number", "step", "latitude", "longitude").values], axis=1)   # t, m, s, y, x
    lead = (a.step.values / np.timedelta64(1, "D")).round().astype(int)
    nt, nm, _, ny, nx = q.shape
    q = q.reshape(nt, nm, len(lead), ny * nx)
    with np.errstate(invalid="ignore"):
        keep = np.nanmax(q, axis=(0, 1, 2)) >= Q_KEEP
        wq = np.stack([np.nanmax(q[:, :, (lead >= lo) & (lead <= hi)][..., keep], axis=2) for lo, hi in WINDOWS], axis=2)
    lat, lon = np.meshgrid(a.latitude.values, a.longitude.values, indexing="ij")
    return {"init": np.array([str(t)[:10] for t in a.time.values]), "lat": lat.ravel()[keep].astype("float32"),
            "lon": lon.ravel()[keep].astype("float32"), "q": wq.astype("float16"), "windows": np.array(WINDOWS),
            "members": np.array(["cf"] + [f"pf{int(n)}" for n in b.number.values]), "q_keep": np.array(Q_KEEP)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--months", type=int, nargs="+", default=[1, 2, 3, 4, 11, 12])
    args = ap.parse_args()
    import cdsapi
    cfg = load_config(args.country)
    c = cdsapi.Client(url="https://ewds.climate.copernicus.eu/api", key=os.environ["CDS_API_KEY"], quiet=True, progress=False,
                      timeout=1800)
    out_dir = country_data_dir(args.country) / "reforecast"
    out_dir.mkdir(exist_ok=True)
    for m in args.months:
        out = out_dir / f"glofas_v4_{args.year}_{m:02d}.npz"
        if out.exists():
            print(f"{out.name} : déjà présent")
            continue
        raw = Path(tempfile.mkdtemp()) / "refc.grib"
        t0 = time.time()
        c.retrieve("cems-glofas-reforecast", request(cfg, args.year, m), str(raw))
        r = reduce(raw)
        raw.unlink()
        save_grid(out, **r)
        print(f"{out.name} : {len(r['init'])} initialisations, {r['q'].shape[1]} membres, {r['q'].shape[3]} mailles de rivière, "
              f"{out.stat().st_size / 1e6:.1f} Mo, {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
