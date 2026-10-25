"""Calendrier cultural : recommandations officielles par région (config/calendrier_cultural.yml) et fenêtres saisies à la main (inputs/calendrier_cultural.csv).

Sortie : docs/data/<pays>/calendrier.json {source, season, general, regions: {pcode_région: [textes]}, windows: {pcode: [{c, o, d0, d1, src}]}}
Fenêtres (CSV facultatif) : pcode (région, district... ou ALL), culture, operation (semis, repiquage, recolte, soudure...), mois_debut, decade_debut (1-3),
mois_fin, decade_fin (1-3), source. Elles s'affichent dans la fiche de la zone, avec la période en cours mise en évidence.
Usage : python scripts/build_calendar.py --country mdg
"""
from __future__ import annotations

import argparse

import pandas as pd

from common import INPUTS_DIR, country_docs_dir, load_yaml, read_units, write_json
from connector_dhs import norm


def build(cfg: dict, units: pd.DataFrame, windows: pd.DataFrame | None = None) -> dict:
    by_name = {norm(n): p for p, n in zip(units[units.level == 1].pcode, units[units.level == 1].name)}
    regions: dict[str, list[str]] = {}
    unknown = set()
    for rule in cfg.get("rules", []):
        for name in rule["regions"]:
            pc = by_name.get(norm(name))
            if pc is None:
                unknown.add(name)
                continue
            if rule["text"] not in regions.setdefault(pc, []):
                regions[pc].append(rule["text"])
    wins: dict[str, list] = {}
    if windows is not None and len(windows):
        valid = set(units.pcode) | {"ALL"}
        for r in windows.itertuples():
            try:
                row = {"c": str(r.culture), "o": str(r.operation), "d0": [int(r.mois_debut), int(r.decade_debut)], "d1": [int(r.mois_fin), int(r.decade_fin)],
                       "src": "" if pd.isna(getattr(r, "source", "")) else str(r.source)}
            except (TypeError, ValueError, AttributeError):
                continue
            if str(r.pcode) in valid and 1 <= row["d0"][0] <= 12 and 1 <= row["d1"][0] <= 12 and row["d0"][1] in (1, 2, 3) and row["d1"][1] in (1, 2, 3):
                wins.setdefault(str(r.pcode), []).append(row)
    return {"season": cfg.get("season", ""), "source": cfg.get("source", {}), "general": cfg.get("general", []), "regions": regions, "windows": wins,
            "unknown_regions": sorted(unknown)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    if args.country != "mdg":
        print("Calendrier cultural : seul Madagascar est configuré.")
        return
    cfg = load_yaml("calendrier_cultural.yml")
    path = INPUTS_DIR / "calendrier_cultural.csv"
    out = build(cfg, read_units(args.country), pd.read_csv(path, dtype={"pcode": str}) if path.exists() else None)
    write_json(country_docs_dir(args.country) / "calendrier.json", out)
    print(f"Calendrier cultural : {len(out['regions'])} régions avec recommandations, {sum(len(v) for v in out['windows'].values())} fenêtres saisies"
          + (f" ; régions inconnues : {out['unknown_regions']}" if out["unknown_regions"] else ""))


if __name__ == "__main__":
    main()
