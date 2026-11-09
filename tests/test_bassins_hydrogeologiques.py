"""Bassins hydrogéologiques (scripts/bassins_hydrogeologiques.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bassins_hydrogeologiques as B  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


sf = np.array([[1, 1, 2, 2], [1, 1, 2, 2]])
gw = np.array([[7, 7, 7, 9], [7, 7, 9, 9]])                 # étiquettes différentes, une maille passe de 2 à 7
land = np.ones_like(sf, bool)
m = B.match_labels(gw, sf, land)
check("appariement au bassin de surface le plus recouvrant", m[0, 0] == 1 and m[1, 3] == 2)
slope = np.array([[1.0, 1.0, 1.0, 5.0], [5.0, 5.0, 5.0, 5.0]])
r = B.divergence(gw, sf, land, slope)
check("une maille divergente sur 8", abs(r["part_divergente"] - 1 / 8) < 1e-12)
check("taux : 1 maille divergente sur 3 en zone plate, aucune en pente", abs(r["taux_plat"] - 1 / 3) < 1e-12 and r["taux_pente"] == 0)
dep = B.depth_raster((2, 2), 0.0, 2.0, 1.0, [0.5, 1.5], [1.5, 0.5], [3.0, 9.0])
check("profondeur du point le plus proche", dep[0, 0] == 3.0 and dep[1, 1] == 9.0)
dl = B.depth_raster((1, 2), 0.0, 1.0, 1.0, [0.2, 1.8], [0.5, 0.5], [2.0, 6.0], k=2)
check("profondeur lissée : moyenne pondérée, sans marche", 2.0 < dl[0, 0] < 4.0 < dl[0, 1] < 6.0)
dn, ix = B.depth_raster((1, 2), 0.0, 1.0, 1.0, [0.2, 1.8], [0.5, 0.5], [2.0, 6.0], return_idx=True)
check("indice du fokontany le plus proche", list(ix[0]) == [0, 1])
tb = B.table_by(np.array(["a", "a", "b"]), {"x": np.array([True, False, True])}).set_index("g")
check("table par groupe", tb.loc["a", "x"] == 0.5 and tb.loc["b", "mailles"] == 1)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
