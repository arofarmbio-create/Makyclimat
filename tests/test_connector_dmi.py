"""Teste le calcul du DMI à partir d'ERSST v5 (connector_dmi.py), sans réseau.

Usage : python tests/test_connector_dmi.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import connector_dmi as D  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


txt = """sst.sst[2][2][3]
[0][0], -9.96921E36, 26.02834, 25.654982
[0][1], 25.84527, 25.913343, 26.103895
[1][0], -9.96921E36, 27.311953, 27.022852
[1][1], 26.866732, 27.002375, 27.22482

sst.time[2]
82757.0, 82788.0
"""
a = D.parse_ascii(txt.split("sst.sst")[1], 2, 2, 3)
check("lecture OPeNDAP : forme et valeurs", a.shape == (2, 2, 3) and abs(a[1, 1, 2] - 27.22482) < 1e-6)
check("valeur de remplissage (terre) -> NaN", np.isnan(a[0, 0, 0]) and np.isnan(a[1, 0, 0]))
m = D.box_mean(a, (39, 40, 25, 27))
check("moyenne de zone ignorant la terre", np.isfinite(m).all() and 25.6 < m[0] < 26.2, str(m))

years = np.repeat(np.arange(1985, 2027), 12)
months = np.tile(np.arange(1, 13), 2026 - 1985 + 1)
seas = 2 * np.sin(2 * np.pi * months / 12)
west, east = 27 + seas, 28 + seas
k = (years == 2026) & (months == 8)
west2 = west.copy()
west2[k] += 0.8                                      # ouest plus chaud de 0,8 °C en août 2026 : dipôle positif
d = D.dmi_series(west2, east, years, months)
check("cycle saisonnier retiré : DMI nul hors anomalie", np.allclose(d[~k], 0, atol=1e-9))
check("anomalie ouest +0,8 °C -> DMI +0,8", abs(d[k][0] - 0.8) < 1e-9, str(d[k]))

print(f"\n{FAILS} ÉCHEC(S)" if FAILS else "\nTous les tests passent")
sys.exit(1 if FAILS else 0)
