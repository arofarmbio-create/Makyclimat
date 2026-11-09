"""Recharge du karst (scripts/recharge_karst.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import recharge_karst as K  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


ref = pd.DataFrame({"fkarst": [0.0, 0.4, 0.6, 0.9, 0.5, 0.8],
                    "Obs_gwr/p": [0.01, 0.05, 0.07, 0.09, 0.30, 0.20],
                    "arid1_humid0": [1, 1, 1, 1, 0, 1],
                    "Country": ["Kenya", "Kenya", "Spain", "Madagascar", "Brazil", "China"]})
kr = K.karst_ratios(ref, 0.3).set_index("clim")
check("karst seulement, Madagascar exclu", kr.loc["aride", "n"] == 3 and kr.loc["humide", "n"] == 1)
check("médiane aride", abs(kr.loc["aride", "med"] - 0.07) < 1e-12)
kr5 = K.karst_ratios(ref, 0.5).set_index("clim")
check("seuil de sensibilité", kr5.loc["aride", "n"] == 2)

t, lo, hi = K.mix([20.0, 20.0, 20.0], [10.0] * 3, [40.0] * 3, [0.0, 1.0, 0.5], [500.0] * 3, [0.02] * 3, [0.07] * 3, [0.3] * 3)
check("sans karst : T2 inchangée", t[0] == 20.0 and lo[0] == 10.0 and hi[0] == 40.0)
check("karst pur : recharge karstique", np.isclose(t[1], 35.0) and np.isclose(lo[1], 10.0) and np.isclose(hi[1], 150.0))
check("mélange à 50 %", np.isclose(t[2], 27.5) and np.isclose(hi[2], 95.0))
t2, _, _ = K.mix([20.0], [10.0], [40.0], [np.nan], [500.0], [0.02], [0.07], [0.3])
check("part karstique manquante : traitée comme nulle", t2[0] == 20.0)

grid = pd.DataFrame({"T2_mmpa": [20.0, 20.0], "T2_bas_mmpa": [10.0, 10.0], "T2_haut_mmpa": [40.0, 40.0],
                     "LTA_P_mmpa": [500.0, 1000.0], "Aridity": [0.3, 0.8]})
g = K.apply(grid, np.array([1.0, 1.0]), K.karst_ratios(ref, 0.3))
check("climat de la maille choisit le rapport", np.isclose(g.T2K_mmpa[0], 0.07 * 500) and np.isclose(g.T2K_mmpa[1], 0.30 * 1000))
j = K.nearest([0.0, 10.0], [0.0, 10.0], [9.0, 0.5], [9.0, 0.5])
check("maille la plus proche", list(j) == [1, 0])

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
