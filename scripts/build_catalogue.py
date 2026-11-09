"""Génère le catalogue d'indicateurs du site (secteurs, ODD, cadres nationaux, statut) à partir des fichiers config/.

Depuis le 09/11/2026 (principe « le site est la vitrine de la recherche », prompt_maitre.md §0) : chaque indicateur
reçoit aussi son type de résultat, son niveau de preuve (calculé à partir des statuts du registre des méthodes) et son
incertitude, d'après config/indicateurs_preuve.yml.
"""
from __future__ import annotations

import argparse

import re

from common import country_docs_dir, load_yaml, write_json


def niveau(ids: list[str], reg: dict) -> tuple[str, str]:
    """(code, libellé) du niveau de preuve à partir des statuts du registre."""
    st = [reg[i][1] for i in ids if i in reg]
    if not st:
        return "non_evalue", "Non évalué par la thèse"
    if any("✅" in x for x in st):
        return "teste_ok", "Testé : au moins un résultat soutenu"
    if any(("⚠" in x) or ("🟡" in x) for x in st):
        return "teste_partiel", "Testé : résultat partiel ou à confirmer"
    if any(("❌" in x) or ("⬛" in x) for x in st):
        return "teste_non", "Testé : non établi ou négatif"
    return "en_cours", "Test en cours"


def preuves(inds: list[dict]) -> None:
    """Ajoute type, preuve et incertitude à chaque indicateur (première règle qui correspond)."""
    from build_site_recherche import registre
    reg = registre()
    regles = load_yaml("indicateurs_preuve.yml")["regles"]
    for i in inds:
        r = next(x for x in regles if re.search(x["motif"], i["id"]))
        code, lib = niveau(r.get("preuve", []), reg)
        i["type"] = r["type"]
        i["preuve"] = {"niveau": code, "libelle": lib, "tests": [{"id": t, "statut": reg[t][1]} for t in r.get("preuve", []) if t in reg]}
        i["incertitude"] = r.get("incertitude", "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    sectors = load_yaml("sectors.yml")["sectors"]
    inds = load_yaml("indicators.yml")["indicators"]
    pol = load_yaml("policy_frameworks.yml")
    sector_ids = {s["id"] for s in sectors}
    sdg_goals = {str(g["id"]) for g in pol["sdg"]["goals"]}
    nat_ids = {a["id"] for a in pol["madagascar"]["pge_r"]["axes"]} | \
              {p["id"] for p in pol["madagascar"]["priorites_budgetaires_2026"]}
    for i in inds:  # contrôle de cohérence : toute référence doit exister
        for s in i["sectors"]:
            assert s in sector_ids, f"secteur inconnu {s} dans {i['id']}"
        for t in i["sdg"]:
            assert t.split(".")[0] in sdg_goals, f"ODD inconnu {t} dans {i['id']}"
        for n in i.get("national", []):
            assert n in nat_ids, f"cadre national inconnu {n} dans {i['id']}"
    preuves(inds)
    write_json(country_docs_dir(args.country) / "catalogue.json",
               {"sectors": sectors, "indicators": inds,
                "sdg": pol["sdg"], "national": pol["madagascar"]})
    print(f"Catalogue écrit : {len(inds)} indicateurs, {len(sectors)} secteurs")


if __name__ == "__main__":
    main()
