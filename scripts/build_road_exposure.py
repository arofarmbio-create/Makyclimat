"""Routes principales exposées aux crues et éloignement des routes, par fokontany.

Source : OpenStreetMap (© contributeurs, ODbL) via Overpass : routes de classe trunk, primary, secondary et tertiary de Madagascar (les pistes et
chemins ne sont pas pris en compte : leur cartographie est trop incomplète). Croisées avec la HAND de MakyClimat (hauteur au-dessus du cours d'eau
le plus proche, Copernicus GLO-90, 0,005°) :
  route_km           longueur de routes principales dans l'unité (km)
  route_basse5_km    longueur à moins de 5 m au-dessus d'un cours d'eau (km) : tronçons susceptibles d'être coupés par une crue
  route_basse5_pct   part de cette longueur (%)
  route_dist_km      distance du centroïde du fokontany à la route principale la plus proche (km) : proxy d'enclavement (moyenne pondérée par la population au-dessus)
Limites : EXPOSITION topographique, pas une coupure constatée (ponts, radiers, digues et remblais surélevés ne sont pas vus par un MNT de 550 m) ;
distance à vol d'oiseau, pas un temps de trajet ; OpenStreetMap n'est pas un recensement : une route absente peut être non cartographiée.
Sortie : data/<pays>/external/routes.csv (tous les niveaux). Usage : python scripts/build_road_exposure.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time

import numpy as np
import pandas as pd
import requests

from common import country_data_dir, country_docs_dir, grid_dir, load_config, read_units

SRC = ("© contributeurs OpenStreetMap (ODbL) via Overpass, routes trunk/primary/secondary/tertiary ; HAND MakyClimat (Copernicus GLO-90) : "
       "exposition topographique, pas une coupure constatée")
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
KM_LAT = 110.57


def seg_km(lon1, lat1, lon2, lat2):
    dx = (lon2 - lon1) * 111.32 * np.cos(np.deg2rad((lat1 + lat2) / 2))
    dy = (lat2 - lat1) * KM_LAT
    return np.hypot(dx, dy)


def densify(coords, step_km=0.25):
    """Points régulièrement espacés le long d'une ligne [(lon, lat), ...], chacun avec la longueur (km) qu'il représente."""
    pts, wts = [], []
    for (x1, y1), (x2, y2) in zip(coords[:-1], coords[1:]):
        L = float(seg_km(x1, y1, x2, y2))
        if L <= 0:
            continue
        n = max(1, int(np.ceil(L / step_km)))
        t = (np.arange(n) + 0.5) / n
        pts.append(np.c_[x1 + (x2 - x1) * t, y1 + (y2 - y1) * t])
        wts.append(np.full(n, L / n))
    if not pts:
        return np.zeros((0, 2)), np.zeros(0)
    return np.vstack(pts), np.concatenate(wts)


def accumulate(pts, wts, ids, hand, sea, lon0, lat0, res, n):
    """Longueur de route (km) par identifiant d'unité : totale et à HAND < 5 m. Points en mer ou hors grille ignorés."""
    h, w = ids.shape
    r = np.floor((lat0 - pts[:, 1]) / res).astype(int)
    c = np.floor((pts[:, 0] - lon0) / res).astype(int)
    ok = (r >= 0) & (r < h) & (c >= 0) & (c < w)
    r, c, wt = r[ok], c[ok], wts[ok]
    u = ids[r, c]
    good = (u > 0) & ~sea[r, c]
    low = good & np.isfinite(hand[r, c]) & (hand[r, c] < 5)
    return (np.bincount(u[good], weights=wt[good], minlength=n), np.bincount(u[low], weights=wt[low], minlength=n))


def fetch_roads(bbox, tiles=(4, 6), cache=None):
    """Géométries (liste de listes de (lon, lat)) des routes principales, par petites tuiles (reprise possible grâce au cache)."""
    lon0, lat0, lon1, lat1 = bbox
    xs, ys = np.linspace(lon0, lon1, tiles[0] + 1), np.linspace(lat0, lat1, tiles[1] + 1)
    store = json.loads(cache.read_text()) if cache is not None and cache.exists() else {}
    for i in range(tiles[0]):
        for j in range(tiles[1]):
            key = f"{i},{j}"
            if key in store:
                continue
            q = (f'[out:json][timeout:120];way["highway"~"^(trunk|primary|secondary|tertiary)$"]({ys[j]:.4f},{xs[i]:.4f},{ys[j+1]:.4f},{xs[i+1]:.4f});out geom;')
            data, t0 = None, time.time()
            for k in range(6):
                try:
                    r = requests.post(MIRRORS[k % len(MIRRORS)], data={"data": q}, timeout=150, headers={"User-Agent": "MakyClimat (recherche doctorale)"})
                    if r.ok:
                        data = r.json()
                        break
                    print(f"tuile {key} : HTTP {r.status_code} ({MIRRORS[k % len(MIRRORS)]})", flush=True)
                except Exception as ex:  # noqa: BLE001
                    print(f"tuile {key} : {type(ex).__name__}", flush=True)
                time.sleep(10)
            if data is None:
                print(f"tuile {key} abandonnée", flush=True)
                continue
            store[key] = [{"id": e["id"], "g": [(p["lon"], p["lat"]) for p in e["geometry"]]} for e in data.get("elements", []) if "geometry" in e]
            print(f"tuile {key} : {len(store[key])} routes en {time.time() - t0:.0f} s", flush=True)
            if cache is not None:
                cache.write_text(json.dumps(store))
    missing = [f"{i},{j}" for i in range(tiles[0]) for j in range(tiles[1]) if f"{i},{j}" not in store]
    if missing:
        raise RuntimeError(f"tuiles manquantes : {missing} (relancer pour reprendre)")
    seen, lines = set(), []
    for v in store.values():
        for e in v:
            if e["id"] not in seen:
                seen.add(e["id"])
                lines.append([tuple(p) for p in e["g"]])
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    a = ap.parse_args()
    import rasterio.features
    from affine import Affine
    from scipy.spatial import cKDTree
    from shapely.geometry import shape
    z = np.load(grid_dir(a.country) / "hydro.npz", allow_pickle=False)
    hand, sea = z["hand"].astype("float32"), z["sea"]
    lon0, lat0, res = float(z["lon0"]), float(z["lat0"]), float(z["res"])
    h, w = hand.shape
    units = read_units(a.country)
    leaves = units[units.level == 4].reset_index(drop=True)
    geoms = {}
    for f in sorted((country_docs_dir(a.country) / "geo" / "adm4").glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            geoms[ft["properties"]["c"]] = shape(ft["geometry"])
    shapes = [(geoms[c], i + 1) for i, c in enumerate(leaves.pcode) if c in geoms]
    ids = rasterio.features.rasterize(shapes, out_shape=(h, w), transform=Affine(res, 0, lon0, 0, -res, lat0), fill=0, dtype="int32")
    n = len(leaves) + 1
    lines = fetch_roads(load_config(a.country)["map"]["bbox"], cache=country_data_dir(a.country) / "_osm_routes_cache.json")
    P, W = [], []
    for ln in lines:
        p, wt = densify(ln)
        if len(p):
            P.append(p), W.append(wt)
    pts, wts = np.vstack(P), np.concatenate(W)
    tot, low = accumulate(pts, wts, ids, hand, sea, lon0, lat0, res, n)
    df = pd.DataFrame({"route_km": tot[1:], "route_basse5_km": low[1:]}, index=leaves.pcode.values)
    kx = np.cos(np.deg2rad(-19.0)) * 111.32
    tree = cKDTree(np.c_[pts[:, 0] * kx, pts[:, 1] * KM_LAT])
    dist, _ = tree.query(np.c_[leaves.lon.values * kx, leaves.lat.values * KM_LAT])
    df["route_dist_km"] = dist
    pop = leaves.set_index("pcode")["pop"].fillna(0)
    pairs = units[units.level == 4].set_index("pcode")[["adm1", "adm2", "adm3"]]
    d = df.join(pairs)
    d["pw"] = pop.reindex(d.index).values
    d["dxp"] = d.route_dist_km * d.pw
    parts = [df.copy()]
    for col in ("adm3", "adm2", "adm1"):
        g = d.groupby(col).agg(route_km=("route_km", "sum"), route_basse5_km=("route_basse5_km", "sum"), pw=("pw", "sum"), dxp=("dxp", "sum"))
        g["route_dist_km"] = g.dxp / g.pw.where(g.pw > 0)
        parts.append(g[["route_km", "route_basse5_km", "route_dist_km"]])
    allu = pd.concat(parts)
    allu = allu[~allu.index.duplicated(keep="first")]
    allu["route_basse5_pct"] = 100 * allu.route_basse5_km / allu.route_km.where(allu.route_km > 0)
    long = allu.reset_index(names="pcode").melt(id_vars="pcode", var_name="indicateur", value_name="valeur").dropna()
    long["valeur"] = long.valeur.round(2)
    long["date"], long["source"] = dt.date.today().isoformat(), SRC
    ext = country_data_dir(a.country) / "external"
    ext.mkdir(parents=True, exist_ok=True)
    long.to_csv(ext / "routes.csv", index=False)
    nat = allu.loc[[p for p in allu.index if len(p) == 4]].sum(numeric_only=True)
    print(f"Routes principales : {nat.route_km:,.0f} km, dont {100 * nat.route_basse5_km / nat.route_km:.1f} % à moins de 5 m au-dessus d'un cours d'eau ; "
          f"distance médiane fokontany-route {np.median(dist):.1f} km ; {len(long)} valeurs")


if __name__ == "__main__":
    main()
