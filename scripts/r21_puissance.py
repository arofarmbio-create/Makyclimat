"""R-21 : analyse de puissance du critère principal H1, alignée sur l'inférence par saisons (relecture Codex, 11/11).

Critère (protocole, section 9, option 1) : gain de détection à 1-3 jours, ensemble GloFAS contre contrôle, à charge
d'alerte comparable ; gain pertinent fixé à 30 points par le porteur du projet (11/11/2026), puissance visée 80 %.

Structure réelle : unités épisode x district éligibles (validation/r21_eligibilite.csv). Modèle simulé (2e version,
après la relecture de Codex du 11/11 à 13:25 et 13:28) :
- chaque méthode a sa propre probabilité de détection par unité : contrôle p_c (moyenne P_C, écart type SIGMA_C entre
  épisodes), ensemble p_e = p_c + g ; les quatre issues appariées (deux, ensemble seul, contrôle seul, aucune) sont
  simulées, avec une corrélation KAPPA entre les deux méthodes pour une même unité ;
- le gain g varie entre saisons (écart type tau) et entre épisodes (omega) ; après bornage des probabilités dans
  [0, 1], le décalage est recalé numériquement pour que le gain moyen simulé soit exactement le gain annoncé ;
- dépendance intra-épisode : avec la probabilité r, une unité reprend le tirage commun de son épisode.
Tests (unilatéraux, alpha = 0,05) :
- A, principal : permutation exacte des signes par saison sur T = somme_s (b_s - c_s) / racine(n_s), où b_s et c_s
  comptent les unités détectées par une seule méthode dans la saison s ; la saison est l'unité d'échange.
- B, comparaison : McNemar exact par épisode (épisode détecté si au moins un de ses districts l'est).
Erreur de type I contrôlée par simulation sous gain nul. Aucune donnée de score lue (verrou R-21).
Sortie : validation/r21_puissance.md. Usage : python scripts/r21_puissance.py [--sim 3000]
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom

ROOT = Path(__file__).resolve().parent.parent
ALPHA = 0.05
P_C = 0.40                     # détection moyenne du contrôle par unité (hypothèse, sensibilité à documenter)
SIGMA_C = 0.15                 # hétérogénéité de cette détection entre épisodes
KAPPA = 0.5                    # corrélation des deux méthodes pour une même unité (tirage uniforme partagé)


def structure(fichier, avec_lot=False):
    u = pd.read_csv(fichier)
    u = u[(u.eligible == 1) | (avec_lot & (u.raison == "mois en cours de téléchargement"))]
    ep = u.groupby("episode").agg(saison=("saison", "first"), n=("adm2", "size")).reset_index()
    return ep


def probabilites(gain, tau, omega, z_c, z_s, z_e, decalage):
    p_c = np.clip(P_C + SIGMA_C * z_c, 0.02, 0.98)
    p_e = np.clip(p_c + decalage + tau * z_s + omega * z_e, 0.0, 1.0)
    return p_c, p_e


def recaler(gain, tau, omega, rng, n=200_000):
    """Décalage tel que la moyenne de p_e - p_c, après bornage, vaille exactement le gain annoncé."""
    z = rng.standard_normal((3, n))
    lo, hi = gain - 1.0, gain + 1.0
    for _ in range(60):
        mi = (lo + hi) / 2
        p_c, p_e = probabilites(gain, tau, omega, z[0], z[1], z[2], mi)
        lo, hi = (mi, hi) if (p_e - p_c).mean() < gain else (lo, mi)
    return (lo + hi) / 2


def simuler(ep, gain, tau, omega, r, n_sim, rng, signes):
    saisons = np.sort(ep.saison.unique())
    si = np.searchsorted(saisons, ep.saison.to_numpy())
    S, E = len(saisons), len(ep)
    decalage = recaler(gain, tau, omega, rng)
    z_s = rng.standard_normal((n_sim, S))[:, si]
    p_c, p_e = probabilites(gain, tau, omega, rng.standard_normal((n_sim, E)), z_s,
                            rng.standard_normal((n_sim, E)), decalage)
    b_s = np.zeros((n_sim, S)); c_s = np.zeros((n_sim, S)); n_s = np.zeros(S)
    det_e = np.zeros((n_sim, E), bool); det_c = np.zeros((n_sim, E), bool)
    for k, n in enumerate(ep.n.to_numpy()):
        def tirer(taille):                                  # (U, V) : V = U avec la probabilité KAPPA
            u = rng.random((n_sim, taille))
            v = np.where(rng.random((n_sim, taille)) < KAPPA, u, rng.random((n_sim, taille)))
            return u, v
        (uc, vc), (up, vp) = tirer(1), tirer(n)
        commun = rng.random((n_sim, n)) < r
        u, v = np.where(commun, uc, up), np.where(commun, vc, vp)
        ctl, ens = u < p_c[:, k:k + 1], v < p_e[:, k:k + 1]   # quatre issues appariées par unité
        b_s[:, si[k]] += (ens & ~ctl).sum(1); c_s[:, si[k]] += (ctl & ~ens).sum(1); n_s[si[k]] += n
        det_e[:, k] = ens.any(1); det_c[:, k] = ctl.any(1)
    # A : permutation des signes par saison (exacte, 2^S combinaisons)
    x = (b_s - c_s) / np.sqrt(n_s)
    t_obs = x.sum(1)
    t_perm = x @ signes.T                                       # n_sim x 2^S
    p_a = (t_perm >= t_obs[:, None] - 1e-12).mean(1)
    # B : McNemar par épisode (détecté par une méthode si au moins un district l'est)
    b, c = (det_e & ~det_c).sum(1), (det_c & ~det_e).sum(1)
    p_b = np.where(b + c > 0, binom.sf(b - 1, b + c, 0.5), 1.0)
    return float((p_a <= ALPHA).mean()), float((p_b <= ALPHA).mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", type=int, default=3000)
    ap.add_argument("--avec-lot-en-cours", action="store_true",
                    help="compter aussi les unités des mois en cours de téléchargement (projection)")
    ap.add_argument("--eligibilite", default=str(ROOT / "validation" / "r21_eligibilite.csv"))
    args = ap.parse_args()
    rng = np.random.default_rng(20261111)
    ep = structure(args.eligibilite, args.avec_lot_en_cours)
    S = ep.saison.nunique()
    signes = np.array(list(itertools.product((1, -1), repeat=S)), float)
    L = ["# R-21 — Analyse de puissance du critère H1 (inférence par saisons)", "",
         f"Calcul du {dt.date.today():%d/%m/%Y} par [`scripts/r21_puissance.py`](../scripts/r21_puissance.py), "
         f"{args.sim} simulations par case, graine fixe. Structure réelle tirée de "
         f"[`r21_eligibilite.csv`](r21_eligibilite.csv) : **{int(ep.n.sum())} unités épisode × district, "
         f"{len(ep)} épisodes, {S} saisons**. Détection du contrôle par unité : {P_C} en moyenne (écart type {SIGMA_C} "
         f"entre épisodes) ; corrélation des méthodes par unité : {KAPPA}. Gain moyen recalé exactement. "
         "Test A (principal) : permutation exacte des signes par saison. Test B : McNemar exact par épisode. "
         "Unilatéraux, α = 0,05. τ : écart type du gain entre saisons ; ω = 0,10 entre épisodes ; r : part des "
         "districts d'un épisode qui partagent le même résultat.", ""]
    for gain in (0.0, 0.20, 0.30):
        titre = "Erreur de type I (gain nul)" if gain == 0 else f"Gain de {gain * 100:.0f} points"
        L += [f"## {titre}", "", "| τ | r | Test A (saisons) | Test B (épisodes) |", "|---:|---:|---:|---:|"]
        for tau, r in itertools.product((0.0, 0.10, 0.20), (0.3, 0.6, 0.9)):
            a, b = simuler(ep, gain, tau, 0.10, r, args.sim, rng, signes)
            L.append(f"| {tau:.2f} | {r:.1f} | {100 * a:.0f} % | {100 * b:.0f} % |".replace(".", ","))
        L.append("")
    sortie = ROOT / "validation" / ("r21_puissance_projection.md" if args.avec_lot_en_cours else "r21_puissance.md")
    sortie.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Écrit : {sortie}")


if __name__ == "__main__":
    main()
