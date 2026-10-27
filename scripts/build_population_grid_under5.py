"""Enfants de moins de 5 ans PRÉCIS par fokontany : grille d'âge/sexe à 100 m (WorldPop) sommée dans chaque polygone.

Télécharge les deux bandes d'âge « 0 an » (t_00) et « 1 à 4 ans » (t_01) de la grille WorldPop
« Age and sex structures », R2025A, 100 m, contrainte (constrained), et additionne les deux pour obtenir
les moins de 5 ans. Contrairement à la grille de population totale (build_population_grid.py, millésime HDX),
cette grille d'âge/sexe n'est pas republiée sur HDX : elle est récupérée directement chez WorldPop (Université
de Southampton). Si le téléchargement échoue (réseau, 404, millésime retiré), la colonne pop_under5 existante
est conservée -- aucune valeur n'est inventée.

Usage : python scripts/build_population_grid_under5.py --country mdg [--year 2016]
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from build_population_grid import zonal_sum
from common import country_docs_dir, download, load_config, read_units, units_path

# WorldPop « Global Age/Sex Structures », R2025A, 100 m, constrained. Pas de miroir HDX connu pour ce jeu de
# données (contrairement à la grille de population totale) : téléchargement direct chez WorldPop/Southampton.
WORLDPOP_AGESEX_BASE = "https://worldpop-public-data.soton.ac.uk/GIS/AgeSex_structures/Global_2015_2030/R2025A"
# Bandes d'âge à sommer pour les moins de 5 ans : "00" = 0 an, "01" = 1 à 4 ans (WorldPop regroupe ainsi, pas
# d'année individuelle entre 1 et 4 ans dans ce jeu de données).
AGE_BANDS_UNDER5 = ("00", "01")


def agesex_url(iso3: str, year: int, band: str) -> str:
    iso3_l = iso3.lower()
    return (f"{WORLDPOP_AGESEX_BASE}/{year}/{iso3.upper()}/v1/100m/constrained/"
            f"{iso3_l}_t_{band}_{year}_CN_100m_R2025A_v1.tif")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--year", type=int)
    ap.add_argument("--tif", action="append", default=[],
                     help="fichier .tif local à utiliser à la place du téléchargement (répéter pour chaque bande, "
                          "dans l'ordre de AGE_BANDS_UNDER5) ; sert surtout aux tests/vérifications manuelles")
    args = ap.parse_args()
    cfg = load_config(args.country)
    iso3 = cfg["iso3"]
    year = args.year or int(cfg["population"].get("agesex_year", 2016))

    import geopandas as gpd

    if args.tif:
        if len(args.tif) != len(AGE_BANDS_UNDER5):
            raise SystemExit(f"--tif doit être fourni {len(AGE_BANDS_UNDER5)} fois (une par bande d'âge).")
        tifs = [Path(p) for p in args.tif]
    else:
        tmp = Path(tempfile.mkdtemp(prefix="agesex_"))
        tifs = []
        for band in AGE_BANDS_UNDER5:
            url = agesex_url(iso3, year, band)
            tif = tmp / f"t_{band}.tif"
            print("Téléchargement de la grille âge/sexe :", url)
            if not download(url, tif, timeout=600):
                print(f"Grille âge/sexe introuvable (404) pour la bande {band} : pop_under5 existante conservée.")
                return
            tifs.append(tif)

    units = read_units(args.country)
    geo = country_docs_dir(args.country) / "geo" / "adm4"
    parts = [gpd.read_file(f) for f in sorted(geo.glob("*.geojson"))]
    polys = pd.concat(parts, ignore_index=True)
    polys = gpd.GeoDataFrame(polys, geometry="geometry", crs=4326).reset_index(drop=True)
    print(f"{len(polys)} fokontany ; calcul des sommes enfants -5 ans (bandes {', '.join(AGE_BANDS_UNDER5)})…")

    sums_total = np.zeros(len(polys), dtype="float64")
    grid_total = 0.0
    for tif in tifs:
        sums, total = zonal_sum(tif, polys)
        sums_total += sums
        grid_total += total
    got = float(np.sum(sums_total))
    print(f"Population -5 ans de la grille : {grid_total:,.0f} ; attribuée aux fokontany : {got:,.0f} "
          f"({100 * got / grid_total:.1f} %)")
    if grid_total <= 0 or got < 0.9 * grid_total:
        raise SystemExit("Moins de 90 % des enfants -5 ans de la grille sont attribués : limites ou grille à vérifier.")

    pop5_by = dict(zip(polys["c"].astype(str), sums_total))
    m4 = units.level == 4
    units.loc[m4, "pop_under5"] = units.loc[m4, "pcode"].map(pop5_by)
    units.loc[m4, "pop_under5_source"] = f"WorldPop Age/Sex Structures R2025A {year} (100 m, bandes 0 an + 1-4 ans)"
    for lv, key in ((3, "adm3"), (2, "adm2"), (1, "adm1")):
        s = units[m4].groupby(key)["pop_under5"].sum()
        mk = units.level == lv
        units.loc[mk, "pop_under5"] = units.loc[mk, "pcode"].map(s)
        units.loc[mk, "pop_under5_source"] = "Somme des fokontany"
    units["pop_under5_year"] = year
    units.to_csv(units_path(args.country), index=False)
    print(f"Enfants -5 ans mis à jour (année {year}) — total national : "
          f"{units[units.level == 1]['pop_under5'].sum():,.0f}")


if __name__ == "__main__":
    main()
