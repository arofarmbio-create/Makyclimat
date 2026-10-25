"""Calcule la NORMALE mensuelle de pluie (moyenne CHIRPS sur la période de référence) recadrée sur le pays.

Usage : python scripts/build_climatology.py --country mdg [--start 1991 --end 2020]
Télécharge ~360 fichiers mensuels (environ 1 Go au total, 10 à 20 minutes). À lancer UNE fois
(workflow « Construire la normale de pluie »), puis jamais : le résultat est conservé dans le dépôt.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from chirps import fetch_array
from common import grid_dir, load_config, save_grid


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--start", type=int)
    ap.add_argument("--end", type=int)
    args = ap.parse_args()
    cfg = load_config(args.country)
    y0, y1 = cfg["rainfall"]["baseline_years"]
    y0, y1 = args.start or y0, args.end or y1
    bbox = cfg["map"]["bbox"]
    tmpl = cfg["rainfall"]["monthly_url"]

    jobs = [(y, m) for y in range(y0, y1 + 1) for m in range(1, 13)]

    def one(job):
        y, m = job
        try:
            return job, fetch_array(tmpl.format(y=y, m=m), bbox)
        except Exception as e:  # noqa: BLE001
            print(f"  échec {y}-{m:02d}: {e}")
            return job, None

    sums = {m: None for m in range(1, 13)}
    counts = {m: None for m in range(1, 13)}
    geo = None
    ok = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        for (y, m), res in ex.map(one, jobs):
            if res is None:
                print(f"  manquant: {y}-{m:02d}")
                continue
            arr, lon0, lat0, step = res
            geo = geo or (lon0, lat0, step)
            valid = np.isfinite(arr)
            if sums[m] is None:
                sums[m] = np.zeros_like(arr, dtype="float64")
                counts[m] = np.zeros_like(arr, dtype="int16")
            sums[m][valid] += arr[valid]
            counts[m][valid] += 1
            ok += 1
    if geo is None or ok < 0.8 * len(jobs):
        raise SystemExit(f"Trop de fichiers manquants ({ok}/{len(jobs)}) : normale non écrite.")
    clim = np.stack([np.where(counts[m] > 0, sums[m] / np.maximum(counts[m], 1), np.nan)
                     for m in range(1, 13)]).astype("float32")
    save_grid(grid_dir(args.country) / "clim_monthly.npz", clim=clim,
              lon0=np.array(geo[0]), lat0=np.array(geo[1]), res=np.array(geo[2]),
              years=np.array([y0, y1]), n_files=np.array(ok))
    print(f"Normale écrite ({ok}/{len(jobs)} fichiers), grille {clim.shape[1]}x{clim.shape[2]}")


if __name__ == "__main__":
    main()
