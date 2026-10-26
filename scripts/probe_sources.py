"""Sonde : trouver les couches du visualiseur NASA des éboulements (portail Earthdata)."""
import json
import re
import traceback

import pandas as pd
import requests

P = "https://gis.earthdata.nasa.gov/portal/sharing/rest/content/items/"
out = []


def get(u, **kw):
    r = requests.get(u, timeout=60, **kw)
    out.append(f"{u[:150]} -> {r.status_code} {len(r.text)} car.")
    return r


try:
    r = get(P + "a7b17eff544a4ce5ae045c32dbb99f7b/data", params={"f": "json"})
    txt = r.text
    urls = sorted(set(re.findall(r'https?://[^"\\ ]+(?:FeatureServer|MapServer)[^"\\ ]*', txt)))
    ids = sorted(set(re.findall(r'"(?:itemId|webmap|id)"\s*:\s*"([0-9a-f]{32})"', txt)))
    out.append("urls de services : " + json.dumps(urls[:20]))
    out.append("ids : " + json.dumps(ids[:20]))
    for i in ids[:6]:
        rr = get(P + i, params={"f": "json"})
        try:
            j = rr.json()
            out.append(f"   {i}: {j.get('type')} | {j.get('title')} | {j.get('url')}")
            if j.get("type") == "Web Map":
                d = get(P + i + "/data", params={"f": "json"}).json()
                def walk(l, depth=0):
                    out.append("   " * (depth + 3) + f"{l.get('title')} | {l.get('url')} | {l.get('itemId')} | {l.get('layerType')}")
                    for k in ("layers", "featureCollection"):
                        v = l.get(k)
                        if isinstance(v, list):
                            for x in v:
                                walk(x, depth + 1)
                for l in d.get("operationalLayers", []):
                    walk(l)
        except Exception as e:
            out.append("   illisible " + str(e))
    cand = [u for u in urls if "COOLR" in u or "andslide" in u]
    out.append("candidats : " + json.dumps(cand))
except Exception:
    out.append(traceback.format_exc())
open("data/_probe.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
