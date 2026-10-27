"""Connecteur profondeur de la nappe (niveau statique) : carte continentale publiée (MacDonald et al. 2012).

Source : "Quantitative maps of groundwater resources in Africa" (MacDonald, Bonsor, Dochartaigh & Taylor, 2012,
Environmental Research Letters, DOI 10.1088/1748-9326/7/2/024009 ; profondeur de nappe : Bonsor & MacDonald, 2011,
rapport BGS OR/11/067) — grille continentale à ~5 km, échelle nominale 1:20 000 000.
Accès : GeoTIFF via le service WCS GeoServer de l'UNESCO-IHP ("Depth to groundwater in Africa"), qui republie les
données avec l'autorisation du BGS (permis CP17/019). © British Geological Survey / NERC — tous droits réservés sur la
grille elle-même ; MakyClimat n'affiche PAS la grille mais uniquement une valeur agrégée par fokontany, avec attribution
complète et lien vers la source, conformément à l'usage prévu par cette republication.

État constaté (27/10/2026) : ce service WCS répond 404 (ressource retirée de la plateforme UNESCO-IHP). Le fichier
source a depuis été obtenu directement auprès du BGS ("Africa depth to groundwater map XYZ ASCII file",
~1 000 000 points, classes catégorielles VS/S/SM/M/D/VD) et inspecté point par point : **son emprise s'arrête à
40,8°E en latitudes sud et ne couvre PAS Madagascar** (l'île, à 43°E-51°E, n'a jamais été incluse dans cette étude
continentale — plusieurs études « Afrique » excluent explicitement les îles). Ce n'est donc pas un problème d'accès
mais une absence de couverture géographique, qu'aucun retraitement du fichier ne peut combler. Ce connecteur reste en
place (échoue proprement via le `|| echo` du workflow, voir .github/workflows/build-soilwater.yml) pour le jour où une
source propre à Madagascar (étude BRGM/PGRM, thèse, rapport de forage national) sera identifiée ; en attendant,
`water_table_depth_m` n'est pas produit et build_groundwater.py se rabat automatiquement sur les critères restants
(voir validation/groundwater_limites.md).
Limite essentielle : résolution ~5 km, modélisée à partir de la géologie et du climat (PAS de mesure de puits malgache) ;
à lire comme un ORDRE DE GRANDEUR régional de la profondeur de la nappe, jamais une prévision pour un site précis. Voir
validation/groundwater_limites.md.
Sortie : data/<pays>/external/watertable.csv (pcode, indicateur=water_table_depth_m, valeur en mètres, date, source)
Usage : python scripts/connector_watertable.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import io

import numpy as np
import pandas as pd
import requests

from common import country_data_dir, load_config, read_units

WCS_URL = "https://ihp-wins.unesco.org/geoserver/wcs"
SOURCE = ("MacDonald et al. (2012) Environ. Res. Lett. 7:024009 ; profondeur de nappe : Bonsor & MacDonald (2011) BGS OR/11/067 ; "
          "grille continentale ~5 km, republiée par l'UNESCO-IHP avec l'autorisation du British Geological Survey/NERC (© tous droits "
          "réservés sur la grille d'origine) — ordre de grandeur régional, pas une mesure locale, voir validation/groundwater_limites.md")
H = {"User-Agent": "MakyClimat (projet de doctorat climat Madagascar ; contact : voir dépôt GitHub arofarmbio-create/Makyclimat)"}


def fetch_geotiff(bbox, timeout: int = 180) -> bytes:
    lon_min, lat_min, lon_max, lat_max = bbox
    params = {
        "service": "WCS", "request": "GetCoverage", "version": "2.0.1",
        "coverageId": "geonode__depth_to_groundwater_africa1", "format": "image/tiff",
        "subset": [f"Long({lon_min},{lon_max})", f"Lat({lat_min},{lat_max})"],
        "outputCrs": "EPSG:4326",
    }
    r = requests.get(WCS_URL, params=params, timeout=timeout, headers=H)
    r.raise_for_status()
    if not r.content.startswith(b"II") and not r.content.startswith(b"MM"):
        raise RuntimeError(f"réponse WCS inattendue (pas un GeoTIFF) : {r.content[:200]!r}")
    return r.content


def sample(tiff_bytes: bytes, lons, lats) -> np.ndarray:
    import rasterio
    with rasterio.io.MemoryFile(tiff_bytes) as mem, mem.open() as src:
        band = src.read(1).astype("float64")
        nodata = src.nodata
        if nodata is not None:
            band[band == nodata] = np.nan
        band[band < 0] = np.nan
        rows, cols = rasterio.transform.rowcol(src.transform, lons, lats)
        rows = np.clip(np.asarray(rows), 0, band.shape[0] - 1)
        cols = np.clip(np.asarray(cols), 0, band.shape[1] - 1)
        return band[rows, cols]


def compute(tiff_bytes: bytes, leaves: pd.DataFrame) -> pd.DataFrame:
    vals = sample(tiff_bytes, leaves.lon.to_numpy(), leaves.lat.to_numpy())
    date = dt.date.today().isoformat()
    out = pd.DataFrame({"pcode": leaves.pcode, "indicateur": "water_table_depth_m", "valeur": np.round(vals, 1), "date": date})
    out = out.dropna()
    out["source"] = SOURCE
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cfg = load_config(args.country)
    bbox = cfg["map"]["bbox"]
    tiff_bytes = fetch_geotiff(bbox)
    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]
    out = compute(tiff_bytes, leaves)
    ext = country_data_dir(args.country) / "external"
    ext.mkdir(parents=True, exist_ok=True)
    out.to_csv(ext / "watertable.csv", index=False)
    if len(out):
        print(f"Profondeur de nappe (MacDonald et al. 2012) : {len(out)}/{len(leaves)} fokontany, médiane {out.valeur.median():.1f} m.")
    else:
        print("Profondeur de nappe : aucune valeur exploitable (grille vide ou hors emprise).")


if __name__ == "__main__":
    main()
