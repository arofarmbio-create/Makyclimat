"""Connecteur ONU/OCHA : HDX HAPI (Humanitarian API) — sécurité alimentaire IPC et pauvreté.

Sortie : data/<pays>/external/hapi.csv au format standard (pcode, indicateur, valeur, date, source), lu ensuite par
compute_metrics.py. L'IPC phase 3+ remplace automatiquement la part vulnérable par défaut dans les zones analysées.

Authentification : HAPI n'exige pas de compte. Le connecteur génère lui-même son « app identifier » à chaque
exécution via le point de terminaison officiel /encode_app_identifier (gratuit, public, pas d'inscription ni de
clé à gérer) — voir docs.humdata.org/build/hdx-apis/hapi/api-reference/generate-app-identifier. Une variable
d'environnement HAPI_APP_IDENTIFIER reste possible pour forcer un identifiant précis, mais n'est plus nécessaire :
un identifiant codé à la main (ancien secret GitHub du même nom) causait un 403 Forbidden, probablement mal formé —
la génération via l'API officielle est la méthode documentée et fiable.

Important (vie privée) : l'app identifier encode l'adresse e-mail fournie ci-dessous en base64 (réversible). Ne
jamais journaliser l'URL complète d'une requête HAPI (elle contient ce paramètre) — voir fetch_all().

Usage : python scripts/connector_hapi.py --country mdg
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
APP_NAME = "makyclimat"
APP_EMAIL = "arofarmbio@gmail.com"


def get_app_identifier() -> str:
    """Identifiant d'appli HAPI : variable d'environnement si fournie, sinon généré à la volée via l'API officielle."""
    override = os.environ.get("HAPI_APP_IDENTIFIER", "").strip()
    if override:
        return override
    r = requests.get(BASE + "/encode_app_identifier", params={"application": APP_NAME, "email": APP_EMAIL}, timeout=30)
    r.raise_for_status()
    return r.json()["encoded_app_identifier"]


def fetch_all(path: str, params: dict, app_id: str, page: int = 10000) -> list[dict]:
    rows, offset = [], 0
    while True:
        q = dict(params, app_identifier=app_id, limit=page, offset=offset, output_format="json")
        r = requests.get(BASE + path, params=q, timeout=120)
        if not r.ok:
            # Ne jamais relancer l'exception brute : r.raise_for_status() inclurait l'URL complète,
            # donc l'app_identifier (e-mail encodé en base64, réversible), dans un message qui peut finir
            # journalisé ou commité. On reconstruit un message sans ce paramètre.
            raise RuntimeError(f"HAPI : HTTP {r.status_code} sur {path} (voir la doc HAPI pour le dépannage)")
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
    try:
        app_id = get_app_identifier()
    except Exception as exc:
        print(f"HAPI : impossible d'obtenir un app_identifier ({type(exc).__name__}) : connecteur ignoré.")
        sys.exit(0)
    cfg = load_config(args.country)
    iso = cfg["iso3"]
    known = set(read_units(args.country).pcode)
    out_rows = []

    try:
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
    except RuntimeError as exc:
        print(str(exc))
        print("HAPI indisponible pour cette exécution : indicateurs externes non mis à jour (sortie propre).")
        sys.exit(0)

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
