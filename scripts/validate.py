"""Contrôle qualité AVANT publication. Si un contrôle échoue, le workflow s'arrête et les anciennes données restent en ligne.

Contrôles : fichiers présents, population totale plausible, pas trop d'unités sans donnée de pluie,
valeurs de pluie dans des bornes physiques, données pas trop anciennes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

from common import country_docs_dir, load_config


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--max-age-days", type=int, default=75)
    ap.add_argument("--skip-age", action="store_true", help="Pour les tests avec des données simulées")
    args = ap.parse_args()
    cfg = load_config(args.country)
    base = country_docs_dir(args.country)
    errors = []

    for f in ("meta.json", "index.json", "catalogue.json", "metrics/top.json", "geo/adm1.geojson", "geo/adm2.geojson"):
        if not (base / f).exists():
            errors.append(f"fichier manquant : {f}")
    if errors:
        print("\n".join(errors)); sys.exit(1)

    meta = json.load(open(base / "meta.json", encoding="utf-8"))
    top = json.load(open(base / "metrics" / "top.json", encoding="utf-8"))
    if meta["national"]["pop"] <= 0:
        errors.append("population nationale nulle")
    n_districts = len(top["adm2"])
    nodata = sum(1 for v in top["adm2"].values() if v["l"] == 0)
    if n_districts == 0 or nodata / n_districts > 0.2:
        errors.append(f"{nodata}/{n_districts} districts sans donnée de pluie (> 20 %)")
    for k, v in top["adm2"].items():
        if "pc" in v and not (0 <= v["pc"] <= 1000):
            errors.append(f"% de la normale hors bornes ({k}: {v['pc']})")
        if v["e"] > (v["p"] or 0) + 1:
            errors.append(f"exposés > population ({k})")
        if v["t"] > v["e"] + 1:
            errors.append(f"cibles > exposés ({k})")
    sm, em = cfg["rainfall"]["season_start_month"], cfg["rainfall"]["season_end_month"]
    month = dt.date.today().month
    in_season = (month >= sm or month <= em) if sm > em else (sm <= month <= em)
    if not args.skip_age and in_season:
        through = dt.date.fromisoformat(meta["data_through"])
        age = (dt.date.today() - through).days
        if age > args.max_age_days:
            errors.append(f"données de pluie trop anciennes ({age} jours)")
    if errors:
        print("VALIDATION ÉCHOUÉE :\n- " + "\n- ".join(errors))
        sys.exit(1)
    print(f"Validation OK — {cfg['name']}, pluie jusqu'au {meta['data_through']}, {n_districts} districts.")


if __name__ == "__main__":
    main()
