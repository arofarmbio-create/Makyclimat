"""Choc « crue » au format JIAF : période de retour du débit de rivière récent (GloFAS via Open-Meteo), par commune puis district et région.

Intensité = période de retour (ans) du débit journalier maximal des derniers jours (jours passés de la prévision, jusqu'à aujourd'hui), obtenue en
inversant l'ajustement de Gumbel des maxima annuels 1984-aujourd'hui de la commune (scripts/update_floods.py : crues de 2 et 20 ans).
Au-delà de 20 ans on extrapole : la valeur est plafonnée à 100 ans et à lire comme « supérieure à 20 ans ».
Limites : débit modélisé (maille de ~5 km), incertain sur les petits bassins ; résolution commune (pas fokontany) ; pas une hauteur d'eau ni un dégât.
Usage : python scripts/build_flood_shock.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import math

import numpy as np
import pandas as pd

from common import country_data_dir, grid_dir, load_config, load_grid, read_units

Y2, Y20 = -math.log(-math.log(1 - 1 / 2)), -math.log(-math.log(1 - 1 / 20))


def return_period(q, q2, q20, cap=100.0):
    """Période de retour (ans) d'un débit q d'après une loi de Gumbel passant par les crues de 2 et 20 ans ; NaN si ajustement invalide."""
    q = np.asarray(q, float)
    if not (np.isfinite(q2) and np.isfinite(q20)) or q20 <= q2:
        return np.full(q.shape, np.nan)
    beta = (q20 - q2) / (Y20 - Y2)
    y = (q - q2) / beta + Y2                                 # y = -ln(-ln(F))
    with np.errstate(over="ignore"):
        F = np.exp(-np.exp(-y))
        T = 1.0 / np.maximum(1.0 - F, 1e-9)
    return np.where(np.isfinite(q), np.clip(T, 1.0, cap), np.nan)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cfg = load_config(args.country)
    th = pd.read_csv(country_data_dir(args.country) / "flood_thresholds.csv", dtype={"pcode": str}).set_index("pcode")
    zf = load_grid(grid_dir(args.country) / "flood_forecast.npz")
    dates = [str(x) for x in zf["dates"]]
    today = dt.date.today().isoformat()
    if today not in dates:
        raise SystemExit("prévision de débit non à jour")
    f0 = dates.index(today)
    sl = slice(max(0, f0 - 3), f0 + 1)
    rows = []
    for i, pc in enumerate(zf["pcode"].astype(str)):
        if pc not in th.index or not np.isfinite(zf["q"][i, sl]).any():
            continue
        r = th.loc[pc]
        if not (r.get("q2", np.nan) >= cfg["flood"]["min_q2_m3s"]):
            continue
        q = float(np.nanmax(zf["q"][i, sl]))
        T = float(return_period([q], r["q2"], r["q20"])[0])
        if np.isfinite(T):
            rows.append((pc, T, q / r["q2"]))
    d = pd.DataFrame(rows, columns=["pcode", "T", "ratio"])
    units = read_units(args.country)
    comm = units[units.level == 3][["pcode", "adm1", "adm2"]].merge(d, on="pcode")
    parts = [d]
    for col in ("adm2", "adm1"):
        g = comm.groupby(col).agg(T=("T", "max"), ratio=("ratio", "max")).reset_index().rename(columns={col: "pcode"})
        parts.append(g)
    allv = pd.concat(parts).drop_duplicates("pcode")
    m = allv.rename(columns={"T": "choc_crue_retour_ans", "ratio": "choc_crue_ratio_q2"}).melt(id_vars="pcode", var_name="indicateur", value_name="valeur").dropna()
    m["valeur"] = m["valeur"].round(2)
    m["date"] = today
    m["source"] = "GloFAS (Copernicus/ECMWF) via Open-Meteo ; Gumbel des maxima annuels 1984-aujourd'hui ; plafonné à 100 ans"
    ed = country_data_dir(args.country) / "external"
    ed.mkdir(parents=True, exist_ok=True)
    m[["pcode", "indicateur", "valeur", "date", "source"]].to_csv(ed / "chocs_crue.csv", index=False)
    print(f"{len(d)} communes ; période de retour médiane {d['T'].median():.1f} ans, max {d['T'].max():.1f} ans")


if __name__ == "__main__":
    main()
