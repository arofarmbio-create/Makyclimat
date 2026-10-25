"""Teste les connecteurs qui lisent des fichiers externes (limites OCHA, population COD-PS, pluie CHIRPS)
avec de FAUX fichiers au même format (aucun accès réseau). Nécessite geopandas, rasterio.

Usage : python tests/make_synthetic.py && python tests/test_connectors.py
"""
from __future__ import annotations

import gzip
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


def test_boundaries_and_population() -> None:
    import geopandas as gpd
    from shapely.geometry import box

    import common
    # Faux shapefiles COD-AB : un fichier par niveau, noms et champs comme chez OCHA
    tmp = Path(tempfile.mkdtemp(prefix="fake_codab_"))
    rows = {1: [], 2: [], 3: [], 4: []}
    for r in range(2):
        x0 = 44 + r * 3
        rows[1].append({"ADM1_FR": f"Région {r}", "ADM1_PCODE": f"MG{r}", "geometry": box(x0, -20, x0 + 3, -15)})
        for d in range(2):
            y0 = -20 + d * 2.5
            rows[2].append({"ADM2_FR": f"District {r}{d}", "ADM2_PCODE": f"MG{r}{d}", "ADM1_PCODE": f"MG{r}",
                            "geometry": box(x0, y0, x0 + 3, y0 + 2.5)})
            for c in range(2):
                cx = x0 + c * 1.5
                rows[3].append({"ADM3_FR": f"Commune {r}{d}{c}", "ADM3_PCODE": f"MG{r}{d}{c}", "ADM2_PCODE": f"MG{r}{d}",
                                "geometry": box(cx, y0, cx + 1.5, y0 + 2.5)})
                for f in range(3):
                    fy = y0 + f * 2.5 / 3
                    rows[4].append({"ADM4_FR": f"Fokontany {r}{d}{c}{f}", "ADM4_PCODE": f"MG{r}{d}{c}{f}",
                                    "ADM3_PCODE": f"MG{r}{d}{c}", "geometry": box(cx, fy, cx + 1.5, fy + 2.5 / 3)})
    for lv, rs in rows.items():
        gpd.GeoDataFrame(rs, crs=4326).to_file(tmp / f"mdg_admbnda_adm{lv}_BNGRC_OCHA_20181031.shp")
    # fichier de lignes à ignorer
    gpd.GeoDataFrame([{"geometry": box(0, 0, 1, 1).boundary}], crs=4326).to_file(tmp / "mdg_admbndl_admALL_BNGRC_OCHA_20181031.shp")

    # config d'un pays « fake »
    import yaml
    cfg = common.load_config("mdg")
    cfg["slug"] = "fake"
    with open(common.CONFIG_DIR / "countries" / "fake.yml", "w", encoding="utf-8") as fh:
        yaml.safe_dump(cfg, fh, allow_unicode=True, sort_keys=False)
    try:
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_boundaries.py"), "--country", "fake",
                              "--local-dir", str(tmp)], capture_output=True, text=True)
        check("construction des limites (4 niveaux, lignes ignorées)", out.returncode == 0, (out.stderr or out.stdout).strip().splitlines()[-1])
        units = common.read_units("fake")
        check("nombre d'unités par niveau", units.level.value_counts().sort_index().tolist() == [2, 4, 8, 24],
              str(units.level.value_counts().sort_index().tolist()))
        fk = units[units.level == 4].iloc[0]
        check("lignage (région, district, commune) des fokontany", fk.adm1.startswith("MG") and fk.adm2.startswith("MG")
              and fk.parent == fk.adm3, f"{fk.pcode}: {fk.adm1}/{fk.adm2}/{fk.adm3}")
        check("surfaces et centroïdes renseignés", (units.area_km2 > 0).all() and units.lon.between(43, 51).all())
        geo = common.country_docs_dir("fake") / "geo"
        check("fichiers de limites par district", len(list((geo / "adm4").glob("*.geojson"))) == 4
              and (geo / "adm1.geojson").exists())

        # Population : faux CSV COD-PS niveau 4 avec colonnes parasites
        pop = pd.DataFrame({"ADM4_PCODE": units[units.level == 4].pcode, "ADM4_FR": "x", "F_TL": 400, "M_TL": 500, "T_TL": 900})
        csvp = tmp / "pop4.csv"
        pop.to_csv(csvp, index=False)
        out = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_population.py"), "--country", "fake",
                              "--local-csv", str(csvp)], capture_output=True, text=True)
        check("population par fokontany (colonne T_TL)", out.returncode == 0, (out.stderr or out.stdout).strip().splitlines()[-1])
        u2 = common.read_units("fake")
        check("cumul vers les niveaux supérieurs", u2[u2.level == 4]["pop"].sum() == 24 * 900
              and u2[u2.level == 1]["pop"].sum() == 24 * 900 and u2[u2.level == 3]["pop"].iloc[0] == 3 * 900)
    finally:
        shutil.rmtree(common.country_docs_dir("fake"), ignore_errors=True)
        shutil.rmtree(common.DATA_DIR / "fake", ignore_errors=True)
        (common.CONFIG_DIR / "countries" / "fake.yml").unlink(missing_ok=True)
        shutil.rmtree(tmp, ignore_errors=True)


def test_chirps_reader() -> None:
    import rasterio
    from rasterio.transform import from_origin

    import chirps
    import common
    # Faux fichier CHIRPS Afrique : grille de 0,05° sur un grand rectangle, -9999 = pas de donnée
    tmp = Path(tempfile.mkdtemp(prefix="fake_chirps_"))
    w, h = 1500, 1600
    arr = np.full((h, w), 12.5, dtype="float32")
    arr[:, :200] = -9999.0
    tif = tmp / "chirps.tif"
    with rasterio.open(tif, "w", driver="GTiff", height=h, width=w, count=1, dtype="float32", crs="EPSG:4326",
                       transform=from_origin(-20.0, 40.0, 0.05, 0.05), nodata=-9999.0) as dst:
        dst.write(arr, 1)
    gz = tmp / "chirps.tif.gz"
    with open(tif, "rb") as fi, gzip.open(gz, "wb") as fo:
        shutil.copyfileobj(fi, fo)
    # remplace le téléchargement par une copie locale
    chirps.download = lambda url, dest, **kw: (shutil.copyfile(gz, dest) or True) if "ok" in url else False
    bbox = [43.0, -26.0, 51.0, -11.5]
    res = chirps.fetch_array("http://x/ok.tif.gz", bbox)
    a, lon0, lat0, step = res
    check("recadrage CHIRPS sur la zone du pays", a.shape == (290, 160), str(a.shape))
    check("géoréférence du recadrage (coin nord-ouest)", abs(lon0 - 43.0) < 0.051 and abs(lat0 - (-11.5)) < 0.051 and abs(step - 0.05) < 1e-9,
          f"lon0={lon0}, lat0={lat0}")
    check("valeurs de pluie lues", np.allclose(a[np.isfinite(a)], 12.5))
    check("fichier absent (404) -> None", chirps.fetch_array("http://x/missing.tif.gz", bbox) is None)
    # pixel hors couverture = NaN
    arr2 = arr.copy()
    arr2[:] = -9999.0
    with rasterio.open(tif, "w", driver="GTiff", height=h, width=w, count=1, dtype="float32", crs="EPSG:4326",
                       transform=from_origin(-20.0, 40.0, 0.05, 0.05), nodata=-9999.0) as dst:
        dst.write(arr2, 1)
    with open(tif, "rb") as fi, gzip.open(gz, "wb") as fo:
        shutil.copyfileobj(fi, fo)
    a2 = chirps.fetch_array("http://x/ok.tif.gz", bbox)[0]
    check("nodata -> NaN", np.isnan(a2).all())
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_boundaries_and_population()
    test_chirps_reader()
    print("\nTous les tests de connecteurs passent." if not FAILS else f"\n{FAILS} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)
