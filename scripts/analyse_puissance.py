"""Analyse de puissance des tests de la recharge (09/11/2026) : combien d'unités indépendantes faudrait-il pour qu'un
effet plausible soit détecté ? Ne teste aucune hypothèse ; s'appuie sur des résultats déjà publiés :
- dispersion des résidus ln(mesurée / T2) des sites de fluctuation (`validation/recharge_locale_sites.csv`) ;
- largeur de l'intervalle de la différence d'AUC (`validation/puits_a_sec.md`) ;
- nombre de blocs du bilan de chlorure (`validation/recharge_chlorure_blocs.md`).
Quatre familles de tests : (1) correction locale par classe d'aquifère (simulation) ; (2) différence d'AUC entre deux
cartes ; (3) corrélation de Spearman entre blocs ; (4) test prospectif « au moins 60 % des sites retrouvés ».
Sortie : validation/analyse_puissance.md. Usage : python scripts/analyse_puissance.py
"""
from __future__ import annotations

import datetime as dt
import re

import numpy as np
import pandas as pd
from scipy import stats

from common import ROOT

SEED, NSIM, ALPHA, PUISS = 20261109, 4000, 0.05, 0.80
Z_A, Z_B = stats.norm.ppf(1 - ALPHA / 2), stats.norm.ppf(PUISS)


def sim_correction(n_groupes: int, mu: float, sd_b: float, demi_largeur: float, rng, nsim=NSIM) -> float:
    """Puissance d'une règle de type H-L1 pour une classe : avec n groupes de sites indépendants, chaque groupe est prédit
    par la médiane des autres (validation en laissant un groupe de côté). Réussite si au moins la moitié des groupes sont
    retrouvés (|prédit − vrai| ≤ demi-largeur de l'intervalle de mesure, en log10) ET si l'erreur médiane est au plus la
    moitié de celle de T2 (|résidu|)."""
    ok = 0
    for _ in range(nsim):
        r = rng.normal(mu, sd_b, n_groupes)
        pred = np.array([np.median(np.delete(r, i)) for i in range(n_groupes)])
        err = np.abs(pred - r)
        if np.mean(err <= demi_largeur) >= 0.5 and np.median(err) <= 0.5 * np.median(np.abs(r)):
            ok += 1
    return ok / nsim


def n_auc(se_ref: float, n_ref: int, delta: float) -> float:
    """Blocs nécessaires pour détecter une différence d'AUC delta (erreur type ∝ 1/√n)."""
    return n_ref * (se_ref * (Z_A + Z_B) / delta) ** 2


def puissance_auc(se_ref: float, n_ref: int, n: int, delta: float) -> float:
    se = se_ref * np.sqrt(n_ref / n)
    return float(stats.norm.cdf(delta / se - Z_A))


def n_spearman(rho: float) -> float:
    return ((Z_A + Z_B) / np.arctanh(rho)) ** 2 + 3


def puissance_spearman(rho: float, n: int) -> float:
    return float(stats.norm.cdf(np.arctanh(rho) * np.sqrt(n - 3) - Z_A))


def n_prospectif(p_vrai: float, seuil: float = 0.6, puiss: float = PUISS) -> int:
    """Plus petit nombre de sites tel que, si la vraie proportion retrouvée est p_vrai, la borne basse de l'intervalle
    de Wilson à 95 % dépasse le seuil avec la probabilité voulue."""
    for n in range(5, 2001):
        k = np.arange(n + 1)
        z = Z_A
        ph = k / n
        bas = (ph + z * z / (2 * n) - z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))) / (1 + z * z / n)
        if stats.binom.pmf(k, n, p_vrai)[bas > seuil].sum() >= puiss:
            return n
    return -1


def main() -> None:
    rng = np.random.default_rng(SEED)
    s = pd.read_csv(ROOT / "validation" / "recharge_locale_sites.csv")
    s["res"] = np.log10(s.mes / s.t2_mm)
    s["demi"] = np.log10(s.r_haut / s.r_bas) / 2
    soc = s[s.groupe == "Basement"]
    # un résidu par groupe de validation (sites voisins = une seule information)
    g = soc.groupby("groupe_validation").res.median()
    mu, sd_b, demi = float(g.median()), float(g.std(ddof=1)), float(s.demi.median())

    txt = (ROOT / "validation" / "puits_a_sec.md").read_text(encoding="utf-8")
    m = re.search(r"\| T2L − T2 \| ([+-][\d.]+) \| ([+-]?[\d.]+) à ([+-][\d.]+) \|", txt)
    d_obs, lo, hi = float(m.group(1)), float(m.group(2)), float(m.group(3))
    se_auc = (hi - lo) / (2 * 1.96)
    n_blocs = int(re.search(r"\((\d+) blocs de 20 km\)", txt).group(1))
    nb_cl = int(re.search(r"(\d+) zones, \d+ forages", (ROOT / "validation" / "recharge_chlorure_blocs.md").read_text(encoding="utf-8")).group(1))

    L = ["# Analyse de puissance des tests de la recharge", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/analyse_puissance.py`. **Aucune hypothèse n'est testée ici** : on "
         "estime combien d'unités indépendantes il faudrait pour détecter un effet plausible, à partir de résultats déjà publiés. "
         f"Seuil 5 % bilatéral, puissance visée 80 %, {NSIM} simulations par cas (graine {SEED}).", "",
         "## 1. Correction locale par classe d'aquifère (type H-L1)", "",
         f"Paramètres tirés des sites du socle, un résidu par groupe de sites indépendants ({len(g)} groupes) : résidu médian "
         f"log₁₀(mesurée / T2) = {mu:+.2f} (T2 trop forte d'un facteur {10 ** -mu:.1f}), dispersion entre groupes {sd_b:.2f}, "
         f"demi-largeur médiane de l'intervalle de mesure (rendement spécifique) {demi:.2f}.", "",
         "| Groupes indépendants par classe | Puissance de la règle (dispersion observée) | Si la dispersion était moitié moindre |", "|---|---|---|"]
    res1 = {}
    for n in (3, 4, 6, 8, 10, 15, 20, 30):
        p1, p2 = sim_correction(n, mu, sd_b, demi, rng), sim_correction(n, mu, sd_b / 2, demi, rng)
        res1[n] = p1
        L.append(f"| {n} | {p1:.0%} | {p2:.0%} |")
    n80 = next((n for n, p in res1.items() if p >= PUISS), None)
    L += ["", f"Lecture : avec {len(g)} groupes dans le socle aujourd'hui, la règle réussit rarement même si la correction est juste. "
          + (f"Il faut environ **{n80} groupes indépendants par classe** pour 80 % de puissance." if n80 else
             "Même 30 groupes ne suffisent pas avec la dispersion observée : la règle « moitié des sites retrouvés » est trop exigeante "
             "tant que la dispersion entre sites dépasse la largeur de l'intervalle de mesure ; il faut réduire l'incertitude des mesures "
             "(rendement spécifique) ou expliquer la dispersion (géologie plus fine)."), "",
          "## 2. Différence d'AUC entre deux cartes (puits à sec)", "",
          f"Observé : T2L − T2 = {d_obs:+.3f}, intervalle {lo:+.3f} à {hi:+.3f} avec {n_blocs} blocs, soit une erreur type de {se_auc:.3f}.", "",
          "| Différence à détecter | Puissance avec les blocs actuels | Blocs nécessaires (80 %) |", "|---|---|---|"]
    for dl in (0.05, 0.08, round(d_obs, 2)):
        L.append(f"| {dl:.2f} | {puissance_auc(se_auc, n_blocs, n_blocs, dl):.0%} | {n_auc(se_auc, n_blocs, dl):.0f} |")
    L += ["", "Lecture : le gain observé (+0,11) avait environ une chance sur deux d'être déclaré ; une différence de 0,05 (seuil du "
          "protocole) demande plusieurs fois plus de blocs que le Grand Sud n'en compte. Le test des puits à sec ne peut départager les "
          "cartes que si l'effet est grand, ou en étendant la zone.", "",
          "## 3. Corrélation de Spearman entre blocs (bilan de chlorure)", "",
          f"Blocs disponibles : {nb_cl}.", "", "| ρ à détecter | Puissance avec les blocs actuels | Blocs nécessaires (80 %) |", "|---|---|---|"]
    for rho in (0.2, 0.3, 0.4, 0.5):
        L.append(f"| {rho:.1f} | {puissance_spearman(rho, nb_cl):.0%} | {n_spearman(rho):.0f} |")
    L += ["", "Lecture : avec 36 blocs, seule une corrélation forte (au moins 0,45) est détectable de façon fiable ; la règle H-Cl1 "
          "(ρ ≥ 0,3 dans les trois scénarios) était presque impossible à remplir.", "",
          "## 4. Test prospectif des cartes figées (« au moins 60 % des nouveaux sites retrouvés »)", "",
          "| Vraie part de sites retrouvés | Nouveaux sites indépendants nécessaires pour que la borne basse dépasse 60 % (80 %) |", "|---|---|"]
    for p in (0.70, 0.75, 0.80, 0.90):
        L.append(f"| {p:.0%} | {n_prospectif(p)} |")
    L += ["", "Lecture : pour qu'un test prospectif soit concluant, il faut des dizaines de sites indépendants, sauf si la carte est "
          "très bonne. Les règles actuelles (« au moins 60 % ») sont donc trop faibles en petit nombre : à remplacer par la borne basse "
          "d'un intervalle, comme ci-dessus.", "",
          "## Conséquences", "",
          "1. **Nos « non soutenus de peu » sont surtout des manques de puissance** (sections 2 et 3) : ils ne réfutent pas les idées.",
          "2. **La correction locale bute d'abord sur la dispersion entre sites** (section 1) : plus de sites ne suffit pas, il faut "
          "aussi réduire l'incertitude de mesure (essais de pompage pour le rendement spécifique) et classer les roches plus finement.",
          "3. **Plan de mesures** : viser par classe d'aquifère le nombre de groupes indépendants de la section 1, et pour un test "
          "prospectif le nombre de sites de la section 4.",
          "4. **Règle de méthode** (à appliquer aux prochains protocoles) : calculer la puissance avant de fixer une hypothèse ; si elle "
          "est inférieure à 50 %, le test est déclaré exploratoire dès le départ.", ""]
    (ROOT / "validation" / "analyse_puissance.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"mu {mu:+.2f} sd {sd_b:.2f} demi {demi:.2f} ; n80 correction {n80} ; se_auc {se_auc:.3f}")


if __name__ == "__main__":
    main()
