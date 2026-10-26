"""Sondage ad hoc (GitHub Actions) : vérifier ce qui est réellement en ligne sur le site publié."""
import json
import re

import requests

B = "https://arofarmbio-create.github.io/Makyclimat/"
out = []


def get(path):
    try:
        r = requests.get(B + path, timeout=60, headers={"Cache-Control": "no-cache"})
        return r
    except Exception as e:  # noqa: BLE001
        out.append(f"{path}: ERREUR {e}")


for p in ["", "data/mdg/calendrier.json", "data/mdg/validation.json", "data/mdg/seasonal.json", "data/mdg/cyclones.json", "data/mdg/index.json",
          "data/mdg/response.json", "data/catalogue.json", "data/mdg/catalogue.json", "data/mdg/hydro/meta.json"]:
    r = get(p)
    if r is not None:
        out.append(f"{p or '/'} -> {r.status_code} {len(r.content)} octets")
        if r.status_code == 200 and p == "":
            out.append("   Cyclones passés: " + str("cycsrc" in r.text) + " ; Prévision saisonnière: " + str("seas" in r.text))
for p in ["data/mdg/catalogue.json", "data/catalogue.json"]:
    r = get(p)
    if r is not None and r.status_code == 200:
        t = r.text
        for k in ["susc_inond_pct", "crue_rp100_ecoles_pct", "dhs_", "osm_ecoles", "cyc_nb_100km", "seas_anom_pct", "hapi", "ipc"]:
            out.append(f"   catalogue contient {k}: {k in t}")
r = get("data/mdg/index.json")
if r is not None and r.status_code == 200:
    out.append("   index.json début: " + r.text[:300])
r = get("app.js")
if r is not None and r.status_code == 200:
    out.append(f"app.js: calendarSection={'calendarSection' in r.text}, setupSeasonal={'setupSeasonal' in r.text}, setupCyclones={'setupCyclones' in r.text}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
