"""Test du croisement cultures x HAND sur une petite grille synthétique."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_crop_exposure as B  # noqa: E402

h, w = 4, 4
ids = np.zeros((h, w), dtype="int32")
ids[:, :2] = 1          # unité 1 : colonnes 0-1 (8 cellules)
ids[:, 2:] = 2          # unité 2 : colonnes 2-3 (8 cellules dont 1 en mer)
cult = np.full((h, w), 0.5)
bati = np.zeros((h, w)); bati[0, 0] = 1.0
hand = np.full((h, w), 50.0); hand[:2, :2] = 3.0; hand[:, 2] = 10.0
sea = np.zeros((h, w), bool); sea[3, 3] = True
df = B.per_unit(ids, {"cult": cult, "bati": bati}, hand, sea, np.full(h, 100.0), 3).iloc[1:].reset_index(drop=True)
assert abs(df.cult_ha[0] - 400) < 1e-9 and abs(df.cult_basse5_ha[0] - 200) < 1e-9 and abs(df.cult_basse15_ha[0] - 200) < 1e-9, df
assert abs(df.cult_ha[1] - 350) < 1e-9 and abs(df.cult_basse5_ha[1]) < 1e-9 and abs(df.cult_basse15_ha[1] - 200) < 1e-9, df
assert abs(df.bati_ha[0] - 100) < 1e-9 and abs(df.bati_basse5_ha[0] - 100) < 1e-9

units = pd.DataFrame({"level": [4, 4, 3, 2, 1], "pcode": ["f1", "f2", "c1", "d1", "r1"], "adm1": ["r1"] * 5, "adm2": ["d1"] * 5, "adm3": ["c1"] * 5})
leaf = df.copy(); leaf.index = ["f1", "f2"]
allu = B.rollup(leaf, units)
assert abs(allu.loc["c1", "cult_ha"] - 750) < 1e-9 and abs(allu.loc["r1", "cult_basse5_ha"] - 200) < 1e-9
assert abs(allu.loc["f1", "cult_basse5_pct"] - 50) < 1e-9 and abs(allu.loc["c1", "cult_basse15_pct"] - 100 * 400 / 750) < 1e-9
rows = B.to_rows(allu)
assert set(rows.indicateur) >= {"cult_ha", "cult_basse5_pct", "bati_basse5_pct"} and rows.valeur.notna().all()
print("test_crop_exposure OK")
