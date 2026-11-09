"""Extrait l'emprise de Madagascar de la grille 0,5° de Wan, Döll et Müller Schmied (2024), figshare 23592666 v3.

Usage : .venv/Scripts/python.exe -I scripts/fkarst_mdg.py <3_Updated_grid_mean_GWR_recharge_factors.csv> <sortie.csv>
"""
import sys

import pandas as pd

src, out = sys.argv[1:3]
COLS = ["lon", "lat", "fkarst", "fkarstlandmax", "fland", "Rg_grid", "Rg_wwh", "Rg_land", "Recharge_mmpa",
        "prep_cont_w5e5", "cell_area_km2"]
df = pd.read_csv(src, usecols=COLS)
m = df[(df.lon >= 43) & (df.lon <= 51) & (df.lat >= -26) & (df.lat <= -11.5)].copy()
m = m[m.fland > 0]  # mailles avec des terres émergées
m = m[COLS].sort_values(["lat", "lon"], ascending=[False, True])
m.to_csv(out, index=False, float_format="%.6g")
print("mailles terrestres", len(m))
for s in (0, 0.1, 0.3, 0.5):
    print(f"fkarst > {s}:", int((m.fkarst > s).sum()))
k = m[m.fkarst > 0].sort_values("fkarst", ascending=False)
print(k[["lon", "lat", "fkarst", "fland", "Rg_grid", "Rg_wwh", "Recharge_mmpa"]].to_string(index=False))
print("Rg_grid moyenne", round(m.Rg_grid.mean(), 1), "Rg_wwh moyenne", round(m.Rg_wwh.mean(), 1))
print("Recharge_mmpa non vides", int(m.Recharge_mmpa.notna().sum()))
