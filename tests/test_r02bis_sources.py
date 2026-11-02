"""R-02 bis : fenêtres des cyclones et emprises IMERG (scripts/build_r02bis_sources.py)."""
import datetime as dt
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_r02bis_sources as R  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


land_lon, land_lat = np.array([47.0]), np.array([-19.0])
pts = [[60.0, -19.0, 30], [53.0, -19.0, 60], [50.0, -19.0, 90], [47.5, -19.0, 70], [44.0, -19.0, 40], [38.0, -19.0, 30]]
w = R.window(pts, dt.date(2022, 2, 1), land_lon, land_lat)
# positions toutes les 6 h : à moins de 500 km aux indices 2, 3, 4 (12 h à 24 h après le début)
check("fenêtre : 1 jour avant le premier passage à moins de 500 km, 2 jours après le dernier",
      w == (dt.date(2022, 1, 31), dt.date(2022, 2, 4)))
check("aucun passage à moins de 500 km : pas de fenêtre", R.window([[70.0, -19.0, 30]], dt.date(2022, 2, 1), land_lon, land_lat) is None)
check("distance : 1° de latitude vaut environ 111 km", abs(R.haversine_km(47, -19, 47, -20) - 111.2) < 0.5)
b = R.imerg_box(43.05, 43.25, -25.95, -25.75)
check("emprise IMERG : indices de la grille 0,1°", b == (2230, 2232, 640, 642))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
