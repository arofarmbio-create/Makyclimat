"""Contrôle de l'ET0 du SPEI (scripts/validate_spei_ndvi.py) : le cache Open-Meteo contient une clé « _years »."""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_spei_ndvi as V  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    (d / "et0_cache.json").write_text(json.dumps({"_years": [2016, 2020], "46.00,-20.00": list(range(1, 13)),
                                                  "47.00,-19.00": None, "48.00,-18.00": list(range(3, 15))}))
    (d / "x" / "validation").mkdir(parents=True)
    V.grid_dir, V.DATA_DIR = (lambda c: d), d / "x" / "y"
    E = pd.DataFrame(np.ones((60, 2)), index=[f"{y}-{m:02d}" for y in range(2016, 2021) for m in range(1, 13)])
    df = V.control_et0(E, None, "mdg")
check("clé « _years » et points vides ignorés ; moyenne des points", df.et0_openmeteo_mm.tolist() == [float(x) for x in range(2, 14)])
check("ET0 ERA5-Land par mois du calendrier", df.et0_era5land_pm_mm.tolist() == [1.0] * 12)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
