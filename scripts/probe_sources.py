"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import json
import sys

import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
out = []


def note(msg):
    print(msg)
    out.append(msg)


def pkg(name):
    try:
        p = requests.get("https://data.humdata.org/api/3/action/package_show", params={"id": name}, headers=UA, timeout=60).json()["result"]
        note(f"== {name} | maj {p.get('last_modified','')[:10]} | licence {p.get('license_title')} | {p.get('title')}")
        for x in p["resources"]:
            note(f"   - {x['name']} [{x['format']}] {x.get('size')} {x['url']}")
    except Exception as e:
        note(f"== {name} ECHEC {e}")


for n in ["hrp-projects-mdg", "iati-mdg", "hotosm_mdg_waterways", "mdg-ibtracs-tropical-storm-tracks", "cod-ab-mdg"]:
    pkg(n)

for u, label in [("https://api.hpc.tools/v1/public/fts/flow?countryISO3=MDG&year=2022&limit=2&groupby=cluster", "FTS cluster"),
                 ("https://api.hpc.tools/v1/public/fts/flow?countryISO3=MDG&year=2022&limit=2", "FTS flow"),
                 ("https://api.hpc.tools/v2/public/plan/country/MDG", "plans")]:
    try:
        r = requests.get(u, headers=UA, timeout=60)
        note(f"== {label} {r.status_code} {r.text[:1500]}")
    except Exception as e:
        note(f"== {label} ECHEC {e}")

for q in ["madagascar cyclone", "madagascar floods", "madagascar drought", "madagascar displaced idp", "madagascar cholera", "madagascar food security ipc"]:
    try:
        res = requests.get("https://data.humdata.org/api/3/action/package_search", params={"q": q, "rows": 8}, headers=UA, timeout=60).json()["result"]
        note(f"== HDX '{q}' ({res['count']}) : " + " | ".join(p["name"] for p in res["results"]))
    except Exception as e:
        note(f"== HDX '{q}' ECHEC {e}")

for u in ["https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_S20_00_E047_00_DEM/Copernicus_DSM_COG_30_S20_00_E047_00_DEM.tif",
          "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S20_00_E047_00_DEM/Copernicus_DSM_COG_10_S20_00_E047_00_DEM.tif",
          "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S21E045_Map.tif"]:
    try:
        r = requests.get(u, headers=dict(UA, Range="bytes=0-1023"), timeout=60, stream=True)
        note(f"== GET {u[-55:]} -> {r.status_code} {r.headers.get('content-range')}")
    except Exception as e:
        note(f"== GET {u[-55:]} ECHEC {e}")

open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
