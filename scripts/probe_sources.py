"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import io
import sys

import pandas as pd
import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
out = []


def note(msg):
    print(msg)
    out.append(msg)


def pkg_urls(name):
    p = requests.get("https://data.humdata.org/api/3/action/package_show", params={"id": name}, headers=UA, timeout=60).json()["result"]
    return p["resources"]


def head_csv(url, label, n=3, **kw):
    try:
        r = requests.get(url, headers=UA, timeout=180)
        df = pd.read_csv(io.BytesIO(r.content), low_memory=False, **kw)
        note(f"== {label} : {df.shape} colonnes={list(df.columns)}")
        note(df.head(n).to_string(max_colwidth=60)[:2500])
        return df
    except Exception as e:
        note(f"== {label} ECHEC {e}")


try:
    res = pkg_urls("hrp-projects-mdg")
    u = [x["url"] for x in res if x["name"].startswith("fmdg24") and x["format"] == "CSV"][0]
    df = head_csv(u, "HRP projets 2024", skiprows=[1])
except Exception as e:
    note(f"HRP ECHEC {e}")
try:
    res = pkg_urls("iati-mdg")
    for x in res:
        head_csv(x["url"], "IATI " + x["name"][:40])
except Exception as e:
    note(f"IATI ECHEC {e}")
for name in ["mdg-idmc-idu-events", "mdg-glide-events", "idmc-idp-data-mdg", "madagascar-accessibility-indicators", "madagascar---risk-assessment-indicators"]:
    try:
        res = pkg_urls(name)
        note(f"== {name} : " + " | ".join(f"{x['name']} [{x['format']}] {x['url']}" for x in res[:6]))
        csvs = [x for x in res if x["format"].upper() == "CSV"]
        if csvs:
            head_csv(csvs[0]["url"], name + " (csv)", skiprows=[1] if name.startswith("mdg-") else None)
    except Exception as e:
        note(f"== {name} ECHEC {e}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
