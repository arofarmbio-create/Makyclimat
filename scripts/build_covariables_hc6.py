"""Protocole carte des nappes, H-C6 : covariables de la recharge BGS, une ligne par maille terrestre de la carte de
recharge de l'Afrique (BGS, MacDonald et al. 2021 ; grille de 0,28°) sur Madagascar.

Fichier : data/<pays>/nappes_mondiales/covariables_hc6.csv. Chaque partie ajoute ou remplace ses colonnes ; une partie
à la fois, une requête à la fois par fournisseur (validation/etat_telechargements.md).
  --part grille     : lon, lat, recharge_bgs_mmpa (lit data/<pays>/bgs_recharge_raw/Africa_recharge.tif, hors git ;
                      à lancer sur le poste qui a le fichier) ;
  --part cru        : LTA_P_mmpa, LTA_WD_days, LTA_PET_mm, Aridity (CRU TS v4.10, UEA, licence ODbL ; moyennes
                      annuelles 1981-2010 de la maille CRU de 0,5° qui contient le centre de la maille BGS) ;
  --part geologie   : Aquifer_group (B, I, V -> Basement ; CSF, CSI, CSIF, CSK -> Sedimentary ; U ->
                      Unconsolidated) et GLG, majoritaires dans la maille (carte hydrogéologique BGS de Madagascar,
                      comme connector_geology.py) ;
  --part sol        : Soil_group, classe WRB la plus probable (SoilGrids, ISRIC, CC BY 4.0), majoritaire, sur 2 lettres ;
  --part occupation : Landcover, classe majoritaire regroupée (cropland, grassland, sparse, shrubland, forest, urban ;
                      water si l'eau domine). Globcover 2009 s'il est accessible, sinon ESA WorldCover (déjà résumé
                      dans data/<pays>/grids/soilprops.npz) ; la colonne Landcover_source le dit.
  --part ndvi       : NDVI, MOD13C2 moyenne 2001-2010 (NASA) : à venir, dans la file NASA après IMERG E1.
"""
from __future__ import annotations

import argparse
import calendar
import gzip
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from common import country_data_dir, grid_dir

BBOX = (43.0, -26.0, 51.0, -11.5)
BGS_RES = 0.28
CRU_URL = "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10/{v}/cru_ts4.10.{a}.{b}.{v}.dat.nc.gz"
DECADES = ((1981, 1990), (1991, 2000), (2001, 2010))
AQUIFER_GROUPS = {"B": "Basement", "I": "Basement", "V": "Basement", "CSF": "Sedimentary", "CSI": "Sedimentary",
                  "CSIF": "Sedimentary", "CSK": "Sedimentary", "U": "Unconsolidated"}
WRB_CODES = {"Acrisols": "AC", "Albeluvisols": "AB", "Alisols": "AL", "Andosols": "AN", "Anthrosols": "AT",
             "Arenosols": "AR", "Calcisols": "CL", "Cambisols": "CM", "Chernozems": "CH", "Cryosols": "CR",
             "Durisols": "DU", "Ferralsols": "FR", "Fluvisols": "FL", "Gleysols": "GL", "Gypsisols": "GY",
             "Histosols": "HS", "Kastanozems": "KS", "Leptosols": "LP", "Lixisols": "LX", "Luvisols": "LV",
             "Nitisols": "NT", "Phaeozems": "PH", "Planosols": "PL", "Plinthosols": "PT", "Podzols": "PZ",
             "Regosols": "RG", "Retisols": "RT", "Solonchaks": "SC", "Solonetz": "SN", "Stagnosols": "ST",
             "Technosols": "TC", "Umbrisols": "UM", "Vertisols": "VR"}
WC_GROUPS = {10: "forest", 95: "forest", 20: "shrubland", 30: "grassland", 40: "cropland", 50: "urban", 60: "sparse",
             80: "water", 90: "water"}


def out_path(country: str) -> Path:
    return country_data_dir(country) / "nappes_mondiales" / "covariables_hc6.csv"


# ---------- grille BGS ----------
def bgs_cells(a: np.ndarray, left: float, top: float, res: float, nodata) -> pd.DataFrame:
    """Raster de recharge (nord en haut) -> mailles valides dont le centre est dans l'emprise de Madagascar."""
    rows = []
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            v = float(a[i, j])
            lon, lat = left + (j + 0.5) * res, top - (i + 0.5) * res
            ok = np.isfinite(v) and (nodata is None or v != nodata) and v > -1e30
            if ok and BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]:
                rows.append((round(lon, 4), round(lat, 4), round(v, 2)))
    return pd.DataFrame(rows, columns=["lon", "lat", "recharge_bgs_mmpa"])


def part_grille(country: str) -> pd.DataFrame:
    import rasterio
    from rasterio.windows import from_bounds
    tif = country_data_dir(country) / "bgs_recharge_raw" / "Africa_recharge.tif"
    with rasterio.open(tif) as s:
        w = from_bounds(BBOX[0] - BGS_RES, BBOX[1] - BGS_RES, BBOX[2] + BGS_RES, BBOX[3] + BGS_RES, s.transform)
        w = w.round_offsets().round_lengths()
        a, t = s.read(1, window=w), s.window_transform(w)
        return bgs_cells(a, t.c, t.f, t.a, s.nodata)


def cell_points(lon: float, lat: float, n: int = 7) -> tuple[np.ndarray, np.ndarray]:
    """n x n points régulièrement répartis dans la maille BGS (pour les majorités)."""
    off = (np.arange(n) + 0.5) / n * BGS_RES - BGS_RES / 2
    xs, ys = np.meshgrid(lon + off, lat + off)
    return xs.ravel(), ys.ravel()


def majority(values) -> object:
    v = [x for x in values if x is not None and x == x and x != ""]
    return Counter(v).most_common(1)[0][0] if v else None


# ---------- CRU ----------
def cru_annual(monthly: np.ndarray, years: list[int], months: list[int], var: str) -> float:
    """Moyenne annuelle 1981-2010 d'une maille : pre et wet sommés par année ; pet (mm/jour) x jours du mois, sommé."""
    vals = np.asarray(monthly, float)
    if var == "pet":
        vals = vals * np.array([calendar.monthrange(y, m)[1] for y, m in zip(years, months)])
    s = pd.Series(vals).groupby(np.asarray(years)).sum(min_count=12)
    return float(s.mean())


def part_cru(df: pd.DataFrame) -> pd.DataFrame:
    import requests
    import xarray as xr
    out = {}
    for var in ("pre", "wet", "pet"):
        series = []
        for a, b in DECADES:                                        # un fichier à la fois
            with tempfile.TemporaryDirectory() as tmp:
                gz, nc = Path(tmp) / "f.nc.gz", Path(tmp) / "f.nc"
                with requests.get(CRU_URL.format(v=var, a=a, b=b), stream=True, timeout=600) as r:
                    r.raise_for_status()
                    with open(gz, "wb") as fo:
                        shutil.copyfileobj(r.raw, fo)
                with gzip.open(gz, "rb") as fi, open(nc, "wb") as fo:
                    shutil.copyfileobj(fi, fo)
                ds = xr.open_dataset(nc)
                sub = ds[var].sel(lon=slice(BBOX[0] - 1, BBOX[2] + 1), lat=slice(BBOX[1] - 1, BBOX[3] + 1)).load()
                series.append(sub)
                ds.close()
            print(f"  CRU {var} {a}-{b} lu", flush=True)
        da = xr.concat(series, dim="time")
        yrs = list(pd.DatetimeIndex(da.time.values).year)
        mos = list(pd.DatetimeIndex(da.time.values).month)
        out[var] = [cru_annual(da.sel(lon=lo, lat=la, method="nearest").values, yrs, mos, var)
                    for lo, la in zip(df.lon, df.lat)]
    df = df.copy()
    df["LTA_P_mmpa"] = np.round(out["pre"], 1)
    df["LTA_WD_days"] = np.round(out["wet"], 1)
    df["LTA_PET_mm"] = np.round(out["pet"], 1)
    df["Aridity"] = np.round(df.LTA_P_mmpa / df.LTA_PET_mm, 3)
    return df


# ---------- géologie BGS ----------
def aquifer_group(hgcomb: str | None) -> str | None:
    """« B-L/LM » -> Basement ; code de type avant le tiret."""
    if not hgcomb or hgcomb != hgcomb:
        return None
    return AQUIFER_GROUPS.get(str(hgcomb).split("-")[0].strip().upper())


def part_geologie(df: pd.DataFrame) -> pd.DataFrame:
    import geopandas as gpd
    import connector_geology as G
    with tempfile.TemporaryDirectory() as tmp:
        g = G.read_hydrogeology(G.fetch_shapefile_dir(Path(tmp))).to_crs("EPSG:4326")
    pts = []
    for k, (lo, la) in enumerate(zip(df.lon, df.lat)):
        xs, ys = cell_points(lo, la)
        pts += [(k, x, y) for x, y in zip(xs, ys)]
    p = gpd.GeoDataFrame({"k": [x[0] for x in pts]}, geometry=gpd.points_from_xy([x[1] for x in pts], [x[2] for x in pts]),
                         crs="EPSG:4326")
    j = gpd.sjoin(p, g, how="left", predicate="within")
    df = df.copy()
    df["Aquifer_group"] = [majority([aquifer_group(h) for h in j.loc[j.k == k, "HGComb"]]) for k in range(len(df))]
    df["GLG"] = [majority(j.loc[j.k == k, "GLG"]) if "GLG" in j else None for k in range(len(df))]
    return df


# ---------- sols SoilGrids ----------
SOIL_VRT = "https://files.isric.org/soilgrids/latest/data/wrb/MostProbable.vrt"
SOIL_QML = "https://files.isric.org/soilgrids/latest/data/wrb/MostProbable.qml"


def wrb_legend(qml_text: str) -> dict[int, str]:
    """Légende QGIS (value="3" label="Arenosols") -> {3: "AR"}."""
    import re
    out = {}
    for v, lab in re.findall(r'value="(\d+)"[^>]*label="([A-Za-z]+)"', qml_text):
        code = WRB_CODES.get(lab.strip().capitalize())
        if code:
            out[int(v)] = code
    return out


def read_scale(pixel: float, geographic: bool) -> int:
    """Facteur de réduction pour lire environ 1 km par pixel. La carte WRB est en degrés (0,002°) : un calcul en mètres
    la ramenait à un seul pixel et donnait la même classe partout (02/11/2026)."""
    target = 0.01 if geographic else 1000.0
    return max(1, int(round(target / pixel)))


def part_sol(df: pd.DataFrame) -> pd.DataFrame:
    """Une seule lecture réduite (environ 1 km) de la carte WRB sur l'emprise, puis échantillonnage local."""
    import rasterio
    import requests
    from rasterio.enums import Resampling
    from rasterio.warp import transform as warp
    from rasterio.windows import from_bounds
    legend = wrb_legend(requests.get(SOIL_QML, timeout=120).text)
    if not legend:
        raise RuntimeError("légende WRB de SoilGrids illisible")
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="5"):
        with rasterio.open("/vsicurl/" + SOIL_VRT) as s:
            cx = [BBOX[0], BBOX[2], BBOX[0], BBOX[2]]
            cy = [BBOX[1], BBOX[1], BBOX[3], BBOX[3]]
            X, Y = warp("EPSG:4326", s.crs, cx, cy)
            win = from_bounds(min(X), min(Y), max(X), max(Y), s.transform).round_offsets().round_lengths()
            scale = read_scale(abs(s.transform.a), s.crs.is_geographic)     # pixels d'environ 1 km
            shape = (max(1, int(win.height // scale)), max(1, int(win.width // scale)))
            a = s.read(1, window=win, out_shape=shape, resampling=Resampling.nearest)
            t = s.window_transform(win) * rasterio.Affine.scale(win.width / shape[1], win.height / shape[0])
            crs = s.crs
    codes = []
    for lo, la in zip(df.lon, df.lat):
        xs, ys = cell_points(lo, la, 5)
        X, Y = warp("EPSG:4326", crs, list(xs), list(ys))
        inv = ~t
        vals = []
        for x, y in zip(X, Y):
            c, r = inv * (x, y)
            r, c = int(r), int(c)
            vals.append(legend.get(int(a[r, c])) if 0 <= r < a.shape[0] and 0 <= c < a.shape[1] else None)
        codes.append(majority(vals))
    df = df.copy()
    df["Soil_group"] = codes
    return df


# ---------- occupation du sol ----------
GLOBCOVER_URL = "http://due.esrin.esa.int/files/Globcover2009_V2.3_Global_.zip"


def worldcover_group(fractions: dict[int, float]) -> str | None:
    """Fractions par classe WorldCover -> groupe majoritaire (somme des fractions par groupe)."""
    acc = Counter()
    for c, f in fractions.items():
        g = WC_GROUPS.get(int(c))
        if g and f > 0:
            acc[g] += f
    return acc.most_common(1)[0][0] if acc else None


def part_occupation(df: pd.DataFrame, country: str) -> pd.DataFrame:
    import requests
    import soilwater_core as SC
    try:
        ok = requests.head(GLOBCOVER_URL, timeout=30, allow_redirects=True).status_code == 200
    except requests.RequestException:
        ok = False
    if ok:
        print("Globcover 2009 accessible, mais son traitement n'est pas encore écrit : WorldCover utilisé", flush=True)
    sp = np.load(grid_dir(country) / "soilprops.npz")
    ms = np.load(grid_dir(country) / "monthly_series.npz")
    lcf = sp["lcfrac"].astype("float32")                                     # (classes, h, w), grille 0,05°
    lon0, lat0, res = float(ms["lon0"]), float(ms["lat0"]), float(ms["res"])
    h, w = lcf.shape[1:]
    clat = lat0 - (np.arange(h) + 0.5) * res
    clon = lon0 + (np.arange(w) + 0.5) * res
    groups = []
    for lo, la in zip(df.lon, df.lat):
        ri = np.where(np.abs(clat - la) <= BGS_RES / 2)[0]
        ci = np.where(np.abs(clon - lo) <= BGS_RES / 2)[0]
        fr = {c: float(np.nansum(lcf[k][np.ix_(ri, ci)])) for k, c in enumerate(SC.LC_CLASSES)}
        groups.append(worldcover_group(fr))
    df = df.copy()
    df["Landcover"] = groups
    df["Landcover_source"] = "ESA WorldCover 2021 (Globcover 2009 " + ("accessible mais non traité)" if ok else "inaccessible)")
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--part", required=True, choices=["grille", "cru", "geologie", "sol", "occupation"])
    args = ap.parse_args()
    path = out_path(args.country)
    if args.part == "grille":
        df = part_grille(args.country)
    else:
        df = pd.read_csv(path)
        df = {"cru": part_cru, "geologie": part_geologie, "sol": part_sol}.get(args.part, None)(df) \
            if args.part != "occupation" else part_occupation(df, args.country)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"{path.name} : {len(df)} mailles, colonnes {list(df.columns)}")


if __name__ == "__main__":
    main()
