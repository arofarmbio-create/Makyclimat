"""Bilan hydrique et potentialité en eau souterraine agrégés par SOUS-BASSIN versant (pas seulement par fokontany).

MakyClimat calcule déjà un bilan hydrique mensuel par fokontany (build_soilwater.py) et délimite ses propres
sous-bassins versants à partir du MNT Copernicus GLO-90 (build_hydro.py, hydro_core.py — Priority-Flood,
accumulation, terminaisons de sous-bassins ; voir docs/data/<pays>/hydro/subbasins.geojson). Ce script
réutilise ces deux résultats : il fait la MOYENNE pondérée par surface des indicateurs déjà calculés par
fokontany, à l'échelle de chaque sous-bassin — un sous-bassin est une unité hydrologique cohérente,
contrairement aux limites administratives des fokontany qui n'ont aucune raison de suivre une ligne de
partage des eaux.

Indicateurs agrégés (quand disponibles) : recharge12_mm, recharge12_z, whc_mm, sm_rel_pct, spi3, spi6, spi12
(build_soilwater.py), hand_lt15_pct, slope_mean_pct (build_hydro.py), aquifer_productivity_pct,
aquifer_yield_lsec_mid (connector_geology.py), water_table_depth_m (connector_watertable.py).

Limites : la moyenne de surface lisse les écarts internes à un grand sous-bassin (un sous-bassin de
plusieurs milliers de km² peut contenir des zones très différentes) ; un sous-bassin sans fokontany avec
assez de données n'est pas publié. Les indicateurs eux-mêmes gardent les limites documentées dans
validation/groundwater_limites.md et docs/soilwater (bilan mensuel, pas d'intensité journalière, etc.).
Sortie : docs/data/<pays>/hydro/subbasin_balance.json  { generated, u: { "<id>": {indicateur: valeur, ...} } }
Usage : python scripts/build_subbasin_balance.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import country_data_dir, country_docs_dir, read_units, write_json

INDICATORS = ["recharge12_mm", "recharge12_z", "whc_mm", "sm_rel_pct", "spi3", "spi6", "spi12",
              "hand_lt15_pct", "slope_mean_pct", "aquifer_productivity_pct", "aquifer_yield_lsec_mid", "water_table_depth_m"]
SOURCES = ["soilwater.csv", "hydro.csv", "geology.csv", "watertable.csv"]


def load_long(ext_dir, leaves: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for name in SOURCES:
        p = ext_dir / name
        if p.exists():
            frames.append(pd.read_csv(p)[["pcode", "indicateur", "valeur"]])
    if not frames:
        return pd.DataFrame(columns=["pcode", "indicateur", "valeur"])
    long = pd.concat(frames, ignore_index=True)
    return long[long.indicateur.isin(INDICATORS)]


def aggregate(long: pd.DataFrame, lk: pd.DataFrame, leaves: pd.DataFrame) -> dict:
    wide = long.pivot_table(index="pcode", columns="indicateur", values="valeur", aggfunc="mean")
    t = leaves[["pcode", "area_km2"]].merge(lk[["pcode", "subbasin"]], on="pcode", how="left")
    t = t[t.subbasin.notna() & (t.subbasin > 0)]
    t = t.merge(wide, on="pcode", how="left")
    w = t.area_km2.fillna(1.0).clip(lower=0.01)
    out: dict[str, dict] = {}
    for sub_id, g in t.groupby("subbasin"):
        gw = w.loc[g.index]
        row: dict[str, float] = {}
        for col in INDICATORS:
            if col not in g.columns:
                continue
            v = g[col]
            ok = v.notna()
            if ok.sum() == 0:
                continue
            row[col] = round(float(np.average(v[ok], weights=gw[ok])), 2)
        if row:
            row["n_fokontany"] = int(len(g))
            out[str(int(sub_id))] = row
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    data_dir = country_data_dir(args.country)
    hu_path = data_dir / "hydro_units.csv"
    if not hu_path.exists():
        print("Bilan par sous-bassin : hydro_units.csv absent — lancer build_hydro.py d'abord.")
        return
    lk = pd.read_csv(hu_path, dtype={"pcode": str})
    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]
    long = load_long(data_dir / "external", leaves)
    if long.empty:
        print("Bilan par sous-bassin : aucune source d'indicateur disponible (soilwater/hydro/geology/watertable).")
        return
    out = aggregate(long, lk, leaves)
    hydro_dir = country_docs_dir(args.country) / "hydro"
    hydro_dir.mkdir(parents=True, exist_ok=True)
    write_json(hydro_dir / "subbasin_balance.json", {"generated": dt.date.today().isoformat(), "u": out})
    # mapping fokontany -> sous-bassin, pour que le site sache quelle fiche afficher au clic
    write_json(hydro_dir / "units_sub.json", {"u": {pc: int(s) for pc, s in zip(lk.pcode, lk.subbasin) if s and s > 0}})
    print(f"Bilan par sous-bassin : {len(out)} sous-bassins avec au moins un indicateur, sur {lk.subbasin.gt(0).sum() and lk[lk.subbasin > 0].subbasin.nunique()} au total.")


if __name__ == "__main__":
    main()
