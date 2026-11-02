"""H-C2b : régions entières laissées de côté (scripts/validate_nappes_hc2b.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_nappes_hc2b as B  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


d = B.nearest_km(np.array([0.0]), np.array([0.0]), np.array([0.0, 1.0]), np.array([1.0, 0.0]))
check("distance au plus proche : 1° = 111 km", abs(d[0] - 111.2) < 0.5, f"{d[0]:.1f}")
rng = np.random.default_rng(6)
n = 200
df = pd.DataFrame({"region": np.repeat(["A", "B", "C", "D", "E"], 40), "lat": rng.uniform(-25, -15, n), "lon": rng.uniform(44, 49, n),
                   "fan_m": rng.uniform(0, 40, n), "hand": rng.uniform(0, 40, n)})
df["mesure_m"] = 3 + 0.1 * df.hand + rng.normal(0, 0.3, n)
df.loc[df.region == "E", "region"] = "E"
small = df.iloc[:5].assign(region="F")
df = pd.concat([df, small], ignore_index=True)


def perfect(tr, te):
    p = (3 + 0.1 * te.hand).to_numpy()
    return p, p - 1, p + 1


def mean_krige(tr, te):
    return np.full(len(te), tr.mesure_m.mean())


pts, regs = B.region_cv(df, hybrid=perfect, krige=mean_krige)
check("région de moins de 10 forages écartée", set(regs.region) == {"A", "B", "C", "D", "E"})
dec = B.decide(pts, regs)
check("hybride parfait : H-C2b confirmée", dec["ok"] and dec["regions_gagnees"] == 5)
t = B.distance_table(pts)
check("tableau par distance produit", len(t) >= 1 and t.forages.sum() == len(pts))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
