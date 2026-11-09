"""Données des pages « Nappes » et « Preuves » du site (docs/data/<pays>/recherche.json).

Rend visibles les résultats scientifiques avec leur incertitude (protocole doctoral : M3, H6, E4, M7) :
- nappes par région : niveau statique médian et fourchette à 80 %, part extrapolée, distance au forage, recharge T2,
  T2L et T2K (cartes figées) ;
- atlas des grands bassins les plus peuplés ;
- verdicts des tests de la recharge et de la combinaison des preuves ;
- fiche « preuves » de chaque module affiché : type de résultat (E4), tests du registre et leur statut, remarque de
  puissance (`analyse_puissance_retro.md`).
Les statuts sont relus dans `validation/etat_des_lieux_registre.md` à chaque exécution : le site suit le registre.
Usage : python scripts/build_site_recherche.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import re

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir, read_units, write_json

# Type de résultat (protocole doctoral E4) : reconstitution d'un état passé, anticipation (avant l'événement), suivi
# pendant l'événement.
MODULES = [
    ("Cyclones : régions touchées", "anticipation (avant l'arrivée du cyclone)", ["R-01"], ""),
    ("Inondation : fokontany touchés dans une zone atteinte", "reconstitution (après l'événement)", ["R-02", "R-03", "R-40"],
     "8 activations EMS seulement : stabilité non établissable (puissance insuffisante)"),
    ("Seuils d'action anticipée (cyclones)", "anticipation", ["R-04"], ""),
    ("Crue de rivière : période de retour et prévision d'ensemble", "anticipation et suivi", ["R-07", "R-08", "R-11", "R-12", "R-21"], ""),
    ("Inondation pluviale (cumul, ruissellement, intensité)", "suivi pendant l'événement", ["R-09", "R-10", "R-23"],
     "R-23 : aucune durée de pluie n'a de compétence à l'échelle du périmètre"),
    ("Éboulements", "anticipation", ["R-13"], ""),
    ("Sécheresse : SPI et SPEI", "suivi", ["R-14", "R-15", "R-17", "R-24"], ""),
    ("Humidité du sol et indice de nappe", "suivi", ["R-16", "R-18", "R-36", "R-37"],
     "H-N1 (7 sites) : puissance insuffisante, 5 sites sur 7 dans le sens attendu"),
    ("Prévision saisonnière et planification", "anticipation (1 à 12 mois)", ["R-25", "R-26", "R-27", "R-22", "R-39"],
     "144 tests corrigés : une région « non prévisible » ne prouve pas l'absence de lien"),
    ("Fusion des sources de pluie (E1)", "reconstitution", ["R-35"], "5 stations : test sans puissance (5 sur 5 exigés)"),
    ("Nappes : niveau statique, recharge, atlas", "reconstitution (état moyen)",
     ["R-41", "R-43", "R-44", "R-45", "R-46", "R-47", "R-48", "R-49", "R-50", "R-51", "R-52", "R-53", "R-54"],
     "8 groupes de sites indépendants seulement ; voir l'onglet Nappes"),
    ("Vulnérabilité cumulative", "reconstitution", ["R-20"], ""),
    ("Potentiel pour point d'eau peu profond", "reconstitution", ["R-19"], ""),
]


def registre() -> dict:
    """{R-xx: (question courte, statut, résultat)} lus dans le registre ; la colonne « Statut » est repérée dans
    l'en-tête de chaque tableau (les tableaux n'ont pas tous les mêmes colonnes)."""
    out, i_stat, i_res = {}, -1, None
    for line in (ROOT / "validation" / "etat_des_lieux_registre.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("| ID "):
            h = [x.strip() for x in line.strip().strip("|").split("|")]
            i_stat = h.index("Statut") if "Statut" in h else -1
            i_res = next((k for k, x in enumerate(h) if x.startswith(("Résultat", "État"))), None)
        elif re.match(r"^\| R-\d+ ", line):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            q = re.sub(r"`", "", c[1])
            res = re.sub(r"`", "", c[i_res]) if i_res is not None and i_res < len(c) else ""
            out[c[0]] = (q[:160] + ("…" if len(q) > 160 else ""), re.sub(r"`", "", c[i_stat]),
                         res[:300] + ("…" if len(res) > 300 else ""))
    return out


def classe_statut(s: str) -> str:
    if "✅" in s:
        return "ok"
    if "❌" in s or "⬛" in s:
        return "ko"
    if "⚠" in s or "🟡" in s:
        return "partiel"
    return "attente"


def combinaison() -> dict:
    t = (ROOT / "validation" / "combinaison_preuves.md").read_text(encoding="utf-8")
    sc = re.search(r"Scénario de dépôt de chlorure retenu : \*\*(\w+)\*\*", t)
    lignes = {}
    for m in re.finditer(r"^\| (bas|central|haut)(?: \(retenu\))? \| ([+-][\d.]+) \| ([^|]+) \| ([+-][\d.]+) \| ([^|]+) \|", t, re.M):
        lignes[m.group(1)] = {"q1": m.group(3).strip(), "q2": m.group(5).strip()}
    return {"scenario": sc.group(1) if sc else None, "par_scenario": lignes}


def nappes_regions(country: str) -> list[dict]:
    units = read_units(country)
    fk = units[units.level == 4][["pcode", "adm1", "lon", "lat"]]
    reg = dict(zip(units[units.level == 1].pcode, units[units.level == 1].name))
    c = pd.read_csv(country_data_dir(country) / "external" / "nappes_carte.csv", dtype={"pcode": str})
    p = c.pivot_table(index="pcode", columns="indicateur", values="valeur")
    fk = fk.join(p, on="pcode")
    hd = ROOT / "inputs" / "hydrogeologie"
    g = pd.read_csv(hd / "recharge_t2c.csv")[["lon", "lat", "region", "T2_mmpa"]]
    g = g.merge(pd.read_csv(hd / "recharge_t2l.csv")[["lon", "lat", "T2L_mmpa", "domaine"]], on=["lon", "lat"], how="left")
    g = g.merge(pd.read_csv(hd / "recharge_t2k.csv")[["lon", "lat", "T2K_mmpa"]], on=["lon", "lat"], how="left")
    rows = []
    for code, s in fk.groupby("adm1"):
        nom = reg.get(code, code)
        r = g[g.region == nom]
        dom = r[r.domaine == "dans le domaine"]
        rows.append({
            "region": nom, "fokontany": int(len(s)),
            "niveau_m": round(float(s.niveau_statique_m.median()), 1),
            "niveau_bas80_m": round(float(s.niveau_statique_bas80_m.median()), 1),
            "niveau_haut80_m": round(float(s.niveau_statique_haut80_m.median()), 1),
            "part_extrapolee": round(float(s.niveau_statique_extrapolation.mean()), 2),
            "distance_forage_km": round(float(s.distance_forage_km.median()), 0),
            "recharge_T2": round(float(r.T2_mmpa.median()), 0) if len(r) else None,
            "recharge_T2L": round(float(dom.T2L_mmpa.median()), 0) if len(dom) else None,
            "recharge_T2K": round(float(r.T2K_mmpa.median()), 0) if len(r) else None,
        })
    return sorted(rows, key=lambda x: x["region"])


def atlas(country: str) -> list[dict]:
    t = pd.read_csv(country_data_dir(country) / "external" / "nappes_bassins.csv").sort_values("population", ascending=False).head(15)
    return [{"nom": f"{x.nom} (n° {int(x.bassin)})", "population": int(x.population), "niveau_m": round(float(x.niveau_median_m), 1),
             "recharge_mm": round(float(x.recharge_mm), 0), "bilan": round(float(x.bilan), 3), "classe": x.classe_bilan,
             "fiabilite": x.fiabilite} for x in t.itertuples()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    a = ap.parse_args()
    reg = registre()
    modules = []
    for nom, typ, ids, remarque in MODULES:
        tests = [{"id": i, "question": reg[i][0], "statut": reg[i][1], "resultat": reg[i][2], "classe": classe_statut(reg[i][1])}
                 for i in ids if i in reg]
        modules.append({"module": nom, "type": typ, "tests": tests, "remarque": remarque})
    tests_recharge = [{"id": i, "question": reg[i][0], "statut": reg[i][1], "resultat": reg[i][2], "classe": classe_statut(reg[i][1])}
                      for i in ("R-43", "R-45", "R-46", "R-47", "R-48", "R-49", "R-50", "R-51", "R-52", "R-53", "R-54") if i in reg]
    out = {"genere": dt.date.today().isoformat(),
           "nappes": {"regions": nappes_regions(a.country), "atlas": atlas(a.country), "tests": tests_recharge,
                      "combinaison": combinaison()},
           "preuves": modules,
           "calibrage_saisonnier": "Prévisions de fin de saison par analogues : la fourchette P10-P90 contient l'observation dans 77 % des cas (attendu 80 %) (`hindcast.json`).",
           "manques": ["Population exposée : aucun intervalle n'est encore calculé ; la valeur affichée est une estimation centrale.",
                       "Projections climatiques (CMIP6, 2030 à 2100) : en préparation (`protocole_cmip6.md`)."]}
    write_json(ROOT / "docs" / "data" / a.country / "recherche.json", out)
    print(f"recherche.json : {len(out['nappes']['regions'])} régions, {len(modules)} modules, {len(tests_recharge)} tests de recharge")


if __name__ == "__main__":
    main()
