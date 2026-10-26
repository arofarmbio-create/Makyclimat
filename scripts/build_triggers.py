"""Déclencheurs d'action anticipée : seuils simples et lisibles (pas un score composite),
calibrés sur les mêmes données que validate_events.py (validation/cyclones_indicateurs_par_region.csv),
avec taux de détection (POD) et taux de fausses alertes (FAR) mesurés par seuil.

Contrairement au modèle de validate_events.py (régression logistique multi-variables, utile pour évaluer
la pertinence des indicateurs), ce script teste des seuils UNIVARIÉS sur une seule variable physique
(part de la population exposée au vent >= 34 nœuds, période de retour locale de la pluie sur 3 jours) :
c'est la forme que doit prendre un déclencheur opérationnel (une règle simple, pas une probabilité
calculée). Aucun paramètre n'est appris sur les données (les seuils testés sont fixés a priori, en unités
physiques rondes) : la évaluation par seuil n'a donc pas besoin d'un « laisser un événement de côté »
pour éviter le surapprentissage — mais l'échantillon (13 cyclones, 24 régions) reste petit, et une région
non citée touchée dans les rapports n'est pas forcément épargnée (listes partielles) : le FAR est donc
probablement surestimé, pas sous-estimé.

Usage : python scripts/build_triggers.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import DATA_DIR

VAL_DIR = DATA_DIR.parent / "validation"


def confusion(flag: np.ndarray, pos: np.ndarray) -> dict:
    flag, pos = np.asarray(flag, bool), np.asarray(pos, bool)
    tp, fp, fn, tn = int((flag & pos).sum()), int((flag & ~pos).sum()), int((~flag & pos).sum()), int((~flag & ~pos).sum())
    pod = tp / (tp + fn) if tp + fn else float("nan")
    far = fp / (tp + fp) if tp + fp else float("nan")
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "pod": pod, "far": far}


def events_covered(df: pd.DataFrame, flag: np.ndarray) -> tuple[int, int]:
    """Parmi les événements qui ont touché au moins une région (d'après les rapports), combien ont
    au moins une région correctement signalée par le déclencheur (sensibilité au niveau événement,
    distincte de la sensibilité au niveau région : un événement avec 5 régions touchées et 1 seule
    détectée compte comme « couvert » ici, mais pas dans le POD région par région)."""
    d = df.assign(flag=flag)
    with_pos = d.groupby("evenement")["pos"].sum()
    with_pos = with_pos[with_pos > 0].index
    covered = d[d.evenement.isin(with_pos)].groupby("evenement").apply(lambda g: bool((g.flag & g.pos).any()))
    return int(covered.sum()), int(len(with_pos))


def scan(df: pd.DataFrame, col: str, thresholds: list[float], label_fmt) -> list[dict]:
    rows = []
    for t in thresholds:
        flag = df[col].values >= t
        c = confusion(flag, df["pos"].values)
        n_cov, n_tot = events_covered(df, flag)
        rows.append({
            "variable": col, "seuil_brut": t, "seuil_lisible": label_fmt(t),
            "n_regions_signalees": int(flag.sum()),
            **c,
            "evenements_couverts": n_cov, "evenements_avec_impact": n_tot,
            "part_evenements_couverts": round(n_cov / n_tot, 2) if n_tot else float("nan"),
        })
    return rows


def main() -> None:
    df = pd.read_csv(VAL_DIR / "cyclones_indicateurs_par_region.csv")
    rows = []
    # Vent : part de la population du fokontany dans le rayon de vent >= 34 nœuds (tempête tropicale), par région.
    rows += scan(df, "cov34", [0.01, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70],
                 lambda t: f"≥ {round(t*100)} % de la population dans le rayon de vent ≥ 34 nœuds")
    rows += scan(df, "cov64", [0.01, 0.05, 0.10, 0.20, 0.30],
                 lambda t: f"≥ {round(t*100)} % de la population dans le rayon de vent ≥ 64 nœuds (force cyclonique)")
    # Pluie : période de retour locale (90e centile des fokontany de la région) du cumul max sur 3 jours.
    rows += scan(df, "rp90", [1.5, 2, 3, 5, 8, 10, 15],
                 lambda t: f"pluie sur 3 jours d'une période de retour locale ≥ {t:g} ans")
    out = pd.DataFrame(rows)
    out.to_csv(VAL_DIR / "declencheurs_anticipation.csv", index=False)

    # Combinaison simple (l'un OU l'autre) à un point de fonctionnement « équilibré » choisi pour
    # illustrer le compromis, PAS comme seuil recommandé : voir declencheurs_anticipation.md.
    flag_combo = (df["cov34"].values >= 0.10) | (df["rp90"].values >= 5)
    c = confusion(flag_combo, df["pos"].values)
    n_cov, n_tot = events_covered(df, flag_combo)
    combo = {"variable": "cov34>=0.10 OU rp90>=5", "seuil_lisible": "vent ≥ 34 nds sur 10 % de la population OU pluie 3j de retour ≥ 5 ans",
             **c, "evenements_couverts": n_cov, "evenements_avec_impact": n_tot,
             "part_evenements_couverts": round(n_cov / n_tot, 2) if n_tot else float("nan")}
    pd.DataFrame([combo]).to_csv(VAL_DIR / "declencheurs_anticipation_combine.csv", index=False)

    print(f"{len(df)} paires région-événement, {int(df['pos'].sum())} régions documentées touchées sur {df.evenement.nunique()} cyclones")
    print(out.to_string(index=False))
    print("\ncombiné :", combo)


if __name__ == "__main__":
    main()
