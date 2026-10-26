"""Sonde : événements d'éboulement NASA COOLR pour Madagascar."""
import traceback
import requests
import pandas as pd

out = []
cands = ["https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides?f=json",
         "https://gis.earthdata.nasa.gov/gis05/rest/services?f=json",
         "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/FeatureServer?f=json",
         "https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Points/MapServer?f=json",
         "https://maps.nccs.nasa.gov/arcgis/rest/services?f=json",
         "https://maps.nccs.nasa.gov/mapping/rest/services/COOLR?f=json",
         "https://data.humdata.org/api/3/action/package_search?q=landslide%20madagascar&rows=10",
         "https://data.humdata.org/api/3/action/package_search?q=desinventar%20madagascar&rows=10"]
try:
    base = None
    for c in cands:
        try:
            rr = requests.get(c, timeout=40)
            out.append(f"{c} -> {rr.status_code} {rr.text[:700]!r}")
            if rr.ok and '"fields"' in rr.text and base is None:
                base = c
        except Exception as e:
            out.append(f"{c} -> erreur {e}")
    if base:
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
        out.append(f"adresse retenue : {base} ; événements dans l'emprise : {len(df)}")
        if len(df):
            df.to_csv("validation/coolr_madagascar_brut.csv", index=False)
            out.append(df.head(8).to_string())
except Exception:
    out.append(traceback.format_exc())
open("data/_probe.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
