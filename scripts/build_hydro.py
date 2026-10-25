"""Hydrologie de terrain du pays : rivières, bassins versants, hauteur au-dessus du drainage (HAND), pente, par fokontany.

Source : modèle numérique de terrain Copernicus GLO-90 (ESA/Copernicus, accès libre, Amazon S3), ré-échantillonné à 0,005° (~550 m).
Méthode : voir scripts/hydro_core.py (Priority-Flood, accumulation, Strahler, HAND). Résultats :
  docs/data/<pays>/hydro/rivers.geojson, basins.geojson, subbasins.geojson   (cartes)
  data/<pays>/external/hydro.csv                                              (indicateurs par unité, format des connecteurs)
  data/<pays>/hydro_units.csv                                                 (bassin et sous-bassin de chaque fokontany)
  data/<pays>/grids/hydro.npz                                                 (grilles pour les modèles hydrologiques suivants)
Limites : MNT de ~550 m (les bassins de moins de ~50 km² et les petits ruisseaux ne sont pas résolus), pas de réseau artificiel (digues, canaux de
riziculture), le HAND est un indicateur de SUSCEPTIBILITÉ topographique à l'inondation, pas une carte de crue.
Usage : python scripts/build_hydro.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

import hydro_core as H
from common import country_data_dir, country_docs_dir, grid_dir, load_config, read_units, write_json

DEM_URL = ("https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM/"
           "Copernicus_DSM_COG_30_{ns}{lat:02d}_00_{ew}{lon:03d}_00_DEM.tif")


def tile_url(lat0: int, lon0: int) -> str:
    return DEM_URL.format(ns="S" if lat0 < 0 else "N", lat=abs(lat0), ew="W" if lon0 < 0 else "E", lon=abs(lon0))


def read_tile_http(lat0: int, lon0: int, res: float, how: str = "average"):
    """Une tuile de 1° ré-échantillonnée à `res` (moyenne, ou minimum pour conserver les vallées) ; None si la tuile n'existe pas (pleine mer)."""
    import rasterio
    from rasterio.enums import Resampling
    n = int(round(1 / res))
    try:
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="3"):
            with rasterio.open(tile_url(lat0, lon0)) as src:
                if how == "min":   # le rééchantillonnage « min » n'existe pas à la lecture : on lit pleine résolution et on prend le minimum par bloc
                    full = src.read(1).astype("float32")
                    if src.nodata is not None:
                        full[full == src.nodata] = np.inf
                    b = max(1, min(full.shape) // n)
                    full = full[: n * b, : n * b]
                    a = full.reshape(n, b, n, b).min(axis=(1, 3))
                    a[~np.isfinite(a)] = 0.0
                    return a
                a = src.read(1, out_shape=(n, n), resampling=Resampling.average).astype("float32")
                if src.nodata is not None:
                    a[a == src.nodata] = 0.0
                return a
    except Exception as e:  # tuile absente (404) ou erreur réseau
        if "HTTP response code: 404" in str(e) or "No such file" in str(e) or "not recognized" in str(e) or "404" in str(e):
            return None
        raise


def read_dem(bbox, res: float = 0.005, reader=read_tile_http, workers: int = 6, how: str = "average"):
    """Mosaïque du MNT sur l'emprise (lon_min, lat_min, lon_max, lat_max). Retourne (dem, lon0, lat0) avec lat0 = bord nord."""
    lon_min, lat_min, lon_max, lat_max = bbox
    lons = list(range(math.floor(lon_min), math.ceil(lon_max)))
    lats = list(range(math.floor(lat_min), math.ceil(lat_max)))
    n = int(round(1 / res))
    dem = np.zeros((len(lats) * n, len(lons) * n), dtype="float32")
    jobs = [(la, lo) for la in lats for lo in lons]
    with ThreadPoolExecutor(workers) as ex:
        tiles = list(ex.map(lambda t: reader(t[0], t[1], res) if how == "average" else reader(t[0], t[1], res, how), jobs))
    found = 0
    for (la, lo), t in zip(jobs, tiles):
        if t is None:
            continue
        found += 1
        r0 = (lats[-1] - la) * n          # ligne du bord nord de la tuile (la = bord sud)
        c0 = (lo - lons[0]) * n
        dem[r0:r0 + n, c0:c0 + n] = t[:n, :n]
    print(f"MNT : {found}/{len(jobs)} tuiles lues, grille {dem.shape}")
    return dem, float(lons[0]), float(lats[-1] + 1)


def sea_mask(dem: np.ndarray) -> np.ndarray:
    """Mer = cellules à 0 m ou moins reliées au bord de la grille (les lacs et cuvettes intérieures ne sont pas de la mer)."""
    from scipy import ndimage
    low = dem <= 0.5
    lab, n = ndimage.label(low, structure=np.ones((3, 3)))
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    return np.isin(lab, edge[edge > 0])


def polygons(labels: np.ndarray, ids: set[int], lon0: float, lat0: float, res: float, tol: float):
    """Polygones (shapely) par identifiant à partir d'une grille d'étiquettes."""
    import rasterio.features
    from affine import Affine
    from shapely.geometry import shape
    from shapely.ops import unary_union
    tr = Affine(res, 0, lon0, 0, -res, lat0)
    mask = np.isin(labels, list(ids))
    parts: dict[int, list] = {}
    for geom, v in rasterio.features.shapes(labels.astype("int32"), mask=mask, transform=tr, connectivity=8):
        parts.setdefault(int(v), []).append(shape(geom))
    return {k: unary_union(v).simplify(tol, preserve_topology=True) for k, v in parts.items()}


def geom_json(g, nd=4):
    from shapely.geometry import mapping
    m = mapping(g)

    def rnd(c):
        return [round(c[0], nd), round(c[1], nd)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]
    return {"type": m["type"], "coordinates": rnd(m["coordinates"])}


def process(dem, lon0, lat0, res, hcfg, dem_route=None):
    """Chaîne hydrologique complète sur une grille MNT. Retourne un dict de grilles et de listes."""
    h, w = dem.shape
    sea = sea_mask(dem)
    lats = lat0 - (np.arange(h) + 0.5) * res
    row_area = H.cell_area_km2(lats, res)
    area = np.repeat(row_area, w)
    # acheminement sur le MNT « minimum » si fourni : la moyenne sur ~550 m comble les gorges plus étroites que la maille
    # et peut faire franchir une ligne de partage à un grand fleuve (ex. Mangoky capté par la Tsiribihina)
    z, ds = H.fill_and_route(np.where(sea, -1.0, dem if dem_route is None else dem_route), sea)
    sea_flat = sea.ravel()
    acc = H.accumulate(ds, area, sea_flat)
    stream_min = hcfg.get("stream_min_km2", 100)
    stream = (~sea_flat) & (acc >= stream_min)
    order = H.strahler(ds, stream)
    hand = H.hand(z, ds, stream, sea_flat)
    dx = res * 111320.0 * np.cos(np.deg2rad(lats))
    slope = H.slope_percent(np.where(sea, 0.0, dem), dx, res * 110574.0)
    slope[sea] = np.nan
    out = H.basin_outlets(ds, sea_flat)
    big = out & (acc >= hcfg.get("basin_min_km2", 500))
    lab_main = H.jump_labels(out | sea_flat, ds)
    term = H.subbasin_terminals(ds, sea_flat, acc, hcfg.get("subbasin_min_km2", 300))
    lab_sub = H.jump_labels(term | sea_flat, ds)
    return {"dem": dem, "z": z, "ds": ds, "sea": sea, "acc": acc, "stream": stream, "order": order, "hand": hand, "slope": slope,
            "area": area, "out": out, "big": big, "lab_main": lab_main, "lab_sub": lab_sub, "term": term, "shape": (h, w)}


def rank_basins(P, res):
    """Identifiants 1..n des grands bassins (du plus grand au plus petit) et des sous-bassins ; tables d'attributs."""
    h, w = P["shape"]
    land = ~P["sea"].ravel()
    area = P["area"]
    mains = np.where(P["big"])[0]
    tot = {int(o): float(area[land & (P["lab_main"] == o)].sum()) for o in mains}
    order = sorted(tot, key=lambda o: -tot[o])
    main_id = {o: i + 1 for i, o in enumerate(order)}
    main = np.zeros(h * w, dtype="int32")
    for o, i in main_id.items():
        main[land & (P["lab_main"] == o)] = i
    subs = np.where(P["term"] & ~P["sea"].ravel())[0]
    sub_id = {int(s): i + 1 for i, s in enumerate(subs)}
    sub = np.zeros(h * w, dtype="int32")
    lab = P["lab_sub"]
    # étiquette -> id par recherche (vectorisé)
    keys = np.array(list(sub_id.keys()), dtype=np.int64)
    vals = np.array(list(sub_id.values()), dtype="int32")
    srt = np.argsort(keys)
    pos = np.searchsorted(keys[srt], lab)
    pos = np.clip(pos, 0, len(keys) - 1)
    ok = land & (keys[srt][pos] == lab)
    sub[ok] = vals[srt][pos[ok]]
    return main.reshape(h, w), sub.reshape(h, w), main_id, sub_id, tot


def unit_stats(units, geoms, P, main, sub, lon0, lat0, res):
    """Statistiques par fokontany (puis cumul vers communes, districts et régions)."""
    import rasterio.features
    from affine import Affine
    h, w = P["shape"]
    tr = Affine(res, 0, lon0, 0, -res, lat0)
    leaves = units[units.level == 4].reset_index(drop=True)
    shapes = [(geoms[c], i + 1) for i, c in enumerate(leaves.pcode) if c in geoms]
    ids = rasterio.features.rasterize(shapes, out_shape=(h, w), transform=tr, fill=0, dtype="int32")
    flat = ids.ravel()
    land = ~P["sea"].ravel()
    m = (flat > 0) & land
    n = len(leaves) + 1
    slope, hand, acc, dem = P["slope"].ravel(), P["hand"].ravel(), P["acc"], P["dem"].ravel()
    cnt = np.bincount(flat[m], minlength=n).astype(float)
    s_sum = np.bincount(flat[m], weights=np.nan_to_num(slope[m]), minlength=n)
    s30 = np.bincount(flat[m], weights=(np.nan_to_num(slope[m]) > 30), minlength=n)
    s15 = np.bincount(flat[m], weights=(np.nan_to_num(slope[m]) >= 15), minlength=n)
    e_sum = np.bincount(flat[m], weights=dem[m], minlength=n)
    h5 = np.bincount(flat[m], weights=(np.isfinite(hand[m]) & (hand[m] < 5)), minlength=n)
    h15 = np.bincount(flat[m], weights=(np.isfinite(hand[m]) & (hand[m] < 15)), minlength=n)
    amax = np.zeros(n)
    np.maximum.at(amax, flat[m], acc[m])
    df = pd.DataFrame({"cnt": cnt, "s_sum": s_sum, "s30": s30, "s15": s15, "e_sum": e_sum, "h5": h5, "h15": h15, "amax": amax})[1:]
    df.index = leaves.pcode.values[: len(df)] if len(df) == len(leaves) else leaves.pcode.values
    # fokontany plus petits qu'une cellule : on prend la cellule du centroïde
    small = df.cnt == 0
    if small.any():
        sm = leaves[small.values]
        r = np.clip(((lat0 - sm.lat.values) / res).astype(int), 0, h - 1)
        c = np.clip(((sm.lon.values - lon0) / res).astype(int), 0, w - 1)
        k = r * w + c
        okl = land[k]
        idx = df.index[small.values]
        df.loc[idx, "cnt"] = np.where(okl, 1.0, 0.0)
        df.loc[idx, "s_sum"] = np.where(okl, np.nan_to_num(slope[k]), 0.0)
        df.loc[idx, "s30"] = np.where(okl, np.nan_to_num(slope[k]) > 30, 0.0)
        df.loc[idx, "s15"] = np.where(okl, np.nan_to_num(slope[k]) >= 15, 0.0)
        df.loc[idx, "e_sum"] = np.where(okl, dem[k], 0.0)
        df.loc[idx, "h5"] = np.where(okl, np.isfinite(hand[k]) & (hand[k] < 5), 0.0)
        df.loc[idx, "h15"] = np.where(okl, np.isfinite(hand[k]) & (hand[k] < 15), 0.0)
        df.loc[idx, "amax"] = np.where(okl, acc[k], 0.0)
    # bassin dominant de chaque fokontany
    dom = {}
    for name, lab in (("basin", main), ("subbasin", sub)):
        d = pd.DataFrame({"u": flat[m], "b": lab.ravel()[m]})
        d = d[d.b > 0]
        top = d.groupby(["u", "b"]).size().reset_index(name="n").sort_values("n").groupby("u").last()
        arr = np.zeros(len(leaves), dtype=int)
        arr[top.index.values - 1] = top.b.values
        dom[name] = arr
    pairs = units[["pcode", "level", "adm1", "adm2", "adm3"]].set_index("pcode")
    leaf_ix = df.index
    rows = []
    agg_cols = ["cnt", "s_sum", "s30", "s15", "e_sum", "h5", "h15"]
    for lv, key in ((4, None), (3, "adm3"), (2, "adm2"), (1, "adm1")):
        if key is None:
            g = df.copy()
        else:
            g = df[agg_cols].groupby(pairs.loc[leaf_ix, key].values).sum()
            g["amax"] = df["amax"].groupby(pairs.loc[leaf_ix, key].values).max()
        for pc, r in g.iterrows():
            if r.cnt <= 0 or not pc:
                continue
            rows += [(pc, "hand_lt5_pct", 100 * r.h5 / r.cnt), (pc, "hand_lt15_pct", 100 * r.h15 / r.cnt), (pc, "slope_mean_pct", r.s_sum / r.cnt),
                     (pc, "slope_gt30_pct", 100 * r.s30 / r.cnt), (pc, "slope_ge15_pct", 100 * r.s15 / r.cnt), (pc, "elev_mean_m", r.e_sum / r.cnt), (pc, "river_max_km2", r.amax)]
    ext = pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur"])
    ext["valeur"] = ext.valeur.round(2)
    ext["date"] = dt.date.today().isoformat()
    ext["source"] = "Copernicus GLO-90 : calcul MakyClimat (hydro_core)"
    lk = pd.DataFrame({"pcode": leaves.pcode, "basin": dom["basin"], "subbasin": dom["subbasin"]})
    return ext, lk


def write_all(country, P, main, sub, main_id, sub_id, tot, units, ext, lk, lon0, lat0, res, hcfg):
    from shapely.geometry import LineString
    from scipy.spatial import cKDTree
    h, w = P["shape"]
    hydro_dir = country_docs_dir(country) / "hydro"
    hydro_dir.mkdir(parents=True, exist_ok=True)
    # rivières
    rs = H.reaches(P["ds"], P["stream"], P["acc"], P["order"], w, lon0, lat0, res)
    feats = []
    for pts, a, o in rs:
        g = LineString(pts).simplify(res * 0.6)
        if g.is_empty:
            continue
        feats.append({"type": "Feature", "properties": {"a": int(round(a)), "o": int(o)}, "geometry": geom_json(g)})
    (hydro_dir / "rivers.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")), encoding="utf-8")
    # bassins
    comm = units[units.level == 3].reset_index(drop=True)
    tree = cKDTree(np.c_[comm.lon, comm.lat])
    area = P["area"].reshape(h, w)
    popc = units[units.level == 4].set_index("pcode")["pop"].fillna(0)
    bpop = lk.assign(pop=lk.pcode.map(popc)).groupby("basin")["pop"].sum()
    spop = lk.assign(pop=lk.pcode.map(popc)).groupby("subbasin")["pop"].sum()
    pol_main = polygons(main, set(main_id.values()), lon0, lat0, res, res * 0.8)
    mfeat, minfo = [], {}
    for o, i in main_id.items():
        r, c = divmod(int(o), w)
        lon, lat = lon0 + (c + 0.5) * res, lat0 - (r + 0.5) * res
        nm = "Bassin de " + comm.name.iloc[int(tree.query([lon, lat])[1])]
        info = {"id": i, "name": nm, "area_km2": round(tot[o]), "pop": int(round(bpop.get(i, 0))), "outlet": [round(lon, 4), round(lat, 4)]}
        minfo[i] = info
        if i in pol_main:
            mfeat.append({"type": "Feature", "properties": info, "geometry": geom_json(pol_main[i])})
    (hydro_dir / "basins.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": mfeat}, separators=(",", ":")), encoding="utf-8")
    # sous-bassins : bassin parent, aval, surface
    pol_sub = polygons(sub, set(sub_id.values()), lon0, lat0, res, res * 0.8)
    inv = {v: k for k, v in sub_id.items()}
    sfeat = []
    sub_flat, main_flat = sub.ravel(), main.ravel()
    for i, geom in pol_sub.items():
        t = inv[i]
        down = int(sub_flat[P["ds"][t]]) if not P["sea"].ravel()[P["ds"][t]] else 0
        cells = sub_flat == i
        parent = int(np.bincount(main_flat[cells][main_flat[cells] > 0]).argmax()) if (main_flat[cells] > 0).any() else 0
        sfeat.append({"type": "Feature", "properties": {"id": i, "basin": parent, "down": down, "area_km2": round(float(area.ravel()[cells].sum())),
                                                        "pop": int(round(spop.get(i, 0)))}, "geometry": geom_json(geom)})
    (hydro_dir / "subbasins.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": sfeat}, separators=(",", ":")), encoding="utf-8")
    write_json(hydro_dir / "meta.json", {"generated": dt.date.today().isoformat(), "res_deg": res, "stream_min_km2": hcfg.get("stream_min_km2", 100),
                                         "basin_min_km2": hcfg.get("basin_min_km2", 500), "subbasin_min_km2": hcfg.get("subbasin_min_km2", 300),
                                         "n_basins": len(mfeat), "n_subbasins": len(sfeat), "n_reaches": len(feats), "basins": list(minfo.values()),
                                         "dem": "Copernicus GLO-90 (ESA), ré-échantillonné à 0,005°"})
    # indicateurs et grilles
    ext_dir = country_data_dir(country) / "external"
    ext_dir.mkdir(parents=True, exist_ok=True)
    ext[["pcode", "indicateur", "valeur", "date", "source"]].to_csv(ext_dir / "hydro.csv", index=False)
    lk.to_csv(country_data_dir(country) / "hydro_units.csv", index=False)
    write_json(hydro_dir / "units.json", {"u": {pc: int(b) for pc, b in zip(lk.pcode, lk.basin) if b > 0}})
    np.savez_compressed(grid_dir(country) / "hydro.npz", basin=main.astype("int16"), subbasin=sub.astype("int32"), hand=np.nan_to_num(P["hand"], nan=-1).astype("float16"),
                        slope=np.clip(np.nan_to_num(P["slope"], nan=0), 0, 255).astype("uint8"), acc=np.log10(np.maximum(P["acc"], 1)).astype("float16").reshape(h, w),
                        sea=P["sea"], lon0=np.array(lon0), lat0=np.array(lat0), res=np.array(res))
    return minfo


def run(country: str, reader=read_tile_http, res: float | None = None, hcfg: dict | None = None, bbox=None) -> dict:
    cfg = load_config(country)
    hcfg = {**cfg.get("hydro", {}), **(hcfg or {})}
    res = res or hcfg.get("res_deg", 0.005)
    bbox = bbox or hcfg.get("bbox") or cfg["map"]["bbox"]
    dem, lon0, lat0 = read_dem(bbox, res, reader)
    dem_route = None
    if hcfg.get("route_resampling", "min") == "min" and reader is read_tile_http:
        dem_route, _, _ = read_dem(bbox, res, reader, how="min")
    P = process(dem, lon0, lat0, res, hcfg, dem_route)
    main_lab, sub_lab, main_id, sub_id, tot = rank_basins(P, res)
    units = read_units(country)
    from shapely.geometry import shape
    geoms = {}
    for f in sorted((country_docs_dir(country) / "geo" / "adm4").glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            geoms[ft["properties"]["c"]] = shape(ft["geometry"])
    ext, lk = unit_stats(units, geoms, P, main_lab, sub_lab, lon0, lat0, res)
    minfo = write_all(country, P, main_lab, sub_lab, main_id, sub_id, tot, units, ext, lk, lon0, lat0, res, hcfg)
    top = sorted(minfo.values(), key=lambda x: -x["area_km2"])[:12]
    print("Plus grands bassins :", "; ".join(f"{b['name']} {b['area_km2']} km²" for b in top))
    print(f"{len(minfo)} bassins, {len(sub_id)} sous-bassins, {int(P['stream'].sum())} cellules de rivière")
    return {"P": P, "ext": ext, "lk": lk, "minfo": minfo}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    run(args.country)


if __name__ == "__main__":
    main()
