"""Sonde : événements d'éboulement NASA COOLR pour Madagascar (via le portail Earthdata)."""
import traceback

import pandas as pd
import requests

B = "https://gis.earthdata.nasa.gov/portal/rest/services/Landslides/"
out = []


def fetch(layer, name):
    base = B + layer + "/FeatureServer/0"
    r = requests.get(base, params={"f": "json"}, timeout=60)
    out.append(f"{layer} -> {r.status_code}")
    if not r.ok:
        return
    out.append("champs : " + ", ".join(f["name"] for f in r.json().get("fields", [])))
    rows, off = [], 0
    while True:
        q = requests.get(base + "/query", params={"f": "json", "where": "1=1", "geometry": "42,-26,52,-11", "geometryType": "esriGeometryEnvelope",
                         "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "true", "outSR": 4326,
                         "resultOffset": off, "resultRecordCount": 1000}, timeout=120)
        j = q.json()
        feats = j.get("features", [])
        for f in feats:
            a = dict(f["attributes"]); g = f.get("geometry") or {}
            a["lon"], a["lat"] = g.get("x"), g.get("y")
            rows.append(a)
        if len(feats) < 1000:
            break
        off += 1000
    df = pd.DataFrame(rows)
    out.append(f"{name} : {len(df)} dans l'emprise de Madagascar")
    if len(df):
        df.to_csv(f"validation/coolr_{name}_madagascar.csv", index=False)
        out.append(df.head(6).to_string()[:1500])


try:
    fetch("COOLR_Events_Points", "evenements")
    fetch("COOLR_Reports_Points", "rapports")
except Exception:
    out.append(traceback.format_exc())
open("data/_probe.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
