"""Analyse de puissance rétrospective des tests antérieurs au 09/11/2026 (aucune hypothèse testée) : ces tests
avaient-ils une chance réelle de conclure ? Effectifs tirés des rapports publiés.

1. Tests du signe entre sites ou événements (E1 : 5 stations ; H-N1 : 7 sites ; THMS H-M1 : 12 sites ; R-02 : 8
   activations EMS, l'événement étant l'unité indépendante) : nombre minimal de cas favorables pour p < 0,05
   (unilatéral) et puissance selon la probabilité p qu'un site soit favorable.
2. Téléconnexions par région (R-25) : 144 tests (régions × cibles × modèles) corrigés par Benjamini-Hochberg à 10 %,
   45 saisons ; puissance de retenir au moins un vrai lien parmi k, pour une corrélation r (approximation de Fisher).
Sortie : validation/analyse_puissance_retro.md. Usage : python scripts/analyse_puissance_retro.py
"""
from __future__ import annotations

import datetime as dt

import numpy as np
from scipy import stats

from common import ROOT
from puissance_hn7 import bh

SEED, NSIM = 20261109, 4000
SIGNE = [("E1, fusion des pluies (R-35)", "stations GSOD", 5, "2 sur 5, p = 0,81"),
         ("Nappes contre SPI-12, H-N1 (R-36)", "sites MGMERL", 7, "5 sur 7, p = 0,23"),
         ("THMS, H-M1 (R-44)", "sites de nappe", 12, "2 sur 12"),
         ("Fokontany touchés, R-02 (8 activations EMS)", "événements", 8, "AUC 0,16 à 0,62 selon l'événement")]


def k_min(n: int, alpha: float = 0.05) -> int | None:
    for k in range(n + 1):
        if stats.binom.sf(k - 1, n, 0.5) < alpha:
            return k
    return None


def puissance_signe(n: int, p: float) -> float:
    k = k_min(n)
    return float(stats.binom.sf(k - 1, n, p)) if k is not None else 0.0


def puissance_bh(m: int, k: int, r: float, n: int, rng, nsim=NSIM, q=0.10) -> float:
    """Probabilité de retenir au moins un des k vrais liens parmi m tests (z de Fisher, bilatéral)."""
    mu = np.arctanh(r) * np.sqrt(n - 3)
    hits = 0
    for _ in range(nsim):
        z = rng.normal(size=m)
        z[:k] += mu
        p = 2 * stats.norm.sf(np.abs(z))
        if bh(p, q)[:k].any():
            hits += 1
    return hits / nsim


def main() -> None:
    rng = np.random.default_rng(SEED)
    L = ["# Analyse de puissance rétrospective des tests antérieurs", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/analyse_puissance_retro.py`. **Aucune hypothèse n'est testée** : on "
         "demande si ces tests avaient une chance réelle de conclure. Effectifs tirés des rapports publiés.", "",
         "## 1. Tests du signe entre sites ou événements (seuil 5 %, unilatéral)", "",
         "| Test | Unités | n | Résultat publié | Favorables nécessaires | Puissance si p = 0,6 | 0,7 | 0,8 | 0,9 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for nom, unite, n, res in SIGNE:
        k = k_min(n)
        L.append(f"| {nom} | {unite} | {n} | {res} | {k} sur {n} | " + " | ".join(f"{puissance_signe(n, p):.0%}" for p in (0.6, 0.7, 0.8, 0.9)) + " |")
    L += ["", "p = probabilité qu'une unité donnée soit favorable si l'effet existe. Avec 5 stations, le test du signe exige 5 sur 5 : "
          "il ne réussit qu'environ une fois sur trois même si la fusion aide 80 % des stations.", "",
          "## 2. Téléconnexions par région (R-25 : 144 tests, Benjamini-Hochberg à 10 %, 45 saisons)", "",
          "| r | 5 vrais liens | 20 vrais liens | 50 vrais liens |", "|---|---|---|---|"]
    for r in (0.2, 0.3, 0.4, 0.5):
        L.append(f"| {r:.1f} | " + " | ".join(f"{puissance_bh(144, k, r, 45, rng):.0%}" for k in (5, 20, 50)) + " |")
    L += ["", "Probabilité de retenir au moins un vrai lien. Avec 144 tests, un lien modéré (r = 0,3) n'est retenu que s'il est "
          "répandu dans beaucoup de régions et de cibles.", "",
          "## 3. Ce que cela change pour la rédaction", "",
          "| Résultat publié | Avant | Lecture corrigée |", "|---|---|---|",
          "| E1 : fusion non démontrée | « non soutenue » | **test sans puissance** (5 stations) : ni confirmé ni réfuté ; il faut des stations DGM |",
          "| H-N1 : SPI-12 et nappes | « non soutenue » | **puissance faible** (7 sites ; 7 sur 7 exigés) : 5 sur 7 va dans le sens attendu |",
          "| THMS, H-M1 | « non soutenue » | 2 sur 12 : **résultat négatif réel** (10 favorables exigés ; on en est loin) |",
          "| R-02 : fokontany touchés | AUC instable | l'unité indépendante est l'événement : **8 seulement** ; la stabilité ne peut pas être établie |",
          "| R-25 : téléconnexions | quelques régions non prévisibles | la correction sur 144 tests ne laisse passer que des liens forts ou répandus ; "
          "les régions « non prévisibles » ne prouvent pas l'absence de lien |",
          "| R-01 : régions touchées par un cyclone | AUC 0,84, 21 cyclones | effet fort : la puissance n'est pas en cause |", "",
          "Règle (adoptée le 09/11/2026) : ces lectures corrigées remplacent « non soutenue » par « non établi, puissance insuffisante » "
          "dans la thèse, sauf pour THMS (négatif réel).", ""]
    (ROOT / "validation" / "analyse_puissance_retro.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[4:12]))


if __name__ == "__main__":
    main()
