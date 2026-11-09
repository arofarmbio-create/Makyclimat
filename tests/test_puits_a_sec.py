"""Puits à sec et recharge (scripts/puits_a_sec.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import puits_a_sec as P  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


check("AUC parfaite", P.auc([3, 4], [1, 2]) == 1.0)
check("AUC nulle", P.auc([1, 2], [3, 4]) == 0.0)
check("ex aequo comptés pour moitié", P.auc([1], [1]) == 0.5)
u = pd.DataFrame({"Dry": ["Yes", "Yes", "Yes", "Yes", None],
                  "Functionality issues": ["No water, the well is dry", "No water, the well is dry, Mechanical failure",
                                           "Débit insuffisant", "Maintenance problem", "No water, the well is dry"]})
pr, dry = P.selection(u)
check("cas principal : à sec sans panne", list(pr) == [True, False, True, False, False])
check("sensibilité : tous Dry = Yes", list(dry) == [True, True, True, True, False])
b = P.blocs([-23.0, -23.05, -24.0], [44.0, 44.05, 44.0])
check("blocs de 20 km", b[0] == b[1] and b[0] != b[2])
cas = pd.DataFrame({"lat": [-23.0, -23.5], "lon": [44.0, 44.5], "A": [10.0, 20.0], "B": [50.0, 60.0]})
ref = pd.DataFrame({"lat": [-23.0, -23.5, -24.0], "lon": [44.0, 44.5, 45.0], "A": [30.0, 40.0, 50.0], "B": [10.0, 20.0, 30.0]})
bs = P.bootstrap(cas, ref, ["A", "B"], n=50, seed=1)
check("bootstrap reproductible et borné", len(bs["A"]) == 50 and np.nanmax(bs["A"]) <= 1 and np.nanmin(bs["B"]) >= 0)
check("recharge faible chez les cas : AUC élevée", np.nanmedian(bs["A"]) > 0.5 > np.nanmedian(bs["B"]))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
