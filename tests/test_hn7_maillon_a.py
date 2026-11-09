"""H-N7 maillon A (scripts/hn7_maillon_a.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import hn7_maillon_a as H  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    FAILS += 0 if cond else 1


df = pd.DataFrame({"year": [2000] * 3 + [2001] * 2, "month": [7, 8, 9, 7, 8], "value": [1.0, 2.0, 3.0, 5.0, 5.0]})
v = H.indice_jas(df, [2001, 2002])
check("indice JAS de l'année précédente ; mois manquant → nan", v[0] == 2.0 and np.isnan(v[1]))
oni = pd.DataFrame({"year": [2000], "center_month": [8], "season": ["JAS"], "oni": [1.5]})
check("ONI : saison centrée sur août", H.indice_jas(oni, [2001])[0] == 1.5)
x = np.arange(30.0)
r, p = H.perm_p(x, x, n=200)
check("permutation : lien parfait, p faible", r > 0.99 and p < 0.01)
check("MSSS : prédicteur parfait proche de 1", H.msss_loo(x, 2 * x + 1) > 0.99)
print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
