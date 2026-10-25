"""Génère le catalogue d'indicateurs du site (secteurs, ODD, cadres nationaux, statut) à partir des fichiers config/."""
from __future__ import annotations

import argparse

from common import country_docs_dir, load_yaml, write_json


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
    write_json(country_docs_dir(args.country) / "catalogue.json",
               {"sectors": sectors, "indicators": inds,
                "sdg": pol["sdg"], "national": pol["madagascar"]})
    print(f"Catalogue écrit : {len(inds)} indicateurs, {len(sectors)} secteurs")


if __name__ == "__main__":
    main()
