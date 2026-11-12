"""R-21 bis, D1–D4, protocole version 6, section 12.

API en mémoire : aucun fichier réel n'est chargé à l'import ou à l'exécution.
Les mois ont le format de r21_scores.lire ; A associe mailles et districts
(ou bassins). Les unités portent episode, saison, territoire, dates.
Les appelants fournissent les unités éligibles et les jours témoins R-21.
Le branchement aux données et l'exécution scientifique restent à autoriser.
CHIRPS et les observations EMS ne sont jamais lus ici.
"""
from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd

from r21_scores import PIS, TOLERANCE, alertes, charge, seuils
from validate_reforecast_impact import season_of

KS = np.round(np.arange(0.50, 2.001, 0.05), 2)
CLASSES = list("abcden")
METHODES = ("controle", "ensemble", "reanalyse")


def etendre(dates, rayon):
    return sorted({d + dt.timedelta(days=k) for d in dates
                   for k in range(-rayon, rayon + 1)})


def fenetres_reanalyse(mois, dates, q):
    """Maxima t+1:t+3 aux seules initialisations R-21, sur la même grille.

    Chaque maille exige trois valeurs finies ; un jour absent invalide toute
    l'initialisation. Les NaN restent distincts d'un débit nul.
    """
    q = np.asarray(q, float)
    if q.ndim != 2 or len(dates) != len(q) or len(set(dates)) != len(dates):
        raise ValueError("Réanalyse : dates uniques et tableau jour × maille requis")
    pos = {d: i for i, d in enumerate(dates)}
    resultat = []
    for y, m, inits, idx, _ in mois:
        v = np.full((len(inits), 1, len(idx)), np.nan)
        for i, t in enumerate(inits):
            jj = [pos.get(t + dt.timedelta(days=k)) for k in (1, 2, 3)]
            if all(j is not None for j in jj):
                v[i, 0] = q[np.ix_(jj, idx)].max(axis=0)
        resultat.append((y, m, inits, idx, v))
    return resultat


def seuils_reanalyse(mois, n_mailles, saisons):
    """Réutilise Gumbel R-21 ; maxima mensuels sur fenêtres finies seulement.

    Le mois entièrement manquant reste NaN, donc ne compte pas parmi les
    30 blocs requis par maille. Aucun changement aux seuils des prévisions.
    """
    blocs = []
    for y, m, inits, idx, q in mois:
        finite = np.isfinite(q[:, 0])
        maximum = np.where(finite, q[:, 0], -np.inf).max(axis=0)
        maximum[~finite.any(axis=0)] = np.nan
        blocs.append((y, m, inits[:1], idx, maximum[None, None, :]))
    return seuils(blocs, n_mailles, saisons)


def rapports(mois, thr, A, jours, pi=None):
    """R(j), contrôle/réanalyse ou rang d'ensemble, et couverture finie.

    NaN = non-dépassement (rang conservé sur 11 membres). Une initialisation
    est documentée valide si au moins une valeur du membre de contrôle, ou
    de l'ensemble respectivement, est finie sur une maille retenue. Les
    membres manquants contribuent zéro au rang, jamais une alerte.
    """
    out = np.full((len(jours), A.shape[1]), np.nan)
    pos = {d: i for i, d in enumerate(jours)}
    for _, _, inits, idx, q in mois:
        if pi is not None and (q.shape[1] != 11 or not 0 < pi <= 1):
            raise ValueError("Ensemble : 11 membres et 0 < pi <= 1 requis")
        for col in range(A.shape[1]):
            mask = (np.asarray(A[idx, col].toarray()).ravel() > 0) & np.isfinite(thr[idx])
            if not mask.any():
                continue
            values = q[:, :, mask] / thr[idx[mask]]
            finite = np.isfinite(values)
            r = np.where(finite, values, 0).max(axis=2)
            if pi is None:
                rt, valid = r[:, 0], finite[:, 0].any(axis=1)
            else:
                rang = math.ceil(11 * pi - 1e-12)
                rt = np.sort(r, axis=1)[:, -rang]
                valid = finite.any(axis=(1, 2))
            for i, t in enumerate(inits):
                if valid[i]:
                    for k in (1, 2, 3):
                        j = pos.get(t + dt.timedelta(days=k))
                        if j is not None:
                            out[j, col] = np.fmax(out[j, col], rt[i])
    return out


def classer(dates, jours, valeurs, riviere=True):
    """Priorité a, n, e, d, c, b ; couverture publiée sur J seulement."""
    if not dates:
        raise ValueError("Une unité doit avoir des dates de fiche")
    lookup = dict(zip(jours, valeurs))
    dates = set(dates)
    central = np.array([lookup.get(d, np.nan) for d in dates])
    valide = np.isfinite(central)
    couverture = float(valide.mean())
    if not riviere:
        classe = "a"
    elif not valide.any():
        classe = "n"
    elif (central[valide] >= 1).any():
        classe = "e"
    else:
        autour = np.array([lookup.get(d, np.nan) for d in etendre(dates, 3)])
        maximum = autour[np.isfinite(autour)].max()
        classe = "d" if maximum >= 1 else "c" if maximum >= .5 else "b"
    return {"classe": classe, "couverture": couverture,
            "couverture_faible": couverture < .5}


def calibrer_k(ctrl, reference, temoins, jours):
    """Même support fini pour cible et k ; écart, proximité de 1, puis k."""
    commun = np.asarray(temoins, bool) & np.isfinite(reference) & np.isfinite(ctrl)
    cible = charge(ctrl >= 1, commun, jours)
    charges = np.array([charge(reference >= k, commun, jours) for k in KS])
    if not np.isfinite(cible) or cible == 0:
        i = int(np.flatnonzero(KS == 1)[0])
        return dict(k=1., cible=cible, charge=charges[i], ecart=np.nan,
                    hors_tolerance=True, jours_communs=int(commun.sum()))
    distances = np.abs(charges - cible)
    candidats = np.flatnonzero(np.isclose(distances, distances.min(), rtol=0, atol=1e-12))
    i = min(candidats, key=lambda j: (round(abs(KS[j] - 1), 10), KS[j]))
    ecart = charges[i] / cible - 1
    return dict(k=float(KS[i]), cible=cible, charge=charges[i], ecart=ecart,
                hors_tolerance=bool(abs(ecart) > TOLERANCE + 1e-12),
                jours_communs=int(commun.sum()))


def lecture(p, pc, ic_ecart, hors_tolerance):
    """Règles de lecture figées ; aucun test confirmatoire."""
    if hors_tolerance > 3:
        return "descriptif : charge non comparable"
    if not np.isfinite([p, pc, *ic_ecart]).all():
        return "non évaluable"
    if p <= .25:
        return "référence basse : A, erreur hydrologique ou B"
    if p >= .40 and p - pc >= .15 - 1e-12 and ic_ecart[0] > 0:
        return "C privilégiée (exploratoire)"
    if p >= .40:
        return "descriptif : aucune attribution"
    return "hypothèses mêlées"


def comparer(unites, methodes=METHODES, n_boot=2000, graine=20261112,
             sans_riviere=False):
    """Support commun, exclusions, IC appariés par bootstrap des saisons.

    Colonnes attendues : saison et classe_<méthode>. a reste au dénominateur
    sauf dans la sensibilité sans rivière ; n est toujours exclu.
    """
    if n_boot < 1:
        raise ValueError("n_boot doit être positif")
    cols = ["classe_" + m for m in methodes]
    if not unites[cols].isin(CLASSES).all().all():
        raise ValueError("Classe inconnue")
    mauvais = ["n", "a"] if sans_riviere else ["n"]
    commun = ~unites[cols].isin(mauvais).any(axis=1)
    u = unites.loc[commun]
    exclusions = {m: unites["classe_" + m].value_counts().reindex(CLASSES, fill_value=0).to_dict()
                  for m in methodes}
    if u.empty:
        return dict(n=0, taux={m: np.nan for m in methodes}, ic={}, exclusions=exclusions,
                    exclus_communs=int((~commun).sum()))
    counts = pd.DataFrame({m: (u["classe_" + m] == "e").astype(int) for m in methodes})
    counts["saison"] = u.saison
    counts["n"] = 1
    sommes = counts.groupby("saison").sum()
    tir = np.random.default_rng(graine).integers(0, len(sommes), (n_boot, len(sommes)))
    nb = sommes.n.to_numpy()[tir].sum(axis=1)
    boot = {m: sommes[m].to_numpy()[tir].sum(axis=1) / nb for m in methodes}
    ic = {m: np.percentile(boot[m], [2.5, 97.5]).tolist() for m in methodes}
    if "reanalyse" in methodes and "controle" in methodes:
        ic["ecart"] = np.percentile(boot["reanalyse"] - boot["controle"], [2.5, 97.5]).tolist()
    return dict(n=len(u), taux={m: float(counts[m].mean()) for m in methodes}, ic=ic,
                exclusions=exclusions, exclus_communs=int((~commun).sum()))


def croisement(unites, prevision):
    return pd.crosstab(unites.classe_reanalyse, unites["classe_" + prevision]).reindex(
        index=CLASSES, columns=CLASSES, fill_value=0)


def sensibilites(unites):
    """Même support évaluable que le principal, même pour J±1 et k=1."""
    result = {}
    for nom in ("pm1", "k1"):
        u = unites.copy()
        for m in METHODES:
            if nom == "k1" and m != "reanalyse":
                continue
            col = "classe_" + m
            eligible = ~u[col].isin(["a", "n"])
            detection = u["detecte_k1" if nom == "k1" else "detecte_pm1_" + m]
            u.loc[eligible, col] = np.where(detection[eligible], "e", "b")
        result[nom] = comparer(u)
    return result


def diagnostic(mois, reanalyse, A, territoires, jours, temoins, unites, pis=None):
    """D1/D2 ou D3a, calcul en mémoire et sorties tabulaires.

    Pour les bassins, pis doit être le dictionnaire des pi appris au district.
    k est toujours recalibré ici. jours comprend J±3, mais seuls les jours
    témoins explicitement fournis servent aux charges. Unités : liste de dicts.
    """
    if len(territoires) != A.shape[1] or len(set(territoires)) != len(territoires):
        raise ValueError("Territoires incompatibles avec A")
    if jours != sorted(set(jours)) or np.shape(temoins) != (len(jours), len(territoires)):
        raise ValueError("Jours triés uniques et masque témoin aligné requis")
    saisons = sorted({u["saison"] for u in unites})
    if not saisons or not mois or not reanalyse:
        raise ValueError("Mois et unités non vides requis")
    if len(mois) != len(reanalyse) or any(
            (a[0], a[1], list(a[2])) != (b[0], b[1], list(b[2])) or not np.array_equal(a[3], b[3])
            for a, b in zip(mois, reanalyse)):
        raise ValueError("Réanalyse et prévision doivent partager mois, initialisations et mailles")
    S, _ = seuils(mois, A.shape[0], saisons)
    SR, _ = seuils_reanalyse(reanalyse, A.shape[0], saisons)
    sj = np.array([season_of(d) for d in jours])
    lignes, plis = [], []
    for s in saisons:
        app = sj != s
        test = sj == s
        ja = [d for d, ok in zip(jours, app) if ok]
        jt = [d for d, ok in zip(jours, test) if ok]
        ctrl, pmax = alertes(mois, S[s], A, jours)
        riviere = np.asarray(A[np.isfinite(S[s])].sum(axis=0)).ravel() > 0
        tem = np.asarray(temoins, bool) & riviere
        cible = charge(ctrl[app], tem[app], ja)
        if pis is None:
            ch = np.array([charge(pmax[app] >= pi - 1e-6, tem[app], ja) for pi in PIS])
            if not np.isfinite(ch).any():
                raise ValueError("Pi R-21 non déterminable : fournir les pi des plis districts")
            pi = float(PIS[np.nanargmin(np.abs(ch - cible))])
        else:
            pi = float(pis[s])
        rc = rapports(mois, S[s], A, jours)
        re = rapports(mois, S[s], A, jours, pi)
        # Les mailles retenues restent celles de R-21, même si la réanalyse
        # dispose d'un seuil fini sur une maille écartée par la prévision.
        sr = np.where(np.isfinite(S[s]), SR[s], np.nan)
        rr = rapports(reanalyse, sr, A, jours)
        cal = calibrer_k(rc[app], rr[app], tem[app], ja)
        k = cal["k"]
        rt = rr / k
        commun_test = tem[test] & np.isfinite(rc[test]) & np.isfinite(rr[test])
        plis.append(dict(saison=s, pi=pi, **cal,
                         charge_controle_test=charge(ctrl[test], commun_test, jt),
                         charge_reanalyse_test=charge(rt[test] >= 1, commun_test, jt)))
        for u in (u for u in unites if u["saison"] == s):
            if not set(etendre(u["dates"], 3)).issubset(jours):
                raise ValueError("jours doit couvrir J±3 pour chaque unité")
            col = territoires.index(u["territoire"]) if u["territoire"] in territoires else None
            riv = col is not None and bool(riviere[col])
            row = {key: value for key, value in u.items() if key != "dates"}
            row["riviere"] = riv
            for m, values in zip(METHODES, (rc, re, rt)):
                serie = values[:, col] if col is not None else np.full(len(jours), np.nan)
                row.update({key + "_" + m: value for key, value in
                            classer(u["dates"], jours, serie, riv).items()})
                row["detecte_pm1_" + m] = bool(riv and any(
                    serie[j] >= 1 for j, d in enumerate(jours) if d in etendre(u["dates"], 1)))
            row["detecte_k1"] = bool(riv and any(rr[j, col] >= 1 for j, d in enumerate(jours)
                                               if d in u["dates"]))
            lignes.append(row)
    U, P = pd.DataFrame(lignes), pd.DataFrame(plis)
    comparaisons = {"commun": comparer(U), "sans_riviere": comparer(U, sans_riviere=True),
                   "reanalyse_controle": comparer(U, ("controle", "reanalyse"))}
    comparaisons.update(sensibilites(U))
    pair = comparaisons["reanalyse_controle"]
    interpretation = lecture(pair["taux"]["reanalyse"], pair["taux"]["controle"],
                             pair["ic"].get("ecart", [np.nan, np.nan]), int(P.hors_tolerance.sum()))
    effectifs = {m: U.groupby(["saison", "episode", "classe_" + m]).size() for m in METHODES}
    return dict(unites=U, plis=P, comparaisons=comparaisons, lecture=interpretation,
                effectifs=effectifs, croisements={m: croisement(U, m) for m in METHODES[:2]})


def comparer_echelles(districts, bassins):
    """D3 : comparaison descriptive sur les mêmes épisodes, sans appariement
    artificiel entre districts et bassins de tailles différentes.
    """
    episodes = sorted(set(districts.episode) & set(bassins.episode))
    return {e: {"districts": comparer(districts[districts.episode == e]),
                "bassins": comparer(bassins[bassins.episode == e])} for e in episodes}


def rattachements(fokontany):
    """D3 : table en mémoire adm2, bassin, population, commune, sous_bassin.

    Le dénominateur est toute la population du district, y compris les lignes
    sans bassin. Le recoupement existe même sur une ligne de population nulle.
    """
    if (fokontany.population < 0).any() or not np.isfinite(fokontany.population).all():
        raise ValueError("Populations finies et positives ou nulles requises")
    total = fokontany.groupby("adm2").population.sum()
    if (total <= 0).any():
        raise ValueError("Population totale du district nulle")
    table = fokontany.dropna(subset=["bassin"]).groupby(["adm2", "bassin"]).agg(
        population=("population", "sum"), communes=("commune", lambda x: sorted(set(x))),
        sous_bassins=("sous_bassin", lambda x: sorted(set(x.dropna())))).reset_index()
    table["part"] = table.population / table.adm2.map(total)
    table["principal"] = table.part >= .20 - 1e-12
    return table


def unites_bassins(unites, liens, sensibilite=False):
    """Union des dates des seuls districts rattachés, sans intervalle rempli."""
    selection = liens if sensibilite else liens[liens.principal]
    groupes = {}
    for u in unites:
        for b in selection.loc[selection.adm2 == u["territoire"], "bassin"]:
            key = (u["saison"], u["episode"], b)
            g = groupes.setdefault(key, {"dates": set(), "districts": set()})
            g["dates"].update(u["dates"])
            g["districts"].add(u["territoire"])
    return [dict(saison=s, episode=e, territoire=b, dates=sorted(g["dates"]),
                 districts=sorted(g["districts"])) for (s, e, b), g in sorted(groupes.items())]


def temoins_bassins(jours, bassins, touches, liens):
    """Aucun recoupement avec un district déclaré, même sous 20 %."""
    recoupe = {b: set(liens.loc[liens.bassin == b, "adm2"]) for b in bassins}
    return np.array([[not (recoupe[b] & set(touches.get((d.year, d.month), ())))
                      for b in bassins] for d in jours], bool)


def centroides(fokontany):
    """D4 : centroïdes lat/lon pondérés par la population des fokontany."""
    result = {}
    for district, g in fokontany.groupby("adm2"):
        if not np.isfinite(g[["lat", "lon", "population"]]).all().all() or (g.population < 0).any() or g.population.sum() <= 0:
            raise ValueError("Coordonnées ou populations invalides")
        result[district] = tuple(np.average(g[["lat", "lon"]], weights=g.population, axis=0))
    return result


def contexte_cyclonique(dates, centre, positions):
    """Positions publiées (date/datetime, lat, lon), aucune interpolation."""
    fenetre = set(etendre(dates, 1))
    distances = []
    for date, lat, lon in positions:
        date = date.date() if isinstance(date, dt.datetime) else date
        if date not in fenetre:
            continue
        if not np.isfinite([*centre, lat, lon]).all():
            raise ValueError("Position cyclonique invalide")
        a, b = np.radians(centre), np.radians([lat, lon])
        h = np.sin((b[0] - a[0]) / 2) ** 2 + np.cos(a[0]) * np.cos(b[0]) * np.sin((b[1] - a[1]) / 2) ** 2
        distances.append(float(6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))))
    distance = min(distances) if distances else np.nan
    classe = "aucun cyclone" if not distances else "<100 km" if distance < 100 else "100–300 km" if distance <= 300 else ">300 km"
    return {"distance_km": distance, "contexte": classe, "chirps": "différé (section 12)"}


def diagnostic_contexte(unites, dates_unites, centres, positions):
    """D4 : contexte et comparaisons sur support commun par classe cyclonique."""
    lignes = []
    for u in unites.to_dict("records"):
        cle = (u["episode"], u["territoire"])
        lignes.append(dict(u, **contexte_cyclonique(dates_unites[cle], centres[u["territoire"]], positions)))
    U = pd.DataFrame(lignes)
    return U, {c: comparer(g) for c, g in U.groupby("contexte")}


if __name__ == "__main__":
    raise SystemExit("API en mémoire uniquement ; aucun calcul réel autorisé par cette livraison.")
