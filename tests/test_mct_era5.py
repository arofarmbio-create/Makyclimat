"""Indice du canal de Mozambique (scripts/build_mct_era5.py) : moyenne pondérée et lecture d'un jeu ERA5 simulé."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_mct_era5 as M  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


lats = np.array([0.0, 60.0])
f = np.array([[1.0, 1.0], [3.0, 3.0]])
check("moyenne pondérée par cos(latitude) : (1 x 1 + 3 x 0,5) / 1,5", np.isclose(M.area_mean(f, lats), 2.5 / 1.5))
f2 = f.copy()
f2[0, 0] = np.nan
check("valeur manquante ignorée", np.isclose(M.area_mean(f2, lats), (1 + 3 * 0.5 * 2) / (1 + 0.5 * 2)))

try:
    import pandas as pd
    import xarray as xr
    t = pd.to_datetime(["2020-01-01", "2020-03-01", "2020-12-01"])
    la, lo = np.array([-10.0, -30.0]), np.array([30.0, 50.0])
    vo = np.full((3, 1, 2, 2), -2e-5)
    ds = xr.Dataset({k: (("valid_time", "pressure_level", "latitude", "longitude"), v)
                     for k, v in (("vo", vo), ("u", np.ones_like(vo)), ("v", -np.ones_like(vo)))},
                    coords={"valid_time": t, "pressure_level": [850], "latitude": la, "longitude": lo})
    rows = M.rows_from_dataset(ds)
    check("seuls décembre, janvier et février gardés ; tourbillon en 1e-5 s-1",
          [(r[0], r[1]) for r in rows] == [(2020, 1), (2020, 12)] and np.isclose(rows[0][2], -2.0) and rows[0][4] == -1.0)
except ImportError:
    print("xarray absent : test du jeu simulé sauté")

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
