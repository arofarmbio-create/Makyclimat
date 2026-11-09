"""Atlas avec fourchette de recharge (scripts/atlas_fourchette_recharge.py), sur données simulées."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import atlas_fourchette_recharge as A  # noqa: E402

FAILS = 0


def check(name, cond):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name)
    FAILS += 0 if cond else 1


base = {"bassin": [1, 2], "nom": ["a", "b"], "population": [10.0, 20.0], "fiabilite": ["partielle"] * 2}
t2 = pd.DataFrame({**base, "recharge_mm": [7.0, 50.0], "bilan": [3.0, 0.05], "classe_bilan": ["élevé", "faible"]})
t2c = pd.DataFrame({"bassin": [1, 2], "recharge_mm": [67.0, 50.0], "bilan": [0.3, 0.05], "classe_bilan": ["modéré", "faible"]})
m = A.compare(t2, t2c)
check("classe changée : incertain", m.set_index("bassin").loc[1, "statut"] == "incertain")
check("classe identique : stable", m.set_index("bassin").loc[2, "statut"] == "stable")
c = A.cross(m)
check("tableau croisé", c.loc["élevé", "modéré"] == 1 and c.loc["faible", "faible"] == 1 and int(c.values.sum()) == 2)
print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
