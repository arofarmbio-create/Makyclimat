"""Connecteur géologie et type d'aquifère : carte hydrogéologique nationale de Madagascar (BGS Africa Groundwater Atlas).

Source : British Geological Survey, Africa Groundwater Atlas — "Africa Groundwater Atlas Country Hydrogeology Maps"
(MacDonald et al./BGS, publié 2019-2021), shapefile Madagascar à l'échelle 1:5 000 000.
Téléchargement : la page de téléchargement existe sous deux domaines proches (africangroundwateratlas.org et
africagroundwateratlas.org, orthographe variable selon le miroir) et le nom exact du fichier a changé au moins une
fois ; plutôt que de figer une URL qui casse au premier changement, ce connecteur lit la page de téléchargement et
en extrait lui-même le lien « Madagascar » (gratuit, pas d'inscription).
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
import re
import zipfile
from pathlib import Path

import pandas as pd
import requests

from common import country_data_dir, read_units

DOWNLOAD_PAGES = ["https://africagroundwateratlas.org/downloadGIS.html", "https://africangroundwateratlas.org/downloadGIS.html"]
SOURCE = ("British Geological Survey, Africa Groundwater Atlas Country Hydrogeology Maps (1:5 000 000), licence CC BY-SA — "
          "https://africagroundwateratlas.org/ ; échelle continentale, pas un sondage de terrain, voir validation/groundwater_limites.md")
H = {"User-Agent": "MakyClimat (projet de doctorat climat Madagascar ; contact : voir dépôt GitHub arofarmbio-create/Makyclimat)"}


def find_madagascar_zip_url() -> str:
    """Lit la page de téléchargement de l'Atlas et en extrait le lien « Madagascar » (le nom exact du fichier et le
    domaine ont déjà changé une fois ; on ne les fige donc pas en dur)."""
    last_err: Exception | None = None
    for page_url in DOWNLOAD_PAGES:
        try:
            r = requests.get(page_url, timeout=60, headers=H)
            r.raise_for_status()
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
        m = re.search(r'href="([^"]*[Mm]adagascar[^"]*\.zip)"', r.text)
        if m:
            url = m.group(1)
            return url if url.startswith("http") else re.sub(r"/[^/]*$", "/" + url.lstrip("/"), page_url)
    raise RuntimeError(f"lien Madagascar introuvable sur {DOWNLOAD_PAGES} (dernière erreur : {last_err})")

# productivité (classes documentées du User Guide BGS Africa Groundwater Atlas) : rang 0-100 et débit médian indicatif (L/s)
PRODUCTIVITY = {
    "VL": (10, 0.05), "L": (30, 0.3), "LM": (50, 1.25), "M": (70, 3.5), "H": (85, 12.5), "VH": (95, 30.0),
}


def fetch_shapefile_dir(tmp: Path) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    zip_url = find_madagascar_zip_url()
    r = requests.get(zip_url, timeout=120, headers=H)
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
    # Les shapefiles pays de l'Atlas préfixent parfois les champs par le nom du pays
    # (ex. Madagascar -> "MadGLG"/"MadHGComb" au lieu de "GLG"/"HGComb") : on cherche
    # une correspondance qui se termine par le nom du champ, pas une égalité stricte.
    col_glg = next((c for c in g.columns if c.upper().endswith("GLG")), None)
    col_hg = next((c for c in g.columns if c.upper().endswith("HGCOMB") or c.upper().endswith("HG_COMB")), None)
    if col_hg is None:
        raise RuntimeError(f"champ HGComb introuvable (colonnes disponibles : {list(g.columns)})")
    g = g.rename(columns={col_hg: "HGComb", **({col_glg: "GLG"} if col_glg else {})})
    return g[["HGComb"] + (["GLG"] if "GLG" in g.columns else []) + ["geometry"]]


def productivity_value(hgcomb: str) -> tuple[float, float] | None:
    """Extrait (rang 0-100, débit médian L/s) depuis un champ HGComb du type "B-L/LM" (type
    d'aquifère "B", productivité "L" à "LM" — le BGS combine parfois deux classes adjacentes pour
    indiquer une fourchette de productivité plutôt qu'une classe unique "B-L"). On moyenne les
    classes reconnues de la fourchette ; si aucune n'est reconnue, on ne produit pas de valeur."""
    if not isinstance(hgcomb, str) or "-" not in hgcomb:
        return None
    tail = hgcomb.split("-", 1)[-1].strip().upper()
    codes = [c.strip() for c in tail.split("/") if c.strip() in PRODUCTIVITY]
    if not codes:
        return None
    pcts = [PRODUCTIVITY[c][0] for c in codes]
    ylds = [PRODUCTIVITY[c][1] for c in codes]
    return sum(pcts) / len(pcts), sum(ylds) / len(ylds)


def sample_points(g, lons, lats) -> list[str | None]:
    import geopandas as gpd
    from shapely.geometry import Point
    pts = gpd.GeoDataFrame(geometry=[Point(lo, la) for lo, la in zip(lons, lats)], crs=4326)
    joined = gpd.sjoin(pts, g, how="left", predicate="within")
    joined = joined.loc[~joined.index.duplicated()]
    result = joined.reindex(range(len(lons))).get("HGComb")
    n_matched = int(result.notna().sum()) if result is not None else 0
    if n_matched == 0:
        # Diagnostic (27/10/2026) : le point-dans-polygone "within" ne trouve aucune correspondance.
        # On retente avec "intersects" (plus tolérant aux géométries limites/invalides) avant d'abandonner.
        joined2 = gpd.sjoin(pts, g, how="left", predicate="intersects")
        joined2 = joined2.loc[~joined2.index.duplicated()]
        result2 = joined2.reindex(range(len(lons))).get("HGComb")
        n2 = int(result2.notna().sum()) if result2 is not None else 0
        print(f"[diag] sjoin within=0 match ; intersects={n2} match sur {len(lons)} points ; "
              f"g.crs={g.crs} ; g bounds={tuple(round(x, 2) for x in g.total_bounds)} ; "
              f"exemples HGComb bruts={list(g['HGComb'].dropna().unique()[:10])}")
        if n2 > 0:
            return result2
    return result


def compute(g, leaves: pd.DataFrame) -> pd.DataFrame:
    hg = sample_points(g, leaves.lon.to_numpy(), leaves.lat.to_numpy())
    rows = []
    date = dt.date.today().isoformat()
    n_hg_notna = 0
    n_code_none = 0
    for pc, h in zip(leaves.pcode, hg):
        if isinstance(h, str):
            n_hg_notna += 1
        val = productivity_value(h)
        if val is None:
            if isinstance(h, str):
                n_code_none += 1
            continue
        pct, yld = val
        rows.append((pc, "aquifer_productivity_pct", pct, date))
        rows.append((pc, "aquifer_yield_lsec_mid", yld, date))
    out = pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur", "date"])
    out["source"] = SOURCE
    if out.empty:
        examples = [h for h in hg if isinstance(h, str)][:15]
        print(f"[diag] fokontany avec HGComb assigné (non-null) : {n_hg_notna}/{len(leaves)} ; "
              f"parmi eux, productivity_value() a échoué pour {n_code_none} ; "
              f"exemples de valeurs HGComb brutes rencontrées : {examples}")
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
