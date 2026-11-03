"""Phase 0 du module eaux souterraines (scripts/audit_nappes_phase0.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_nappes_phase0 as A  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Deux régions : A dense (90 forages, erreurs de 1 m), B rare (10 forages, erreurs de 5 m)
p = pd.DataFrame({"region": ["A"] * 90 + ["B"] * 10, "dist_km": [10.0] * 90 + [120.0] * 10, "mesure_m": 5.0})
for m in A.METHODS:
    p[f"pred_{m}"] = 5.0 + np.r_[np.ones(90), 5 * np.ones(10)]
    p[f"err_{m}"] = np.abs(p[f"pred_{m}"] - p.mesure_m)
check("critère 1 : chaque région pèse autant (moyenne de 1 et 5 = 3, pas 1,4)", A.criterion1(p, "hybride") == 3.0)
check("critère 2 : seuls les forages à plus de 50 km", A.criterion2(p, "hybride") == 5.0)
lo, hi = A.bootstrap(p, A.criterion1, "hybride", n=500)
check("intervalle de confiance par rééchantillonnage des régions", 1.0 <= lo <= 3.0 <= hi <= 5.0, f"[{lo:.1f} ; {hi:.1f}]")
p["bas_hybride"], p["haut_hybride"] = p.pred_hybride - 2, p.pred_hybride + 2
cr, cd = A.coverage(p)
check("couverture : 100 % dans A (erreur 1 < 2), 0 % dans B (erreur 5 > 2)",
      dict(zip(cr.region, cr.couverture)) == {"A": 1.0, "B": 0.0})
check("couverture par classe de distance", set(cd.distance) == {"0-25 km", "plus de 100 km"})
fl = A.flow(1000, 1000, 999, 999, 980)
check("diagramme de flux : 5 étapes dans l'ordre", [n for _, n in fl] == [1000, 1000, 999, 999, 980])

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
