"""Transfert par analogues (scripts/transfert_analogues.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import transfert_analogues as A  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


check("GLiM : métamorphique -> socle, grès -> sédimentaire, non consolidé, glace -> inconnu",
      list(A.aquifer(["mt", "ss", "su", "ig"])) == ["Basement", "Sedimentary", "Unconsolidated", "Unknown"])

# Grille 2 × 2 de 1° : coin sud-ouest (0, 0) ; valeurs 8 (mt), 3 (ss), vide, 1 (su)
grid = np.array([[8, 3], [-9999, 1]], dtype=float)
head = {"ncols": 2, "nrows": 2, "xllcorner": 0.0, "yllcorner": 0.0, "cellsize": 1.0, "nodata_value": -9999}
c = A.glim_class([1.5, 1.5, 0.5, 0.5], [0.5, 1.5, 0.5, 1.5], grid, head)
check("lecture de la classe par maille, maille vide -> voisine", c[0] == "mt" and c[1] == "ss" and c[3] == "su" and c[2] in ("mt", "su"))

# Recharge = f(pluie) et type : le socle recharge 10 fois moins
rng = np.random.default_rng(0)
n = 200
src = pd.DataFrame({"P": rng.uniform(200, 2000, n), "PET": rng.uniform(1000, 2000, n), "aquifer": rng.choice(["Basement", "Sedimentary"], n),
                    "country": rng.choice(list("ABCDEFGH"), n), "lat": rng.uniform(-30, 30, n), "lon": rng.uniform(60, 120, n)})
src["Aridity"] = src.P / src.PET
src["R"] = 0.1 * src.P * np.where(src.aquifer == "Basement", 0.1, 1.0)
lo = A.loco(src)
check("niveau 1 : le modèle bat la référence naïve dans la plupart des pays", (lo.erreur_modele < lo.erreur_naive).mean() > 0.7)
test = src.iloc[:5].copy()
pred = 10 ** A.knn_log(src.iloc[5:], test)
check("prédiction du bon ordre de grandeur", np.all(np.abs(np.log10(pred / test.R)) < 0.5))
check("test du signe : 10 sur 12 -> p < 0,05", A.sign_test(10, 12) < 0.05 and A.sign_test(8, 12) > 0.05)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
