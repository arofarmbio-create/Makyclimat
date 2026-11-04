"""Recharge par fluctuation de nappe (scripts/recharge_fluctuation.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import recharge_fluctuation as R  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Nappe qui monte de 1 m en janvier (4 cm par jour pendant 25 jours), redescend lentement ensuite
t = pd.date_range("2020-06-01", "2023-05-31", freq="6h")
lvl = np.full(len(t), -10.0)
cur = -10.0
for i, x in enumerate(t):
    if x.month == 1 and x.day <= 25:
        cur += 0.01                    # 4 cm par jour (pas de 6 h) pendant 25 jours = 1 m
    elif x.month in (5, 6, 7, 8, 9, 10):
        cur -= 0.005 / 4
    lvl[i] = cur
d = pd.DataFrame({"t": t, "level": lvl, "ec": 1.0})
r = R.wtf_daily(d, 0.05)
check("journalier : 1 m de remontée × Sy 0,05 = 50 mm/an", 45 < r < 55, f"{r:.1f}")
res = R.site_recharge(d, "Basement")
check("site retenu (36 mois) et fourchette Sy bas < haut", res["retenu"] and res["r_bas"] < res["r_haut"], f"{res.get('r_bas')}, {res.get('r_haut')}")
check("mensuel ≤ journalier (le pas mensuel lisse)", res["r_mm"] <= res["r_jour_mm"] + 1e-9)

t1 = R.ratio_test([0.1, 0.2, 0.3, 0.25, 0.15, 0.4, 0.2, 0.3], n=500)
check("rapports tous sous 1 : T2 surestimée", t1["surestimee"] and t1["part_sous_1"] == 1.0)
t2 = R.ratio_test([0.5, 1.5, 2.0, 0.8, 1.2], n=500)
check("rapports mélangés : pas de conclusion", not t2["surestimee"])
check("aucun site : pas de conclusion", not R.ratio_test([np.nan])["surestimee"])

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
