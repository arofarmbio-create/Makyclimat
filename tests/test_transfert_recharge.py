"""H-C5 : transfert de la recharge entre pays (scripts/validate_transfert_recharge.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_transfert_recharge as T  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


rng = np.random.default_rng(5)
n = 240
df = pd.DataFrame({"Country": np.repeat([f"P{i}" for i in range(12)], 20),
                   "LTA_P_mmpa": rng.uniform(100, 1500, n), "LTA_WD_days": rng.uniform(10, 150, n),
                   "LTA_PET_mm": rng.uniform(1100, 2400, n), "Aridity": rng.uniform(0.05, 1.5, n), "NDVI": rng.uniform(0.1, 0.8, n),
                   "Aquifer_group": rng.choice(["Basement", "Sedimentary"], n), "Soil_group": rng.choice(["AR", "LP"], n),
                   "Landcover": rng.choice(["cropland", "grassland"], n)})
logr = -1.0 + 1.6 * np.log10(df.LTA_P_mmpa) + 0.4 * (df.Aquifer_group == "Sedimentary") + rng.normal(0, 0.1, n)
df["Recharge_mmpa"] = 10 ** logr - 1

check("log10(R + 1) : une recharge nulle donne 0", T.target([0.0, 9.0]).tolist() == [0.0, 1.0])
a = df.iloc[:3].copy()
check("Gower : distance nulle à soi-même, positive sinon", np.allclose(np.diag(T.gower(a, a)), 0) and T.gower(a, a)[0, 1] > 0)
res = T.leave_one_country_out(df)
check("pays laissé de côté : un résultat par pays", len(res) == 12 and set(res.pays) == set(df.Country))
check("relation réelle : T1 bat la référence naïve dans tous les pays", (res.erreur_T1 < res.erreur_naif).all())
w, k, p = T.sign_test(res.erreur_T1, res.erreur_naif)
check("test du signe : 12 sur 12, p < 0,025", w == 12 and p < 0.025, f"p = {p:.4f}")
df2 = df.assign(Recharge_mmpa=10 ** rng.normal(1.3, 0.5, n) - 1)
r2 = T.leave_one_country_out(df2)
w2, k2, p2 = T.sign_test(r2.erreur_T1, r2.erreur_naif)
check("aucune relation : T1 ne passe pas H-C5", p2 >= 0.025, f"{w2} sur {k2}, p = {p2:.3f}")

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
