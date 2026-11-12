"""R-21 : scores de H1, exploratoire (décision du porteur du projet du 12/11/2026), selon la fiche de méthode figée
(validation/r21_fiche_methode.md, sections 2 à 5, relue sans blocage par Codex le 11/11 à 18:49).

H1 : à charge d'alerte comparable, l'ensemble GloFAS v4 détecte plus de districts touchés, 1 à 3 jours avant, que le
membre de contrôle. Chaîne, sans aucun paramètre nouveau (fonctions reprises de scripts/r21_cci_temoins.py) :
- unités : épisode × district éligibles (validation/r21_eligibilite.csv, 425 unités, 22 épisodes, 12 saisons) ; dates
  de l'unité = dates de ses fiches (fiches et épisodes recalculés par scripts/r21_eligibilite.py, contrôle d'égalité) ;
- pli = saison testée s : seuils de Gumbel sans s (section 2) ; seuil de probabilité pi de l'ensemble choisi sur les
  jours-districts témoins des autres saisons pour égaler la charge du contrôle (section 4, pas de 0,02, ± 20 %) ;
- détection : une méthode détecte une unité si l'un de ses jours de fiche est en alerte (initialisation 1 à 3 jours
  avant ; contrôle : une maille du district dépasse ; ensemble : part des membres ≥ pi) ;
- test A (section 5) : T = Σ_s (b_s − c_s) / √n_s, permutation exacte des signes par saison (2^S), unilatéral,
  α = 0,05 ; b_s, c_s = unités détectées par l'ensemble seul, par le contrôle seul ; n_s = unités de la saison ;
- après les scores (section 5, point 3) : CCI des différences observée sur les épisodes (ANOVA), puissance lue sur la
  grille ; elle ne change pas le statut, fixé avant les scores (exploratoire).
Un district sans maille de rivière retenue ne peut être détecté par aucune méthode : il reste dans la population
figée et compte comme non détecté par les deux.

Sorties : validation/r21_scores.md, validation/r21_scores_plis.csv, validation/r21_scores_unites.csv.
Usage : python scripts/r21_scores.py --country mdg
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from common import country_data_dir, locate_points, read_units
from r21_cci_temoins import (MOIS, PIS, TOLERANCE, alertes, cci_anova, charge, fr, lire, repere_puissance, seuils)
from r21_eligibilite import EXCLUES, SAISONS, episodes, fiches
from r21_puissance import P_C
from validate_reforecast_impact import season_of

ROOT = Path(__file__).resolve().parent.parent
ALPHA = 0.05


def test_a(b, c, n):
    """Statistique T et valeur p unilatérale de la permutation exacte des signes par saison."""
    x = (np.asarray(b, float) - np.asarray(c, float)) / np.sqrt(np.asarray(n, float))
    t = float(x.sum())
    signes = np.array(list(itertools.product((1, -1), repeat=len(x))))
    perm = signes @ x
    return t, float((perm >= t - 1e-12).mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cles, mois = lire(country_data_dir(args.country) / "reforecast")
    publies = {(y, m) for y, m, *_ in mois}

    lat = np.array([k[0] for k in cles]); lon = np.array([k[1] for k in cles])
    units = read_units(args.country).set_index("pcode")
    dist = np.array([units.at[c, "adm2"] if c else "" for c in locate_points(args.country, lon, lat)])
    districts = sorted(set(dist) - {""})
    di = {d: i for i, d in enumerate(districts)}
    lignes = [i for i, d in enumerate(dist) if d]
    A = sparse.csr_matrix((np.ones(len(lignes), "float32"), (lignes, [di[dist[i]] for i in lignes])),
                          shape=(len(dist), len(districts)))

    # Jours et témoins : exactement comme l'estimation de la CCI sur témoins (scripts/r21_cci_temoins.py)
    tous = fiches(args.country, filtre_dommages=False)
    touches = {(y, m): set(tous[[d.year == y and d.month == m for d in tous.d]].adm2) for y, m in publies}
    jours, saison_j, mois_j = [], [], []
    for (y, m) in sorted(publies):
        s = season_of(dt.date(y, m, 1))
        if m not in MOIS or not SAISONS[0] <= s <= SAISONS[1] or s in EXCLUES or (y == 2019 and m <= 3):
            continue
        for j in range(1, calendar.monthrange(y, m)[1] + 1):
            jours.append(dt.date(y, m, j)); saison_j.append(s); mois_j.append((y, m))
    saison_j = np.array(saison_j)
    pos = {d: i for i, d in enumerate(jours)}
    temoin_base = np.array([[d not in touches[ym] for d in districts] for ym in mois_j])
    saisons = sorted(set(saison_j))

    # Unités éligibles et leurs dates de fiche
    el = pd.read_csv(ROOT / "validation" / "r21_eligibilite.csv", dtype={"adm2": str})
    el = el[el.eligible == 1]
    f = episodes(fiches(args.country))
    groupes_f = dict(list(f.groupby(["episode", "adm2"])))
    dates = {k: sorted(set(g.d)) for k, g in groupes_f.items()}
    controle = [(len(groupes_f[(r.episode, r.adm2)]) if (r.episode, r.adm2) in groupes_f else -1, r.fiches)
                for r in el.itertuples()]                     # « fiches » = lignes de fiche, comme r21_eligibilite.py
    assert all(a == b for a, b in controle), "unités recalculées différentes de r21_eligibilite.csv"
    assert len(el) == 425 and el.episode.nunique() == 22 and el.saison.nunique() == 12, "population figée modifiée"

    S, n_blocs = seuils(mois, len(cles), saisons)
    plis, unites = [], []
    for s in sorted(el.saison.unique()):
        ctrl, pmax = alertes(mois, S[s], A, jours)
        riviere = np.asarray(A[np.isfinite(S[s])].sum(0)).ravel() > 0
        tem = temoin_base & riviere
        app = saison_j != s
        jours_app = [d for d, a in zip(jours, app) if a]
        cible = charge(ctrl[app], tem[app], jours_app)
        ch = np.array([charge(pmax[app] >= pi - 1e-6, tem[app], jours_app) for pi in PIS])
        k = int(np.nanargmin(np.abs(ch - cible)))
        pi, ecart = PIS[k], ch[k] / cible - 1
        test = saison_j == s
        jt = [d for d, a in zip(jours, test) if a]
        u_s = el[el.saison == s]
        for r in u_s.itertuples():
            j = [pos[d] for d in dates[(r.episode, r.adm2)] if d in pos]
            col = di.get(r.adm2)
            e = bool(col is not None and j and (pmax[j, col] >= pi - 1e-6).any())
            c = bool(col is not None and j and ctrl[j, col].any())
            unites.append({"episode": r.episode, "saison": s, "adm2": r.adm2, "jours": len(j),
                           "riviere": int(col is not None and bool(riviere[col])), "ensemble": int(e), "controle": int(c)})
        U = pd.DataFrame([u for u in unites if u["saison"] == s])
        plis.append({"saison": s, "unites": len(U), "episodes": U.episode.nunique(), "pi": pi,
                     "charge_cible": round(cible, 3), "charge_ensemble_app": round(ch[k], 3), "ecart": round(ecart, 3),
                     "hors_tolerance": int(abs(ecart) > TOLERANCE),
                     "charge_controle_test": round(charge(ctrl[test], tem[test], jt), 3),
                     "charge_ensemble_test": round(charge(pmax[test] >= pi - 1e-6, tem[test], jt), 3),
                     "det_ensemble": int(U.ensemble.sum()), "det_controle": int(U.controle.sum()),
                     "b_ensemble_seul": int(((U.ensemble == 1) & (U.controle == 0)).sum()),
                     "c_controle_seul": int(((U.ensemble == 0) & (U.controle == 1)).sum())})
        print(f"saison {s} : pi={pi} écart {ecart:+.0%} ; {len(U)} unités", flush=True)

    P, U = pd.DataFrame(plis), pd.DataFrame(unites)
    P.to_csv(ROOT / "validation" / "r21_scores_plis.csv", index=False, encoding="utf-8")
    U.to_csv(ROOT / "validation" / "r21_scores_unites.csv", index=False, encoding="utf-8")
    t, p = test_a(P.b_ensemble_seul, P.c_controle_seul, P.unites)
    n = len(U)
    pe, pc = U.ensemble.mean(), U.controle.mean()
    D = [g.ensemble.to_numpy(float) - g.controle.to_numpy(float) for _, g in U.groupby("episode")]
    cci = cci_anova(D)
    b, c = int(P.b_ensemble_seul.sum()), int(P.c_controle_seul.sum())
    sortie = ROOT / "validation" / "r21_scores.md"
    L = ["# R-21 — Scores de H1 (exploratoire)", "",
         f"Calcul du {dt.date.today():%d/%m/%Y} par [`scripts/r21_scores.py`](../scripts/r21_scores.py), méthode figée de la "
         "[fiche](r21_fiche_methode.md) (sections 2 à 5), sans paramètre nouveau. **Statut : exploratoire**, décidé par "
         "le porteur du projet le 12/11/2026 avant les scores ; il ne change pas au vu des résultats. Un résultat net "
         "appelle un test confirmatoire déclaré d'avance sur des données indépendantes (autres saisons ou pays). "
         f"{len(mois)} mois GloFAS v4, {n_blocs} blocs mensuels. Détail : [plis](r21_scores_plis.csv), "
         "[unités](r21_scores_unites.csv).", "",
         "## Résultat", "",
         f"- Population figée : {n} unités épisode × district, {U.episode.nunique()} épisodes, {len(P)} saisons ; "
         f"{int((U.riviere == 0).sum())} unités sans maille de rivière retenue (non détectables par les deux méthodes).",
         f"- Détection 1 à 3 jours avant : **ensemble {fr(100 * pe, 1)} %** ({int(U.ensemble.sum())}), **contrôle "
         f"{fr(100 * pc, 1)} %** ({int(U.controle.sum())}) ; écart {fr(100 * (pe - pc), 1)} points. Discordances : "
         f"ensemble seul {b}, contrôle seul {c}.",
         f"- **Test A** (permutation exacte des signes sur {len(P)} saisons, {2 ** len(P)} combinaisons, unilatéral) : "
         f"T = {fr(t, 2)}, **p = {fr(p, 4)}** ; au seuil de {fr(ALPHA, 2)} : "
         f"{'gain de l’ensemble indiqué (exploratoire)' if p <= ALPHA else 'pas de gain de l’ensemble mis en évidence'}.",
         f"- Plis hors tolérance de charge (± {100 * TOLERANCE:.0f} %) : {int(P.hors_tolerance.sum())} sur {len(P)}.",
         f"- CCI des différences observée sur les épisodes (section 5, point 3) : {fr(cci) if np.isfinite(cci) else 'non définie'}"
         + (f" ; puissance pour un gain de 30 points : {repere_puissance(cci)}." if np.isfinite(cci) else "."), "",
         f"**Lecture des hypothèses de puissance.** La simulation supposait une détection moyenne du contrôle de "
         f"{fr(100 * P_C, 0)} % et un gain de 30 points. Observé : contrôle {fr(100 * pc, 1)} %, et {b + c} unités "
         "discordantes seulement : l'information du test tient dans ces discordances. Les repères de puissance "
         "ci-dessus, conditionnels à ces hypothèses, surestiment donc la puissance réelle pour un gain plausible à ce "
         "niveau de détection ; l'absence de gain démontré n'est pas une preuve d'absence de gain. La détection est "
         f"nulle pour les deux méthodes dans {int((P.det_ensemble + P.det_controle == 0).sum())} saisons sur {len(P)}.", "",
         "**Réserves.** Statut exploratoire (transportabilité de la CCI des témoins non démontrée). Une absence de fiche "
         "n'est pas une absence d'impact : la charge est mesurée sur des jours sans impact confirmé. Échantillon enrichi "
         "en événements (décembre-mars des saisons à fiches) ; 22 épisodes seulement.", "",
         "## Plis (saison testée)", "",
         "| Saison | Unités | Épisodes | pi | Charge cible | Écart (app.) | Charge contrôle (test) | Charge ensemble (test) "
         "| Ensemble | Contrôle | Ensemble seul | Contrôle seul |", "|---:|" + "---:|" * 11]
    L += [f"| {r.saison} | {r.unites} | {r.episodes} | {fr(r.pi, 2)} | {fr(r.charge_cible, 2)} | {100 * r.ecart:+.0f} %"
          f"{' ⚠' if r.hors_tolerance else ''} | {fr(r.charge_controle_test, 2)} | {fr(r.charge_ensemble_test, 2)} | {r.det_ensemble} "
          f"| {r.det_controle} | {r.b_ensemble_seul} | {r.c_controle_seul} |" for r in P.itertuples()]
    L += ["", "Charges : épisodes d'alerte pour 100 jours-districts témoins (district avec maille de rivière)."]
    sortie.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"ensemble {pe:.3f} contrôle {pc:.3f} ; T={t:.3f} p={p:.4f} ; CCI {cci:.3f} ; écrit : {sortie}")


if __name__ == "__main__":
    main()
