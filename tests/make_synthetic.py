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
    print(f"Démo écrite : {len(units)} unités, grille {h}x{w}")


if __name__ == "__main__":
    main()
