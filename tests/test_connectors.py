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


def test_hapi() -> None:
    import connector_hapi
    import common

    calls = []

    class R:
        def __init__(self, data): self._d = data
        def raise_for_status(self): pass
        def json(self): return {"data": self._d}

    ipc = [{"admin_level": 2, "admin1_code": "R1", "admin2_code": "R1D1", "population_fraction_in_phase": 0.35,
            "population_in_phase": 3500, "reference_period_end": "2025-12-31", "resource_hdx_id": "x"},
           {"admin_level": 2, "admin1_code": "R1", "admin2_code": "R1D1", "population_fraction_in_phase": 0.50,
            "population_in_phase": 5000, "reference_period_end": "2026-03-31", "resource_hdx_id": "x"},
           {"admin_level": 1, "admin1_code": "R2", "population_fraction_in_phase": 0.2, "population_in_phase": 900,
            "reference_period_end": "2026-03-31", "resource_hdx_id": "x"}]
    pov = [{"admin_level": 1, "admin1_code": "R1", "headcount_ratio": 71.5, "reference_period_end": "2022-12-31",
            "resource_hdx_id": "y"}]

    def fake_get(url, params=None, timeout=0):
        calls.append(params)
        return R(ipc if url.endswith("/food-security") else pov)

    connector_hapi.requests.get = fake_get
    rows = connector_hapi.fetch_all(connector_hapi.FOOD_SECURITY, {"location_code": "DEM"}, "abc")
    check("HAPI : identifiant transmis", calls[0]["app_identifier"] == "abc" and len(rows) == 3)
    best = connector_hapi.latest_per_zone(rows)
    check("HAPI : analyse la plus récente par zone", best["R1D1"]["population_in_phase"] == 5000 and "R2" in best)
    # exécution complète
    import os, sys as _s
    os.environ["HAPI_APP_IDENTIFIER"] = "abc"
    _s.argv = ["connector_hapi.py", "--country", "demo"]
    connector_hapi.main()
    out = pd.read_csv(common.country_data_dir("demo") / "external" / "hapi.csv")
    v = out.set_index(["pcode", "indicateur"])["valeur"]
    check("HAPI : IPC fraction -> pourcentage", abs(v[("R1D1", "ipc_phase3plus_pct")] - 50) < 1e-6)
    check("HAPI : pauvreté région", abs(v[("R1", "poverty_headcount")] - 71.5) < 1e-6)
    # sans identifiant : sortie propre
    os.environ.pop("HAPI_APP_IDENTIFIER")
    try:
        connector_hapi.main()
        ok = False
    except SystemExit as e:
        ok = e.code == 0
    check("HAPI : sans identifiant, ignoré sans erreur", ok)
    (common.country_data_dir("demo") / "external" / "hapi.csv").unlink()


def test_population_grid() -> None:
    import geopandas as gpd
    import rasterio
    from rasterio.transform import from_origin

    import build_population_grid as bpg

    res = [{"url": "http://x/mdg_pop_2020_CN_100m.tif"}, {"url": "http://x/mdg_pop_2025_CN_100m_R2025A.tif"},
           {"url": "http://x/mdg_pop_2025_1km.tif"}, {"url": "http://x/readme.pdf"}]
    check("grille : choix du fichier 100 m de l'année", bpg.choose_resource(res, 2025)["url"].endswith("2025_CN_100m_R2025A.tif"))
    check("grille : à défaut, année la plus proche", bpg.choose_resource([{"url": "m_pop_2015_CN_100m.tif"}, {"url": "m_pop_2010_CN_100m.tif"}], 2025)["url"].startswith("m_pop_2015"))
    check("grille : aucune ressource .tif -> None", bpg.choose_resource([{"url": "a.pdf"}], 2025) is None)
    from shapely.geometry import box
    tmp = Path(tempfile.mkdtemp(prefix="fake_pop_"))
    tif = tmp / "pop.tif"
    arr = np.ones((100, 200), dtype="float32")  # 200 x 100 pixels de 0.01°, 1 personne chacun
    arr[:, :100] = 2.0
    with rasterio.open(tif, "w", driver="GTiff", height=100, width=200, count=1, dtype="float32", crs="EPSG:4326",
                       transform=from_origin(45.0, -15.0, 0.01, 0.01), nodata=-99999.0) as dst:
        dst.write(arr, 1)
    polys = gpd.GeoDataFrame({"c": ["A", "B"]}, geometry=[box(45.0, -16.0, 46.0, -15.0), box(46.0, -16.0, 47.0, -15.0)], crs=4326)
    sums, total = bpg.zonal_sum(tif, polys)
    check("grille : somme par polygone", np.allclose(sums, [20000, 10000]), str(sums))
    check("grille : total conservé", abs(total - 30000) < 1e-6)
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_hapi()
    test_population_grid()
    test_boundaries_and_population()
    test_chirps_reader()
    print("\nTous les tests de connecteurs passent." if not FAILS else f"\n{FAILS} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)
