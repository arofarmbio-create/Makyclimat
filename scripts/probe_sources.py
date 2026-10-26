"""Sondage ad hoc (GitHub Actions) : repérer les activations Copernicus EMS qui concernent Madagascar."""
import re
from concurrent.futures import ThreadPoolExecutor

import requests

H = {"User-Agent": "Mozilla/5.0 MakyClimat"}


def look(n):
    code = f"EMSR{n}"
    try:
        r = requests.get(f"https://rapidmapping.emergency.copernicus.eu/{code}/", timeout=40, headers=H)
        if r.status_code != 200:
            return None
        t = r.text
        if "adagascar" not in t:
            return None
        title = re.search(r"<title>\s*(.*?)\s*</title>", t, re.S)
        h1 = re.findall(r"(?:Tropical|Flood|Storm|Cyclone|Landslide)[^<\n]{0,90}", t)[:2]
        links = sorted(set(re.findall(r"https://cems-mapping-website[^\"'\s<>]+_vector\.zip", t)))
        kinds = {}
        for l in links:
            k = re.search(r"_(DEL|GRA|REF)_", l)
            key = k.group(1) if k else "?"
            kinds[key] = kinds.get(key, 0) + 1
        return f"{code} | {title.group(1) if title else ''} | {h1} | zips {kinds}"
    except Exception as e:  # noqa: BLE001
        return f"{code} erreur {e}"


with ThreadPoolExecutor(16) as ex:
    res = [r for r in ex.map(look, range(150, 1100)) if r]
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(res))
print("\n".join(res))
