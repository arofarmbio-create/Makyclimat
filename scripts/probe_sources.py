"""Sonde : événements d'éboulement NASA COOLR pour Madagascar."""
import json, requests, pandas as pd
base = "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer/0"
out = []
r = requests.get(base, params={"f": "json"}, timeout=60)
out.append(f"couche -> {r.status_code}")
try:
    fields = [f["name"] for f in r.json()["fields"]]
    out.append("champs : " + ", ".join(fields))
except Exception as e:
    out.append("champs illisibles " + str(e)); fields = []
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
    if len(feats) < 1000 or not j.get("exceededTransferLimit", False) and len(feats) == 0:
        break
    off += 1000
df = pd.DataFrame(rows)
out.append(f"événements dans l'emprise : {len(df)}")
if len(df):
    df.to_csv("validation/coolr_madagascar_brut.csv", index=False)
    out.append(df.head(8).to_string())
open("data/_probe.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
