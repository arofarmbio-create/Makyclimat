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


def test_forecast_and_floods() -> None:
    import datetime as dt

    import openmeteo as om
    import update_floods as uf
    import update_forecast as ufc
    import common

    units = common.read_units("demo")
    lons, lats = ufc.build_points(units, 0.25)
    leaves = units[units.level == 4]
    ix, iy = om.cell_key(leaves.lon.to_numpy(), leaves.lat.to_numpy(), 0.25)
    keys = {(int(a), int(b)) for a, b in zip(np.round(lons / 0.25), np.round(lats / 0.25))}
    check("prévision : chaque fokontany a sa maille de 0,25°", all((int(a), int(b)) in keys for a, b in zip(ix, iy)), f"{len(lons)} mailles")

    calls = []
    days = [(dt.date(2026, 2, 1) + dt.timedelta(days=i)).isoformat() for i in range(5)]

    def fake(url, params, **kw):
        calls.append((url, params))
        n = len(params["latitude"].split(","))
        if "flood" in url:
            return [{"latitude": 1.0, "longitude": 2.0, "daily": {"time": days, "river_discharge": [1.0, None, 3.0, 4.0, 5.0]}} for _ in range(n)]
        d = {"time": days}
        for v in om.DAILY_VARS:
            d[v] = [1.0, 2.0, None, 4.0, 5.0]
        return [{"daily": dict(d)} for _ in range(n)] if n > 1 else {"daily": d}

    om.get_json = fake
    dates, arr = ufc.fetch(lons[:85], lats[:85], {"forecast_days": 4, "past_days": 1}, "Indian/Antananarivo", batch=40)
    check("prévision : 85 mailles envoyées par lots de 40 (3 appels)", len(calls) == 3 and arr["precipitation_sum"].shape == (85, 5))
    check("prévision : valeur manquante -> NaN", np.isnan(arr["precipitation_sum"][0, 2]) and arr["precipitation_sum"][0, 3] == 4.0)
    check("prévision : variables et fuseau demandés", "wind_gusts_10m_max" in calls[0][1]["daily"] and calls[0][1]["timezone"] == "Indian/Antananarivo")
    calls.clear()
    com = units[units.level == 3][["pcode", "lon", "lat"]].reset_index(drop=True)
    fd, q = uf.forecast(com.iloc[:5], {"forecast_days": 16})
    check("débits : prévision lue, valeur manquante -> NaN", q.shape == (5, 5) and np.isnan(q[0, 1]) and "flood" in calls[0][0])
    # lois de Gumbel : on retrouve les débits de crue d'un échantillon connu
    rng = np.random.default_rng(1)
    mu, beta = 100.0, 30.0
    sample = rng.gumbel(mu, beta, 20000)
    lv = uf.gumbel_levels(sample)
    true2 = mu - beta * np.log(-np.log(0.5))
    true20 = mu - beta * np.log(-np.log(1 - 1 / 20))
    check("Gumbel : crues de 2 et 20 ans retrouvées à 3 %", abs(lv[2] - true2) / true2 < 0.03 and abs(lv[20] - true20) / true20 < 0.03,
          f"{lv[2]:.1f}/{true2:.1f} {lv[20]:.1f}/{true20:.1f}")
    check("Gumbel : trop peu d'années -> pas de seuil", np.isnan(uf.gumbel_levels([1, 2, 3])[2]))
    idx = [f"{y}-{m:02d}-{d:02d}" for y in (2000, 2001) for m in range(1, 13) for d in range(1, 29)]
    vals = [float(i) for i in range(len(idx))]
    check("maxima annuels : années incomplètes ignorées", len(uf.annual_maxima(idx[:250], vals[:250])) == 0)
    om.get_json = lambda url, params, **kw: [{"latitude": 1.0, "longitude": 2.0, "daily": {
        "time": [f"{y}-{m:02d}-{d:02d}" for y in range(1984, 2000) for m in range(1, 13) for d in range(1, 29)] +
                [f"{y}-12-{d:02d}" for y in range(1984, 2000) for d in range(29, 32)],
        "river_discharge": list(np.random.default_rng(3).gumbel(50, 10, 16 * 12 * 28 + 16 * 3))}} for _ in params["latitude"].split(",")]
    th = uf.thresholds({"flood": {"history_start": 1984}}, com.iloc[:12], batch=10, last_year=1999)
    th2 = uf.thresholds({"flood": {"history_start": 1984}}, com.iloc[:12], batch=10, last_year=1999, existing=th.iloc[:5], max_locations=4)
    check("seuils : reprise sans refaire les communes déjà calculées", len(th2) == 9 and th2.pcode.is_unique)
    check("seuils de crue : une ligne par commune, q2 < q5 < q10 < q20", len(th) == 12 and (th.q2 < th.q5).all() and (th.q5 < th.q10).all() and (th.q10 < th.q20).all(),
          str(th.iloc[0][["q2", "q5", "q10", "q20", "n_years"]].to_dict()))


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


def test_heigit() -> None:
    import connector_heigit as CH
    import compute_metrics as CM
    from common import read_units
    units = read_units("demo")
    d2 = units[units.level == 2].pcode.tolist()[:2]
    access = pd.DataFrame({"ADM2_PCODE": d2, "access_pop_hospitals_1h": [600, 200], "access_pop_hospitals_2h": [900, 300], "access_pop_primary_healthcare_1h": [800, 250],
                           "access_pop_education_5km": [950, 100]})
    demo = pd.DataFrame({"ADM2_PCODE": d2, "total_pop": [1000, 400]})
    coping = pd.DataFrame({"ADM2_PCODE": d2, "RAI_total_pop": [21.6, 0.0]})
    df = CH.build(access, demo, coping)
    g = lambda pc, ind: float(df[(df.pcode == pc) & (df.indicateur == ind)].valeur.iloc[0])
    check("HeiGIT : part à moins d'1 h d'un hôpital", g(d2[0], "acc_hosp_1h_pct") == 60.0 and g(d2[1], "acc_hosp_1h_pct") == 50.0)
    check("HeiGIT : personnes à plus de 2 h d'un hôpital", g(d2[0], "pop_no_hosp_2h") == 100 and g(d2[1], "pop_no_hosp_2h") == 100)
    check("HeiGIT : accès rural repris tel quel", g(d2[0], "rai_pct") == 21.6)
    check("HeiGIT : pourcentages dans [0, 100]", df[df.indicateur.str.endswith("_pct")].valeur.between(0, 100).all())
    defs = {i["id"]: i for i in __import__("common").load_yaml("indicators.yml")["indicators"]}
    direct = {pc: {r.indicateur: r.valeur for r in df[df.pcode == pc].itertuples()} for pc in d2}
    out = CM.aggregate_external(units, direct, defs)
    kid = units[(units.level == 3) & (units.parent == d2[0])].pcode.iloc[0]
    reg = units[units.pcode == d2[0]].parent.iloc[0]
    check("héritage : la commune reprend la valeur du district (indicateur « inherit: down »)", out.get(kid, {}).get("acc_hosp_1h_pct") == 60.0)
    check("pas d'héritage pour un nombre de personnes", "pop_no_hosp_2h" not in out.get(kid, {}))
    check("région : moyenne pondérée par la population des districts", reg in out and "acc_hosp_1h_pct" in out[reg])


if __name__ == "__main__":
    test_heigit()
    test_forecast_and_floods()
    test_hapi()
    test_population_grid()
    test_boundaries_and_population()
    test_chirps_reader()
    print("\nTous les tests de connecteurs passent." if not FAILS else f"\n{FAILS} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)
