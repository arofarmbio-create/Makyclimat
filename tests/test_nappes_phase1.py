"""Phase 1 du module eaux souterraines (scripts/nappes_phase1.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nappes_phase1 as P  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Grille SPI de 2 mois, 2 x 2 mailles de 1° (coin nord-ouest 44 E, 20 S) ; SPI-3 = numéro de maille + 10 × mois
spi = {"mois": np.array(["2025-01", "2025-02"]), "lon0": np.array(44.0), "lat0": np.array(-20.0), "res": np.array(1.0),
       "spi3": np.array([[[0, 1], [2, 3]], [[10, 11], [12, 13]]], dtype="float16"),
       "spi12": np.zeros((2, 2, 2), dtype="float16")}
df = pd.DataFrame({"lon": [44.5, 45.5, 44.5, 45.5], "lat": [-20.5, -21.5, -21.5, -20.5],
                   "date": pd.to_datetime(["2025-01-10", "2025-02-03", "2026-07-01", "2024-06-01"])})
o = P.date_features(df, spi)
check("SPI-3 lu au mois et à la maille du forage", o.spi3.iloc[0] == 0 and o.spi3.iloc[1] == 13)
check("relevé postérieur à la dernière grille : dernier mois complet", o.spi3.iloc[2] == 12)
check("relevé antérieur aux grilles : pas de SPI", np.isnan(o.spi3.iloc[3]))
check("saison : janvier et février en saison des pluies, juin et juillet non", list(o.saison) == [1, 1, 0, 0])

# Deux régions ; S1 réduit l'erreur partout -> gardées ; écart démontré seulement si les IC sont sous 0
p0 = pd.DataFrame({"region": ["A"] * 20 + ["B"] * 20, "dist_km": [10.0] * 20 + [120.0] * 20, "mesure_m": 5.0,
                   "err_hybride": [2.0] * 20 + [4.0] * 20})
p1 = p0.assign(err_hybride=p0.err_hybride - 1)
res = P.compare(p0, p1, n=200)
check("critère 1 : S0 = 3, S1 = 2", res["c1"]["s0"] == 3.0 and res["c1"]["s1"] == 2.0)
check("écart sur les mêmes tirages : toujours -1", res["c1"]["ecart_ic"] == (-1.0, -1.0))
check("règle : gardées et démontré", P.decide(res) == (True, True))
p2 = p0.assign(err_hybride=np.r_[np.ones(20), 5 * np.ones(20)])
check("règle : critère 2 dégradé -> rejetées", P.decide(P.compare(p0, p2, n=200)) == (False, False))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
