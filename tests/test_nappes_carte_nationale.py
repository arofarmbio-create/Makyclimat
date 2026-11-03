"""Carte nationale du niveau statique (scripts/nappes_carte_nationale.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nappes_carte_nationale as M  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


tab = pd.DataFrame({"distance": ["0-25 km", "25-50 km", "50-100 km", "plus de 100 km"], "erreur_hybride": [2.4, 2.8, 3.4, 2.9]})
e = M.expected_error([5, 30, 60, 300], tab)
check("erreur attendue selon la classe de distance", np.allclose(e, [2.4, 2.8, 3.4, 2.9]))

fk = pd.DataFrame({"pcode": ["a", "b", "c", "d"], "region": ["R1", "R1", "R2", "R2"], "profondeur_m": [2.0, 4.0, 10.0, np.nan],
                   "erreur_attendue_m": [2.4, 2.4, 3.4, 3.4], "extrapolation": [0.0, 1.0, 0.0, 0.0], "distance_km": [5, 15, 60, 80],
                   "bas80_m": [1, 2, 5, 6], "haut80_m": [3, 6, 15, 16]})
a = M.aggregate(fk, "region").set_index("region")
check("agrégat : médiane par région et part en extrapolation", a.loc["R1", "profondeur_mediane_m"] == 3.0
      and a.loc["R1", "part_extrapolation"] == 0.5 and a.loc["R2", "fokontany"] == 2)
x = M.to_external(fk, "2026-11-03")
check("sortie au format du système, valeurs manquantes retirées",
      list(x.columns) == ["pcode", "indicateur", "valeur", "date", "source"] and not ((x.pcode == "d") & (x.indicateur == "niveau_statique_m")).any())
check("aucune valeur de Fan publiée", not x.indicateur.str.contains("fan").any())

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
