"""Nappe régionale (scripts/nappe_regionale.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nappe_regionale as N  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


x = np.arange(10.0)
check("Spearman parfait inverse", np.isclose(N.spearman(x, -x ** 3), -1.0))
check("Spearman : trop peu de points → nan", np.isnan(N.spearman([1, 2], [2, 1])))
rng = np.random.default_rng(0)
zz = rng.normal(size=200)
xx, yy = zz + 0.1 * rng.normal(size=200), zz + 0.1 * rng.normal(size=200)
check("partielle : lien dû à z effacé", abs(N.partielle(xx, yy, zz)) < 0.3 < N.spearman(xx, yy))
f = pd.DataFrame({"NivPiezo_m": [100.0, np.nan], "Alt_m": [150.0, 80.0], "SWL_m": [10.0, 5.0],
                  "BasCrep1_m": [30.0, np.nan], "BasCrep2_m": [45.0, np.nan]})
check("charge : NivPiezo, sinon altitude − niveau statique", list(N.charge(f)) == [100.0, 75.0])
p = N.profondeur(f)
check("profondeur captée = crépine la plus profonde", p[0] == 45.0 and np.isnan(p[1]))
h = N.interp_charge(np.array([0.0]), np.array([0.0]), np.array([0.0, 0.0, 1.0]), np.array([0.01, -0.01, 1.0]), np.array([10.0, 20.0, 99.0]))
check("interpolation : voisins proches dominants", 14.0 < h[0] < 16.0, f"{h[0]:.2f}")
df = pd.DataFrame({"a": x, "b": -x, "bloc": np.repeat([1, 2, 3, 4, 5], 2)})
b = N.boot(df, {"r": lambda s: N.spearman(s.a, s.b)}, n=20)
check("bootstrap par blocs", len(b["r"]) == 20 and np.nanmax(b["r"]) <= -0.99)
check("intervalle", N.ic([1, 2, 3, np.nan])[0] >= 1)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
