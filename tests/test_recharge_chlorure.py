"""Bilan de chlorure (scripts/recharge_chlorure.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import recharge_chlorure as C  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


cp = C.cl_pluie([0.0, 30.0, 1e6], 2.2, 0.4, 30.0)
check("chlore de la pluie : côte, décroissance, intérieur", np.isclose(cp[0], 2.2) and np.isclose(cp[1], 0.4 + 1.8 / np.e) and np.isclose(cp[2], 0.4))
D = C.depot([500.0], [1e6], (2.2, 0.4, 30.0, 0.3))
check("dépôt = P × Cl × (1 + s)", np.isclose(D[0], 500 * 0.4 * 1.3))
check("recharge mm/an = dépôt / chlorure de nappe", np.isclose(D[0] / 26.0, 10.0))
f = pd.DataFrame({"cl": [100.0, 100.0, 100.0, 100.0], "dist_km": [2.0, 20.0, 20.0, 20.0],
                  "NO3-_mg/l": [1.0, 80.0, 1.0, 1.0], "EC_µ/cm": [500.0, 500.0, 4000.0, 4000.0],
                  "Na+_mg/l": [10.0, 10.0, 3000.0, 50.0], "Cl-_mg/l": [100.0, 100.0, 100.0, 100.0]})
g, n = C.filtre(f)
check("filtres : côte, nitrate, autre source de sels", len(g) == 1 and g.index[0] == 3, str(n))
z = C.zones(np.array([-23.0, -23.1, -23.2, -25.0]), np.array([44.0, 44.0, 44.0, 46.0]))
check("zones par lien simple à 20 km", z[0] == z[1] == z[2] and z[3] != z[0])
check("écart log10", np.isclose(C.ecart([200.0], [100.0])[0], np.log10(2)))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
