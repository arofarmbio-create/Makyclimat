"""Eau dans le sol : humidité du sol, excédent hydrique (recharge) et indice relatif de nappe, à partir de données réelles.

Données : pluie CHIRPS mensuelle (1981-aujourd'hui), évapotranspiration de référence FAO-56 d'ERA5-Land (Open-Meteo, 2016-2020),
texture et carbone organique du sol (SoilGrids 2.0, ISRIC), occupation du sol (ESA WorldCover 2021).
Méthodes publiées : voir scripts/soilwater_core.py (Saxton & Rawls 2006, NRCS NEH-4, FAO-56, Thornthwaite & Mather 1957, scores normaux).
Résultats :
  data/<pays>/external/soilwater.csv        indicateurs par zone (lus par compute_metrics)
  docs/data/<pays>/soilwater/series.json    36 derniers mois et normale mensuelle, par région, district et commune
  docs/data/<pays>/soilwater/status.json    état de chaque étape et limites
  data/<pays>/grids/soilprops.npz, et2 cache : cache de données statiques
« Niveau statique » : sans mesures de puits, seul un INDICE RELATIF est possible (recharge cumulée sur 12 mois standardisée, méthode de Bloomfield & Marchant 2013).
Pour obtenir des mètres, fournir inputs/niveau_statique_puits.csv (voir README).
Usage : python scripts/build_soilwater.py --country mdg [--max-et0-batches 150]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

import soilwater_core as C
from common import country_data_dir, country_docs_dir, grid_dir, load_config, load_grid, read_units, save_grid, write_json

SOIL_LAYERS = [("0-5cm", 5), ("5-15cm", 10), ("15-30cm", 15), ("30-60cm", 30), ("60-100cm", 40)]
ET0_YEARS = (2016, 2020)
STATUS: dict = {"steps": {}, "limits": [
    "Bilan mensuel : le ruissellement réel dépend de l'intensité journalière de la pluie, non représentée ici.",
    "Évapotranspiration de référence (gazon) sans coefficient cultural ; climatologie 2016-2020 d'ERA5-Land, pas de variation d'une année à l'autre.",
    "Texture du sol de SoilGrids (250 m) : les sols ferrallitiques argileux sont plus perméables que leur texture ne l'indique.",
    "Niveau statique : indice relatif seulement, faute de mesures de puits ; l'indice est une approximation de la recharge, pas un niveau mesuré.",
]}


def step(name):
    def deco(fn):
        def run(*a, **k):
            t0 = time.time()
            try:
                out = fn(*a, **k)
                STATUS["steps"][name] = {"ok": True, "seconds": round(time.time() - t0, 1)}
                return out
            except Exception as e:  # noqa: BLE001
                STATUS["steps"][name] = {"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}"}
                print(f"ÉCHEC {name}: {e}")
                traceback.print_exc()
                return None
        return run
    return deco


# ---------------- Lecture des données (remplaçables dans les tests) ----------------


def read_soilgrids(var: str, layer: str, grid: dict):
    """Une couche SoilGrids reprojetée sur la grille de pluie (moyenne). Valeurs en g/kg (argile, sable) ou dg/kg (carbone)."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.vrt import WarpedVRT
    url = f"/vsicurl/https://files.isric.org/soilgrids/latest/data/{var}/{var}_{layer}_mean.vrt"
    tr = from_origin(grid["lon0"], grid["lat0"], grid["res"], grid["res"])
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="3"):
        with rasterio.open(url) as src:
            with WarpedVRT(src, crs="EPSG:4326", transform=tr, width=grid["w"], height=grid["h"], resampling=Resampling.average,
                           nodata=src.nodata, src_nodata=src.nodata) as vrt:
                a = vrt.read(1).astype("float64")
                a[(a == src.nodata) | (a < 0)] = np.nan
                return a


WC_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{ns}{lat:02d}{ew}{lon:03d}_Map.tif"


def read_worldcover(grid: dict, sub: int = 10):
    """Fractions de chaque classe WorldCover par cellule de la grille de pluie (échantillonnage de 10 x 10 points par cellule)."""
    import math
    import rasterio
    from rasterio.windows import from_bounds
    h, w, res, lon0, lat0 = grid["h"], grid["w"], grid["res"], grid["lon0"], grid["lat0"]
    fine = np.zeros((h * sub, w * sub), dtype="uint8")
    lat_min, lon_max = lat0 - h * res, lon0 + w * res
    n_ok = 0
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="3"):
        for la in range(int(math.floor(lat_min / 3) * 3), int(math.ceil(lat0 / 3) * 3), 3):      # coin sud-ouest de la tuile
            for lo in range(int(math.floor(lon0 / 3) * 3), int(math.ceil(lon_max / 3) * 3), 3):
                url = "/vsicurl/" + WC_URL.format(ns="S" if la < 0 else "N", lat=abs(la), ew="W" if lo < 0 else "E", lon=abs(lo))
                x0, x1, y0, y1 = max(lo, lon0), min(lo + 3, lon_max), max(la, lat_min), min(la + 3, lat0)
                if x1 <= x0 or y1 <= y0:
                    continue
                try:
                    with rasterio.open(url) as src:
                        r0, r1 = int(round((lat0 - y1) / res * sub)), int(round((lat0 - y0) / res * sub))
                        c0, c1 = int(round((x0 - lon0) / res * sub)), int(round((x1 - lon0) / res * sub))
                        win = from_bounds(x0, y0, x1, y1, transform=src.transform)
                        a = src.read(1, window=win, out_shape=(r1 - r0, c1 - c0), resampling=rasterio.enums.Resampling.nearest)
                        fine[r0:r1, c0:c1] = np.where(a > 0, a, fine[r0:r1, c0:c1])
                        n_ok += 1
                except Exception as e:  # tuile absente (mer) ou erreur
                    if "404" not in str(e) and "No such file" not in str(e) and "not recognized" not in str(e):
                        print("WorldCover", la, lo, str(e)[:120])
    print(f"WorldCover : {n_ok} tuiles lues")
    return fractions_from_fine(fine, h, w, sub)


def fractions_from_fine(fine: np.ndarray, h: int, w: int, sub: int):
    blocks = fine.reshape(h, sub, w, sub).transpose(0, 2, 1, 3).reshape(h, w, sub * sub)
    valid = (blocks > 0).sum(axis=2)
    out = np.zeros((len(C.LC_CLASSES), h, w), dtype="float32")
    for i, k in enumerate(C.LC_CLASSES):
        out[i] = (blocks == k).sum(axis=2) / np.maximum(valid, 1)
    out[:, valid == 0] = np.nan
    return out


def read_et0_points(lons, lats, cache_path, max_batches=150, batch=4, pause=1.0):
    """ET0 mensuelle moyenne (mm/mois) d'ERA5-Land (Open-Meteo, archive) pour des points ; cache reprenable. Retourne dict (lon, lat) -> 12 valeurs ou None."""
    import openmeteo as om
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    if cache.get("_years") != list(ET0_YEARS):      # période différente : on repart de zéro pour garder une climatologie homogène
        cache = {"_years": list(ET0_YEARS)}
    keys = [f"{lo:.2f},{la:.2f}" for lo, la in zip(lons, lats)]
    todo = [k for k in keys if k not in cache]
    done = 0
    for i in range(0, len(todo), batch):
        if done >= max_batches:
            break
        ks = todo[i:i + batch]
        params = {"latitude": ",".join(k.split(",")[1] for k in ks), "longitude": ",".join(k.split(",")[0] for k in ks),
                  "start_date": f"{ET0_YEARS[0]}-01-01", "end_date": f"{ET0_YEARS[1]}-12-31", "daily": "et0_fao_evapotranspiration", "timezone": "UTC"}
        try:
            payload = om.get_json("https://archive-api.open-meteo.com/v1/archive", params, retries=6, pause=2.0)
        except Exception as e:  # noqa: BLE001
            print("ET0 : arrêt du lot", str(e)[:150])
            break
        for k, item in zip(ks, om.as_list(payload)):
            d = pd.DataFrame(item["daily"])
            d["date"] = pd.to_datetime(d["time"])
            d = d.dropna()
            if len(d) < 0.9 * 365 * (ET0_YEARS[1] - ET0_YEARS[0] + 1):
                continue
            mon = d.groupby([d.date.dt.year, d.date.dt.month]).et0_fao_evapotranspiration.sum()      # mm par mois
            clim = mon.groupby(level=1).mean()
            if len(clim) == 12:
                cache[k] = [round(float(x), 1) for x in clim.values]
        done += 1
        cache_path.write_text(json.dumps(cache))
        time.sleep(pause)
    cache_path.write_text(json.dumps(cache))
    return {k: cache.get(k) for k in keys}


def read_chirps_month(y: int, m: int, cfg: dict):
    from chirps import fetch_array
    r = fetch_array(cfg["rainfall"]["monthly_url"].format(y=y, m=m), cfg["map"]["bbox"])
    return None if r is None else r[0]


# ---------------- Étapes ----------------


@step("sols et occupation du sol")
def static_props(grid, readers, cache_path):
    h, w = grid["h"], grid["w"]
    if cache_path.exists():
        z = load_grid(cache_path)
        if z["h"] == h and z["w"] == w and bool(z.get("complete", False)):
            print("Propriétés du sol : cache")
            return {k: z[k] for k in ("whc", "cn2", "hsg", "clay", "sand", "om", "lcfrac")}
    tot_w = sum(t for _, t in SOIL_LAYERS)
    acc = {}
    for var in ("clay", "sand", "soc"):
        s = np.zeros((h, w))
        wt = np.zeros((h, w))
        for layer, thick in SOIL_LAYERS:
            a = readers["soil"](var, layer, grid)
            ok = np.isfinite(a)
            s[ok] += a[ok] * thick
            wt[ok] += thick
        acc[var] = np.where(wt >= tot_w * 0.5, s / np.maximum(wt, 1), np.nan)
    clay, sand = acc["clay"] / 10.0, acc["sand"] / 10.0          # g/kg -> %
    om = acc["soc"] / 10.0 * 1.724 / 10.0                         # dg/kg -> g/kg -> % de carbone x 1,724 = matière organique
    lcfrac = readers["landcover"](grid)
    wp, fc = C.saxton_rawls(sand / 100.0, clay / 100.0, np.clip(om, 0.1, 8.0))
    tex = C.usda_texture(sand, clay)
    hsg = np.where(tex >= 0, C.HSG_ARRAY[np.clip(tex, 0, len(C.TEXTURES) - 1)], -1)
    cn2 = np.zeros((h, w))
    whc = np.zeros((h, w))
    wsum = np.zeros((h, w))
    for i, k in enumerate(C.LC_CLASSES):
        f = np.nan_to_num(lcfrac[i])
        cn_k = C.cn_lookup(np.full((h, w), k), np.where(hsg >= 0, hsg, 3))
        whc_k = C.whc_mm(fc, wp, C.LANDCOVER[k]["root_m"])
        ok = f > 0
        cn2 += np.where(ok, f * cn_k, 0.0)
        whc += np.where(ok & np.isfinite(whc_k), f * whc_k, 0.0)
        wsum += np.where(ok, f, 0.0)
    good = (wsum > 0.3) & np.isfinite(clay) & np.isfinite(sand)
    cn2 = np.where(good, cn2 / np.maximum(wsum, 1e-9), np.nan)
    whc = np.where(good, whc / np.maximum(wsum, 1e-9), np.nan)
    save_grid(cache_path, whc=whc.astype("float32"), cn2=cn2.astype("float32"), hsg=hsg.astype("int8"), clay=clay.astype("float32"),
              sand=sand.astype("float32"), om=om.astype("float32"), lcfrac=lcfrac.astype("float16"), h=np.array(h), w=np.array(w), complete=np.array(True))
    return {"whc": whc, "cn2": cn2, "hsg": hsg, "clay": clay, "sand": sand, "om": om, "lcfrac": lcfrac}


@step("évapotranspiration de référence")
def et0_grid(grid, land, readers, cache_path, max_batches):
    from scipy import ndimage
    from scipy.interpolate import RegularGridInterpolator
    h, w, res, lon0, lat0 = grid["h"], grid["w"], grid["res"], grid["lon0"], grid["lat0"]
    st = 0.25
    cols = np.arange(np.floor(lon0 / st) * st, lon0 + w * res + st, st)
    rows = np.arange(np.floor((lat0 - h * res) / st) * st, lat0 + st, st)
    LO, LA = np.meshgrid(cols, rows)
    rr = np.clip(((lat0 - LA) / res).astype(int), 0, h - 1)
    cc = np.clip(((LO - lon0) / res).astype(int), 0, w - 1)
    # un point par maille de 0,25° qui contient de la terre (au moins une cellule de pluie terrestre)
    has_land = np.zeros(LO.shape, dtype=bool)
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            has_land |= land[np.clip(rr + dr, 0, h - 1), np.clip(cc + dc, 0, w - 1)]
    pts = np.where(has_land)
    lons, lats = LO[pts], LA[pts]
    got = readers["et0"](lons, lats, cache_path, max_batches)
    grid12 = np.full((12,) + LO.shape, np.nan)
    n_ok = 0
    for (i, j), lo, la in zip(zip(*pts), lons, lats):
        v = got.get(f"{lo:.2f},{la:.2f}")
        if v:
            grid12[:, i, j] = v
            n_ok += 1
    STATUS["et0_points"] = {"obtenus": n_ok, "demandés": int(len(lons))}
    if n_ok < 0.9 * len(lons):
        raise RuntimeError(f"ET0 incomplète : {n_ok}/{len(lons)} points (relancer le workflow pour poursuivre)")
    # comblement des mailles sans donnée par la plus proche, puis interpolation bilinéaire vers la grille de pluie
    out = np.zeros((12, h, w))
    clat = lat0 - (np.arange(h) + 0.5) * res
    clon = lon0 + (np.arange(w) + 0.5) * res
    for m in range(12):
        g = grid12[m]
        bad = ~np.isfinite(g)
        idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
        g = g[tuple(idx)]
        f = RegularGridInterpolator((rows, cols), g, bounds_error=False, fill_value=None)
        PY, PX = np.meshgrid(clat, clon, indexing="ij")
        out[m] = f(np.stack([PY.ravel(), PX.ravel()], axis=1)).reshape(h, w)
    return out


@step("pluie mensuelle")
def rain_series(grid, cfg, country, fetch):
    """Pluie mensuelle (T, h, w) de novembre de la 1re saison au dernier mois complet. Les mois de novembre à avril viennent de monthly_series.npz."""
    ms = load_grid(grid_dir(country) / "monthly_series.npz")
    years = [int(y) for y in ms["years"]]
    smonths = [int(m) for m in ms["months"]]          # 11 12 1 2 3 4
    have = {}
    for yi, y in enumerate(years):
        for k, m in enumerate(smonths):
            yy = y - 1 if m >= 11 else y
            have[(yy, m)] = np.asarray(ms["arr"][yi, k], dtype="float32")
    first = (years[0] - 1, 11)
    today = dt.date.today()
    last = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    ym, order = first, []
    while ym <= last:
        order.append(ym)
        ym = (ym[0] + (ym[1] == 12), ym[1] % 12 + 1)
    need = [x for x in order if x not in have]

    def one(x):
        try:
            return x, fetch(x[0], x[1], cfg)
        except Exception as e:  # noqa: BLE001
            print("  échec pluie", x, str(e)[:100])
            return x, None
    with ThreadPoolExecutor(max_workers=6) as ex:
        for x, a in ex.map(one, need):
            if a is not None:
                have[x] = a
    # on s'arrête au premier mois manquant (série continue)
    series, labels = [], []
    for x in order:
        a = have.get(x)
        if a is None or a.shape != (grid["h"], grid["w"]):
            break
        series.append(a)
        labels.append(f"{x[0]}-{x[1]:02d}")
    STATUS["rain"] = {"first": labels[0], "last": labels[-1], "months": len(labels), "fetched": len([x for x in need if x in have])}
    return np.stack(series), labels


def zone_means(units, leaf_vals: dict, level_keys=("adm1", "adm2", "adm3")):
    """Moyenne pondérée par la surface des valeurs des fokontany, pour chaque région, district et commune."""
    leaves = units[units.level == 4].reset_index(drop=True)
    out = {}
    wts = leaves.area_km2.fillna(1.0).to_numpy()
    for key in level_keys:
        grp = leaves.groupby(key).indices
        for pc, ix in grp.items():
            if not pc:
                continue
            out[pc] = {n: _wmean(v[ix], wts[ix]) for n, v in leaf_vals.items()}
    return out


def _wmean(v, w):
    ok = np.isfinite(v)
    return float(np.sum(v[ok] * w[ok]) / np.sum(w[ok])) if ok.any() and np.sum(w[ok]) > 0 else np.nan


def main(country="mdg", readers=None, max_et0_batches=150):
    cfg = load_config(country)
    ms = load_grid(grid_dir(country) / "monthly_series.npz")
    h, w = ms["arr"].shape[-2:]
    grid = {"lon0": float(ms["lon0"]), "lat0": float(ms["lat0"]), "res": float(ms["res"]), "h": int(h), "w": int(w)}
    rd = {"soil": read_soilgrids, "landcover": read_worldcover, "et0": read_et0_points, "chirps": read_chirps_month}
    rd.update(readers or {})
    out_dir = country_docs_dir(country) / "soilwater"
    out_dir.mkdir(parents=True, exist_ok=True)
    land = np.isfinite(np.asarray(ms["arr"][-1, 0], dtype="float32"))
    props = static_props(grid, rd, grid_dir(country) / "soilprops.npz")
    et0 = et0_grid(grid, land, rd, grid_dir(country) / "et0_cache.json", max_et0_batches) if props is not None else None
    rain = rain_series(grid, cfg, country, rd["chirps"]) if props is not None else None
    status_path = out_dir / "status.json"
    STATUS["generated"] = dt.date.today().isoformat()
    if props is None or et0 is None or rain is None:
        write_json(status_path, STATUS)
        print("Bilan hydrique non calculé : voir status.json")
        return None
    P, labels = rain
    T = P.shape[0]
    valid = land & np.isfinite(props["whc"]) & np.isfinite(et0[0]) & (props["whc"] > 0)
    Pc = np.nan_to_num(P[:, valid], nan=0.0).astype("float64")
    pet = np.stack([et0[m][valid] for m in range(12)]).astype("float64")
    W, A, X = C.run_balance(Pc, pet, props["whc"][valid].astype("float64"), month0=11)
    rel = W / props["whc"][valid][None, :]                         # stock relatif (0-1)
    month0 = 11
    sm_z = C.monthly_standardized(rel, month0)
    rech12 = C.rolling_sum(X, 12)
    rz = C.monthly_standardized(rech12, month0)
    spi_full = {f"spi{n}": C.spi(Pc, n, month0) for n in (3, 6, 12)}
    spis = {k: v[T - 1] for k, v in spi_full.items()}                       # SPI de l'OMM sur le dernier mois complet
    last = T - 1
    cal = np.array([(month0 - 1 + t) % 12 for t in range(T)])
    smn = np.stack([np.nanmean(rel[cal == m], axis=0) for m in range(12)])       # normale mensuelle du stock relatif
    # --- valeurs par fokontany (cellule du centroïde), puis par zone ---
    units = read_units(country)
    leaves = units[units.level == 4].reset_index(drop=True)
    from common import sample_grid
    idx_valid = -np.ones((h, w), dtype=int)
    idx_valid[valid] = np.arange(valid.sum())

    def leaf_series(arr2d_or_1d, full=None):
        g = np.full((h, w), np.nan)
        g[valid] = arr2d_or_1d
        return sample_grid(g, grid["lon0"], grid["lat0"], grid["res"], leaves.lon.to_numpy(), leaves.lat.to_numpy())
    lv = {"whc_mm": sample_grid(np.where(valid, props["whc"], np.nan), grid["lon0"], grid["lat0"], grid["res"], leaves.lon.to_numpy(), leaves.lat.to_numpy()),
          "cn2": sample_grid(np.where(valid, props["cn2"], np.nan), grid["lon0"], grid["lat0"], grid["res"], leaves.lon.to_numpy(), leaves.lat.to_numpy()),
          "sm_rel_pct": leaf_series(100 * rel[last]), "sm_z": leaf_series(sm_z[last]), "recharge12_mm": leaf_series(rech12[last]), "recharge12_z": leaf_series(rz[last])}
    for k, v in spis.items():
        lv[k] = leaf_series(v)
    zm = zone_means(units, lv)
    try:                                                                   # historique SPI par région (moyenne des fokontany) pour la validation
        recs = []
        start = max(0, T - 12 * 12)
        for t in range(start, T):
            ym = (labels[t] if isinstance(labels[t], str) else str(labels[t]))
            row = {k: leaf_series(v[t]) for k, v in spi_full.items()}
            dfm = pd.DataFrame({"adm1": leaves.adm1.values, **row})
            g = dfm.groupby("adm1").mean().reset_index()
            g.insert(0, "mois", ym)
            recs.append(g)
        from common import DATA_DIR
        vd = DATA_DIR.parent / "validation"
        vd.mkdir(exist_ok=True)
        pd.concat(recs).round(2).to_csv(vd / "spi_regions.csv", index=False)
    except Exception as ex:  # noqa: BLE001
        print("historique SPI non écrit :", ex)
    rows = []
    date = dt.date.today().isoformat()
    for i, pc in enumerate(leaves.pcode):
        for k, v in lv.items():
            if np.isfinite(v[i]):
                rows.append((pc, k, round(float(v[i]), 2), date))
    for pc, d in zm.items():
        for k, v in d.items():
            if np.isfinite(v):
                rows.append((pc, k, round(v, 2), date))
    ext = pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur", "date"])
    ext["source"] = "CHIRPS, ERA5-Land (ET0), SoilGrids, WorldCover : bilan de Thornthwaite-Mather (MakyClimat)"
    ed = country_data_dir(country) / "external"
    ed.mkdir(parents=True, exist_ok=True)
    ext.to_csv(ed / "soilwater.csv", index=False)
    # --- séries : 36 derniers mois et normale mensuelle par région, district, commune ---
    n36 = min(36, T)
    ser_sm = {k: leaf_series(100 * rel[t]) for k, t in enumerate(range(T - n36, T))}
    ser_rz = {k: leaf_series(np.nan_to_num(rz[t], nan=np.nan)) for k, t in enumerate(range(T - n36, T))}
    ser_n = {m: leaf_series(100 * smn[m]) for m in range(12)}
    zones = {}
    for name, dct in (("sm", ser_sm), ("rz", ser_rz), ("n", ser_n)):
        for key, vals in dct.items():
            z = zone_means(units, {"v": vals})
            for pc, d in z.items():
                zones.setdefault(pc, {}).setdefault(name, {})[key] = d["v"]
    U = {}
    for pc, d in zones.items():
        U[pc] = {"sm": [None if not np.isfinite(d["sm"].get(k, np.nan)) else int(round(d["sm"][k])) for k in range(n36)],
                 "rz": [None if not np.isfinite(d["rz"].get(k, np.nan)) else round(float(d["rz"][k]), 1) for k in range(n36)],
                 "n": [None if not np.isfinite(d["n"].get(m, np.nan)) else int(round(d["n"][m])) for m in range(12)]}
    write_json(out_dir / "series.json", {"months": labels[-n36:], "month_numbers": [int(l[5:]) for l in labels[-n36:]], "u": U})
    STATUS["summary"] = {"dernier_mois": labels[-1], "cellules_calculées": int(valid.sum()), "zones": len(U),
                         "stock_relatif_moyen_pct": round(float(np.nanmean(100 * rel[last])), 1)}
    write_json(status_path, STATUS)
    print("Bilan hydrique OK :", STATUS["summary"])
    return {"rel": rel, "sm_z": sm_z, "rz": rz, "X": X, "ext": ext, "labels": labels, "valid": valid, "props": props, "series": U}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--max-et0-batches", type=int, default=150)
    a = ap.parse_args()
    main(a.country, max_et0_batches=a.max_et0_batches)
