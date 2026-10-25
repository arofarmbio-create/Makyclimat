"""Population PRÉCISE par fokontany : somme d'une grille de population à 100 m (WorldPop) dans chaque polygone.

Par défaut, trouve automatiquement la grille sur HDX (jeu « Madagascar - Spatial Distribution of Population
2015-2030 », WorldPop R2025A, 100 m). Remplace la population du fichier OCHA COD-PS (référence 2018) et recalcule
les totaux des niveaux supérieurs. Si la grille est introuvable, la population COD-PS est conservée.

Usage : python scripts/build_population_grid.py --country mdg [--tif fichier.tif | --url URL] [--year 2025]
"""
from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from common import country_docs_dir, download, hdx_resources, load_config, read_units, units_path

HDX_POP_GRID_DATASET = "c4591e47-f0fd-4dbd-81a0-6504f97e8f56"  # WorldPop R2025A, Madagascar, 100 m


def choose_resource(resources: list[dict], year: int) -> dict | None:
    best, best_score = None, -1
    for r in resources:
        url = str(r.get("url", ""))
        text = (url + " " + str(r.get("name", ""))).lower()
        if not url.lower().endswith(".tif"):
            continue
        score = 0
        score += 10 if re.search(rf"(?<!\d){year}(?!\d)", text) else 0
        score += 5 if "100m" in text or "3arc" in text else 0
        score += 3 if "constrained" in text or "_cn_" in text else 0
        score -= 4 if "1km" in text else 0
        if score > best_score:
            best, best_score = r, score
    return best


def zonal_sum(tif: Path, polygons) -> tuple[np.ndarray, float]:
    """Somme de la grille par polygone (pixel attribué selon son centre). Retourne (sommes, total de la grille)."""
    import rasterio
    from rasterio.features import rasterize
    from rasterio.windows import Window

    n = len(polygons)
    sums = np.zeros(n + 1, dtype="float64")
    total = 0.0
    sindex = polygons.sindex
    with rasterio.open(tif) as src:
        nodata = src.nodata
        band = 1500
        for r0 in range(0, src.height, band):
            h = min(band, src.height - r0)
            win = Window(0, r0, src.width, h)
            arr = src.read(1, window=win).astype("float64")
            bad = ~np.isfinite(arr) | (arr < 0) | ((arr == nodata) if nodata is not None else False)
            arr[bad] = 0.0
            if not arr.any():
                continue
            total += arr.sum()
            tr = src.window_transform(win)
            x0, y_top = tr.c, tr.f
            x1, y_bot = x0 + tr.a * src.width, y_top + tr.e * h
            idx = list(sindex.query(__import__("shapely.geometry", fromlist=["box"]).box(
                min(x0, x1), min(y_top, y_bot), max(x0, x1), max(y_top, y_bot))))
            if not idx:
                continue
            shapes = [(polygons.geometry.iloc[i], int(i) + 1) for i in idx]
            ids = rasterize(shapes, out_shape=(h, src.width), transform=tr, fill=0, dtype="int32")
            sums += np.bincount(ids.ravel(), weights=arr.ravel(), minlength=n + 1)[: n + 1]
    return sums[1:], total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--tif")
    ap.add_argument("--url")
    ap.add_argument("--year", type=int)
    args = ap.parse_args()
    cfg = load_config(args.country)
    year = args.year or int(cfg["population"].get("grid_year", 2025))

    import geopandas as gpd

    if args.tif:
        tif, label = Path(args.tif), f"grille locale {Path(args.tif).name}"
    else:
        url = args.url
        if not url:
            res = choose_resource(hdx_resources(cfg["population"].get("grid_hdx_dataset", HDX_POP_GRID_DATASET)), year)
            if res is None:
                print("Aucune grille .tif trouvée sur HDX : population COD-PS conservée.")
                return
            url = res["url"]
        tif = Path(tempfile.mkdtemp(prefix="popgrid_")) / "pop.tif"
        print("Téléchargement de la grille :", url)
        if not download(url, tif, timeout=600):
            print("Grille introuvable (404) : population COD-PS conservée.")
            return
        label = f"WorldPop {Path(url).name}"

    units = read_units(args.country)
    geo = country_docs_dir(args.country) / "geo" / "adm4"
    parts = [gpd.read_file(f) for f in sorted(geo.glob("*.geojson"))]
    polys = pd.concat(parts, ignore_index=True)
    polys = gpd.GeoDataFrame(polys, geometry="geometry", crs=4326).reset_index(drop=True)
    print(f"{len(polys)} fokontany ; calcul des sommes de population…")
    sums, total = zonal_sum(tif, polys)
    got = float(np.sum(sums))
    print(f"Population de la grille : {total:,.0f} ; attribuée aux fokontany : {got:,.0f} ({100 * got / total:.1f} %)")
    if total <= 0 or got < 0.9 * total:
        raise SystemExit("Moins de 90 % de la population de la grille est attribuée : limites ou grille à vérifier.")

    pop_by = dict(zip(polys["c"].astype(str), sums))
    m4 = units.level == 4
    units.loc[m4, "pop"] = units.loc[m4, "pcode"].map(pop_by)
    units.loc[m4, "pop_source"] = label + " (100 m)"
    for lv, key in ((3, "adm3"), (2, "adm2"), (1, "adm1")):
        s = units[m4].groupby(key)["pop"].sum()
        mk = units.level == lv
        units.loc[mk, "pop"] = units.loc[mk, "pcode"].map(s)
        units.loc[mk, "pop_source"] = "Somme des fokontany"
    units["pop_year"] = year
    units.to_csv(units_path(args.country), index=False)
    print(f"Population mise à jour (année {year}) — total national : {units[units.level == 1]['pop'].sum():,.0f}")


if __name__ == "__main__":
    main()
