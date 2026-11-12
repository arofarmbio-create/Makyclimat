"""R-21, étape 2 : couverture effective des seuils de crue calculés sur les reprévisions GloFAS publiées.

Mesure, sans calculer aucun score (verrou R-21 maintenu) :
1. les mois disponibles par saison (nov. Y - avr. Y+1) ;
2. la part des mailles de rivière rattachées à un district dont le seuil existe (>= MIN_SEASONS saisons hors saison
   testée), avec la règle actuelle (maximum sur les mois disponibles, quels qu'ils soient) ;
3. le biais de cette règle : sur les saisons complètes, rapport entre le maximum d'un seul mois et celui de déc.-mars ;
4. la couverture de deux corrections à « mêmes mois dans chaque saison » : janvier seul, et blocs mensuels déc.-mars.
Sortie : validation/r21_couverture_seuils.md (agrégats seulement).
Usage : python scripts/r21_couverture_seuils.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

import numpy as np

from common import country_data_dir, locate_points, read_units
from validate_reforecast_impact import (MIN_SEASONS, THR_SEASONS, VERIF_SEASONS, gumbel_q, load_months, season_of)

ROOT = Path(__file__).resolve().parent.parent
MOIS = {11: "nov.", 12: "déc.", 1: "jan.", 2: "fév.", 3: "mars", 4: "avr."}
PORTEE = (12, 1, 2, 3)
Q_MIN = 5.0


def lire_mois(files):
    """Maximum du contrôle par mois : {(saison, mois): [fenêtre, maille]} sur l'union des mailles."""
    keys = {}
    for f in files:
        z = np.load(f, allow_pickle=False)
        for a, b in zip(z["lat"], z["lon"]):
            keys.setdefault((round(float(a), 3), round(float(b), 3)), len(keys))
    windows = np.load(files[0], allow_pickle=False)["windows"]
    out = {}
    for f in files:
        y, m = map(int, re.search(r"(\d{4})_(\d{2})", f.name).groups())
        s = season_of(dt.date(y, m, 1))
        if s is None or not THR_SEASONS[0] <= s <= THR_SEASONS[1]:
            continue
        z = np.load(f, allow_pickle=False)
        idx = np.array([keys[(round(float(a), 3), round(float(b), 3))] for a, b in zip(z["lat"], z["lon"])])
        a = np.full((len(windows), len(keys)), np.nan, dtype="float32")
        a[:, idx] = z["q"][:, 0].astype("float32").max(axis=0)
        out[(s, m)] = a
    return keys, windows, out


def maxima(mois, seasons, garder):
    """[saison, fenêtre, maille] : maximum sur les mois retenus par garder(saison, mois)."""
    forme = next(iter(mois.values())).shape
    M = np.full((len(seasons),) + forme, np.nan, dtype="float32")
    for (s, m), a in mois.items():
        if garder(s, m):
            i = int(s - seasons[0])
            M[i] = np.fmax(M[i], a)
    return M


def seuil_loso(X, n_min, T=2):
    """Gumbel par fenêtre et maille sur les blocs X[bloc, fenêtre, maille] ; NaN si moins de n_min blocs."""
    n = np.isfinite(X).sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        q = gumbel_q(np.nanmean(X, 0), np.nanstd(X, 0, ddof=1), T)
    q[n < n_min] = np.nan
    return q, n


def couverture(q, n, eligible):
    """Part des mailles éligibles (rivière et district) dotées d'un seuil, par fenêtre : (min, max) en %."""
    parts = [100 * np.isfinite(q[w, eligible]).mean() for w in range(q.shape[0])]
    return min(parts), max(parts)


def pct(x):
    return f"{x:.0f}".replace(".", ",")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    files = load_months(country_data_dir(args.country) / "reforecast")
    keys, windows, mois = lire_mois(files)
    seasons = np.arange(THR_SEASONS[0], THR_SEASONS[1] + 1)
    lat = np.array([k[0] for k in keys]); lon = np.array([k[1] for k in keys])
    units = read_units(args.country).set_index("pcode")
    district = np.array([bool(c) and bool(units.at[c, "adm2"]) for c in locate_points(args.country, lon, lat)])

    dispo = {s: sorted((m for (t, m) in mois if t == s), key=lambda m: (m < 11, m)) for s in seasons}
    presentes = [s for s in seasons if dispo[s]]
    L = ["# R-21 — Couverture effective des seuils de crue", "",
         f"Calcul du {dt.date.today():%d/%m/%Y} par [`scripts/r21_couverture_seuils.py`](../scripts/r21_couverture_seuils.py) "
         f"sur {len(files)} fichiers mensuels de la release `reprevisions-glofas-v4`. Aucun score calculé (verrou R-21). "
         f"Mailles : union des {len(keys)} mailles des fichiers ; éligibles = rattachées à un district et crue de 2 ans "
         f"≥ {Q_MIN:g} m³/s (règle du script R-21). Minimum d'apprentissage : {MIN_SEASONS} blocs hors saison testée. "
         f"Fenêtres : {', '.join(f'{a}-{b} j' for a, b in windows)}.", "",
         "## 1. Mois disponibles par saison", "", "| Saison | Mois | Nombre |", "|---|---|---:|"]
    for s in presentes:
        L.append(f"| {s} | {', '.join(MOIS[m] for m in dispo[s])} | {len(dispo[s])} |")
    L += ["", f"{len(presentes)} saisons ont au moins un mois. Retirer la saison testée en laisse au plus "
          f"{len(presentes) - 1}.", ""]

    # 2. Règle actuelle
    M = maxima(mois, seasons, lambda s, m: True)
    q_all, _ = seuil_loso(M, 3)       # éligibilité sans minimum d'apprentissage, pour ne pas surestimer la couverture
    with np.errstate(invalid="ignore"):
        eligible = district & (np.nan_to_num(np.nanmax(np.where(np.isfinite(q_all), q_all, -1), 0), nan=-1) >= Q_MIN)
    tests = [s for s in presentes if VERIF_SEASONS[0] <= s <= VERIF_SEASONS[1]]
    L += ["## 2. Règle actuelle : maximum sur les mois disponibles", "",
          f"Mailles éligibles : {int(eligible.sum())} (crue de 2 ans estimée sur toutes les saisons disponibles, au moins "
          f"3, ≥ {Q_MIN:g} m³/s pour une fenêtre, district connu). Le script R-21 applique ce filtre saison par saison.", "",
          "| Saison testée | Saisons d'apprentissage | Mailles éligibles avec seuil (min–max sur les fenêtres) |",
          "|---|---:|---|"]
    for s in tests:
        X = M[seasons != s]
        q, n = seuil_loso(X, MIN_SEASONS)
        a, b = couverture(q, n, eligible)
        L.append(f"| {s} | {int(np.nanmax(n[:, eligible]))} au plus | {pct(a)} – {pct(b)} % |")
    L.append("")

    # 3. Biais d'un maximum partiel
    completes = [s for s in presentes if all(m in dispo[s] for m in PORTEE)]
    L += ["## 3. Biais d'un maximum calculé sur un seul mois", "",
          f"Saisons où déc.-mars sont tous disponibles : {', '.join(map(str, completes))}. Pour chacune, rapport entre le "
          "maximum d'un mois et le maximum de déc.-mars, médiane sur les mailles éligibles et les fenêtres "
          "(1 = aucun biais).", "", "| Mois seul | Rapport médian | Part des cas où le mois porte le maximum |",
          "|---|---:|---:|"]
    ref = maxima(mois, seasons, lambda s, m: m in PORTEE)
    for m0 in PORTEE:
        part = maxima(mois, seasons, lambda s, m, m0=m0: m == m0)
        r, eg = [], []
        for s in completes:
            i = int(s - seasons[0])
            with np.errstate(invalid="ignore", divide="ignore"):
                x = (part[i][:, eligible] / ref[i][:, eligible]).ravel()
            x = x[np.isfinite(x)]
            r.append(x); eg.append(x >= 0.999)
        r = np.concatenate(r); eg = np.concatenate(eg)
        mediane = f"{np.median(r):.2f}".replace(".", ",")
        L.append(f"| {MOIS[m0]} | {mediane} | {pct(100 * eg.mean())} % |")
    L += ["", "Un seuil appris sur des saisons d'un ou deux mois est donc trop bas : il gonfle les dépassements prévus, "
          "différemment selon les saisons.", ""]

    # 4. Corrections : mêmes mois dans chaque saison
    L += ["## 4. Corrections à mois identiques", "",
          "**A. Janvier seul** (maximum de janvier, une valeur par saison). **B. Blocs mensuels déc.-mars** : chaque mois "
          "disponible est un bloc, seuil de Gumbel sur les maxima mensuels ; la période de retour mensuelle "
          "T_m = 1 / (1 − 0,5^(1/4)) ≈ 6,3 correspond à la crue de 2 ans sur déc.-mars si les mois étaient indépendants "
          "(hypothèse à discuter : persistance des débits d'un mois à l'autre). Seuil exigé : 30 blocs.", "",
          "| Saison testée | A : saisons avec janvier | A : couverture | B : blocs déc.-mars | B : couverture |",
          "|---|---:|---|---:|---|"]
    J = maxima(mois, seasons, lambda s, m: m == 1)
    blocs = sorted(k for k in mois if k[1] in PORTEE)
    B = np.stack([mois[k] for k in blocs])
    bs = np.array([k[0] for k in blocs])
    t_m = 1 / (1 - 0.5 ** 0.25)
    for s in tests:
        qa, na = seuil_loso(J[seasons != s], MIN_SEASONS)
        qb, nb = seuil_loso(B[bs != s], 30, T=t_m)
        a1, a2 = couverture(qa, na, eligible)
        b1, b2 = couverture(qb, nb, eligible)
        L.append(f"| {s} | {int(np.nanmax(na[:, eligible]))} | {pct(a1)} – {pct(a2)} % | {int(np.nanmax(nb[:, eligible]))} "
                 f"| {pct(b1)} – {pct(b2)} % |")
    manque_jan = [s for s in seasons if 1 not in dispo[s]]
    manque_dm = [(s + (m < 11), m) for s in seasons for m in PORTEE if m not in dispo[s]]
    L += ["", f"Saisons sans janvier : {', '.join(map(str, manque_jan))} ({len(manque_jan)} mois à télécharger pour "
          f"avoir janvier sur les {len(seasons)} saisons {THR_SEASONS[0]}-{THR_SEASONS[1]}). "
          f"Mois de déc.-mars manquants sur ces saisons : {len(manque_dm)}.", ""]
    sortie = ROOT / "validation" / "r21_couverture_seuils.md"
    sortie.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Écrit : {sortie}")


if __name__ == "__main__":
    main()
