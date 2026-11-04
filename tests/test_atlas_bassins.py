"""Atlas des nappes par bassin (scripts/atlas_bassins.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import atlas_bassins as A  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


check("fiabilité mesurée : 10 relevés et moins de 30 % d'extrapolation", A.reliability(10, 0.2) == "mesurée")
check("fiabilité partielle : un relevé", A.reliability(1, 0.9) == "partielle")
check("fiabilité non mesurée : aucun relevé et 60 % d'extrapolation ou plus", A.reliability(0, 0.6) == "non mesurée")
check("bilan pondéré par la surface : (1×10 + 3×30) / (100×10 + 100×30) = 0,025",
      abs(A.basin_balance([1, 3], [100, 100], [10, 30]) - 0.025) < 1e-12)
check("bilan sans recharge : manquant", np.isnan(A.basin_balance([1], [0], [10])))
fk = pd.DataFrame({"basin": [1, 1, 2], "area_km2": [10.0, 30.0, 5.0], "pop_ajustee": [100.0, 300.0, 50.0], "niveau_m": [3.0, 5.0, 8.0],
                   "erreur_m": 2.1, "extrapolation": [0.0, 0.0, 1.0], "r_mm": 100.0, "v_mm": 1000.0, "tau_ans": 10.0,
                   "prelev_mm": [1.0, 3.0, 50.0], "prelev_sans_reseau_mm": [1.0, 3.0, 50.0], "elev_mean_m": 100.0,
                   "slope_mean_pct": 2.0, "hand_lt5_pct": 10.0, "whc_mm": 80.0, "sm_rel_pct": 40.0})
t = A.aggregate(fk, pd.Series({1: 12}), {1: "Bassin A"}).set_index("bassin")
check("agrégat : surface, nom, fiabilité, classe de bilan", t.loc[1, "surface_km2"] == 40 and t.loc[1, "nom"] == "Bassin A"
      and t.loc[1, "fiabilite"] == "mesurée" and t.loc[2, "fiabilite"] == "non mesurée" and t.loc[2, "classe_bilan"] == "élevé")

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
