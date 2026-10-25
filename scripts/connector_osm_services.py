"""Connecteur OpenStreetMap : écoles et formations sanitaires recensées, comptées par fokontany.

Source : OpenStreetMap (© contributeurs OpenStreetMap, licence ODbL) via l'API Overpass, sur la frontière de Madagascar.
Indicateurs (nombre, par fokontany ; les communes, districts et régions en font la somme) :
  osm_ecoles      écoles, collèges, lycées, maternelles et universités (amenity = school, kindergarten, college, university)
  osm_sante       formations sanitaires (amenity = hospital, clinic, doctors ; healthcare = hospital, clinic, centre, doctor)
  osm_hopitaux    dont hôpitaux (amenity ou healthcare = hospital)
Limite essentielle : ce sont des comptes MINIMAUX. OpenStreetMap n'est pas un recensement ; en zone rurale beaucoup d'écoles et de CSB
ne sont pas encore cartographiés. Un zéro veut dire « rien de cartographié », pas « aucun service ». À utiliser pour repérer les
services connus et comparer à une liste officielle, pas pour conclure à un manque.
Sortie : data/<pays>/external/osm_services.csv (pcode, indicateur, valeur, date, source) ; cache de 7 jours.
Usage : python scripts/connector_osm_services.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time

import pandas as pd
import requests

from common import country_data_dir, country_docs_dir, read_units

SOURCE = "© contributeurs OpenStreetMap (ODbL), via Overpass : comptes minimaux, pas un recensement"
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
QUERY = """[out:json][timeout:600];
area["ISO3166-1"="MG"][admin_level=2]->.a;
(
  nwr["amenity"~"^(school|kindergarten|college|university)$"](area.a);
  nwr["amenity"~"^(hospital|clinic|doctors)$"](area.a);
  nwr["healthcare"~"^(hospital|clinic|centre|doctor)$"](area.a);
);
out center tags;"""
EDU = {"school", "kindergarten", "college", "university"}
HEALTH_AMENITY = {"hospital", "clinic", "doctors"}
HEALTH_HC = {"hospital", "clinic", "centre", "doctor"}


def fetch() -> list[dict]:
    last = None
    for attempt in range(3):
        for url in MIRRORS:
            try:
                r = requests.post(url, data={"data": QUERY}, timeout=700, headers={"User-Agent": "MakyClimat (recherche doctorale)"})
                if r.status_code == 200:
                    return r.json()["elements"]
                last = f"{url} : HTTP {r.status_code}"
            except Exception as e:  # réseau, délai, JSON tronqué
                last = f"{url} : {e}"
        time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"Overpass indisponible ({last})")


def classify(elements: list[dict]) -> pd.DataFrame:
    """Une ligne par service (kind: edu / sante, hopital: bool, lon, lat), sans doublons (même nom à moins de ~100 m)."""
    rows, seen = [], set()
    for e in elements:
        t = e.get("tags", {})
        lon = e.get("lon", (e.get("center") or {}).get("lon"))
        lat = e.get("lat", (e.get("center") or {}).get("lat"))
        if lon is None or lat is None:
            continue
        am, hc = t.get("amenity"), t.get("healthcare")
        if am in EDU:
            kind, hosp = "edu", False
        elif am in HEALTH_AMENITY or hc in HEALTH_HC:
            kind, hosp = "sante", (am == "hospital" or hc == "hospital")
        else:
            continue
        key = (kind, (t.get("name") or "").strip().lower(), round(lon, 3), round(lat, 3))
        if t.get("name") and key in seen:
            continue
        seen.add(key)
        rows.append((kind, hosp, float(lon), float(lat)))
    return pd.DataFrame(rows, columns=["kind", "hopital", "lon", "lat"])


def count_by_unit(points: pd.DataFrame, geoms: dict) -> pd.DataFrame:
    """Compte les services dans chaque fokontany (point dans polygone, via STRtree)."""
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    codes = list(geoms.keys())
    tree = STRtree([geoms[c] for c in codes])
    out = {c: [0, 0, 0] for c in codes}
    for kind, hosp, lon, lat in points.itertuples(index=False):
        p = Point(lon, lat)
        for i in tree.query(p, predicate="intersects"):
            c = codes[int(i)]
            if kind == "edu":
                out[c][0] += 1
            else:
                out[c][1] += 1
                out[c][2] += int(hosp)
            break
    return pd.DataFrame.from_dict(out, orient="index", columns=["osm_ecoles", "osm_sante", "osm_hopitaux"])


def to_rows(counts: pd.DataFrame) -> pd.DataFrame:
    long = counts.rename_axis("pcode").reset_index().melt(id_vars="pcode", var_name="indicateur", value_name="valeur")
    long["date"] = dt.date.today().isoformat()
    long["source"] = SOURCE
    return long


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.country != "mdg":
        print("Connecteur OpenStreetMap services : seul Madagascar est configuré.")
        return
    out = country_data_dir(args.country) / "external" / "osm_services.csv"
    if out.exists() and not args.force and time.time() - out.stat().st_mtime < 7 * 86400:
        print("OpenStreetMap services : fichier de moins de 7 jours, conservé.")
        return
    from shapely.geometry import shape
    geoms = {}
    for f in sorted((country_docs_dir(args.country) / "geo" / "adm4").glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            geoms[ft["properties"]["c"]] = shape(ft["geometry"])
    pts = classify(fetch())
    counts = count_by_unit(pts, geoms)
    out.parent.mkdir(parents=True, exist_ok=True)
    to_rows(counts).to_csv(out, index=False)
    print(f"OpenStreetMap : {(pts.kind == 'edu').sum()} écoles, {(pts.kind == 'sante').sum()} formations sanitaires cartographiées ; "
          f"{int((counts.osm_ecoles > 0).sum())} fokontany avec école, {int((counts.osm_sante > 0).sum())} avec formation sanitaire")


if __name__ == "__main__":
    main()
