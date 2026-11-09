"""Puissance du maillon A de H-N7 selon deux améliorations (avant tout calcul) : (a) résultat continu (pluie du mois le
plus fort de la saison) au lieu du résultat binaire ; (b) un seul test (une région, un indice) au lieu de 9 tests
corrigés. Simulation vectorisée : 45 saisons, Spearman bilatéral à 5 % (ou Benjamini-Hochberg à 10 % sur 9 tests,
1 vrai lien). Sortie : ajout à validation/puissance_hn7.md. Usage : python scripts/puissance_hn7_variantes.py
"""
from __future__ import annotations

import numpy as np
from scipy import stats

from common import ROOT
from puissance_hn7 import bh

N, NSIM, SEED, P_EXT = 45, 4000, 20261109, 0.30


def rang(a):
    return np.argsort(np.argsort(a, axis=1), axis=1).astype(float)


def p_spearman(x, y):
    """p bilatéraux de Spearman, ligne par ligne (approximation t)."""
    rx, ry = rang(x), rang(y + 1e-9 * np.random.default_rng(0).normal(size=y.shape))
    rx -= rx.mean(1, keepdims=True)
    ry -= ry.mean(1, keepdims=True)
    rho = (rx * ry).sum(1) / np.sqrt((rx ** 2).sum(1) * (ry ** 2).sum(1))
    t = rho * np.sqrt((N - 2) / np.clip(1 - rho ** 2, 1e-12, None))
    return 2 * stats.t.sf(np.abs(t), N - 2)


def simule(r, continu, un_test, rng):
    ntest = 1 if un_test else 9
    seuil = stats.norm.ppf(1 - P_EXT)
    ps = np.empty((NSIM, ntest))
    for t in range(ntest):
        rr = r if t == 0 else 0.0
        x = rng.normal(size=(NSIM, N))
        lat = rr * x + np.sqrt(1 - rr ** 2) * rng.normal(size=(NSIM, N))
        y = lat if continu else (lat > seuil).astype(float)
        ps[:, t] = p_spearman(x, y)
    if un_test:
        return float((ps[:, 0] < 0.05).mean())
    return float(np.mean([bh(row)[0] for row in ps]))


def main():
    rng = np.random.default_rng(SEED)
    L = ["", "## Variantes pour gagner en puissance (simulation du 09/11/2026, avant tout calcul)", "",
         f"Un seul vrai lien ; part des saisons extrêmes {P_EXT:.0%} pour la version binaire ; {NSIM} simulations.", "",
         "| r | Binaire, 9 tests (protocole actuel) | Continu, 9 tests | Binaire, 1 test | **Continu, 1 test** |", "|---|---|---|---|---|"]
    for r in (0.2, 0.3, 0.4, 0.5):
        v = [simule(r, c, u, rng) for c, u in ((False, False), (True, False), (False, True), (True, True))]
        L.append(f"| {r:.1f} | " + " | ".join(f"{x:.0%}" for x in v[:3]) + f" | **{v[3]:.0%}** |")
    L += ["", "Lecture : le résultat continu et le test unique ajoutent chacun de la puissance ; ensemble, ils rendent détectable un "
          "lien d'environ 0,4 et donnent une chance réelle à un lien de 0,3. Un lien de 0,2 reste hors de portée avec 45 saisons.", ""]
    with open(ROOT / "validation" / "puissance_hn7.md", "a", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
