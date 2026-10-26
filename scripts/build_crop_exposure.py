"""Cultures et bâti exposés aux crues : croisement de l'occupation du sol (ESA WorldCover 2021, 10 m) et de la hauteur au-dessus du
cours d'eau le plus proche (HAND, calculée par MakyClimat depuis Copernicus GLO-90, 0,005°).

Pourquoi : la table d'exposition aux crues de HeiGIT a une colonne « cultures » entièrement à zéro pour Madagascar (non renseignée à la source).
Plutôt que de publier des zéros, on calcule nous-mêmes :
  cult_ha            surface cultivée (ha) de l'unité (WorldCover classe 40 « Cropland »)
  cult_basse5_ha     surface cultivée à moins de 5 m au-dessus d'un cours d'eau (ha)
  cult_basse15_ha    idem à moins de 15 m
  cult_basse5_pct    part de la surface cultivée à moins de 5 m (%)
  cult_basse15_pct   idem à moins de 15 m
  bati_ha, bati_basse5_ha, bati_basse5_pct   même calcul pour le bâti (classe 50 « Built-up »)
Limites : EXPOSITION topographique (zone basse près d'un cours d'eau), pas une hauteur d'eau ni un dégât ; HAND à 0,005° (~550 m) ;
les fractions WorldCover sont moyennées par cellule ; WorldCover distingue mal rizières et autres cultures ; pas de calendrier cultural ici.
Sortie : data/<pays>/external/cultures.csv (tous les niveaux, avec cumul vers communes, districts et régions).
Usage : python scripts/build_crop_exposure.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

import numpy as np
import pandas as pd

from common import country_data_dir, country_docs_dir, grid_dir, read_units

SRC = ("ESA WorldCover 2021 (10 m) croisé avec la HAND de MakyClimat (Copernicus GLO-90) : exposition topographique, "
       "pas une hauteur d'eau ni un dégât")
CROP, BUILT = 40, 50


def cell_area_ha(lat0: float, res: float, h: int) -> np.ndarray:
    lats = lat0 - (np.arange(h) + 0.5) * res
    return ((res * 111.32) ** 2 * np.cos(np.deg2rad(lats)) * 100.0)       # ha par cellule, par ligne


def per_unit(ids: np.ndarray, frac: dict, hand: np.ndarray, sea: np.ndarray, area_row: np.ndarray, n: int) -> pd.DataFrame:
    """Surfaces (ha) par identifiant d'unité (1..n-1), toutes cellules de terre. frac : {"cult": (h,w), "bati": (h,w)}."""
    h, w = ids.shape
    area = np.repeat(area_row[:, None], w, axis=1)
    land = ~sea
    ok = (ids > 0) & land
    h5 = np.isfinite(hand) & (hand < 5)
    h15 = np.isfinite(hand) & (hand < 15)
    out = {}
    for k, f in frac.items():
        f = np.nan_to_num(f)
        ha = f * area
        out[f"{k}_ha"] = np.bincount(ids[ok], weights=ha[ok], minlength=n)
        out[f"{k}_basse5_ha"] = np.bincount(ids[ok & h5], weights=ha[ok & h5], minlength=n)
        out[f"{k}_basse15_ha"] = np.bincount(ids[ok & h15], weights=ha[ok & h15], minlength=n)
    return pd.DataFrame(out)


def rollup(leaf: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    """leaf : index pcode (fokontany) avec colonnes *_ha ; renvoie lignes pour tous les niveaux + pourcentages."""
    pairs = units[units.level == 4].set_index("pcode")[["adm1", "adm2", "adm3"]]
    d = leaf.join(pairs)
    parts = [leaf.assign(level_key=leaf.index)]
    for col in ("adm3", "adm2", "adm1"):
        g = d.groupby(col)[list(leaf.columns)].sum()
        g["level_key"] = g.index
        parts.append(g)
    allu = pd.concat(parts)
    allu = allu[~allu.index.duplicated(keep="first")].drop(columns="level_key")
    for k in ("cult", "bati"):
        tot = allu[f"{k}_ha"].where(allu[f"{k}_ha"] > 0)
        allu[f"{k}_basse5_pct"] = 100 * allu[f"{k}_basse5_ha"] / tot
        if k == "cult":
            allu["cult_basse15_pct"] = 100 * allu["cult_basse15_ha"] / tot
    return allu


def to_rows(allu: pd.DataFrame) -> pd.DataFrame:
    keep = ["cult_ha", "cult_basse5_ha", "cult_basse15_ha", "cult_basse5_pct", "cult_basse15_pct", "bati_ha", "bati_basse5_ha", "bati_basse5_pct"]
    long = allu[keep].reset_index(names="pcode").melt(id_vars="pcode", var_name="indicateur", value_name="valeur").dropna()
    long["valeur"] = long.valeur.round(2)
    long["date"] = dt.date.today().isoformat()
    long["source"] = SRC
    return long


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    a = ap.parse_args()
    import rasterio.features
    from affine import Affine
    from shapely.geometry import shape

    import build_soilwater as BS
    import soilwater_core as C
    z = np.load(grid_dir(a.country) / "hydro.npz", allow_pickle=False)
    hand, sea = z["hand"].astype("float32"), z["sea"]
    lon0, lat0, res = float(z["lon0"]), float(z["lat0"]), float(z["res"])
    h, w = hand.shape
    fr = BS.read_worldcover({"h": h, "w": w, "res": res, "lon0": lon0, "lat0": lat0}, sub=4)
    frac = {"cult": fr[C.LC_CLASSES.index(CROP)], "bati": fr[C.LC_CLASSES.index(BUILT)]}
    print(f"surface cultivée selon WorldCover : {np.nansum(frac['cult'] * cell_area_ha(lat0, res, h)[:, None]) / 1e6:.2f} millions d'ha")
    units = read_units(a.country)
    leaves = units[units.level == 4].reset_index(drop=True)
    geoms = {}
    for f in sorted((country_docs_dir(a.country) / "geo" / "adm4").glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            geoms[ft["properties"]["c"]] = shape(ft["geometry"])
    shapes = [(geoms[c], i + 1) for i, c in enumerate(leaves.pcode) if c in geoms]
    ids = rasterio.features.rasterize(shapes, out_shape=(h, w), transform=Affine(res, 0, lon0, 0, -res, lat0), fill=0, dtype="int32")
    n = len(leaves) + 1
    area_row = cell_area_ha(lat0, res, h)
    df = per_unit(ids, frac, hand, sea, area_row, n).iloc[1:].reset_index(drop=True)
    df.index = leaves.pcode.values
    # fokontany plus petits qu'une cellule : cellule du centroïde, surface = surface de l'unité
    cnt = np.bincount(ids[(ids > 0) & ~sea], minlength=n)[1:]
    for i in np.where(cnt == 0)[0]:
        r = int(np.clip((lat0 - leaves.lat.values[i]) / res, 0, h - 1))
        c = int(np.clip((leaves.lon.values[i] - lon0) / res, 0, w - 1))
        if sea[r, c]:
            continue
        ha = float(leaves.area_km2.values[i]) * 100.0
        for k in ("cult", "bati"):
            f = float(np.nan_to_num(frac[k][r, c]))
            df.iloc[i, df.columns.get_loc(f"{k}_ha")] = f * ha
            df.iloc[i, df.columns.get_loc(f"{k}_basse5_ha")] = f * ha * float(np.isfinite(hand[r, c]) and hand[r, c] < 5)
            df.iloc[i, df.columns.get_loc(f"{k}_basse15_ha")] = f * ha * float(np.isfinite(hand[r, c]) and hand[r, c] < 15)
    allu = rollup(df, units)
    rows = to_rows(allu)
    ext = country_data_dir(a.country) / "external"
    rows.to_csv(ext / "cultures.csv", index=False)
    nat = allu.loc[[p for p in allu.index if len(p) == 4]].sum(numeric_only=True)
    print(f"Cultures : {nat.cult_ha / 1e6:.2f} M ha, dont {100 * nat.cult_basse5_ha / nat.cult_ha:.1f} % à moins de 5 m et {100 * nat.cult_basse15_ha / nat.cult_ha:.1f} % à moins de 15 m d'un cours d'eau ; {len(rows)} valeurs")


if __name__ == "__main__":
    main()
