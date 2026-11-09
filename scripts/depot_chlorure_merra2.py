"""Dépôt atmosphérique de chlorure dans le Grand Sud de Madagascar d'après MERRA-2 (NASA GMAO), estimation indépendante
de nos choix pour situer les trois scénarios de validation/protocole_recharge_chlorure.md.

Collection (vérifiée dans la spécification officielle, Bosilovich, Lucchesi et Suarez 2016, GMAO Office Note No. 9
v1.1, p. 25-26 et tableau 6.2) : tavgM_2d_adg_Nx (M2TMNXADG, « Aerosol Diagnostics (extended) », moyennes mensuelles,
0,625° x 0,5°, doi:10.5067/RZIK2TV7PP38). Les dépôts de sel de mer n'y sont PAS dans tavgM_2d_aer_Nx (M2TMNXAER),
qui ne porte que les masses et épaisseurs optiques. Variables (kg m-2 s-1), 5 classes de taille chacune :
SSDP001-005 dépôt sec, SSWT001-005 dépôt humide (grande échelle), SSSV001-005 lessivage convectif,
SSSD001-005 sédimentation. Dépôt total de sel de mer = somme des 20 variables.
Chlorure = 0,55 x sel de mer : fraction massique du chlorure dans le sel marin de référence (19,35 g/kg de Cl pour
une salinité de 35,17 g/kg, Millero et al. 2008, Deep-Sea Res. I 55:50-72 : 19,352 / 35,165 = 0,550 ; valeur
de référence connue, non relue sur l'article le 09/11/2026).

Accès : OPeNDAP cloud de la NASA (opendap.earthdata.nasa.gov), compte Earthdata (secrets EARTHDATA_USER /
EARTHDATA_PASSWORD, jamais affichés), jeton Bearer comme scripts/build_ndvi_mod13c2.py. Sous-ensemble de 10 x 10
mailles seulement, une requête à la fois, 30 s entre deux essais, 3 essais au plus.

Usage : python scripts/depot_chlorure_merra2.py --probe          (noms des variables et format d'un mois)
        python scripts/depot_chlorure_merra2.py --part merra2    (240 mois 2001-2020 -> moyenne par maille)
        python scripts/depot_chlorure_merra2.py --part synthese  (distance à la côte, classes, scénarios -> JSON)
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "mdg"
RAW = DATA / "depot_chlorure_raw"
MAILLES = DATA / "depot_chlorure_merra2_mailles.csv"
OUT = DATA / "depot_chlorure.json"

COLLECTION = "C1276812865-GES_DISC"          # M2TMNXADG v5.12.4 (CMR, vérifié le 09/11/2026)
OPENDAP = "https://opendap.earthdata.nasa.gov/collections/" + COLLECTION + "/granules/"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
VARS = [f"SS{k}{b:03d}" for k in ("DP", "WT", "SV", "SD") for b in range(1, 6)]
# Grille MERRA-2 : lon = -180 + 0,625 i (576), lat = -90 + 0,5 j (361). Emprise 43-47,5 E, 25,7-22,5 S, avec une maille
# de marge : lon 42,5 à 48,125 (i 356-365), lat -26,5 à -22,0 (j 127-136).
I0, I1, J0, J1 = 356, 365, 127, 136
LON = -180 + 0.625 * np.arange(I0, I1 + 1)
LAT = -90 + 0.5 * np.arange(J0, J1 + 1)
SEC_AN = 365.25 * 86400
CL_SEL = 0.55
SCENARIOS = {"bas": (1.8, 0.3, 10.0, 0.0), "central": (2.2, 0.4, 30.0, 0.3), "haut": (5.4, 1.0, 100.0, 0.5)}
CLASSES = [("moins de 30 km", 0, 30), ("30 à 100 km", 30, 100), ("plus de 100 km", 100, 1e9)]


def fetch(s, url: str, tries: int = 3, pause: float = 30.0, sleep=time.sleep) -> str | None:
    """Une requête, 3 essais au plus, 30 s entre deux essais."""
    import requests
    for k in range(tries):
        try:
            r = s.get(url, timeout=180)
            if r.status_code == 200:
                return r.text
            if r.status_code in (401, 403):
                raise RuntimeError(f"accès refusé (HTTP {r.status_code}) : compte Earthdata")
            if r.status_code in (400, 404):
                print(f"  HTTP {r.status_code} : {r.text[:300]}", flush=True)
                return None
            why = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            why = type(e).__name__
        print(f"  essai {k + 1} : {why}", flush=True)
        if k + 1 < tries:
            sleep(pause)
    return None


def granule_id(s, year: int, month: int) -> str | None:
    r = s.get(CMR, params={"collection_concept_id": COLLECTION, "page_size": 5,
                           "temporal": f"{year}-{month:02d}-01T00:00:00Z,{year}-{month:02d}-02T00:00:00Z"}, timeout=60)
    r.raise_for_status()
    ids = [e["title"] for e in r.json()["feed"]["entry"] if f".{year}{month:02d}.nc4" in e["title"]]
    return ids[0] if ids else None


def parse_csv(text: str, var: str, shape: tuple[int, int]) -> np.ndarray:
    """Réponse DAP4 CSV d'une variable [time][lat][lon] : lignes « /SSDP001[0][j], v, v, ... »."""
    rows = []
    for ln in text.splitlines():
        if re.match(r"^\s*/?" + re.escape(var) + r"(\[\d+\])+\s*,", ln):
            rows.append([float(x) for x in ln.split(",")[1:]])
    a = np.array(rows, dtype="float64")
    if a.shape != shape:
        raise ValueError(f"{var} : forme {a.shape} au lieu de {shape}")
    return a


def part_merra2(probe: bool) -> None:
    import os

    import requests
    # session à jeton, comme pour MOD13C2 (méthode recommandée pour l'OPeNDAP cloud)
    tok = requests.post("https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
                        auth=(os.environ["EARTHDATA_USER"], os.environ["EARTHDATA_PASSWORD"]), timeout=60)
    tok.raise_for_status()
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {tok.json()['access_token']}"
    RAW.mkdir(parents=True, exist_ok=True)
    sub = f"[0][{J0}:{J1}][{I0}:{I1}]"
    shape = (J1 - J0 + 1, I1 - I0 + 1)
    if probe:
        g = granule_id(s, 2010, 1)
        dmr = fetch(s, OPENDAP + g + ".dmr.xml")
        names = re.findall(r'<Float32 name="(SS\w+)"', dmr or "")
        print(f"granule {g} ; variables SS : {names}", flush=True)
        t = fetch(s, OPENDAP + g + ".dap.csv?dap4.ce=/lat[" + f"{J0}:{J1}];/lon[{I0}:{I1}];/{VARS[0]}{sub}")
        print(t[:1500] if t else "aucune réponse")
        return
    total = np.zeros(shape)
    parts = {k: np.zeros(shape) for k in ("DP", "WT", "SV", "SD")}
    n = 0
    for y in range(2001, 2021):
        for m in range(1, 13):
            cache = RAW / f"merra2_adg_{y}{m:02d}.csv"
            if cache.exists():
                text = cache.read_text(encoding="utf-8")
            else:
                g = granule_id(s, y, m)
                ce = ";".join(f"/{v}{sub}" for v in VARS)
                text = fetch(s, OPENDAP + g + ".dap.csv?dap4.ce=" + ce) if g else None
                time.sleep(1.0)
                if text is None:
                    print(f"  {y}-{m:02d} : manquant", flush=True)
                    continue
                cache.write_text(text, encoding="utf-8")
            for v in VARS:
                a = parse_csv(text, v, shape)
                total += a
                parts[v[2:4]] += a
            n += 1
            print(f"  {y}-{m:02d} : lu", flush=True)
    if n == 0:
        raise SystemExit("aucun mois lu")
    f = lambda a: a / n * SEC_AN * 1e6                 # kg m-2 s-1 -> mg m-2 an-1
    jj, ii = np.meshgrid(LAT, LON, indexing="ij")
    df = pd.DataFrame({"lon": ii.ravel(), "lat": jj.ravel(),
                       "sel_mer_total_mg_m2_an": f(total).ravel().round(1),
                       **{f"sel_mer_{k}_mg_m2_an": f(a).ravel().round(1) for k, a in parts.items()},
                       "chlorure_mg_m2_an": (CL_SEL * f(total)).ravel().round(1)})
    df.attrs["mois"] = n
    df.to_csv(MAILLES, index=False)
    (RAW / "merra2_mois_lus.txt").write_text(str(n))
    print(f"{MAILLES.name} : {len(df)} mailles, {n} mois sur 240")


POINTS = {"Kwale MWC (Kenya)": (39.3776, -4.462), "Kuruman (Afrique du Sud)": (23.43, -27.45),
          "Stella (Afrique du Sud)": (24.86, -26.55), "Alldays (Afrique du Sud)": (29.10, -22.67)}
VALIDATION = DATA / "depot_chlorure_merra2_validation.csv"


def indices_point(lon: float, lat: float) -> tuple[int, int]:
    """Indices (i, j) de la maille MERRA-2 qui contient le point."""
    return int(round((lon + 180) / 0.625)), int(round((lat + 90) / 0.5))


def part_validation() -> None:
    """Validation : dépôt de sel de mer MERRA-2 aux sites mesurés, 2011-2020 (protocole_combinaison_preuves.md)."""
    import os

    import requests
    tok = requests.post("https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
                        auth=(os.environ["EARTHDATA_USER"], os.environ["EARTHDATA_PASSWORD"]), timeout=60)
    tok.raise_for_status()
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {tok.json()['access_token']}"
    rows = []
    for nom, (lon, lat) in POINTS.items():
        i, j = indices_point(lon, lat)
        sub = f"[0][{j}:{j}][{i}:{i}]"
        parts, n = {k: 0.0 for k in ("DP", "WT", "SV", "SD")}, 0
        for y in range(2011, 2021):
            for m in range(1, 13):
                g = granule_id(s, y, m)
                text = fetch(s, OPENDAP + g + ".dap.csv?dap4.ce=" + ";".join(f"/{v}{sub}" for v in VARS)) if g else None
                time.sleep(1.0)
                if text is None:
                    continue
                for v in VARS:
                    parts[v[2:4]] += float(parse_csv(text, v, (1, 1))[0, 0])
                n += 1
        f = lambda a: a / max(n, 1) * SEC_AN * 1e6 * CL_SEL
        rows.append({"site": nom, "lon": lon, "lat": lat, "maille_lon": -180 + 0.625 * i, "maille_lat": -90 + 0.5 * j, "mois": n,
                     "chlorure_total_mg_m2_an": round(f(sum(parts.values())), 1),
                     "chlorure_humide_mg_m2_an": round(f(parts["WT"] + parts["SV"]), 1),
                     **{f"chlorure_{k}_mg_m2_an": round(f(a), 1) for k, a in parts.items()}})
        print(f"{nom} : {n} mois", flush=True)
    pd.DataFrame(rows).to_csv(VALIDATION, index=False)
    print(pd.DataFrame(rows).to_string())


def cl_pluie(d_km, cl_c, cl_i, L):
    return cl_i + (cl_c - cl_i) * np.exp(-np.asarray(d_km, float) / L)


def depot_scenario(p_mm, d_km, sc):
    cl_c, cl_i, L, s = sc
    return np.asarray(p_mm, float) * cl_pluie(d_km, cl_c, cl_i, L) * (1 + s)


def table_scenarios(p_mm: float = 500.0, dists=(10, 30, 100, 200)) -> dict:
    return {k: {f"{d} km": round(float(depot_scenario(p_mm, d, sc)), 0) for d in dists} for k, sc in SCENARIOS.items()}


def distance_et_terre(lat, lon, zip_path):
    """Distance au trait de côte Natural Earth 10 m (UTM 38S, km) et indicateur « centre de maille sur terre »."""
    import os
    import tempfile
    import zipfile

    import geopandas as gpd
    from shapely.ops import polygonize
    with tempfile.TemporaryDirectory() as td:
        zipfile.ZipFile(zip_path).extractall(td)
        shp = [os.path.join(r, f) for r, _, fs in os.walk(td) for f in fs if f.endswith(".shp")][0]
        lines = gpd.read_file(shp, bbox=(42.0, -26.5, 51.0, -11.0))
    coast = lines.to_crs("EPSG:32738").geometry.union_all()
    land = gpd.GeoSeries(list(polygonize(lines.geometry.union_all())), crs="EPSG:4326").union_all()
    pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs="EPSG:4326")
    return pts.to_crs("EPSG:32738").distance(coast).to_numpy() / 1000.0, pts.within(land).to_numpy()


def part_synthese() -> None:
    import glob
    df = pd.read_csv(MAILLES)
    z = glob.glob(str(DATA / "chlorure_pluie_raw" / "natural_earth" / "*.zip"))[0]
    df["distance_cote_km"], df["terre"] = distance_et_terre(df.lat, df.lon, z)
    df["distance_cote_km"] = df.distance_cote_km.round(1)
    box = (df.lon >= 43 - 0.32) & (df.lon <= 47.5 + 0.32) & (df.lat >= -25.7 - 0.25) & (df.lat <= -22.5 + 0.25)
    t = df[box & df.terre].copy()
    classes = {}
    for nom, a, b in CLASSES:
        c = t[(t.distance_cote_km >= a) & (t.distance_cote_km < b)].chlorure_mg_m2_an
        classes[nom] = {"n_mailles": int(len(c)), "mediane": round(float(c.median()), 0) if len(c) else None,
                        "min": round(float(c.min()), 0) if len(c) else None,
                        "max": round(float(c.max()), 0) if len(c) else None}
    print(json.dumps(classes, ensure_ascii=False, indent=1))
    # mise à jour de la section MERRA-2 de depot_chlorure.json (le reste du fichier est conservé)
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    sec = out.setdefault("merra2", {})
    sec["statut"] = "calculé"
    sec["par_classe_distance_chlorure_mg_m2_an"] = classes
    sec["mailles_terre"] = t[["lon", "lat", "distance_cote_km", "chlorure_mg_m2_an", "sel_mer_DP_mg_m2_an",
                              "sel_mer_WT_mg_m2_an", "sel_mer_SV_mg_m2_an", "sel_mer_SD_mg_m2_an"]].to_dict("records")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return t, classes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["merra2", "synthese", "validation"], default="merra2")
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    if a.part == "merra2":
        part_merra2(a.probe)
    elif a.part == "validation":
        part_validation()
    else:
        part_synthese()
        print(json.dumps(table_scenarios(), ensure_ascii=False))


if __name__ == "__main__":
    main()
