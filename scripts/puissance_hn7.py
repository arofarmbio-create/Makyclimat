"""Analyse de puissance du maillon A de H-N7 (validation/protocole_climat_extremes_nappes.md), avant tout calcul.
Simulation seule, sans les données de pluie : 45 saisons ; prédicteur = indice océanique de juillet-septembre ;
résultat = au moins un mois extrême dans la saison (variable latente seuillée pour une fréquence p de saisons
extrêmes) ; lien = corrélation r entre l'indice et la variable latente. Épreuve 3 du protocole : Spearman bilatéral,
correction de Benjamini-Hochberg à 10 % sur 9 tests (3 régions × 3 indices), dont k vrais effets ; les épreuves 1, 2
et 4 s'y ajoutent, donc la puissance réelle est au plus celle calculée ici.
Sortie : validation/puissance_hn7.md. Usage : python scripts/puissance_hn7.py
"""
from __future__ import annotations

import datetime as dt

import numpy as np
from scipy import stats

from common import ROOT

N, NTEST, FDR, NSIM, SEED = 45, 9, 0.10, 3000, 20261109


def bh(p: np.ndarray, q: float = FDR) -> np.ndarray:
    """Rejets de Benjamini-Hochberg."""
    m = len(p)
    o = np.argsort(p)
    ok = p[o] <= q * np.arange(1, m + 1) / m
    k = np.max(np.nonzero(ok)[0]) + 1 if ok.any() else 0
    rej = np.zeros(m, bool)
    rej[o[:k]] = True
    return rej


def puissance(r: float, p_ext: float, k_vrais: int, rng, n=N, nsim=NSIM) -> float:
    """Probabilité qu'au moins un des k vrais effets soit retenu après correction."""
    seuil = stats.norm.ppf(1 - p_ext)
    hits = 0
    for _ in range(nsim):
        ps = np.empty(NTEST)
        for t in range(NTEST):
            x = rng.normal(size=n)
            rr = r if t < k_vrais else 0.0
            lat = rr * x + np.sqrt(1 - rr ** 2) * rng.normal(size=n)
            y = (lat > seuil).astype(float)
            if y.std() == 0:
                ps[t] = 1.0
                continue
            ps[t] = stats.spearmanr(x, y).pvalue
        if bh(ps)[:k_vrais].any():
            hits += 1
    return hits / nsim


def main() -> None:
    rng = np.random.default_rng(SEED)
    L = ["# Analyse de puissance du maillon A de H-N7 (avant tout calcul)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/puissance_hn7.py`. Simulation seule, sans les données de pluie : "
         f"{N} saisons, {NTEST} tests (3 régions × 3 indices), Benjamini-Hochberg à {FDR:.0%}, {NSIM} simulations par case. "
         "r = corrélation entre l'indice de juillet-septembre et la pluie latente de la saison ; p = part des saisons avec au "
         "moins un mois extrême. Seule l'épreuve 3 (Spearman) est simulée : la puissance réelle, avec les quatre épreuves, est "
         "au plus celle-ci.", ""]
    for k in (1, 3):
        L += [f"## {k} vrai(s) lien(s) parmi les 9 tests", "", "| r | p = 20 % | p = 30 % | p = 45 % |", "|---|---|---|---|"]
        for r in (0.2, 0.3, 0.4, 0.5):
            L.append(f"| {r:.1f} | " + " | ".join(f"{puissance(r, p, k, rng):.0%}" for p in (0.2, 0.3, 0.45)) + " |")
        L.append("")
    L += ["## Lecture", "",
          "- Avec 45 saisons et un résultat binaire, seul un lien fort (r d'au moins 0,4 à 0,5) a de bonnes chances d'être "
          "retenu après correction ; un lien modéré (r = 0,2 à 0,3), plausible d'après la littérature (« moins clair » dans le "
          "sud-ouest), est presque indétectable.",
          "- Règle adoptée le 09/11/2026 : si la puissance est inférieure à 50 % pour l'effet plausible, le test est déclaré "
          "**exploratoire dès le départ** ; un résultat négatif ne réfutera alors pas le lien océan → pluies extrêmes.",
          "- Gains possibles sans changer l'hypothèse : remplacer le résultat binaire par le **nombre de mois extrêmes** ou par "
          "la pluie maximale mensuelle (variable continue, plus puissante) ; réduire le nombre de tests (une région, un "
          "indice choisis par la littérature). Ces changements seraient datés dans le protocole avant tout calcul.", ""]
    (ROOT / "validation" / "puissance_hn7.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
