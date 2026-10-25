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


BASE = "https://hot.storage.heigit.org/heigit-hdx-public/risk_assessment_inputs/mdg/"
for f in ["MDG_ADM2_access.csv", "MDG_ADM2_vulnerability.csv", "MDG_ADM2_coping.csv", "MDG_ADM2_cyclone_exposure.csv", "MDG_ADM2_demographics.csv"]:
    try:
        r = requests.get(BASE + f, headers=UA, timeout=120)
        df = pd.read_csv(io.BytesIO(r.content))
        note(f"== {f} HTTP {r.status_code} {df.shape}")
        note("   colonnes : " + ", ".join(df.columns))
        note(df.head(3).T.head(40).to_string(max_colwidth=30))
    except Exception as e:
        note(f"== {f} ECHEC {type(e).__name__}: {str(e)[:200]}")
try:
    r = requests.get("https://data.humdata.org/api/3/action/package_show", params={"id": "madagascar---risk-assessment-indicators"}, headers=UA, timeout=60).json()["result"]
    note("== ressources : " + " | ".join(f"{x['name']}" for x in r["resources"]))
    note("   notes : " + (r.get("notes") or "")[:1200])
except Exception as e:
    note(f"== package ECHEC {e}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
