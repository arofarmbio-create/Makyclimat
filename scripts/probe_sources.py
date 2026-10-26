"""Sondage ad hoc (GitHub Actions) : sources d'eau souterraine pour Madagascar."""
import re

import requests

H = {"User-Agent": "Mozilla/5.0 MakyClimat (recherche doctorale)"}
out = []


def get(u, **kw):
    try:
        return requests.get(u, timeout=90, headers=H, **kw)
    except Exception as e:  # noqa: BLE001
        out.append(f"{u}: ERREUR {e}")


r = get("https://www2.bgs.ac.uk/africaGroundwaterAtlas/downloadGIS.html")
if r is not None:
    out.append(f"BGS page -> {r.status_code}")
    for m in re.findall(r'href="([^"]*)"[^>]*>([^<]*adagascar[^<]*)<', r.text):
        out.append(f"   lien Madagascar : {m}")
    zips = re.findall(r'href="([^"]+\.zip)"', r.text)
    out.append(f"   {len(zips)} archives sur la page, exemples : {zips[:4]}")
    out += ["   ~ " + z for z in zips if "adag" in z.lower() or "MDG" in z or "mg" in z.lower().split("/")[-1][:3]]
for u in ["https://data.waterpointdata.org/resource/jwn9-ihcz.json?$select=count(*)&clean_country_name=Madagascar",
          "https://data.waterpointdata.org/resource/jwn9-ihcz.json?$select=count(*)&country_name=Madagascar",
          "https://data.waterpointdata.org/resource/eqje-vguj.json?$select=count(*)&clean_country_name=Madagascar"]:
    r = get(u)
    if r is not None:
        out.append(f"WPDx {u.split('resource/')[1][:60]} -> {r.status_code} {r.text[:200]}")
r = get("https://data.waterpointdata.org/resource/jwn9-ihcz.json?$limit=2&clean_country_name=Madagascar")
if r is not None:
    out.append("WPDx exemple : " + r.text[:900])
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
