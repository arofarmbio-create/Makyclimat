"""Débits de rivière (modèle GloFAS via l'API gratuite Open-Meteo) : seuils de crue et prévision, par commune.

  python scripts/update_floods.py --country mdg --thresholds   (une fois par an) : débits annuels maximaux 1984-aujourd'hui,
        crues de période de retour 2, 5, 10, 20 ans (loi de Gumbel) -> data/<pays>/flood_thresholds.csv
  python scripts/update_floods.py --country mdg                (toutes les 6 heures) : débit prévu -> grids/flood_forecast.npz
Résolution du modèle : environ 5 km ; incertain sur les petits bassins. À lire comme un signal, à confirmer par les services
hydrologiques. Le débit retourné est celui de la maille de rivière la plus proche du centroïde de la commune.
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import sys
import time

import numpy as np
import pandas as pd

import openmeteo as om
from common import country_data_dir, grid_dir, load_config, read_units, save_grid

EULER = 0.5772156649


def gumbel_levels(annual_max, periods=(2, 5, 10, 20)):
    """Débits de crue de période de retour T par ajustement de Gumbel (méthode des moments)."""
    x = np.asarray([v for v in annual_max if np.isfinite(v)], dtype=float)
    if len(x) < 15 or x.std() <= 0:
        return {T: float("nan") for T in periods}
    beta = x.std(ddof=1) * math.sqrt(6) / math.pi
    mu = x.mean() - EULER * beta
    return {T: float(mu - beta * math.log(-math.log(1 - 1 / T))) for T in periods}


def annual_maxima(times, values):
    s = pd.Series(values, index=pd.to_datetime(times))
    s = s[s.notna()]
    g = s.groupby(s.index.year)
    full = g.count() >= 300  # années quasi complètes
    return g.max()[full].to_numpy()


def thresholds(cfg, communes, batch=3, last_year=None, existing=None, max_locations=None, save=None):
    """Seuils par commune. Reprise possible : les communes déjà calculées sont conservées ; arrêt propre si l'API refuse (quota)."""
    start = cfg["flood"].get("history_start", 1984)
    last_year = last_year or dt.date.today().year - 1
    rows = [] if existing is None or len(existing) == 0 else existing.to_dict("records")
    done = {r["pcode"] for r in rows}
    todo = communes[~communes.pcode.isin(done)].reset_index(drop=True)
    if max_locations:
        todo = todo.iloc[:max_locations]
    for i in range(0, len(todo), batch):
        sub = todo.iloc[i:i + batch]
        params = {"latitude": ",".join(f"{x:.4f}" for x in sub.lat), "longitude": ",".join(f"{x:.4f}" for x in sub.lon),
                  "daily": "river_discharge", "start_date": f"{start}-01-01", "end_date": f"{last_year}-12-31"}
        try:
            payload = om.get_json(om.FLOOD_URL, params, retries=4, pause=5.0)
        except (RuntimeError, ValueError) as e:
            print(f"::warning::Seuils de crue interrompus après {len(rows)} communes : {e}")
            break
        for (pc, lon, lat), item in zip(zip(sub.pcode, sub.lon, sub.lat), om.as_list(payload)):
            d = item["daily"]
            am = annual_maxima(d["time"], [np.nan if v is None else v for v in d["river_discharge"]])
            lv = gumbel_levels(am)
            rows.append({"pcode": pc, "lon": lon, "lat": lat, "cell_lat": item.get("latitude"), "cell_lon": item.get("longitude"),
                         "n_years": len(am), "q_mean": float(np.mean(am)) if len(am) else np.nan,
                         **{f"q{T}": v for T, v in lv.items()}})
        if save:
            save(pd.DataFrame(rows))
        time.sleep(1.0)
        if (i // batch) % 20 == 0:
            print(f"  seuils : {len(rows)}/{len(communes)}")
    return pd.DataFrame(rows)


def forecast(communes, fc_cfg, batch=40):
    q, dates = [None] * len(communes), None
    for i in range(0, len(communes), batch):
        sub = communes.iloc[i:i + batch]
        params = {"latitude": ",".join(f"{x:.4f}" for x in sub.lat), "longitude": ",".join(f"{x:.4f}" for x in sub.lon),
                  "daily": "river_discharge", "forecast_days": fc_cfg["forecast_days"], "past_days": 3}
        try:
            payload = om.get_json(om.FLOOD_URL, params)
        except ValueError:
            params["past_days"] = 0
            payload = om.get_json(om.FLOOD_URL, params)
        for k, item in enumerate(om.as_list(payload)):
            d = item["daily"]
            dates = dates or d["time"]
            q[i + k] = [np.nan if v is None else v for v in d["river_discharge"]]
    return dates, np.array(q, dtype="float32")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--thresholds", action="store_true")
    ap.add_argument("--max-locations", type=int, default=None, help="plafond de communes par exécution (quota de l'API)")
    args = ap.parse_args()
    cfg = load_config(args.country)
    units = read_units(args.country)
    communes = units[units.level == 3][["pcode", "lon", "lat"]].reset_index(drop=True)
    th_path = country_data_dir(args.country) / "flood_thresholds.csv"
    if args.thresholds:
        old = pd.read_csv(th_path, dtype={"pcode": str}) if th_path.exists() else None
        df = thresholds(cfg, communes, existing=old, max_locations=args.max_locations,
                        save=lambda d: d.to_csv(th_path, index=False))
        print(f"Seuils de crue : {len(df)}/{len(communes)} communes ({int(df.q2.notna().sum()) if len(df) else 0} avec ajustement valide).")
        if len(df) == 0:
            sys.exit("Aucun seuil calculé (API indisponible ou quota atteint) : relancer plus tard.")
        return
    if not th_path.exists():
        sys.exit("Seuils de crue absents : lancer d'abord --thresholds (workflow « Seuils de crue »).")
    dates, q = forecast(communes, cfg["forecast"])
    if np.isnan(q).mean() > 0.2:
        sys.exit("Prévision de débit incomplète : non enregistrée.")
    save_grid(grid_dir(args.country) / "flood_forecast.npz", pcode=communes.pcode.to_numpy().astype(str), dates=np.array(dates),
              q=q, fetched_at=np.array(dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")))
    print(f"Débits prévus : {len(communes)} communes, {dates[0]} à {dates[-1]}")


if __name__ == "__main__":
    main()
