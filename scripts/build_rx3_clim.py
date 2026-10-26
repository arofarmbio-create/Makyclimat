"""Climatologie locale des pluies extrêmes : cumul maximal sur 3 jours de chaque saison humide (nov.-avril), par fokontany.

Source : CHIRPS journalier (CHC/UCSB), saisons de `--start` à `--end` (année de fin). Sert à dire si une pluie observée est
« exceptionnelle pour cet endroit » (période de retour empirique = (N+1)/(1+nombre de saisons au moins aussi fortes)).
Sortie : data/<pays>/grids/rx3_annual.npz  (saisons, matrice (saisons, fokontany) en mm) ; reprise possible (saisons déjà faites ignorées).
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np

from chirps_daily import days_between, leaf_series, roll3_max
from common import grid_dir, load_config, read_units


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--start", type=int, default=2006)
    ap.add_argument("--end", type=int, default=2020)
    a = ap.parse_args()
    bbox = load_config(a.country)["map"]["bbox"]
    leaves = read_units(a.country)
    leaves = leaves[leaves.level == 4].reset_index(drop=True)
    path = grid_dir(a.country) / "rx3_annual.npz"
    done = {}
    if path.exists():
        z = np.load(path, allow_pickle=True)
        if len(z["codes"]) == len(leaves) and (z["codes"] == leaves.pcode.values).all():
            done = {int(s): m for s, m in zip(z["seasons"], z["rx3"])}
    sampler = None
    for y in range(a.start, a.end + 1):
        if y in done:
            continue
        days = days_between(dt.date(y - 1, 11, 1), dt.date(y, 4, 30))
        v, sampler = leaf_series(days, bbox, leaves.lon.values, leaves.lat.values, sampler, workers=10)
        miss = int(np.isnan(v).all(axis=1).sum())
        if miss > 5:
            print(f"saison {y}: {miss} jours absents : ignorée")
            continue
        done[y] = roll3_max(v)
        print(f"saison {y}: médiane nationale du maximum 3 j = {np.nanmedian(done[y]):.0f} mm ({miss} jours absents)", flush=True)
        seasons = sorted(done)
        np.savez_compressed(path, seasons=np.array(seasons), rx3=np.vstack([done[s] for s in seasons]).astype("float32"), codes=leaves.pcode.values.astype(str))
    print(f"{len(done)} saisons enregistrées")


if __name__ == "__main__":
    main()
