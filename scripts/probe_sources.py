"""Sondage de sources depuis GitHub Actions : le résultat est écrit dans data/_probe.txt (lisible dans le dépôt)."""
import sys

import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
out = []


def note(msg):
    print(msg)
    out.append(str(msg))


def hdx_search(q, rows=10):
    try:
        r = requests.get("https://data.humdata.org/api/3/action/package_search", params={"q": q, "rows": rows}, headers=UA, timeout=90)
        res = r.json()["result"]
        note(f"== HDX « {q} » : {res['count']} jeux")
        for p in res["results"]:
            note(f"  - {p['name']} | {p['title'][:80]} | maj {p.get('metadata_modified','')[:10]} | org {p.get('organization',{}).get('name','')}")
            for x in p["resources"][:6]:
                note(f"      {x['format']:6} {x['name'][:70]} {x['url'][:110]}")
    except Exception as e:
        note(f"== HDX « {q} » ECHEC {type(e).__name__}: {str(e)[:200]}")


for q in ["Madagascar displacement tracking matrix", "Madagascar IOM DTM", "Madagascar population movement", "Madagascar internally displaced persons",
          "Madagascar population density high resolution", "worldpop Madagascar population counts"]:
    hdx_search(q)
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
sys.exit(0)
