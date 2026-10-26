"""Susceptibilité aux inondations par fokontany : probabilité estimée d'être inondé ou endommagé quand un cyclone ou une crue touche la zone.

Modèle : régression logistique sur les variables de terrain (HAND, altitude, pente, plus grande rivière, densité de population),
appris sur les dégâts cartographiés par satellite (Copernicus EMS, 6 cyclones) et évalué en laissant chaque événement de côté
(voir validation/README.md et validation/ems_resultats.json : coefficients, AUC, Brier). Calcul sans réseau.
Lecture : CONDITIONNELLE à un aléa réel (cyclone ou forte crue) sur la zone ; ce n'est pas une prévision de crue.
Sortie : data/<pays>/external/susceptibilite.csv (pcode, indicateur, valeur, date, source) au niveau fokontany.
Usage : python scripts/build_susceptibility.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

import numpy as np
import pandas as pd

from common import DATA_DIR, country_data_dir, read_units
from validate_events import predict

VAL = DATA_DIR.parent / "validation" / "ems_resultats.json"
SRC = ("MakyClimat : régression logistique sur HAND, altitude, pente, rivière et densité de population, apprise sur les dégâts "
       "cartographiés par satellite (Copernicus EMS, 6 cyclones) ; conditionnelle à un aléa réel, pas une prévision")


def features(units: pd.DataFrame, hydro: pd.DataFrame) -> pd.DataFrame:
    leaves = units[units.level == 4]
    hy = hydro[hydro.pcode.isin(set(leaves.pcode))].pivot_table(index="pcode", columns="indicateur", values="valeur").reset_index()
    t = leaves[["pcode", "pop", "area_km2"]].merge(hy, on="pcode", how="left")
    t["lhand5"] = np.log1p(t.hand_lt5_pct)
    t["lhand15"] = np.log1p(t.hand_lt15_pct)
    t["lslope"] = np.log1p(t.slope_mean_pct)
    t["lelev"] = np.log1p(t.elev_mean_m.clip(lower=0))
    t["lriver"] = np.log1p(t.river_max_km2)
    t["lpopdens"] = np.log1p(t["pop"].fillna(0) / t.area_km2.clip(lower=0.01))
    return t


def compute(units: pd.DataFrame, hydro: pd.DataFrame, model: dict) -> pd.DataFrame:
    t = features(units, hydro)
    cols = model["colonnes"]
    ok = t[cols].notna().all(axis=1)
    p = np.full(len(t), np.nan)
    p[ok.values] = predict((np.array(model["moyenne"]), np.array(model["ecart_type"]), model["intercept"], np.array(model["coefficients"])), t.loc[ok, cols].values)
    out = pd.DataFrame({"pcode": t.pcode, "indicateur": "susc_inond_pct", "valeur": np.round(100 * p, 1)}).dropna()
    out["date"] = dt.date.today().isoformat()
    out["source"] = SRC
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    a = ap.parse_args()
    if a.country != "mdg" or not VAL.exists():
        print("Susceptibilité : modèle indisponible pour ce pays.")
        return
    model = json.loads(VAL.read_text(encoding="utf-8"))["modele"].get("terrain seul")
    if model is None:
        print("Susceptibilité : modèle « terrain seul » absent (relancer la validation fokontany).")
        return
    ext = country_data_dir(a.country) / "external"
    hydro = pd.read_csv(ext / "hydro.csv")
    out = compute(read_units(a.country), hydro, model)
    out.to_csv(ext / "susceptibilite.csv", index=False)
    print(f"Susceptibilité : {len(out)} fokontany ; médiane {out.valeur.median():.0f} %, p90 {out.valeur.quantile(.9):.0f} %")


if __name__ == "__main__":
    main()
