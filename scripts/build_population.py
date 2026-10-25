"""Connecteur POPULATION : population par unité administrative (OCHA COD-PS, via HDX).

Usage : python scripts/build_population.py --country mdg [--local-csv fichier_adm4.csv]
Écrit la colonne pop de data/<pays>/units.csv puis cumule vers les niveaux supérieurs.
Remplaçable plus tard par WorldPop (grille 100 m) ou par un recensement : il suffit de réécrire cette colonne.
"""
from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from common import download, hdx_resources, load_config, read_units, units_path

PREFERRED_TOTALS = ["T_TL", "TOTAL", "T_T", "POPULATION", "POP", "TOTAL_POP", "TOTALPOP", "ALL"]


def pick_total(df: pd.DataFrame, level: int) -> str:
    cols = {c.upper(): c for c in df.columns}
    for k in PREFERRED_TOTALS:
        if k in cols:
            return cols[k]
    cand = [c for c in df.columns if re.search(r"(?i)^(t_?tl|total)", c)]
    if cand:
        return cand[0]
    num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and "PCODE" not in c.upper()]
    if not num:
        raise SystemExit(f"Aucune colonne de population trouvée au niveau {level} : {list(df.columns)}")
    best = max(num, key=lambda c: pd.to_numeric(df[c], errors="coerce").sum())
    print(f"  colonne population déduite (somme maximale) : {best}")
    return best


def load_level_csvs(cfg: dict, local_csv: str | None) -> dict[int, pd.DataFrame]:
    out: dict[int, pd.DataFrame] = {}
    if local_csv:
        out[4] = pd.read_csv(local_csv)
        return out
    work = Path(tempfile.mkdtemp(prefix="cod_ps_"))
    for i, r in enumerate(hdx_resources(cfg["population"]["hdx_dataset"])):
        url = str(r.get("url", ""))
        label = (str(r.get("name", "")) + " " + url).lower()
        if not url.lower().endswith(".csv"):
            continue
        m = re.search(r"adm(?:in)?_?([0-4])", label)
        if not m:
            continue
        lv = int(m.group(1))
        dest = work / f"pop{i}.csv"
        if download(url, dest):
            out[lv] = pd.read_csv(dest)
            print(f"  population niveau {lv}: {url}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--local-csv")
    args = ap.parse_args()
    cfg = load_config(args.country)
    units = read_units(args.country)
    tables = load_level_csvs(cfg, args.local_csv)
    year = cfg["population"].get("reference_year", "")

    units["pop"] = np.nan
    units["pop_source"] = ""
    pop_by_code: dict[str, float] = {}
    if 4 in tables:
        t = tables[4]
        pc = next((c for c in t.columns if c.upper() == "ADM4_PCODE"), None)
        if pc is None:
            raise SystemExit(f"Colonne ADM4_PCODE absente : {list(t.columns)}")
        tot = pick_total(t, 4)
        s = pd.Series(pd.to_numeric(t[tot], errors="coerce").values, index=t[pc].astype(str))
        pop_by_code = s.groupby(level=0).sum().to_dict()
        src = "OCHA COD-PS niveau 4"
    elif 3 in tables:
        print("Niveau 4 absent : désagrégation de la population communale selon la surface des fokontany")
        t = tables[3]
        pc = next(c for c in t.columns if c.upper() == "ADM3_PCODE")
        tot = pick_total(t, 3)
        com = pd.Series(pd.to_numeric(t[tot], errors="coerce").values, index=t[pc].astype(str)).to_dict()
        fk = units[units.level == 4]
        area_sum = fk.groupby("parent")["area_km2"].transform("sum")
        for r, a in zip(fk.itertuples(), area_sum):
            if r.parent in com and a > 0:
                pop_by_code[r.pcode] = com[r.parent] * r.area_km2 / a
        src = "OCHA COD-PS niveau 3 désagrégé par surface (estimation)"
    else:
        raise SystemExit("Aucune table de population de niveau 3 ou 4 trouvée sur HDX.")

    m4 = units.level == 4
    units.loc[m4, "pop"] = units.loc[m4, "pcode"].map(pop_by_code)
    units.loc[m4, "pop_source"] = src
    # Cumul vers les niveaux supérieurs (cohérence des totaux)
    for lv, key in ((3, "adm3"), (2, "adm2"), (1, "adm1")):
        sums = units[m4].groupby(key)["pop"].sum()
        mk = units.level == lv
        units.loc[mk, "pop"] = units.loc[mk, "pcode"].map(sums)
        units.loc[mk, "pop_source"] = "Somme des fokontany"
    units["pop_year"] = year
    units.to_csv(units_path(args.country), index=False)
    miss = int(units[m4]["pop"].isna().sum())
    print(f"Population écrite. Fokontany sans population : {miss} / {int(m4.sum())}")
    print(f"Population totale (niveau 1) : {units[units.level == 1]['pop'].sum():,.0f}")


if __name__ == "__main__":
    main()
