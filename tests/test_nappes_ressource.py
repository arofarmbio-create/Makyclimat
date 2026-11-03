"""Recharge, volume, renouvellement et risque (scripts/nappes_ressource.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nappes_ressource as R  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


lo, hi = R.sy_range(["Basement", "Sedimentary", ""])
check("Sy selon le groupe d'aquifère", list(lo) == [0.02, 0.05, 0.02] and list(hi) == [0.08, 0.15, 0.15])
blo, bhi = R.saturated([30, 5], [3, 2], [9, 8])
check("épaisseur saturée bornée à 0", list(blo) == [21, 0] and list(bhi) == [27, 3])
check("10 m saturés à Sy 0,05 = 500 mm d'eau", R.volume_mm(10, 0.05) == 500)
check("renouvellement 500 mm / 50 mm/an = 10 ans ; recharge nulle -> manquant", np.allclose(R.renewal_years([500, 1], [50, 0]), [10, np.nan], equal_nan=True))
check("prélèvements : 1 000 habitants à 15 L/j (Sphère) sur 1 km² = 5,475 mm/an", abs(R.withdrawals_mm(1000, 1.0) - 5.475) < 1e-9)
check("Antananarivo : 47 % desservis par l'eau de surface (6 arrondissements)", len(R.SURFACE_NETWORK) == 6 and set(R.SURFACE_NETWORK.values()) == {0.47})
check("classes d'exploitation", list(R.label([0.05, 0.2, 0.5, np.nan], R.CLASSES)) == ["faible", "modéré", "élevé", ""])
check("eau salée : une classe de plus, sans dépasser « élevé »",
      list(R.worsen(np.array(["faible", "élevé", "modéré"], dtype=object), np.array([True, True, False]))) == ["modéré", "élevé", "modéré"])
check("noms normalisés sans accents ni ponctuation", R.norm("Amoron'i Mania") == R.norm("AMORON I MANIA") == "AMORONIMANIA")

units = pd.DataFrame({"level": [1, 2, 3, 3, 4, 4, 4], "pcode": ["R", "D", "C1", "C2", "F1", "F2", "F3"],
                      "name": ["Androy", "Ambovombe", "Ambanisarika", "Autre", "f1", "f2", "f3"],
                      "adm1": ["R", "R", "R", "R", "R", "R", "R"], "adm2": [None, "D", "D", "D", "D", "D", "D"],
                      "adm3": [None, None, "C1", "C2", "C1", "C1", "C2"], "pop": [0, 0, 0, 0, 100.0, 300.0, 50.0]})
seam = pd.DataFrame({"region": ["ANDROY"], "district": ["AMBOVOMBE"], "commune": ["AMBANISARIKA"], "population": [800.0]})
fac, matched = R.commune_factor(units, seam)
check("facteur communal SEAM / WorldPop = 2 ; commune absente = 1", fac["C1"] == 2.0 and fac["C2"] == 1.0 and matched == 0.5)

fk = pd.DataFrame({"niveau_m": [5.0], "bas80_m": [3.0], "haut80_m": [8.0], "socle_m": [25.0], "groupe": ["Basement"],
                   "r_mm": [50.0], "r_bas_mm": [20.0], "r_haut_mm": [150.0], "pop_ajustee": [5000.0], "area_km2": [1.0],
                   "conductivite_us": [3500.0], "lat": [-24.0]})
r = R.compute(fk).iloc[0]
check("stock central : 20 m × Sy 0,05 = 1 000 mm ; τ = 20 ans", abs(r.v_mm - 1000) < 1e-9 and abs(r.tau_ans - 20) < 1e-9)
check("fourchette de τ : bas = 17 × 0,02 × 1 000 / 150, haut = 22 × 0,08 × 1 000 / 20",
      abs(r.tau_bas_ans - 340 / 150) < 1e-9 and abs(r.tau_haut_ans - 88) < 1e-9)
check("indice 27,375 / 50 = 0,5475 -> élevé ; Grand Sud signalé", abs(r.exploitation - 0.5475) < 1e-9 and r.risque == "élevé" and r.grand_sud)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
