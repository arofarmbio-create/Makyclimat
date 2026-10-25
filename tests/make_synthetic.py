"""Données SIMULÉES pour tester toute la chaîne hors réseau (pays « demo »). Aucune valeur réelle.

Usage : python tests/make_synthetic.py   (crée config/countries/demo.yml et les données demo)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from common import CONFIG_DIR, grid_dir, load_config, save_grid, write_boundaries  # noqa: E402


def rect(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def main() -> None:
    cfg = load_config("mdg")
    cfg["slug"], cfg["name"], cfg["iso3"] = "demo", "Démo (données simulées)", "DEM"
    with open(CONFIG_DIR / "countries" / "demo.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    rng = np.random.default_rng(42)
    lon_a, lon_b, lat_a, lat_b = 43.5, 50.5, -25.5, -12.0
    units, geoms = [], {}

    def split(x0, y0, x1, y1, nx, ny):
        xs, ys = np.linspace(x0, x1, nx + 1), np.linspace(y0, y1, ny + 1)
        for j in range(ny):
            for i in range(nx):
                yield xs[i], ys[j], xs[i + 1], ys[j + 1]

    def add(level, pcode, name, parent, a1, a2, a3, box):
        x0, y0, x1, y1 = box
        units.append({"level": level, "pcode": pcode, "name": name, "parent": parent, "adm1": a1, "adm2": a2,
                      "adm3": a3, "lon": round((x0 + x1) / 2, 5), "lat": round((y0 + y1) / 2, 5),
                      "area_km2": round((x1 - x0) * (y1 - y0) * 111 * 105, 2)})
        geoms[pcode] = rect(x0, y0, x1, y1)

    for r, box1 in enumerate(split(lon_a, lat_a, lon_b, lat_b, 2, 2), 1):
        r1 = f"R{r}"
        add(1, r1, f"Région {r}", "", r1, "", "", box1)
        for d, box2 in enumerate(split(*box1, 2, 1), 1):
            d2 = f"{r1}D{d}"
            add(2, d2, f"District {r}.{d}", r1, r1, d2, "", box2)
            for c, box3 in enumerate(split(*box2, 2, 2), 1):
                c3 = f"{d2}C{c}"
                add(3, c3, f"Commune {r}.{d}.{c}", d2, r1, d2, c3, box3)
                for f, box4 in enumerate(split(*box3, 3, 3), 1):
                    f4 = f"{c3}F{f}"
                    add(4, f4, f"Fokontany {r}.{d}.{c}.{f}", c3, r1, d2, c3, box4)
    for u in units:
        u["pop"] = int(rng.integers(300, 3000)) if u["level"] == 4 else np.nan
        u["pop_year"], u["pop_source"] = 2018, "SIMULÉ"
    # cumuls de population
    import pandas as pd
    df = pd.DataFrame(units)
    for lv, key in ((3, "adm3"), (2, "adm2"), (1, "adm1")):
        sums = df[df.level == 4].groupby(key)["pop"].sum()
        m = df.level == lv
        df.loc[m, "pop"] = df.loc[m, "pcode"].map(sums)
    write_boundaries("demo", df.to_dict("records"), geoms)
    # indicateurs externes simulés (format standard des connecteurs)
    ext = Path(__file__).resolve().parents[1] / "data" / "demo" / "external"
    ext.mkdir(parents=True, exist_ok=True)
    (ext / "demo_external.csv").write_text(
        "pcode,indicateur,valeur,date,source\n"
        "R1,poverty_headcount,70,2024-01-01,test\nR2,poverty_headcount,80,2024-01-01,test\n"
        "R3D1,ipc_phase3plus_pct,30,2026-01-31,test\nR3D1,ipc_phase3plus_pop,1000,2026-01-31,test\n"
        "R1D2,ipc_phase3plus_pop,500,2026-01-31,test\nR1D2,ipc_phase3plus_pop,700,2026-02-28,test\n"
        "R1D1,inconnu_xyz,5,2026-01-01,test\n", encoding="utf-8")

    # Grille de pluie simulée (0,05°) alignée sur la bbox de la config
    x0, ymin, x2, y1 = cfg["map"]["bbox"]  # y1 = latitude du haut (nord)
    res = 0.05
    w, h = int(round((x2 - x0) / res)), int(round((y1 - ymin) / res))
    lons = x0 + res * (np.arange(w) + 0.5)
    lats = y1 - res * (np.arange(h) + 0.5)
    LON, LAT = np.meshgrid(lons, lats)
    base = 450 + 350 * (LAT + 26) / 14           # plus sec au sud (simulation)
    norm = base * 1.0
    ratio = 0.35 + 0.9 * (LAT + 26) / 14 + 0.25 * np.sin(LON * 1.7)  # anomalie spatiale simulée
    act = norm * np.clip(ratio, 0.2, 1.6)
    sea = LON > 50.2                               # « mer » à l'est : NaN pour tester le remplissage côtier
    act[sea], norm[sea] = np.nan, np.nan
    clim = np.stack([norm / 6.0] * 12).astype("float32")
    save_grid(grid_dir("demo") / "season.npz", act=act.astype("float32"), norm=norm.astype("float32"),
              lon0=np.array(x0), lat0=np.array(y1), res=np.array(res),
              data_through=np.array("2026-02-20"), season_start=np.array("2025-11"),
              updated=np.array("2026-02-21T00:00:00+00:00"))
    save_grid(grid_dir("demo") / "clim_monthly.npz", clim=clim, lon0=np.array(x0), lat0=np.array(y1),
              res=np.array(res), years=np.array([1991, 2020]), n_files=np.array(360))
    # série mensuelle de 43 saisons (1982-2025) : El Niño sec, La Niña humide, bruit aléatoire reproductible
    rng = np.random.default_rng(7)
    years = np.arange(1982, 2026)
    phases = np.array(["E" if y % 4 == 0 else "L" if y % 4 == 2 else "N" for y in years])
    fy = np.where(phases == "E", 0.70, np.where(phases == "L", 1.25, 1.0)) * (1 + rng.normal(0, 0.08, len(years)))
    mon = (norm / 6.0)[None, None] * fy[:, None, None, None] * (1 + rng.normal(0, 0.1, (len(years), 6, 1, 1)))
    save_grid(grid_dir("demo") / "monthly_series.npz", arr=mon.astype("float16"), months=np.array([11, 12, 1, 2, 3, 4]),
              years=years, phases=phases, oni=np.where(phases == "E", 1.0, np.where(phases == "L", -1.0, 0.0)).astype("float32"),
              lon0=np.array(x0), lat0=np.array(y1), res=np.array(res))
    # prévision météo simulée (mailles de 0,25°) et débits de rivière simulés, autour du 21 février 2026
    import datetime as _dt
    import update_forecast as _uf
    from common import country_data_dir as _cdd
    import pandas as _pd
    ud = _pd.read_csv(_cdd("demo") / "units.csv", dtype={"pcode": str, "parent": str, "adm1": str, "adm2": str, "adm3": str})
    flons, flats = _uf.build_points(ud, 0.25)
    days = [(_dt.date(2026, 2, 11) + _dt.timedelta(days=i)).isoformat() for i in range(26)]   # 10 jours passés + 16 de prévision
    nP, nT = len(flons), len(days)
    pr = np.full((nP, nT), 3.0, dtype="float32")
    tx = np.full((nP, nT), 30.0, dtype="float32")
    gu = np.full((nP, nT), 40.0, dtype="float32")
    north = flats > -16.5
    pr[north, 12] = 130.0          # 23 février : pluie très forte au nord (alerte)
    gu[north, 12] = 95.0           # rafales de 95 km/h (alerte)
    west = flons < 45.0
    tx[west, 11] = 39.0            # chaleur à l'ouest (alerte)
    south = flats < -24.0
    pr[south, :] = 0.0             # ceinture sèche au sud : plus de 10 jours sans pluie
    save_grid(grid_dir("demo") / "forecast.npz", lon=flons, lat=flats, dates=np.array(days), res=np.array(0.25),
              fetched_at=np.array("2026-02-21T06:00:00+00:00"), today=np.array("2026-02-21"),
              precipitation_sum=pr, temperature_2m_max=tx, temperature_2m_min=tx - 12, wind_gusts_10m_max=gu,
              wind_speed_10m_max=gu / 2, et0_fao_evapotranspiration=np.full((nP, nT), 4.0, dtype="float32"))
    com = ud[ud.level == 3].reset_index(drop=True)
    th = _pd.DataFrame({"pcode": com.pcode, "lon": com.lon, "lat": com.lat, "n_years": 40, "q_mean": 12.0,
                        "q2": 10.0, "q5": 20.0, "q10": 30.0, "q20": 40.0})
    th.to_csv(_cdd("demo") / "flood_thresholds.csv", index=False)
    q = np.full((len(com), nT), 5.0, dtype="float32")
    q[0, 13] = 25.0                # la première commune dépasse la crue de 5 ans (alerte)
    q[1, 13] = 12.0                # la deuxième dépasse la crue de 2 ans (vigilance)
    save_grid(grid_dir("demo") / "flood_forecast.npz", pcode=com.pcode.to_numpy().astype(str), dates=np.array(days), q=q,
              fetched_at=np.array("2026-02-21T06:00:00+00:00"))
    import build_hindcast as _bh
    _argv, sys.argv = sys.argv, ["build_hindcast.py", "--country", "demo"]
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        _bh.main()
    sys.argv = _argv
    print(f"Démo écrite : {len(units)} unités, grille {h}x{w}")


if __name__ == "__main__":
    main()
