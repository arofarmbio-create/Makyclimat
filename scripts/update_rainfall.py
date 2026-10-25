"""Connecteur PLUIE (mise à jour automatique) : cumul de pluie de la saison en cours (CHIRPS) comparé
à la normale pour la même période.

Usage : python scripts/update_rainfall.py --country mdg [--today AAAA-MM-JJ]
Écrit data/<pays>/grids/season.npz (act = pluie cumulée, norm = normale à la même date, data_through).
Début de saison sans aucune donnée récente : le script bascule sur la saison précédente complète,
pour que le site ne reste jamais vide.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import sys

import numpy as np

from chirps import fetch_array, month_fraction_covered, season_months
from common import grid_dir, load_config, load_grid, save_grid


def get_month(cfg: dict, year: int, month: int, today: dt.date):
    """Pluie d'un mois : fichier mensuel s'il existe, sinon somme des dékades disponibles.
    Retourne (tableau mm, fraction du mois couverte, géoréférence, dernière date couverte) ou None."""
    bbox = cfg["map"]["bbox"]
    last_day = calendar.monthrange(year, month)[1]
    month_over = today > dt.date(year, month, last_day)
    if month_over:
        res = fetch_array(cfg["rainfall"]["monthly_url"].format(y=year, m=month), bbox)
        if res is not None:
            arr, lon0, lat0, step = res
            return arr, 1.0, (lon0, lat0, step), dt.date(year, month, last_day)
    total, geo, done = None, None, 0
    for d in (1, 2, 3):
        end_day = 10 * d if d < 3 else last_day
        if dt.date(year, month, end_day) > today:
            break
        res = fetch_array(cfg["rainfall"]["dekad_url"].format(y=year, m=month, d=d), bbox)
        if res is None:
            break
        arr, lon0, lat0, step = res
        geo = geo or (lon0, lat0, step)
        total = arr if total is None else total + arr  # NaN (mer, pas de donnée) se propage
        done = d
    if done == 0:
        return None
    end_day = 10 * done if done < 3 else last_day
    return total, month_fraction_covered(year, month, done), geo, dt.date(year, month, end_day)


def accumulate(cfg: dict, clim: dict, today: dt.date):
    """Cumul de la saison jusqu'à `today`. Retourne None si aucun mois n'est disponible."""
    months = season_months(today, cfg["rainfall"]["season_start_month"], cfg["rainfall"]["season_end_month"])
    act = norm = through = geo = None
    for (y, m) in months:
        got = get_month(cfg, y, m, today)
        if got is None:
            print(f"  pas de données pour {y}-{m:02d} : arrêt du cumul")
            break
        arr, frac, g, last = got
        geo = geo or g
        if arr.shape != clim["clim"][m - 1].shape:
            raise SystemExit(f"Grille incompatible pour {y}-{m:02d} : {arr.shape} vs {clim['clim'][m - 1].shape}")
        n = clim["clim"][m - 1] * frac
        act = arr if act is None else act + arr
        norm = n if norm is None else norm + n
        through = last
        print(f"  {y}-{m:02d} : couverture {frac:.0%}")
    if act is None:
        return None
    return act, norm, through, geo, months


def previous_season_end(cfg: dict, today: dt.date) -> dt.date:
    sm, em = cfg["rainfall"]["season_start_month"], cfg["rainfall"]["season_end_month"]
    y0 = today.year if today.month >= sm else today.year - 1  # année de début de la saison courante
    end_year = y0 if em < sm else y0 - 1
    return dt.date(end_year, em, calendar.monthrange(end_year, em)[1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--today", help="Date simulée AAAA-MM-JJ (tests)")
    args = ap.parse_args()
    cfg = load_config(args.country)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()

    clim_file = grid_dir(args.country) / "clim_monthly.npz"
    if not clim_file.exists():
        raise SystemExit("Normale absente : lancer d'abord build_climatology.py (workflow « normale de pluie »).")
    clim = load_grid(clim_file)

    got = accumulate(cfg, clim, today)
    if got is None:
        fallback = previous_season_end(cfg, today)
        print(f"Aucune donnée pour la saison en cours : repli sur la saison précédente (jusqu'au {fallback}).")
        got = accumulate(cfg, clim, fallback + dt.timedelta(days=1))
    if got is None:
        print("Aucune donnée de pluie disponible (réseau ou source) : rien n'est écrit.")
        sys.exit(1)
    act, norm, through, geo, months = got

    save_grid(grid_dir(args.country) / "season.npz", act=act.astype("float32"), norm=norm.astype("float32"),
              lon0=np.array(geo[0]), lat0=np.array(geo[1]), res=np.array(geo[2]),
              data_through=np.array(through.isoformat()),
              season_start=np.array(f"{months[0][0]}-{months[0][1]:02d}"),
              updated=np.array(dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")))
    print(f"Pluie de saison écrite : données jusqu'au {through}")


if __name__ == "__main__":
    main()
