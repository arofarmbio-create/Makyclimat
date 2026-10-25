"""Prévision météo (Open-Meteo, gratuite, sans clé) sur une grille de mailles de 0,25° couvrant les fokontany.

Écrit data/<pays>/grids/forecast.npz : pour chaque maille, par jour (jours récents puis 16 jours de prévision) :
pluie (mm), température max et min (°C), rafales (km/h), vent moyen max (km/h), évapotranspiration (mm).
Usage : python scripts/update_forecast.py --country mdg        (toutes les 6 heures via le workflow)
Les prévisions sont des sorties de modèle : elles ne remplacent pas les bulletins de Météo Madagascar.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

import numpy as np

import openmeteo as om
from common import grid_dir, load_config, read_units, save_grid


def build_points(units, res):
    leaves = units[units.level == units.level.max()]
    ix, iy = om.cell_key(leaves.lon.to_numpy(), leaves.lat.to_numpy(), res)
    cells = sorted(set(zip(ix.tolist(), iy.tolist())))
    return np.array([c[0] * res for c in cells]), np.array([c[1] * res for c in cells])


def fetch(lons, lats, fc_cfg, tz, batch=40):
    n = len(lons)
    out = {v: [None] * n for v in om.DAILY_VARS}
    dates = None
    for start in range(0, n, batch):
        sl = slice(start, min(n, start + batch))
        params = {"latitude": ",".join(f"{x:.4f}" for x in lats[sl]), "longitude": ",".join(f"{x:.4f}" for x in lons[sl]),
                  "daily": ",".join(om.DAILY_VARS), "forecast_days": fc_cfg["forecast_days"], "timezone": tz,
                  "past_days": fc_cfg["past_days"]}
        try:
            payload = om.get_json(om.FORECAST_URL, params)
        except ValueError:  # certaines configurations refusent past_days élevé : on réessaie avec 2 jours
            params["past_days"] = 2
            payload = om.get_json(om.FORECAST_URL, params)
        for k, item in enumerate(om.as_list(payload)):
            d = item["daily"]
            if dates is None:
                dates = d["time"]
            if d["time"] != dates:
                raise RuntimeError("dates différentes entre mailles")
            for v in om.DAILY_VARS:
                out[v][start + k] = [np.nan if x is None else x for x in d[v]]
    arr = {v: np.array(out[v], dtype="float32") for v in om.DAILY_VARS}
    return dates, arr


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cfg = load_config(args.country)
    fc = cfg["forecast"]
    units = read_units(args.country)
    lons, lats = build_points(units, fc["grid_res"])
    print(f"{len(lons)} mailles de prévision ({fc['grid_res']}°)")
    dates, arr = fetch(lons, lats, fc, cfg.get("timezone", "auto"))
    miss = float(np.isnan(arr["precipitation_sum"]).mean())
    if miss > 0.1:
        sys.exit(f"Prévision incomplète ({miss:.0%} de valeurs manquantes) : non enregistrée.")
    today = dt.date.today().isoformat()
    save_grid(grid_dir(args.country) / "forecast.npz", lon=lons, lat=lats, dates=np.array(dates), res=np.array(fc["grid_res"]),
              fetched_at=np.array(dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")), today=np.array(today),
              **{k: v for k, v in arr.items()})
    print(f"Prévision enregistrée : {dates[0]} à {dates[-1]} ({len(dates)} jours)")


if __name__ == "__main__":
    main()
