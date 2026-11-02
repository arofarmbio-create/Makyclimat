"""Covariables H-C6 (scripts/build_covariables_hc6.py) : grille BGS, moyennes CRU, regroupements, majorités."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_covariables_hc6 as H  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


a = np.array([[10.0, -3.4e38], [20.0, 30.0]], "float32")
d = H.bgs_cells(a, 47.0, -18.0, 0.28, -3.4028230607370965e38)
check("grille BGS : mailles valides seulement, centres calculés", len(d) == 3 and d.iloc[0].lon == 47.14 and d.iloc[0].lat == -18.14)
d2 = H.bgs_cells(np.array([[5.0]], "float32"), 42.5, -11.0, 0.28, None)
check("grille BGS : centre hors de l'emprise de Madagascar écarté", d2.empty)

xs, ys = H.cell_points(47.0, -18.0, 7)
check("49 points dans la maille de 0,28°", len(xs) == 49 and abs(xs.min() - (47.0 - 0.12)) < 1e-9 and xs.max() < 47.14)
check("majorité, valeurs vides ignorées", H.majority(["B", None, "B", "C", ""]) == "B" and H.majority([None]) is None)

years = [2001] * 12 + [2002] * 12
months = list(range(1, 13)) * 2
check("CRU pluie : somme annuelle puis moyenne", H.cru_annual([10.0] * 24, years, months, "pre") == 120.0)
check("CRU ETP : mm/jour x jours du mois", H.cru_annual([1.0] * 24, years, months, "pet") == 365.0)

check("aquifère : B-L/LM -> Basement ; CSIF -> Sedimentary ; U -> Unconsolidated",
      H.aquifer_group("B-L/LM") == "Basement" and H.aquifer_group("CSIF-M") == "Sedimentary" and H.aquifer_group("U-H") == "Unconsolidated")
check("aquifère inconnu ou vide : rien", H.aquifer_group("X-L") is None and H.aquifer_group(None) is None)

qml = '<item value="3" label="Arenosols"/><item value="12" label="Ferralsols"/><item value="99" label="Inconnu"/>'
check("légende WRB -> codes de 2 lettres", H.wrb_legend(qml) == {3: "AR", 12: "FR"})

check("occupation : classe regroupée majoritaire (arbres + mangrove = forêt)",
      H.worldcover_group({10: 0.3, 95: 0.2, 30: 0.4, 40: 0.05}) == "forest")

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
