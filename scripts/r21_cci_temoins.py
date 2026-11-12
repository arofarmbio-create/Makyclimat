"""R-21 : CCI des différences de détection estimée sur jours témoins, avant tout score (fiche de méthode, section 5).

Analyse de sensibilité : aucune unité d'impact n'est lue. Les fiches DesInventar ne sont lues que sur quatre colonnes
(type, date, district, date douteuse ; aucune colonne de dommages) et ne servent qu'à (1) désigner les
jours-districts témoins (aucune fiche de cyclone ou d'inondation dans le mois, filtre de dommages non appliqué) et
(2) reprendre les groupes de districts des épisodes éligibles (validation/r21_eligibilite.csv, colonnes episode et
adm2 seulement). Aucune détection d'épisode réel n'est calculée.

Chaîne (fiche, sections 2, 4 et 5) :
- seuils : blocs mensuels de décembre à mars, maximum du contrôle (membre cf) par maille sur la fenêtre 1-3 j, Gumbel
  des moments sans la saison testée, au moins 30 blocs, période de retour mensuelle T_m = 1 / (1 - 0,5^(1/4)) ;
  mailles retenues si le seuil vaut au moins 5 m3/s (seuil de stockage de la release, q_keep) ;
- alerte d'un district à une initialisation : contrôle si une maille dépasse ; ensemble si la part des 11 membres
  ayant au moins une maille en dépassement atteint le seuil de probabilité pi ; un jour d est en alerte si une
  initialisation de 1 à 3 jours avant alerte ;
- charge : épisodes d'alerte pour 100 jours-districts témoins ; un épisode se termine après 3 jours sans alerte
  (fiche, section 4), donc deux alertes distantes de plus de 3 jours ouvrent deux épisodes ;
  pour chaque pli (saison testée s), seuils sans s, charge cible = contrôle sur les autres saisons, pi (pas de 0,02)
  le plus proche, écart toléré de 20 % ;
- CCI : jours-groupes = (jour témoin de la saison testée, districts témoins avec maille de rivière d'un groupe
  d'épisode réel), au moins 2 districts et au moins une alerte de l'une des méthodes ; D = alerte ensemble - alerte
  contrôle ; CCI par ANOVA à un facteur (effectifs inégaux) ; intervalle à 95 % par bootstrap des saisons ;
- puissance : repères lus sur la grille simulée (validation/r21_puissance.md, population finale, gain de 30 points)
  pour la borne haute et la borne haute + 0,10, par interpolation linéaire entre scénarios d'un même τ ; une valeur
  hors de la grille n'a pas de puissance directement évaluée.

Sorties : validation/r21_cci_temoins.md et validation/r21_cci_temoins.csv (un pli par ligne).
Usage : python scripts/r21_cci_temoins.py --country mdg [--n-boot 2000]
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from common import country_data_dir, locate_points, read_units
from r21_eligibilite import EXCLUES, SAISONS, fiches
from validate_reforecast_impact import EULER, season_of

ROOT = Path(__file__).resolve().parent.parent
MOIS = (12, 1, 2, 3)
T_M = 1 / (1 - 0.5 ** 0.25)
N_BLOCS = 30
Q_MIN = 5.0
PIS = np.round(np.arange(0.02, 1.0001, 0.02), 2)
TOLERANCE = 0.20
FIN_EPISODE = 3                       # 3 jours sans alerte closent un épisode : nouvel épisode si écart > 3 jours
CCI_SEUIL = 0.46                      # seuil de puissance de 80 % (fiche, section 5)
# Grille simulée, population finale (425 unités, 22 épisodes, 12 saisons), gain de 30 points, test A :
# (τ, CCI des différences, puissance %), reprise de validation/r21_puissance.md (calcul du 11/11/2026).
GRILLE = ((0.0, 0.12, 99.8), (0.0, 0.26, 95.5), (0.0, 0.37, 89.1), (0.0, 0.49, 83.2), (0.0, 0.80, 70.6),
          (0.1, 0.14, 99.2), (0.1, 0.28, 93.5), (0.1, 0.38, 88.3), (0.1, 0.50, 82.2), (0.1, 0.81, 68.4),
          (0.2, 0.19, 96.4), (0.2, 0.33, 88.7), (0.2, 0.42, 83.2), (0.2, 0.54, 78.0), (0.2, 0.82, 65.5))


def lire(dossier):
    """Mailles (union), et pour chaque mois : (année, mois, inits, index des mailles, q[init, membre, maille] fenêtre 1-3 j)."""
    cles, mois = {}, []
    for f in sorted(dossier.glob("glofas_v4_*.npz")):
        y, m = map(int, re.search(r"(\d{4})_(\d{2})", f.name).groups())
        z = np.load(f)
        assert tuple(z["windows"][0]) == (1, 3) and z["members"][0] == "cf"
        idx = np.array([cles.setdefault((round(float(a), 3), round(float(b), 3)), len(cles))
                        for a, b in zip(z["lat"], z["lon"])])
        inits = [dt.date.fromisoformat(str(t)) for t in z["init"]]
        mois.append((y, m, inits, idx, z["q"][:, :, 0, :].astype("float32")))
    return cles, mois


def seuils(mois, n_mailles, saisons):
    """Seuil par saison testée et par maille (NaN si moins de N_BLOCS blocs ou sous Q_MIN)."""
    blocs, saison_bloc = [], []
    for y, m, inits, idx, q in mois:
        if m in MOIS:
            b = np.full(n_mailles, np.nan, dtype="float32")
            b[idx] = q[:, 0, :].max(axis=0)
            blocs.append(b)
            saison_bloc.append(season_of(dt.date(y, m, 1)))
    B, sb = np.array(blocs), np.array(saison_bloc)
    S = {}
    for s in saisons:
        X = B[sb != s]
        n = np.isfinite(X).sum(0)
        with np.errstate(invalid="ignore"):
            mu, sd = np.nanmean(X, 0), np.nanstd(X, 0, ddof=1)
        beta = sd * math.sqrt(6) / math.pi
        q = mu - EULER * beta - beta * math.log(-math.log(1 - 1 / T_M))
        q[(n < N_BLOCS) | ~(q >= Q_MIN)] = np.nan
        S[s] = q
    return S, len(B)


def alertes(mois, thr, A, jours):
    """Par jour (index de `jours`) et district : alerte du contrôle et probabilité d'ensemble maximale (1-3 j)."""
    pos = {d: i for i, d in enumerate(jours)}
    ctrl = np.zeros((len(jours), A.shape[1]), bool)
    pmax = np.zeros((len(jours), A.shape[1]), "float32")
    for y, m, inits, idx, q in mois:
        th = thr[idx]
        ok = np.isfinite(th)
        Ai = A[idx[ok]]
        for i, t in enumerate(inits):
            hit = (q[i][:, ok] >= th[ok]).astype("float32")              # membres x mailles retenues
            par_d = (sparse.csr_matrix(hit) @ Ai).toarray() > 0          # membres x districts
            c, p = par_d[0], par_d.mean(0)
            for k in (1, 2, 3):
                j = pos.get(t + dt.timedelta(days=k))
                if j is not None:
                    ctrl[j] |= c
                    np.maximum(pmax[j], p, out=pmax[j])
    return ctrl, pmax


def charge(flag, temoin, jours):
    """Épisodes d'alerte pour 100 jours-districts témoins (flag, temoin : jours x districts)."""
    n_ep = 0
    num = np.array([d.toordinal() for d in jours])
    for k in range(flag.shape[1]):
        a = num[flag[:, k] & temoin[:, k]]
        if len(a):
            n_ep += 1 + int((np.diff(a) > FIN_EPISODE).sum())
    n = temoin.sum()
    return 100 * n_ep / n if n else np.nan


def repere_puissance(cci):
    """Repère de puissance pour une CCI, par τ : interpolation linéaire entre les deux scénarios simulés qui
    l'encadrent ; hors de la grille, aucune puissance n'est évaluée et le scénario le plus proche est cité."""
    morceaux = []
    for tau in sorted({t for t, _, _ in GRILLE}):
        pts = sorted((c, p) for t, c, p in GRILLE if t == tau)
        if cci < pts[0][0]:
            morceaux.append(f"τ = {fr(tau, 1)} : hors grille, sous la plus petite CCI simulée "
                            f"({fr(pts[0][0], 2)} : {fr(pts[0][1], 1)} %)")
        elif cci > pts[-1][0]:
            morceaux.append(f"τ = {fr(tau, 1)} : hors grille, au-dessus de la plus grande CCI simulée")
        else:
            (c0, p0), (c1, p1) = next((a, b) for a, b in zip(pts, pts[1:]) if a[0] <= cci <= b[0])
            morceaux.append(f"τ = {fr(tau, 1)} : {fr(p0 + (p1 - p0) * (cci - c0) / (c1 - c0), 1)} % "
                            f"(entre {fr(c0, 2)} et {fr(c1, 2)})")
    return " ; ".join(morceaux)


def fr(x, nd=3):
    return f"{x:.{nd}f}".replace(".", ",")


def cci_anova(groupes):
    """CCI (ANOVA à un facteur, effectifs inégaux) d'une liste de vecteurs de différences."""
    n = np.array([len(g) for g in groupes], float)
    N, K = n.sum(), len(n)
    if K < 2 or N <= K:
        return np.nan
    som = np.array([g.sum() for g in groupes], float)
    car = sum(float((g ** 2).sum()) for g in groupes)
    tot = som.sum() / N
    msb = ((som / n - tot) ** 2 * n).sum() / (K - 1)
    msw = (car - (som ** 2 / n).sum()) / (N - K)
    n0 = (N - (n ** 2).sum() / N) / (K - 1)
    den = msb + (n0 - 1) * msw
    return float((msb - msw) / den) if den > 0 else np.nan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--graine", type=int, default=20261111)
    args = ap.parse_args()
    dossier = country_data_dir(args.country) / "reforecast"
    cles, mois = lire(dossier)
    publies = {(y, m) for y, m, *_ in mois}

    # Districts des mailles
    lat = np.array([k[0] for k in cles]); lon = np.array([k[1] for k in cles])
    units = read_units(args.country).set_index("pcode")
    dist = np.array([units.at[c, "adm2"] if c else "" for c in locate_points(args.country, lon, lat)])
    districts = sorted(set(dist) - {""})
    di = {d: i for i, d in enumerate(districts)}
    lignes = [i for i, d in enumerate(dist) if d]
    A = sparse.csr_matrix((np.ones(len(lignes), "float32"), (lignes, [di[dist[i]] for i in lignes])),
                          shape=(len(dist), len(districts)))

    # Jours témoins : mois publiés de décembre à mars, saisons 2003-2018 hors 2017 et hors janvier-mars 2019
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
    temoin_base = np.array([[d not in touches[ym] for d in districts] for ym in mois_j])
    saisons = sorted(set(saison_j))

    # Groupes de districts des épisodes éligibles (aucune détection lue)
    el = pd.read_csv(ROOT / "validation" / "r21_eligibilite.csv", dtype={"adm2": str})
    el = el[el.eligible == 1]
    groupes = [np.array([di[a] for a in g.adm2 if a in di]) for _, g in el.groupby("episode")]

    S, n_blocs = seuils(mois, len(cles), saisons)
    plis, cellules = [], []          # cellules : (saison, D) des jours-groupes retenus
    for s in saisons:
        ctrl, pmax = alertes(mois, S[s], A, jours)
        riviere = np.asarray(A[np.isfinite(S[s])].sum(0)).ravel() > 0
        tem = temoin_base & riviere
        app = saison_j != s
        cible = charge(ctrl[app], tem[app], [d for d, a in zip(jours, app) if a])
        jours_app = [d for d, a in zip(jours, app) if a]
        ch = np.array([charge(pmax[app] >= pi - 1e-6, tem[app], jours_app) for pi in PIS])
        k = int(np.nanargmin(np.abs(ch - cible)))
        pi, ecart = PIS[k], ch[k] / cible - 1
        test = saison_j == s
        jt = [d for d, a in zip(jours, test) if a]
        ens_t, ctrl_t, tem_t = pmax[test] >= pi - 1e-6, ctrl[test], tem[test]
        n_jg = 0
        for j in range(len(jt)):
            for g in groupes:
                u = g[tem_t[j, g]]
                if len(u) >= 2 and (ens_t[j, u] | ctrl_t[j, u]).any():
                    cellules.append((s, ens_t[j, u].astype(float) - ctrl_t[j, u].astype(float)))
                    n_jg += 1
        plis.append({"saison": s, "pi": pi, "charge_cible": round(cible, 3), "charge_ensemble_app": round(ch[k], 3),
                     "ecart": round(ecart, 3), "hors_tolerance": int(abs(ecart) > TOLERANCE),
                     "charge_controle_test": round(charge(ctrl_t, tem_t, jt), 3),
                     "charge_ensemble_test": round(charge(ens_t, tem_t, jt), 3),
                     "jours_districts_temoins_test": int(tem_t.sum()), "jours_groupes": n_jg})
        print(f"saison {s} : pi={pi} écart {ecart:+.0%} ; {n_jg} jours-groupes", flush=True)

    P = pd.DataFrame(plis)
    P.to_csv(ROOT / "validation" / "r21_cci_temoins.csv", index=False, encoding="utf-8")
    sc = np.array([c[0] for c in cellules])
    D = [c[1] for c in cellules]
    est = cci_anova(D)
    rng = np.random.default_rng(args.graine)
    par_s = {s: [d for d, x in zip(D, sc) if x == s] for s in saisons}
    boot = np.array([cci_anova([d for s in rng.choice(saisons, len(saisons)) for d in par_s[s]])
                     for _ in range(args.n_boot)])
    lo, hi = np.nanpercentile(boot, [2.5, 97.5])
    tailles = np.array([len(d) for d in D])
    non_nuls = np.array([(d != 0).mean() for d in D])
    sortie = ROOT / "validation" / "r21_cci_temoins.md"
    L = ["# R-21 — CCI des différences estimée sur jours témoins (analyse de sensibilité, avant scores)", "",
         f"Calcul du {dt.date.today():%d/%m/%Y} par [`scripts/r21_cci_temoins.py`](../scripts/r21_cci_temoins.py), "
         f"{len(mois)} mois GloFAS v4, {n_blocs} blocs mensuels décembre-mars, {len(groupes)} groupes de districts "
         "d'épisodes éligibles. Méthode : [fiche, section 5](r21_fiche_methode.md). **Aucune unité d'impact n'est "
         "lue** (DesInventar lu sur quatre colonnes : type, date, district, date douteuse) **; le verrou des scores est "
         "maintenu.** Détail par pli : [`r21_cci_temoins.csv`](r21_cci_temoins.csv).", "",
         "## Résultat", "",
         f"- **CCI des différences : {fr(est)}**, intervalle à 95 % par bootstrap des saisons "
         f"({args.n_boot} tirages) : **{fr(lo)} à {fr(hi)}** ; borne haute + 0,10 : {fr(hi + 0.10)}.",
         f"- Seuil de 80 % de puissance (population finale, 30 points) : CCI ≤ {fr(CCI_SEUIL, 2)}. "
         f"Borne haute {'sous' if hi <= CCI_SEUIL else 'au-dessus de'} ce seuil ; borne haute + 0,10 "
         f"{'sous' if hi + 0.10 <= CCI_SEUIL else 'au-dessus de'} ce seuil.",
         f"- Puissance du test A ([grille simulée](r21_puissance.md), population finale, gain de 30 points), "
         f"interpolation linéaire entre scénarios d'un même τ ; une valeur hors de la grille n'a pas de puissance "
         f"directement évaluée et seul le scénario simulé le plus proche est cité :",
         f"  - borne haute {fr(hi)} : {repere_puissance(hi)} ;",
         f"  - borne haute + 0,10 = {fr(hi + 0.10)} : {repere_puissance(hi + 0.10)}.",
         f"- Jours-groupes retenus : {len(D)} (taille médiane {np.median(tailles):.0f} districts, de "
         f"{tailles.min()} à {tailles.max()}) ; part médiane de districts où les méthodes diffèrent : "
         f"{np.median(non_nuls):.0%}, part moyenne {non_nuls.mean():.1%} (toutes unités : "
         f"{(np.concatenate(D) != 0).mean():.1%}). Les discordances sont rares sur témoins ; la simulation de "
         "puissance suppose un gain de 30 points sur les épisodes, donc bien plus de discordances.",
         f"- Plis hors tolérance de charge (± {TOLERANCE:.0%}) : {int(P.hors_tolerance.sum())} sur {len(P)}.", "",
         "**Réserves.** Transportabilité non démontrée (relecture Codex du 11/11, 14:37) : la CCI des jours témoins "
         "peut différer de celle des épisodes d'impact. Les jours-groupes consécutifs se recouvrent (mêmes "
         "initialisations, groupes qui partagent des districts) : l'estimation ponctuelle les pondère tous. Le bootstrap "
         "rééchantillonne des saisons entières : il préserve les dépendances au sein de chaque saison et suppose les "
         "saisons indépendantes entre elles. H1 reste exploratoire par défaut ; le "
         "porteur décide du statut avant les scores.", "",
         "## Plis (saison testée)", "",
         "| Saison | pi | Charge cible | Charge ensemble (app.) | Écart | Contrôle (test) | Ensemble (test) | "
         "Jours-districts témoins | Jours-groupes |", "|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    L += [f"| {r.saison} | {r.pi:.2f} | {r.charge_cible} | {r.charge_ensemble_app} | {r.ecart:+.0%}"
          f"{' ⚠' if r.hors_tolerance else ''} | {r.charge_controle_test} | {r.charge_ensemble_test} | "
          f"{r.jours_districts_temoins_test} | {r.jours_groupes} |" for r in P.itertuples()]
    L += ["", "Charges : épisodes d'alerte pour 100 jours-districts témoins (district avec maille de rivière)."]
    sortie.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"CCI {est:.3f} [{lo:.3f} ; {hi:.3f}] ; écrit : {sortie}")


if __name__ == "__main__":
    main()
