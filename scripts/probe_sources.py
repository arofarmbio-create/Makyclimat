"""Vérifie depuis GitHub Actions quelles sources de données sont joignables et ce qu'elles contiennent (résultat en annotations)."""
import json
import sys

import requests

H = {"User-Agent": "makyclimat-probe/1.0"}


def note(msg):
    print(msg)
    print("::notice::" + msg.replace("\n", " ")[:900])


def head(url):
    try:
        r = requests.head(url, headers=H, timeout=60, allow_redirects=True)
        note(f"HEAD {url.split('/')[-1]} -> {r.status_code} taille={r.headers.get('content-length')}")
    except Exception as e:
        note(f"HEAD {url} ECHEC {e}")


for u in ["https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af_shp.zip",
          "https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_af_lev06_v1c.zip",
          "https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_af_lev07_v1c.zip",
          "https://data.hydrosheds.org/file/HydroLAKES/HydroLAKES_polys_v10_shp.zip"]:
    head(u)

for q in ["madagascar 3W", "madagascar operational presence", "madagascar who does what where", "madagascar humanitarian response cluster"]:
    try:
        r = requests.get("https://data.humdata.org/api/3/action/package_search", params={"q": q, "rows": 8}, headers=H, timeout=60)
        res = r.json()["result"]
        note(f"HDX '{q}' : {res['count']} résultats : " + " | ".join(f"{p['name']} ({p.get('last_modified','')[:10]})" for p in res["results"][:8]))
    except Exception as e:
        note(f"HDX '{q}' ECHEC {e}")

for url in ["https://api.hpc.tools/v1/public/fts/flow?countryISO3=MDG&year=2022&limit=1",
            "https://api.hpc.tools/v2/public/plan/country/MDG",
            "https://api.reliefweb.int/v1/disasters?appname=makyclimat&filter[field]=country.iso3&filter[value]=MDG&limit=1&fields[include][]=name&fields[include][]=date",
            "https://api.reliefweb.int/v2/disasters?appname=makyclimat&filter[field]=country.iso3&filter[value]=MDG&limit=1"]:
    try:
        r = requests.get(url, headers=H, timeout=60)
        note(f"{url[:70]} -> {r.status_code} {r.text[:200]!r}")
    except Exception as e:
        note(f"{url[:70]} ECHEC {e}")
sys.exit(0)
