"""Sondage ad hoc (GitHub Actions) : activations Copernicus EMS pour Madagascar et structure des fichiers vectoriels."""
import io
import json
import re
import zipfile

import requests

H = {"User-Agent": "Mozilla/5.0 MakyClimat"}
out = []
seen = {}
for q in ["Madagascar cyclone", "Madagascar flood", "Madagascar storm", "Madagascar tropical"]:
    for start in (0, 100):
        try:
            r = requests.get("https://data.jrc.ec.europa.eu/api/3/action/package_search", params={"q": q, "rows": 100, "start": start}, timeout=60, headers=H)
            for p in r.json()["result"]["results"]:
                seen[p["id"]] = p["title"]
        except Exception as e:  # noqa: BLE001
            out.append(f"recherche '{q}' erreur {e}")
mada = {i: t for i, t in seen.items() if "adagascar" in t}
out.append(f"{len(mada)} jeux de données Madagascar")
codes = {}
for i, t in sorted(mada.items(), key=lambda x: x[1]):
    try:
        r = requests.get("https://data.jrc.ec.europa.eu/api/3/action/package_show", params={"id": i}, timeout=60, headers=H).json()["result"]
        txt = json.dumps(r)
        m = re.findall(r"EMSR\d+", txt)
        code = m[0] if m else "?"
        codes[code] = t
        out.append(f"{code} | {t} | {r.get('metadata_created', '')[:10]}")
    except Exception as e:  # noqa: BLE001
        out.append(f"{t}: erreur {e}")
for code in [c for c in codes if c != "?"]:
    try:
        t = requests.get(f"https://rapidmapping.emergency.copernicus.eu/{code}/", timeout=60, headers=H).text
        links = sorted(set(re.findall(r"https://cems-mapping-website[^\"'\s<>]+_vector\.zip", t)))
        out.append(f"{code}: {len(links)} archives vectorielles : " + ", ".join(l.split('/')[-1].replace(code + '_', '').replace('_vector.zip', '') for l in links))
    except Exception as e:  # noqa: BLE001
        out.append(f"{code}: erreur {e}")
# structure d'une archive de dégradation (bâtiments) et d'une de délimitation (inondation)
for name in ["EMSR564_AOI05_GRA_PRODUCT_r1_RTP01_v2", "EMSR564_AOI01_DEL_PRODUCT_r1_RTP01_v1"]:
    try:
        b = requests.get(f"https://cems-mapping-website.s3.eu-west-1.amazonaws.com/static/activations/EMSR564/{name}_vector.zip", timeout=300, headers=H).content
        z = zipfile.ZipFile(io.BytesIO(b))
        out.append(f"-- {name}: {len(b)//1024} ko ; fichiers : " + ", ".join(sorted({n for n in z.namelist() if n.endswith('.shp')})))
        z.extractall(f"/tmp/{name}")
        import glob

        import pyogrio
        for shp in sorted(glob.glob(f"/tmp/{name}/**/*.shp", recursive=True)):
            df = pyogrio.read_dataframe(shp)
            out.append(f"   {shp.split('/')[-1]}: {len(df)} objets, colonnes {list(df.columns)[:12]}")
            for c in df.columns:
                if c.lower() in ("damage_gra", "obj_desc_e", "notation", "event_type", "obj_type", "dmg_src_id"):
                    out.append(f"      {c}: {df[c].value_counts().head(8).to_dict()}")
    except Exception as e:  # noqa: BLE001
        out.append(f"{name}: erreur {e}")
open("data/_probe.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
