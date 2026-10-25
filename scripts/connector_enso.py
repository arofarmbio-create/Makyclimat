"""Connecteur ENSO : télécharge l'indice ONI (NOAA) vers data/enso/oni.csv.

Sources essayées dans l'ordre (gratuites, sans compte) : NOAA CPC puis NOAA PSL.
Usage : python scripts/connector_enso.py
"""
from __future__ import annotations

import sys

import requests

import enso
from common import DATA_DIR

SOURCES = [("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", enso.parse_cpc),
           ("https://psl.noaa.gov/data/correlation/oni.data", enso.parse_psl)]


def main() -> None:
    for url, parser in SOURCES:
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            df = parser(r.text)
            if len(df) > 500:  # depuis 1950 : ~900 trimestres
                dest = DATA_DIR / "enso" / "oni.csv"
                dest.parent.mkdir(parents=True, exist_ok=True)
                df.sort_values(["year", "center_month"]).to_csv(dest, index=False)
                print(f"ONI : {len(df)} trimestres, dernier : {enso.latest(df)} (source {url})")
                return
            print(f"ONI : réponse trop courte ({len(df)} lignes) depuis {url}")
        except Exception as e:  # noqa: BLE001
            print(f"ONI : échec {url} : {e}")
    print("ONI indisponible : les indicateurs ENSO ne seront pas mis à jour.")
    sys.exit(1)


if __name__ == "__main__":
    main()
