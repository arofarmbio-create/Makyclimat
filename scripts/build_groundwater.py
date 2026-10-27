"""Potentiel relatif pour point d'eau peu profond (puits/forage), par fokontany — EXPÉRIMENTAL, NON VALIDÉ.

Ce que c'est : un classement relatif (0-100) des fokontany d'un pays selon 4 critères de terrain déjà
calculés par MakyClimat, combinés par somme pondérée (méthode d'analyse multicritère standard, utilisée
en l'absence de données de forage réelles) :
  - recharge12_z  (40 %) : indice standardisé de recharge hydrique sur 12 mois (bilan de Thornthwaite-Mather,
    CHIRPS + ET0 ERA5-Land ; voir build_soilwater.py) — plus de recharge = plus d'eau disponible pour la nappe.
  - hand_lt15_pct (25 %) : part de la zone à moins de 15 m au-dessus du cours d'eau le plus proche (HAND,
    Copernicus GLO-90) — une zone basse est généralement plus proche de la nappe (forage moins profond).
  - slope_mean_pct (20 %, inversé) : une pente plus faible facilite l'accès au chantier et l'infiltration
    (moins de ruissellement).
  - whc_mm (15 %) : capacité de rétention en eau du sol (SoilGrids) — un sol qui retient l'eau laisse
    plus de temps à l'infiltration vers la nappe qu'un sol qui ruisselle tout de suite.
Chaque critère est transformé en rang percentile (0-1) sur l'ensemble des fokontany du pays avant
pondération, pour que des unités différentes soient comparables.

Ce que ce n'est PAS, et pourquoi ce n'est "Non validé" (pas "Approximation", encore moins "Validé") :
  1. AUCUNE géologie (socle cristallin vs bassin sédimentaire, failles, type d'aquifère) n'est incluse —
     c'est pourtant souvent le facteur dominant du succès réel d'un forage. Donnée non disponible à cette
     résolution pour Madagascar.
  2. AUCUNE donnée réelle de forage (succès, débit, profondeur, salinité) n'existe à notre connaissance
     pour calibrer ou valider ce score. C'est une construction raisonnée, pas un modèle appris.
  3. Une zone HAND basse (bien notée ici) est aussi une zone plus exposée aux inondations et au risque de
     contamination d'un puits peu profond — compromis documenté, pas résolu par ce score.
  4. Usage prévu : présélection de zones à visiter en priorité pour une étude hydrogéologique de terrain
     (sondage électrique, etc.), JAMAIS une décision de forage. Ne remplace pas une étude de terrain.

Entrées : data/<pays>/external/soilwater.csv (recharge12_z, whc_mm), data/<pays>/external/hydro.csv
(hand_lt15_pct, slope_mean_pct) — déjà produits par build_soilwater.py et build_hydro.py.
Sortie : data/<pays>/external/groundwater.csv (pcode, indicateur=potentiel_eau_pct, valeur 0-100, date, source)
Usage : python scripts/build_groundwater.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import country_data_dir, read_units

SRC = ("MakyClimat : classement multicritère (recharge CHIRPS/ET0 40 %, proximité du réseau de drainage HAND 25 %, "
       "pente inversée 20 %, capacité de rétention du sol SoilGrids 15 %) ; construction raisonnée, PAS calibrée sur "
       "des données réelles de forage (aucune disponible) ; n'inclut pas la géologie ; présélection pour étude de "
       "terrain uniquement, jamais une décision de forage — voir validation/groundwater_limites.md")
WEIGHTS = {"recharge12_z": 0.40, "hand_lt15_pct": 0.25, "slope_mean_pct": 0.20, "whc_mm": 0.15}
INVERT = {"slope_mean_pct"}  # pente : plus bas = meilleur score


def pct_rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, na_option="keep")


def compute(hydro: pd.DataFrame, soilwater: pd.DataFrame, leaves: pd.DataFrame) -> pd.DataFrame:
    hy = hydro[hydro.indicateur.isin(["hand_lt15_pct", "slope_mean_pct"])].pivot_table(
        index="pcode", columns="indicateur", values="valeur").reset_index()
    sw = soilwater[soilwater.indicateur.isin(["recharge12_z", "whc_mm"])].pivot_table(
        index="pcode", columns="indicateur", values="valeur").reset_index()
    t = leaves[["pcode"]].merge(hy, on="pcode", how="left").merge(sw, on="pcode", how="left")
    score = pd.Series(0.0, index=t.index)
    weight_used = pd.Series(0.0, index=t.index)
    for col, w in WEIGHTS.items():
        if col not in t.columns:
            continue
        r = pct_rank(t[col])
        if col in INVERT:
            r = 1 - r
        ok = r.notna()
        score[ok] += w * r[ok]
        weight_used[ok] += w
    valid = weight_used >= 0.70  # au moins 70 % des critères disponibles (sinon fokontany sans assez de données)
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
    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]
    out = compute(hydro, soilwater, leaves)
    out.to_csv(ext / "groundwater.csv", index=False)
    print(f"Potentiel eau (expérimental, non validé) : {len(out)} fokontany notés sur {len(leaves)}, "
          f"médiane {out.valeur.median():.0f}/100" if len(out) else "Potentiel eau : aucun fokontany avec assez de critères disponibles.")


if __name__ == "__main__":
    main()
