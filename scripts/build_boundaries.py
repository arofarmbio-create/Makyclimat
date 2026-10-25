"""Connecteur LIMITES : télécharge les limites administratives (OCHA COD-AB, via HDX) jusqu'au niveau 4
(fokontany pour Madagascar), les simplifie et écrit les fichiers du site.

Usage : python scripts/build_boundaries.py --country mdg [--local-dir DOSSIER_AVEC_SHAPEFILES]
À lancer une fois (puis seulement si les limites changent) : workflow « Construire les limites ».
"""
from __future__ import annotations

import argparse
import re
import tempfile
import zipfile
from pathlib import Path

from common import download, hdx_resources, load_config, write_boundaries, round_coords

# Tolérance de simplification (degrés) par niveau : plus fin en bas pour garder la forme des fokontany
TOLERANCE = {1: 0.004, 2: 0.002, 3: 0.0008, 4: 0.0003}


def find_polygon_shapefiles(folder: Path) -> dict[int, Path]:
    found: dict[int, Path] = {}
    for shp in folder.rglob("*.shp"):
        name = shp.name.lower()
        if "bndl" in name or "line" in name:  # fichiers de lignes
            continue
        m = re.search(r"adm(?:in)?_?([0-4])", name)
        if m:
            found[int(m.group(1))] = shp
    return found


def pick_field(columns, level: int, kinds: list[str]) -> str | None:
    cols = {c.upper(): c for c in columns}
    for k in kinds:
        key = f"ADM{level}_{k}".upper()
        if key in cols:
            return cols[key]
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--local-dir", help="Dossier contenant déjà les shapefiles (évite le téléchargement)")
    args = ap.parse_args()
    cfg = load_config(args.country)

    import geopandas as gpd

    work = Path(args.local_dir) if args.local_dir else Path(tempfile.mkdtemp(prefix="cod_ab_"))
    if not args.local_dir:
        res = hdx_resources(cfg["boundaries"]["hdx_dataset"])
        zips = [r for r in res if str(r.get("url", "")).lower().endswith(".zip")
                and "shp" in (str(r.get("name", "")) + str(r.get("url", ""))).lower()]
        if not zips:
            raise SystemExit("Aucune ressource shapefile (.zip) trouvée sur HDX : vérifier le jeu de données.")
        for i, r in enumerate(zips):
            dest = work / f"res{i}.zip"
            print("Téléchargement", r["url"])
            if download(r["url"], dest):
                with zipfile.ZipFile(dest) as z:
                    z.extractall(work / f"res{i}")

    shps = find_polygon_shapefiles(work)
    print("Niveaux trouvés :", {k: v.name for k, v in sorted(shps.items())})
    for lv in (1, 2, 3, 4):
        if lv not in shps:
            raise SystemExit(f"Shapefile du niveau {lv} introuvable.")

    layers = {}
    for lv, shp in shps.items():
        if lv == 0:
            continue
        g = gpd.read_file(shp).to_crs(4326)
        pc = pick_field(g.columns, lv, ["PCODE"])
        nm = pick_field(g.columns, lv, ["FR", "EN", "MG", "NAME"])
        if pc is None or nm is None:
            raise SystemExit(f"Champs PCODE/nom introuvables au niveau {lv} : {list(g.columns)}")
        pp = pick_field(g.columns, lv - 1, ["PCODE"]) if lv > 1 else None
        g = g.rename(columns={pc: "pcode", nm: "name"})
        g["parent"] = g[pp].astype(str) if pp else ""
        g["pcode"] = g["pcode"].astype(str)
        g["geom_s"] = g.geometry.simplify(TOLERANCE[lv], preserve_topology=True)
        # surface en km2 (projection équivalente Afrique Albers recommandée par OCHA)
        g["area_km2"] = g.geometry.to_crs("ESRI:102022").area / 1e6
        c = g.geometry.representative_point()
        g["lon"], g["lat"] = c.x, c.y
        layers[lv] = g[["pcode", "name", "parent", "area_km2", "lon", "lat", "geom_s"]].copy()
        print(f"  niveau {lv}: {len(g)} unités")

    # Lignage : adm1/adm2/adm3 de chaque unité
    parent_of = {}
    for lv in (2, 3, 4):
        parent_of.update(dict(zip(layers[lv].pcode, layers[lv].parent)))

    def ancestors(pcode: str, lv: int) -> dict:
        chain = {lv: pcode}
        cur, l = pcode, lv
        while l > 1:
            cur = parent_of.get(cur, "")
            l -= 1
            chain[l] = cur
        return chain

    units, geoms = [], {}
    for lv, df in layers.items():
        for r in df.itertuples():
            a = ancestors(r.pcode, lv)
            units.append({"level": lv, "pcode": r.pcode, "name": r.name, "parent": r.parent,
                          "adm1": a.get(1, ""), "adm2": a.get(2, ""), "adm3": a.get(3, ""),
                          "lon": round(r.lon, 5), "lat": round(r.lat, 5),
                          "area_km2": round(r.area_km2, 3)})
            geoms[r.pcode] = round_coords(r.geom_s.__geo_interface__)
    write_boundaries(args.country, units, geoms)
    print("Limites écrites :", len(units), "unités")


if __name__ == "__main__":
    main()
