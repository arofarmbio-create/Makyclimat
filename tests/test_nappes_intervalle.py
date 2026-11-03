"""Calibration de l'intervalle selon la distance (scripts/nappes_intervalle.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nappes_intervalle as N  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


p = pd.DataFrame({"mesure_m": [12.0, 8.0, 10.0], "pred_hybride": 10.0, "bas_hybride": 6.0, "haut_hybride": 12.0, "dist_km": 10.0})
check("écart normalisé : sur la borne haute = 1, mi-chemin vers le bas = 0,5, sur la médiane = 0",
      np.allclose(N.scores(p), [1.0, 0.5, 0.0]))
check("classes de distance", list(N.band_of([10, 30, 70, 150])) == ["0-25 km", "25-50 km", "50-100 km", "plus de 100 km"])

# 8 régions ; près des forages l'intervalle est juste, loin il est deux fois trop étroit
rng = np.random.default_rng(1)
rows = []
for r in range(8):
    for near in (True, False):
        n = 60
        sd = 1.0 if near else 2.0
        err = rng.normal(0, sd, n)
        rows.append(pd.DataFrame({"region": f"R{r}", "dist_km": 10.0 if near else 150.0, "pred_hybride": 20.0,
                                  "bas_hybride": 20 - 1.2816, "haut_hybride": 20 + 1.2816, "mesure_m": 20 + err}))
p = pd.concat(rows, ignore_index=True)
k = N.factors(p)
check("k proche de 1 près des forages, proche de 2 loin", 0.8 < k["0-25 km"] < 1.25 and 1.6 < k["plus de 100 km"] < 2.5,
      f"{k['0-25 km']:.2f} ; {k['plus de 100 km']:.2f}")
tab = N.summary(N.cross_calibrate(p)).set_index("classe")
check("couverture loin : environ 50 % avant, environ 80 % après",
      tab.loc["plus de 100 km", "couverture_avant"] < 0.6 and 0.72 < tab.loc["plus de 100 km", "couverture_apres"] < 0.88,
      f"{tab.loc['plus de 100 km', 'couverture_avant']:.2f} -> {tab.loc['plus de 100 km', 'couverture_apres']:.2f}")
w = N.widen(pd.DataFrame({"pred_hybride": [2.0], "bas_hybride": [1.0], "haut_hybride": [3.0], "dist_km": [150.0]}), {"plus de 100 km": 3.0})
check("borne basse ramenée à 0", w.bas_cal.iloc[0] == 0 and w.haut_cal.iloc[0] == 5.0)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
