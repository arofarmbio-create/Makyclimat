"""R-21 : analyse de puissance du critère principal H1 (protocole_verification_impact.md, section 9, option 1).

Critère : gain de détection des épisodes d'impact documentés à 1-3 jours, ensemble GloFAS contre scénario de contrôle,
à charge d'alerte comparable. Résultat binaire par épisode et par méthode ; test apparié exact de McNemar unilatéral
(binomial sur les épisodes discordants), alpha = 0,05. Saison = bloc : les probabilités de discordance varient d'une
saison à l'autre (loi bêta, corrélation intra-saison rho), ce qui réduit l'information quand les épisodes se
concentrent dans peu de saisons. Aucune donnée de score n'est lue (verrou R-21).
Sortie : validation/r21_puissance.md. Usage : python scripts/r21_puissance.py [--episodes N --saisons K]
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
from scipy.stats import binom

ROOT = Path(__file__).resolve().parent.parent
ALPHA = 0.05
N_SIM = 20000


def p_mcnemar(b, c):
    """p unilatéral exact : b = détectés par l'ensemble seul, c = par le contrôle seul."""
    n = b + c
    return np.where(n > 0, binom.sf(b - 1, n, 0.5), 1.0)


def puissance(n_ep, n_saisons, p_ens_seul, p_ctl_seul, rho, rng):
    """Puissance par simulation : épisodes répartis au mieux entre saisons, discordances bêta par saison."""
    taille = np.full(n_saisons, n_ep // n_saisons)
    taille[: n_ep % n_saisons] += 1
    b = np.zeros(N_SIM, int); c = np.zeros(N_SIM, int)
    p_disc = p_ens_seul + p_ctl_seul
    part = p_ens_seul / p_disc
    for m in taille:
        if rho > 0:
            k = (1 - rho) / rho
            pd = rng.beta(p_disc * k, (1 - p_disc) * k, N_SIM)
        else:
            pd = np.full(N_SIM, p_disc)
        d = rng.binomial(m, pd)
        bb = rng.binomial(d, part)
        b += bb; c += d - bb
    return float((p_mcnemar(b, c) < ALPHA).mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    # Cas réels (11/11/2026, épisodes = dates DesInventar regroupées à 3 jours, déc.-mars 2003-2018) : 15 épisodes dans
    # 7 saisons avec les mois publiés ; 25 dans 12 saisons si 7 mois de plus sont téléchargés. Puis grille indicative.
    ap.add_argument("--cas", nargs="*", default=["15:7", "25:12", "10:6", "20:8", "30:12", "50:16"],
                    help="épisodes:saisons")
    args = ap.parse_args()
    cas = [tuple(map(int, c.split(":"))) for c in args.cas]
    rng = np.random.default_rng(20261111)
    scenarios = [(0.25, 0.05), (0.35, 0.05), (0.45, 0.05)]        # gain de détection = différence : 20, 30, 40 points
    L = ["# R-21 — Analyse de puissance du critère H1", "",
         f"Calcul du {dt.date.today():%d/%m/%Y} par [`scripts/r21_puissance.py`](../scripts/r21_puissance.py) "
         f"({N_SIM} simulations par case, graine fixe). Test apparié exact de McNemar unilatéral, α = 0,05. "
         "Épisodes répartis au mieux entre les saisons ; ρ = corrélation intra-saison des discordances.", "",
         "Scénarios : p(ensemble seul) – p(contrôle seul) = gain de détection. Le gain jugé pertinent est à fixer par "
         "le porteur du projet avant les scores.", ""]
    for rho in (0.0, 0.1, 0.3):
        L += [f"## ρ = {rho:.1f}".replace(".", ","), "",
              "| Épisodes (saisons) | " + " | ".join(f"{a:.2f} / {b:.2f} (gain {100 * (a - b):.0f} pts)".replace(".", ",")
                                         for a, b in scenarios) + " |",
              "|---:|" + "---:|" * len(scenarios)]
        for n, k in cas:
            vals = [puissance(n, min(k, n), a, b, rho, rng) for a, b in scenarios]
            L.append(f"| {n} ({k}) | " + " | ".join(f"{100 * v:.0f} %" for v in vals) + " |")
        L.append("")
    sortie = ROOT / "validation" / "r21_puissance.md"
    sortie.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Écrit : {sortie}")


if __name__ == "__main__":
    main()
