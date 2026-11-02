"""H-C6 : recharge transférée à Madagascar (scripts/validate_transfert_madagascar.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_transfert_madagascar as M  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Fluctuation de nappe : +0,5 m par mois de novembre à avril, baisse le reste de l'année ; Sy = 0,02 -> 60 mm/an
idx = pd.date_range("2019-07-01", "2023-06-01", freq="MS")
lv, cur = [], -8.0
for d in idx:
    cur += 0.5 if d.month in (11, 12, 1, 2, 3, 4) else -0.5
    lv.append(cur)
r = M.wtf_recharge(pd.Series(lv, index=idx), 0.02)
check("fluctuation de nappe : 6 remontées de 0,5 m × Sy 0,02 = 60 mm/an", abs(r - 60) < 1e-6, f"{r:.1f}")
check("série vide : pas de valeur", np.isnan(M.wtf_recharge(pd.Series(dtype=float), 0.02)))

rng = np.random.default_rng(2)
n = 120
af = pd.DataFrame({"Country": np.repeat([f"P{i}" for i in range(12)], 10), "LTA_P_mmpa": rng.uniform(200, 2000, n),
                   "LTA_WD_days": rng.uniform(20, 180, n), "LTA_PET_mm": rng.uniform(1100, 2200, n),
                   "Aridity": rng.uniform(0.1, 1.5, n), "NDVI": rng.uniform(0.1, 0.8, n),
                   "Aquifer_group": rng.choice(["Basement", "Sedimentary"], n), "Soil_group": rng.choice(["AR", "FR"], n),
                   "Landcover": rng.choice(["cropland", "forest"], n)})
af["Recharge_mmpa"] = 10 ** (-1.0 + 1.5 * np.log10(af.LTA_P_mmpa) + rng.normal(0, 0.1, n)) - 1
cov = af.drop(columns=["Country", "Recharge_mmpa"]).iloc[:5].copy()
cov["lon"], cov["lat"] = np.linspace(44, 50, 5), np.linspace(-25, -12, 5)
far = cov.iloc[[0]].copy()
far[["LTA_P_mmpa", "NDVI"]] = [9000.0, 5.0]
cov = pd.concat([cov, far], ignore_index=True)
res = M.loco_residuals(af)
pred = M.predict(af, cov, res)
check("prédiction : valeur dans son intervalle de 80 %", ((pred.T2_bas_mmpa <= pred.T2_mmpa) & (pred.T2_mmpa <= pred.T2_haut_mmpa)).all())
check("analogue lointain : maille marquée « extrapolation »", bool(pred.extrapolation.iloc[-1]) and not pred.extrapolation.iloc[:5].any())
ev = M.evaluate(pred, "T2", [("site test", float(pred.T2_mmpa.iloc[0]), float(pred.T2_mmpa.iloc[0]), 0)])
check("référence égale à la prédiction : dans l'intervalle", ev.iloc[-1].dans_intervalle is True)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
