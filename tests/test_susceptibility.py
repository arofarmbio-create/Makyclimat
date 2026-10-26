"""Test de la susceptibilité aux inondations sur données synthétiques."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_susceptibility as B  # noqa: E402

units = pd.DataFrame({"level": [4, 4, 4], "pcode": ["a", "b", "c"], "pop": [1000.0, 500.0, 20.0], "area_km2": [2.0, 5.0, 40.0]})
rows = []
for pc, h5, h15, sl, el, rv in [("a", 80, 100, 0.5, 20, 900), ("b", 10, 40, 3.0, 200, 50), ("c", 0, 0, 20.0, 1500, 2)]:
    for k, v in [("hand_lt5_pct", h5), ("hand_lt15_pct", h15), ("slope_mean_pct", sl), ("elev_mean_m", el), ("river_max_km2", rv)]:
        rows.append({"pcode": pc, "indicateur": k, "valeur": v})
hydro = pd.DataFrame(rows)
model = {"colonnes": ["lhand5", "lhand15", "lslope", "lelev", "lriver", "lpopdens"], "moyenne": [2, 3, 1, 5, 4, 3], "ecart_type": [1] * 6,
         "intercept": -0.3, "coefficients": [1.3, -0.2, -0.3, -0.4, 0.2, 0.3]}
out = B.compute(units, hydro, model)
v = dict(zip(out.pcode, out.valeur))
assert v["a"] > v["b"] > v["c"], v          # plaine inondable > intermédiaire > montagne
assert 0 <= min(v.values()) and max(v.values()) <= 100
assert (out.indicateur == "susc_inond_pct").all()
print("test_susceptibility OK")
