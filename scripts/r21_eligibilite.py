"""R-21 : population éligible figée avant tout score (relecture de Codex, 11/11/2026, point 1).

Unités : épisode x district. Épisode = dates de fiches DesInventar (filtres du script R-21, décembre-mars, saisons
2003-2018) regroupées tant que deux dates successives sont espacées de 3 jours au plus, tous districts confondus.
Une unité est éligible si au moins une initialisation GloFAS publiée précède de 1 à 3 jours l'une des dates de
l'épisode (fenêtre d'échéance 1-3 j). Les reprévisions v4 sont initialisées deux fois par semaine : sans cette
règle explicite, une partie des épisodes n'a aucune prévision à 1-3 jours. Initialisations prises dans tous les
fichiers, donc à cheval sur deux mois. Exclusions : saison 2017 (fiches à date douteuse) et janvier-mars 2019.
Témoins : districts sans aucune fiche de cyclone ou d'inondation (filtre de dommages non appliqué, par prudence)
dans un mois publié. Sorties agrégées : validation/r21_eligibilite.csv et validation/r21_eligibilite.md.
Usage : python scripts/r21_eligibilite.py --country mdg
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import re
from pathlib import Path

import numpy as np
import pandas as pd

from common import country_data_dir, read_units
from validate_reforecast_impact import season_of

ROOT = Path(__file__).resolve().parent.parent
MOIS = (12, 1, 2, 3)
SAISONS = (2003, 2018)
EXCLUES = {2017}                     # saison 2017-2018 : fiches exclues (date douteuse), protocole section 9
LOT_EN_COURS = {(2015, 2), (2015, 3)}
NOMS = {12: "déc.", 1: "jan.", 2: "fév.", 3: "mars"}


def fiches(slug, filtre_dommages=True):
    df = pd.read_csv(country_data_dir(slug) / "external" / "desinventar.csv", dtype=str)
    df = df[df.type.isin(["cyclone", "inondation"]) & df.date.notna() & df.adm2_actuel.notna()
            & (df.date_douteuse != "1")].copy()
    if filtre_dommages:
        num = lambda c: pd.to_numeric(df[c], errors="coerce").fillna(0)
        df = df[(num("touches") > 0) | (num("maisons_endommagees") > 0) | (num("maisons_detruites") > 0)]
    df["d"] = pd.to_datetime(df.date).dt.date
    df["saison"] = [season_of(d) for d in df.d]
    rows = [(d, s, a.strip()) for d, s, adm in zip(df.d, df.saison, df.adm2_actuel) for a in adm.split(";")]
    return pd.DataFrame(rows, columns=["d", "saison", "adm2"])


def episodes(f):
    f = f[np.array([d.month in MOIS for d in f.d]) & f.saison.between(*SAISONS).to_numpy()].copy()
    ep, k, prec = {}, -1, None
    for d in sorted(f.d.unique()):
        if prec is None or (d - prec).days > 3:
            k += 1
        ep[d], prec = k, d
    f["episode"] = f.d.map(ep)
    return f


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    dossier = country_data_dir(args.country) / "reforecast"
    publies, inits = set(), set()
    for f in sorted(dossier.glob("glofas_v4_*.npz")):
        y, m = map(int, re.search(r"(\d{4})_(\d{2})", f.name).groups())
        publies.add((y, m))
        inits |= {dt.date.fromisoformat(str(t)) for t in np.load(f)["init"]}
    f = episodes(fiches(args.country))
    tous = fiches(args.country, filtre_dommages=False)
    districts = sorted(set(read_units(args.country).adm2.dropna()) - {""})

    lignes = []
    for (e, a), g in f.groupby(["episode", "adm2"]):
        dates = sorted(g.d.unique())
        s = int(g.saison.iloc[0])
        mois = sorted({(d.year, d.month) for d in dates})
        bonnes = [t for t in inits if any(1 <= (d - t).days <= 3 for d in dates)]
        if s in EXCLUES:
            raison = "saison exclue (dates douteuses)"
        elif any(d.year == 2019 and d.month <= 3 for d in dates):
            raison = "janvier-mars 2019 exclu"
        elif bonnes:
            raison = ""
        elif any(m in LOT_EN_COURS for m in mois):
            raison = "mois en cours de téléchargement"
        elif not all(m in publies for m in mois):
            raison = "mois non publié"
        else:
            raison = "aucune initialisation 1-3 j avant"
        lignes.append({"episode": e, "debut": dates[0].isoformat(), "saison": s, "adm2": a, "fiches": len(g),
                       "initialisations": " ".join(sorted(t.isoformat() for t in bonnes)),
                       "eligible": int(not raison), "raison": raison})
    u = pd.DataFrame(lignes).sort_values(["episode", "adm2"])
    sortie = ROOT / "validation" / "r21_eligibilite.csv"
    u.to_csv(sortie, index=False, encoding="utf-8")

    el = u[u.eligible == 1]
    ep_el = el.groupby("episode").agg(saison=("saison", "first"), debut=("debut", "first"), districts=("adm2", "size"))
    L = ["# R-21 — Population éligible (épisodes, districts, témoins)", "",
         f"Calcul du {dt.date.today():%d/%m/%Y} par [`scripts/r21_eligibilite.py`](../scripts/r21_eligibilite.py) ; "
         f"{len(publies)} mois GloFAS en local. Détail par unité : [`r21_eligibilite.csv`](r21_eligibilite.csv). "
         "Aucun score calculé.", "",
         "## Unités épisode × district", "",
         f"- Unités avec fiche : {len(u)}, dans {u.episode.nunique()} épisodes.",
         f"- **Éligibles : {len(el)} unités, {el.episode.nunique()} épisodes, {el.saison.nunique()} saisons.**"]
    for r, n in u[u.eligible == 0].raison.value_counts().items():
        L.append(f"- Non éligibles, {r} : {n} unités ({u[u.raison == r].episode.nunique()} épisodes).")
    L += ["", "| Épisode | Début | Saison | Districts éligibles |", "|---:|---|---:|---:|"]
    L += [f"| {e} | {r.debut} | {r.saison} | {r.districts} |" for e, r in ep_el.iterrows()]
    L += ["", "## Saison × mois", "",
          "Témoins : districts sans fiche de cyclone ou d'inondation dans le mois (sur "
          f"{len(districts)} districts) ; jours-districts = témoins × jours du mois. La restriction aux districts "
          "ayant une maille de rivière éligible se fait dans le code des scores.", "",
          "| Saison | Mois | GloFAS | Districts avec unité éligible | Districts témoins | Jours-districts témoins |",
          "|---:|---|---|---:|---:|---:|"]
    for s in range(SAISONS[0], SAISONS[1] + 1):
        for m in MOIS:
            y = s if m >= 11 else s + 1
            if (y, m) in publies:
                etat = "publié"
            elif (y, m) in LOT_EN_COURS:
                etat = "en cours"
            else:
                continue
            touches = set(tous[[d.year == y and d.month == m for d in tous.d]].adm2)
            exclu = s in EXCLUES or (y == 2019 and m <= 3)
            n_tem = 0 if exclu or etat != "publié" else len(set(districts) - touches)
            n_el = el[[d.startswith(f"{y}-{m:02d}") for d in el.debut]].adm2.nunique()
            L.append(f"| {s} | {NOMS[m]} {y} | {etat}{' (exclu)' if exclu else ''} | {n_el} | {n_tem} | "
                     f"{n_tem * calendar.monthrange(y, m)[1]} |")
    (ROOT / "validation" / "r21_eligibilite.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Écrit : {sortie} ; {len(el)} unités éligibles, {el.episode.nunique()} épisodes")


if __name__ == "__main__":
    main()
