"""Liste d'événements indépendants de GloFAS, depuis GDACS (Commission européenne / ONU), pour la validation des crues.

Cahier des charges §4.D (historique des inondations et cyclones), §13 (vérité terrain indépendante, analyse des fausses alertes).
API publique GDACS, sans compte. On ne garde que les sources INDÉPENDANTES du modèle de crue validé :
  - cyclones tropicaux (TC), tous niveaux d'alerte : trajectoires des centres d'alerte cyclonique, pas GloFAS ;
  - inondations (FL) dont la source est DFO (Dartmouth Flood Observatory) ou JRC (avant 2019).
Écartées : les inondations GDACS de source « GLOFAS » (depuis 2019), car valider GloFAS contre GloFAS serait circulaire.
Limites : un cyclone GDACS est daté et attribué au pays, sans région touchée ; il explique un épisode de crue simulé
POSSIBLEMENT, il ne prouve pas une inondation locale. Les inondations non cycloniques récentes restent absentes.
Sortie : validation/evenements_gdacs.csv. Bibliothèque standard seulement (exécutable sans dépendances).
Usage : python scripts/connector_gdacs_events.py [--country Madagascar] [--from 2014-01-01]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import urllib.request
from pathlib import Path

API = ("https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?eventlist=TC;FL&country={country}"
       "&fromDate={start}&toDate={end}&alertlevel=Green;Orange;Red&pageSize=100&pageNumber={page}")
INDEPENDENT_FLOOD_SOURCES = {"DFO", "JRC"}
OUT = Path(__file__).resolve().parent.parent / "validation" / "evenements_gdacs.csv"


def fetch(country: str, start: str, end: str) -> list[dict]:
    feats, page = [], 1
    while True:
        url = API.format(country=country, start=start, end=end, page=page)
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "MakyClimat"}), timeout=120) as r:
            got = json.load(r).get("features", [])
        feats += got
        if len(got) < 100:
            return feats
        page += 1


def keep(p: dict) -> bool:
    return p["eventtype"] == "TC" or (p["eventtype"] == "FL" and str(p.get("source", "")).upper() in INDEPENDENT_FLOOD_SOURCES)


def rows(feats: list[dict]) -> list[dict]:
    out = []
    for f in feats:
        p = f["properties"]
        if not keep(p):
            continue
        c = (f.get("geometry") or {}).get("coordinates") or [None, None]
        out.append({"id": f"gdacs-{p['eventtype'].lower()}-{p['eventid']}", "type": "cyclone" if p["eventtype"] == "TC" else "inondation",
                    "nom": p.get("name", ""), "date_debut": p["fromdate"][:10], "date_fin": p["todate"][:10],
                    "alerte": str(p.get("alertlevel", "")).capitalize(), "source_gdacs": p.get("source", ""),
                    "lon": c[0] if p["eventtype"] == "FL" else "", "lat": c[1] if p["eventtype"] == "FL" else "",
                    "source_url": (p.get("url") or {}).get("report", ""),
                    "remarque": "Pays seulement, région non précisée" if p["eventtype"] == "TC" else "Centre approximatif de l'inondation"})
    return sorted(out, key=lambda r: r["date_debut"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="Madagascar")
    ap.add_argument("--from", dest="start", default="2014-01-01")
    a = ap.parse_args()
    feats = fetch(a.country, a.start, dt.date.today().isoformat())
    rs = rows(feats)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0]) if rs else ["id"])
        w.writeheader()
        w.writerows(rs)
    n_glofas = sum(1 for x in feats if x["properties"]["eventtype"] == "FL" and not keep(x["properties"]))
    print(f"GDACS : {len(feats)} événements, {len(rs)} gardés ({sum(r['type'] == 'cyclone' for r in rs)} cyclones, "
          f"{sum(r['type'] == 'inondation' for r in rs)} inondations DFO/JRC) ; {n_glofas} inondations de source GloFAS écartées")


if __name__ == "__main__":
    main()
