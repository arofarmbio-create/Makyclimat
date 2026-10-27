"""Potentiel relatif pour point d'eau peu profond (puits/forage), par fokontany — EXPÉRIMENTAL, NON VALIDÉ.

Ce que c'est : un classement relatif (0-100) des fokontany d'un pays selon 6 critères combinés par somme
pondérée (méthode d'analyse multicritère standard, utilisée en l'absence de données de forage réelles) :
  - aquifer_productivity_pct (30 %) : classe de productivité de l'aquifère RÉELLE (géologie/hydrogéologie,
    BGS Africa Groundwater Atlas — voir connector_geology.py) — le facteur géologique proprement dit.
  - water_table_depth_m       (20 %, inversé) : niveau statique d'eau RÉEL, mesuré sur des forages
    malgaches (MGMERL — voir connector_watertable.py, couverture ~30 % du pays) — plus la nappe est
    proche de la surface, mieux c'est noté.
  - recharge12_z              (25 %) : indice standardisé de recharge hydrique sur 12 mois (bilan de
    Thornthwaite-Mather, CHIRPS + ET0 ERA5-Land ; voir build_soilwater.py).
  - hand_lt15_pct              (8 %) : part de la zone à moins de 15 m au-dessus du cours d'eau le plus
    proche (HAND, Copernicus GLO-90).
  - slope_mean_pct             (9 %, inversé) : une pente plus faible facilite l'accès au chantier et
    l'infiltration (moins de ruissellement).
  - whc_mm                     (8 %) : capacité de rétention en eau du sol (SoilGrids).
Chaque critère est transformé en rang percentile (0-1) sur l'ensemble des fokontany du pays avant
pondération, pour que des unités différentes soient comparables.

Ce que ce n'est PAS, et pourquoi ce n'est "Non validé" (pas "Approximation", encore moins "Validé") :
  1. La géologie reste à l'échelle continentale grossière (BGS, 1:5 000 000) — pas de faille ni de
     structure locale résolue. La profondeur de nappe, elle, est une mesure réelle (MGMERL) mais
     ponctuelle et partielle (~30 % du pays, rayon 15 km d'un forage mesuré) : les 70 % restants n'ont
     aucune valeur pour ce critère.
  2. Les mesures MGMERL donnent des NIVEAUX réels, pas des RÉSULTATS de forage (succès/échec, débit) qui
     permettraient de calibrer statistiquement les poids choisis. C'est toujours une construction
     raisonnée, pas un modèle appris sur des résultats de forage réels.
  3. Une zone HAND basse (bien notée ici) est aussi une zone plus exposée aux inondations et au risque de
     contamination d'un puits peu profond — compromis documenté, pas résolu par ce score.
  4. Usage prévu : présélection de zones à visiter en priorité pour une étude hydrogéologique de terrain
     (sondage électrique, etc.), JAMAIS une décision de forage. Ne remplace pas une étude de terrain.

Entrées : data/<pays>/external/soilwater.csv (recharge12_z, whc_mm), data/<pays>/external/hydro.csv
(hand_lt15_pct, slope_mean_pct), data/<pays>/external/geology.csv (aquifer_productivity_pct),
data/<pays>/external/watertable.csv (water_table_depth_m).
Sortie : data/<pays>/external/groundwater.csv (pcode, indicateur=potentiel_eau_pct, valeur 0-100, date, source)
Usage : python scripts/build_groundwater.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import country_data_dir, read_units

SRC = ("MakyClimat : classement multicritère (productivité d'aquifère réelle BGS Africa Groundwater Atlas 30 %, "
       "niveau statique d'eau réel MGMERL inversé 20 % (~30 % du pays couvert), recharge CHIRPS/ET0 25 %, proximité du "
       "réseau de drainage HAND 8 %, pente inversée 9 %, capacité de rétention du sol SoilGrids 8 %) ; construction "
       "raisonnée, PAS calibrée sur des données réelles de forage malgaches (aucune disponible) ; présélection pour "
       "étude de terrain uniquement, jamais une décision de forage — voir validation/groundwater_limites.md")
WEIGHTS = {"aquifer_productivity_pct": 0.30, "water_table_depth_m": 0.20, "recharge12_z": 0.25,
           "hand_lt15_pct": 0.08, "slope_mean_pct": 0.09, "whc_mm": 0.08}
INVERT = {"slope_mean_pct", "water_table_depth_m"}  # pente et profondeur de nappe : plus bas = meilleur score


def pct_rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, na_option="keep")


def compute(hydro: pd.DataFrame, soilwater: pd.DataFrame, leaves: pd.DataFrame,
            geology: pd.DataFrame | None = None, watertable: pd.DataFrame | None = None) -> pd.DataFrame:
    hy = hydro[hydro.indicateur.isin(["hand_lt15_pct", "slope_mean_pct"])].pivot_table(
        index="pcode", columns="indicateur", values="valeur").reset_index()
    sw = soilwater[soilwater.indicateur.isin(["recharge12_z", "whc_mm"])].pivot_table(
        index="pcode", columns="indicateur", values="valeur").reset_index()
    t = leaves[["pcode"]].merge(hy, on="pcode", how="left").merge(sw, on="pcode", how="left")
    if geology is not None and len(geology):
        ge = geology[geology.indicateur == "aquifer_productivity_pct"][["pcode", "valeur"]].rename(columns={"valeur": "aquifer_productivity_pct"})
        t = t.merge(ge, on="pcode", how="left")
    if watertable is not None and len(watertable):
        wt = watertable[watertable.indicateur == "water_table_depth_m"][["pcode", "valeur"]].rename(columns={"valeur": "water_table_depth_m"})
        t = t.merge(wt, on="pcode", how="left")
    score = pd.Series(0.0, index=t.index)
    weight_used = pd.Series(0.0, index=t.index)
    weight_available = sum(w for col, w in WEIGHTS.items() if col in t.columns)  # critères dont la source existe cette fois
    for col, w in WEIGHTS.items():
        if col not in t.columns:
            continue
        r = pct_rank(t[col])
        if col in INVERT:
            r = 1 - r
        ok = r.notna()
        score[ok] += w * r[ok]
        weight_used[ok] += w
    # au moins 70 % des critères DISPONIBLES cette fois (si geology/watertable manquent, le seuil porte sur les 4 restants)
    valid = weight_used >= 0.70 * weight_available if weight_available > 0 else pd.Series(False, index=t.index)
    out = pd.DataFrame({
        "pcode": t.pcode,
        "indicateur": "potentiel_eau_pct",
        "valeur": np.round(100 * score / weight_used.replace(0, np.nan), 1),
    })[valid].dropna()
    out["date"] = dt.date.today().isoformat()
    out["source"] = SRC
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    ext = country_data_dir(args.country) / "external"
    try:
        hydro = pd.read_csv(ext / "hydro.csv")
        soilwater = pd.read_csv(ext / "soilwater.csv")
    except FileNotFoundError as exc:
        print(f"Potentiel eau : fichier source manquant ({exc}) — lancer build_hydro.py et build_soilwater.py d'abord.")
        return
    geology = pd.read_csv(ext / "geology.csv") if (ext / "geology.csv").exists() else None
    watertable = pd.read_csv(ext / "watertable.csv") if (ext / "watertable.csv").exists() else None
    if geology is None:
        print("Potentiel eau : geology.csv absent (connecteur géologie non lancé ou indisponible) — critère ignoré pour cette mise à jour.")
    if watertable is None:
        print("Potentiel eau : watertable.csv absent (connecteur profondeur de nappe non lancé ou indisponible) — critère ignoré pour cette mise à jour.")
    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]
    out = compute(hydro, soilwater, leaves, geology, watertable)
    out.to_csv(ext / "groundwater.csv", index=False)
    print(f"Potentiel eau (expérimental, non validé) : {len(out)} fokontany notés sur {len(leaves)}, "
          f"médiane {out.valeur.median():.0f}/100" if len(out) else "Potentiel eau : aucun fokontany avec assez de critères disponibles.")


if __name__ == "__main__":
    main()
