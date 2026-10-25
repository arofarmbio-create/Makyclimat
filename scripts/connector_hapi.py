"""Connecteur ONU/OCHA : HDX HAPI (Humanitarian API) — sécurité alimentaire IPC et pauvreté.

Sortie : data/<pays>/external/hapi.csv au format standard (pcode, indicateur, valeur, date, source), lu ensuite par
compute_metrics.py. L'IPC phase 3+ remplace automatiquement la part vulnérable par défaut dans les zones analysées.

Authentification : HAPI n'exige pas de compte, seulement un « app identifier » (nom d'application + e-mail encodés),
gratuit, à générer dans la documentation interactive de HAPI. Le passer dans la variable d'environnement
HAPI_APP_IDENTIFIER (secret GitHub du même nom). Sans identifiant, le connecteur ne fait rien (sortie propre).

Usage : HAPI_APP_IDENTIFIER=... python scripts/connector_hapi.py --country mdg
Points d'accès et champs vérifiés dans la documentation HAPI v2 ; à confirmer au premier lancement réel.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

import requests

from common import country_data_dir, load_config, read_units

BASE = "https://hapi.humdata.org/api/v2"
FOOD_SECURITY = "/food-security-nutrition-poverty/food-security"
POVERTY = "/food-security-nutrition-poverty/poverty-rate"


def fetch_all(path: str, params: dict, app_id: str, page: int = 10000) -> list[dict]:
    rows, offset = [], 0
    while True:
        q = dict(params, app_identifier=app_id, limit=page, offset=offset, output_format="json")
        r = requests.get(BASE + path, params=q, timeout=120)
        r.raise_for_status()
        data = r.json().get("data", [])
        rows.extend(data)
        if len(data) < page:
            return rows
        offset += page


def pcode_of(row: dict) -> str | None:
    """Code de la zone : admin2 si la ligne est de niveau 2, sinon admin1."""
    lvl = str(row.get("admin_level", ""))
    if lvl == "2" and row.get("admin2_code"):
        return str(row["admin2_code"])
    if row.get("admin1_code"):
        return str(row["admin1_code"])
    return None


def latest_per_zone(rows: list[dict]) -> dict[str, dict]:
    best: dict[str, dict] = {}
    for r in rows:
        pc = pcode_of(r)
        if not pc:
            continue
        key = str(r.get("reference_period_end") or r.get("reference_period_start") or "")
        if pc not in best or key > best[pc]["_k"]:
            best[pc] = dict(r, _k=key)
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    app_id = os.environ.get("HAPI_APP_IDENTIFIER", "").strip()
    if not app_id:
        print("HAPI_APP_IDENTIFIER absent : connecteur HAPI ignoré (voir README).")
        sys.exit(0)
    cfg = load_config(args.country)
    iso = cfg["iso3"]
    known = set(read_units(args.country).pcode)
    out_rows = []

    # IPC : part de la population en phase 3 ou plus, analyse actuelle
    ipc = fetch_all(FOOD_SECURITY, {"location_code": iso, "ipc_phase": "3+", "ipc_type": "current"}, app_id)
    for pc, r in latest_per_zone(ipc).items():
        frac = r.get("population_fraction_in_phase")
        pop = r.get("population_in_phase")
        src = f"IPC via HAPI ({r.get('resource_hdx_id', '')})"
        date = str(r.get("reference_period_end") or "")[:10]
        if frac is not None:
            out_rows.append((pc, "ipc_phase3plus_pct", round(float(frac) * 100, 2), date, src))
        if pop is not None:
            out_rows.append((pc, "ipc_phase3plus_pop", int(float(pop)), date, src))

    # Pauvreté multidimensionnelle (niveau région) : part de la population en situation de pauvreté
    pov = fetch_all(POVERTY, {"location_code": iso}, app_id)
    for pc, r in latest_per_zone(pov).items():
        if r.get("headcount_ratio") is not None:
            out_rows.append((pc, "poverty_headcount", round(float(r["headcount_ratio"]), 2),
                             str(r.get("reference_period_end") or "")[:10], f"MPI via HAPI ({r.get('resource_hdx_id', '')})"))

    matched = [r for r in out_rows if r[0] in known]
    print(f"HAPI : {len(out_rows)} valeurs, dont {len(matched)} reconnues dans nos limites "
          f"({(100 * len(matched) / len(out_rows)) if out_rows else 0:.0f} %)")
    if out_rows and len(matched) < 0.5 * len(out_rows):
        print("ATTENTION : moins de la moitié des codes HAPI correspondent aux pcodes des limites OCHA : vérifier.")
    dest = country_data_dir(args.country) / "external"
    dest.mkdir(parents=True, exist_ok=True)
    with open(dest / "hapi.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pcode", "indicateur", "valeur", "date", "source"])
        w.writerows(out_rows)
    print("Écrit :", dest / "hapi.csv")


if __name__ == "__main__":
    main()
