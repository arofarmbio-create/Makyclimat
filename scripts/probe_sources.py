"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import io
import sys

import pandas as pd
import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
out = []


def note(msg):
    print(msg)
    out.append(str(msg))


try:
    r = requests.get("https://data.humdata.org/api/3/action/package_show", params={"id": "madagascar---risk-assessment-indicators"}, headers=UA, timeout=60).json()["result"]
    note("== notes complètes :\n" + (r.get("notes") or "")[:6000])
    note("   méthodologie : " + (r.get("methodology_other") or "")[:1500] + " | caveats: " + (r.get("caveats") or "")[:1500])
except Exception as e:
    note(f"== package ECHEC {e}")
BASE = "https://hot.storage.heigit.org/heigit-hdx-public/risk_assessment_inputs/mdg/"
for f in ["MDG_ADM2_flood_exposure.csv", "MDG_ADM2_facilities.csv", "MDG_ADM2_evacuability.csv", "MDG_ADM2_rural_population.csv"]:
    try:
        r = requests.get(BASE + f, headers=UA, timeout=120)
        df = pd.read_csv(io.BytesIO(r.content))
        note(f"== {f} HTTP {r.status_code} {df.shape}")
        note("   colonnes : " + ", ".join(df.columns))
        note(df.head(3).T.head(30).to_string(max_colwidth=30))
    except Exception as e:
        note(f"== {f} ECHEC {type(e).__name__}: {str(e)[:200]}")
# IOM DTM Madagascar (API) : colonnes et valeurs
try:
    pk = requests.get("https://data.humdata.org/api/3/action/package_show", params={"id": "mdg-iom-dtm-from-api"}, headers=UA, timeout=60).json()["result"]
    note("== DTM notes : " + (pk.get("notes") or "")[:1500])
    for x in pk["resources"]:
        note(f"   ressource {x['format']} {x['name']} {x['url']}")
    u = [x["url"] for x in pk["resources"] if x["format"].upper() == "CSV"][0]
    df = pd.read_csv(io.BytesIO(requests.get(u, headers=UA, timeout=180).content), skiprows=[1], low_memory=False)
    note(f"== DTM CSV {df.shape} colonnes : {list(df.columns)}")
    note(df.head(6).T.to_string(max_colwidth=40)[:3000])
    for c in df.columns:
        if df[c].nunique() < 15:
            note(f"   {c}: {df[c].value_counts().head(12).to_dict()}")
except Exception as e:
    note(f"== DTM ECHEC {type(e).__name__}: {str(e)[:300]}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
