"""Vérifie depuis GitHub Actions quelles sources de données sont joignables et ce qu'elles contiennent (résultat en annotations)."""
import json
import sys

import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def note(msg):
    print(msg)
    print("::notice::" + msg.replace("\n", " ")[:900])


def get_range(url, extra=None):
    h = dict(UA, Range="bytes=0-1023")
    h.update(extra or {})
    try:
        r = requests.get(url, headers=h, timeout=60, allow_redirects=True, stream=True)
        note(f"GET {url[-60:]} -> {r.status_code} total={r.headers.get('content-range') or r.headers.get('content-length')} type={r.headers.get('content-type')}")
    except Exception as e:
        note(f"GET {url[-60:]} ECHEC {e}")


for u in ["https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af_shp.zip",
          "https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_af_lev06_v1c.zip",
          "https://www.hydrosheds.org/products/hydrorivers",
          "https://zenodo.org/api/records?q=HydroRIVERS&size=3",
          "https://overpass-api.de/api/status",
          "https://source.coop/",
          "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_rivers_lake_centerlines.zip"]:
    get_range(u, {"Referer": "https://www.hydrosheds.org/"} if "hydrosheds" in u else None)

for q in ["hydrosheds madagascar", "madagascar rivers", "madagascar watershed basins", "madagascar groundwater boreholes", "madagascar flood extent historical", "madagascar cyclone track affected"]:
    try:
        r = requests.get("https://data.humdata.org/api/3/action/package_search", params={"q": q, "rows": 6}, headers=UA, timeout=60)
        res = r.json()["result"]
        note(f"HDX '{q}' : {res['count']} : " + " | ".join(f"{p['name']}" for p in res["results"][:6]))
    except Exception as e:
        note(f"HDX '{q}' ECHEC {e}")

for name in ["hrp-projects-mdg", "iati-mdg"]:
    try:
        r = requests.get("https://data.humdata.org/api/3/action/package_show", params={"id": name}, headers=UA, timeout=60)
        p = r.json()["result"]
        note(f"HDX {name} : " + " | ".join(f"{x['name']} [{x['format']}] {x['url'][-70:]}" for x in p["resources"][:6]))
    except Exception as e:
        note(f"HDX {name} ECHEC {e}")

try:
    r = requests.get("https://api.hpc.tools/v1/public/fts/flow", params={"countryISO3": "MDG", "year": 2022, "limit": 1, "groupby": "cluster"}, headers=UA, timeout=60)
    note("FTS cluster : " + r.text[:400])
except Exception as e:
    note(f"FTS ECHEC {e}")
for u in ["https://api.reliefweb.int/v1/reports?appname=makyclimat&limit=1", "https://reliefweb.int/api/v1/disasters?appname=rwint-user-0&limit=1"]:
    try:
        r = requests.get(u, headers=UA, timeout=60)
        note(f"ReliefWeb {u[:50]} -> {r.status_code} {r.text[:150]!r}")
    except Exception as e:
        note(f"ReliefWeb ECHEC {e}")
sys.exit(0)
