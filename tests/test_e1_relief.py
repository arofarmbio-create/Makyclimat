"""E1, H3-E1 : erreur des sources selon le relief (scripts/validate_e1_relief.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_e1_relief as R  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Grille 10 x 10 : bordure de mer, île 8 x 8 ; altitude et rugosité croissent vers l'ouest (colonnes basses)
land = np.zeros((10, 10), bool)
land[1:9, 1:9] = True
cols = np.tile(np.arange(10), (10, 1)).astype(float)
alt = 2000 - 200 * cols
rug = 100 - 10 * cols
expo = np.where(cols < 5, 5.0, -5.0)
c = R.classes(alt, rug, expo, land)
check("Hautes Terres : altitude ≥ 1 000 m", c["altitude"][4, 1] == "Hautes Terres (≥ 1 000 m)" and c["altitude"][4, 8] == "moins de 1 000 m")
check("exposition : au vent et sous le vent", c["exposition"][4, 2] == "au vent (est)" and c["exposition"][4, 7] == "sous le vent (ouest)")
check("côte : bord de l'île à moins de 20 km, centre à l'intérieur", c["côte"][1, 4] == "côte (moins de 20 km)" and c["côte"][4, 4] == "intérieur")
check("rugosité : trois classes", set(c["rugosité"][land]) == {"plat", "moyen", "accidenté"})

# Source A se dégrade avec la rugosité, source B non
r2 = np.stack([np.clip(0.9 - rug / 200, 0, 1), np.full((10, 10), 0.8)])
r2[:, ~land] = np.nan
ev = np.where(land, 100.0, np.nan)[None].repeat(2, axis=0)
tab = R.zone_table(r2, ev, ["A", "B"], c, land)
rr = tab[tab.decoupage == "rugosité"].set_index("classe")
check("r de A plus faible en relief accidenté", rr.loc["accidenté", "r_A"] < rr.loc["plat", "r_A"])
check("mailles comptées : 64 par découpage", tab.groupby("decoupage").mailles.sum().eq(64).all())
rho = R.rank_corr(r2, rug, ["A", "B"], land)
check("Spearman : A négatif", rho["A"] < -0.9)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
