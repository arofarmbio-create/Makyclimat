"""Grilles mensuelles de SPI-3 et SPI-12 (CHIRPS, 0,05°) des 48 derniers mois, pour la phase 1 du protocole-cadre
« eaux souterraines » (variables de date des relevés de forage).

Même calcul qu'en production (build_soilwater.rain_series pour la pluie mensuelle depuis 1981, soilwater_core.spi pour
le SPI : loi gamma par mois du calendrier, normale minimale du pays). Les relevés de forage ne sont pas lus ici : ils
restent sur le poste local ; seules les grilles sont produites.
Sortie : data/<pays>/grids/spi_grilles.npz (spi3, spi12 en float16 [mois, lat, lon], mois AAAA-MM, géoréférence).
Usage : python scripts/build_spi_grilles.py --country mdg [--mois 48]
"""
from __future__ import annotations

import argparse

import numpy as np

import build_soilwater as B
import soilwater_core as C
from common import grid_dir, load_config, load_grid, save_grid


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--mois", type=int, default=48)
    args = ap.parse_args()
    cfg = load_config(args.country)
    ms = load_grid(grid_dir(args.country) / "monthly_series.npz")
    h, w = ms["arr"].shape[-2:]
    grid = {"lon0": float(ms["lon0"]), "lat0": float(ms["lat0"]), "res": float(ms["res"]), "h": int(h), "w": int(w)}
    rain = B.rain_series(grid, cfg, args.country, B.read_chirps_month)
    if rain is None:
        raise SystemExit("pluie mensuelle indisponible ou tronquée : rien n'est écrit")
    P, labels = rain
    flat = np.nan_to_num(P.reshape(len(P), -1).astype("float64"), nan=0.0)
    land = np.isfinite(np.asarray(ms["arr"][-1, 0], dtype="float32")).ravel()
    min_mm = float(cfg["rainfall"].get("min_normal_mm", 25))
    out = {}
    for n in (3, 12):
        z = np.full(flat.shape, np.nan)
        z[:, land] = C.spi(flat[:, land], n, 11, min_mean_mm=min_mm)
        out[f"spi{n}"] = z[-args.mois:].reshape(args.mois, h, w).astype("float16")
    save_grid(grid_dir(args.country) / "spi_grilles.npz", **out, mois=np.array(labels[-args.mois:]),
              lon0=np.array(grid["lon0"]), lat0=np.array(grid["lat0"]), res=np.array(grid["res"]))
    print(f"spi_grilles.npz : {labels[-args.mois]} à {labels[-1]}, {h} x {w} mailles")


if __name__ == "__main__":
    main()
