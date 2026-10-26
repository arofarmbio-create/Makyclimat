"""Sondage ad hoc des sources (exécuté par GitHub Actions) : pages Copernicus EMS pour les cyclones de Madagascar."""
import re
import requests

URLS = [
    "https://emergency.copernicus.eu/mapping/list-of-components/EMSR564",
    "https://emergency.copernicus.eu/mapping/list-of-components/EMSR565",
    "https://emergency.copernicus.eu/EMSR564",
    "https://mapping.emergency.copernicus.eu/activations/EMSR564/",
    "https://data.jrc.ec.europa.eu/dataset/a2de6b9f-5d90-458d-9e5c-7fda53a94703",
    "https://data.jrc.ec.europa.eu/api/3/action/package_show?id=a2de6b9f-5d90-458d-9e5c-7fda53a94703",
    "https://rapidmapping.emergency.copernicus.eu/EMSR564/",
]
out = []
for u in URLS:
    try:
        r = requests.get(u, timeout=60, headers={"User-Agent": "Mozilla/5.0 MakyClimat"})
        t = r.text
        out.append(f"== {u} -> {r.status_code} {len(t)} octets")
        links = sorted(set(re.findall(r'https?://[^"\'\s<>]+\.(?:zip|shp|geojson|json)[^"\'\s<>]*', t)))
        out += ["   " + l for l in links[:40]]
        for l in sorted(set(re.findall(r'https?://[^"\'\s<>]*(?:download|backend|rapidmapping)[^"\'\s<>]*', t)))[:25]:
            out.append("   ~ " + l)
        out.append("   debut: " + re.sub(r"\s+", " ", t[:300]))
    except Exception as e:  # noqa: BLE001
        out.append(f"== {u} -> ERREUR {e}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
