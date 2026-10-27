"""Connecteur géologie et type d'aquifère : carte hydrogéologique nationale de Madagascar (BGS Africa Groundwater Atlas).

Source : British Geological Survey, Africa Groundwater Atlas — "Africa Groundwater Atlas Country Hydrogeology Maps"
(MacDonald et al./BGS, publié 2019-2021), shapefile Madagascar à l'échelle 1:5 000 000.
Téléchargement : https://africangroundwateratlas.org/downloads/Madagascar.zip (gratuit, pas d'inscription).
Licence : CC BY-SA — réutilisation et modification permises (y compris commerciale), à condition de citer la source et de
distribuer les travaux dérivés sous la même licence. Citation : « British Geological Survey. Africa Groundwater Atlas
Country Hydrogeology Maps. » Voir https://africagroundwateratlas.org/.

Champs utilisés :
  GLG     description géologique (âge, lithologie, consolidé/non consolidé) — texte, conservé tel quel.
  HGComb  type d'aquifère + classe de productivité combinés, forme "code type-code productivité" (ex. "B-L" = socle, faible
          productivité). Types : U (sédimentaire non consolidé), CSF/CSI/CSIF/CSK (sédimentaire consolidé, fractures/
          intergranulaire/karst), I (intrusif), V (volcanique), B (socle cristallin). Productivité : VH (>20 L/s), H (5-20),
          M (2-5), LM (0,5-2), L (0,1-0,5), VL (<0,1).

Méthode : point dans le polygone (centroïde de chaque fokontany) — carte à 1:5 000 000, donc une seule valeur par zone,
pas de moyenne pondérée par surface (résolution trop grossière pour ça).
Limite essentielle : échelle continentale (1:5 000 000) pensée pour une vue nationale/régionale, pas pour localiser un
site de forage précis ; aucune faille ni structure locale n'est représentée. Voir validation/groundwater_limites.md.
Sortie : data/<pays>/external/geology.csv (pcode, indicateur, valeur, date, source)
  aquifer_productivity_pct   0-100, rang indicatif de la classe de productivité (VL=10 ... VH=90), à usage de classement relatif
  aquifer_yield_lsec_mid     débit indicatif médian de la classe (L/s), ordre de grandeur, PAS une prévision de débit de forage
Usage : python scripts/connector_geology.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from common import country_data_dir, read_units

ZIP_URL = "https://africangroundwateratlas.org/downloads/Madagascar.zip"
SOURCE = ("British Geological Survey, Africa Groundwater Atlas Country Hydrogeology Maps (1:5 000 000), licence CC BY-SA — "
          "https://africangroundwateratlas.org/ ; échelle continentale, pas un sondage de terrain, voir validation/groundwater_limites.md")
H = {"User-Agent": "MakyClimat (projet de doctorat climat Madagascar ; contact : voir dépôt GitHub arofarmbio-create/Makyclimat)"}

# productivité (classes documentées du User Guide BGS Africa Groundwater Atlas) : rang 0-100 et débit médian indicatif (L/s)
PRODUCTIVITY = {
    "VL": (10, 0.05), "L": (30, 0.3), "LM": (50, 1.25), "M": (70, 3.5), "H": (85, 12.5), "VH": (95, 30.0),
}


def fetch_shapefile_dir(tmp: Path) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    r = requests.get(ZIP_URL, timeout=120, headers=H)
    r.raise_for_status()
    zipfile.ZipFile(io.BytesIO(r.content)).extractall(tmp)
    return tmp


def read_hydrogeology(shp_dir: Path):
    import geopandas as gpd
    shp = next(shp_dir.glob("**/*.shp"), None)
    if shp is None:
        raise RuntimeError("aucun fichier .shp trouvé dans l'archive téléchargée")
    g = gpd.read_file(shp)
    g = g.to_crs(4326) if g.crs else g.set_crs(4326)
    col_glg = next((c for c in g.columns if c.upper() == "GLG"), None)
    col_hg = next((c for c in g.columns if c.upper() in ("HGCOMB", "HG_COMB")), None)
    if col_hg is None:
        raise RuntimeError(f"champ HGComb introuvable (colonnes disponibles : {list(g.columns)})")
    g = g.rename(columns={col_hg: "HGComb", **({col_glg: "GLG"} if col_glg else {})})
    return g[["HGComb"] + (["GLG"] if "GLG" in g.columns else []) + ["geometry"]]


def productivity_code(hgcomb: str) -> str | None:
    if not isinstance(hgcomb, str) or "-" not in hgcomb:
        return None
    tail = hgcomb.split("-")[-1].strip().upper()
    return tail if tail in PRODUCTIVITY else None


def sample_points(g, lons, lats) -> list[str | None]:
    import geopandas as gpd
    from shapely.geometry import Point
    pts = gpd.GeoDataFrame(geometry=[Point(lo, la) for lo, la in zip(lons, lats)], crs=4326)
    joined = gpd.sjoin(pts, g, how="left", predicate="within")
    joined = joined.loc[~joined.index.duplicated()]
    return joined.reindex(range(len(lons))).get("HGComb")


def compute(g, leaves: pd.DataFrame) -> pd.DataFrame:
    hg = sample_points(g, leaves.lon.to_numpy(), leaves.lat.to_numpy())
    rows = []
    date = dt.date.today().isoformat()
    for pc, h in zip(leaves.pcode, hg):
        code = productivity_code(h)
        if code is None:
            continue
        pct, yld = PRODUCTIVITY[code]
        rows.append((pc, "aquifer_productivity_pct", pct, date))
        rows.append((pc, "aquifer_yield_lsec_mid", yld, date))
    out = pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur", "date"])
    out["source"] = SOURCE
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--tmp", default=None)
    args = ap.parse_args()
    import tempfile
    tmp = Path(args.tmp) if args.tmp else Path(tempfile.mkdtemp(prefix="geology_"))
    shp_dir = fetch_shapefile_dir(tmp)
    g = read_hydrogeology(shp_dir)
    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]
    out = compute(g, leaves)
    ext = country_data_dir(args.country) / "external"
    ext.mkdir(parents=True, exist_ok=True)
    out.to_csv(ext / "geology.csv", index=False)
    n = out.pcode.nunique()
    print(f"Géologie/aquifère (BGS Africa Groundwater Atlas) : {n}/{len(leaves)} fokontany avec une classe de productivité.")


if __name__ == "__main__":
    main()
