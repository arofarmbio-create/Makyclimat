"""Teste l'ET0 Penman-Monteith mensuelle et le SPEI (soilwater_core), sans réseau. Usage : python tests/test_spei.py"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import soilwater_core as C  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# FAO-56, exemple 17 (Bangkok, avril) : T moyenne 30,2 °C, ea 2,85 kPa, u2 2 m/s, Rs 22,65 MJ/m²/j, 13°44' N -> 5,72 mm/j
td = 23.24 + 273.15                                         # point de rosée donnant ea = 2,85 kPa
e = C.et0_pm_monthly(30.2 + 273.15, td, 2 / 0.748, 0.0, 22.65e6, 101300.0, 13.73, 2000, 4) / 30
check("ET0 Penman-Monteith : exemple 17 de FAO-56 à 12 % près (température moyenne au lieu de Tmax/Tmin)", abs(e - 5.72) / 5.72 < 0.12, f"{e:.2f} mm/j")
rng = np.random.default_rng(3)
D = rng.normal(20, 40, (600, 2))
z = C.spei(D + 100, np.full(D.shape, 100.0), 1, 1)
ok = np.isfinite(z)
check("SPEI d'un bilan gaussien : moyenne ~0, écart-type ~1", abs(np.nanmean(z)) < 0.1 and abs(np.nanstd(z) - 1) < 0.1,
      f"{np.nanmean(z):.2f} / {np.nanstd(z):.2f}")
m = np.arange(0, 600, 12)
check("SPEI croissant avec le bilan (même mois du calendrier)", np.all(np.diff(z[m, 0][np.argsort(D[m, 0])]) >= -1e-9))
z3 = C.spei(D + 100, np.full(D.shape, 100.0), 3, 1)
check("SPEI-3 : NaN pour les 2 premiers mois", np.isnan(z3[:2]).all() and np.isfinite(z3[2:]).mean() > 0.95)
a, b, g = C.loglogistic_lmoments(rng.normal(0, 1, 5))
check("log-logistique : échantillon trop court -> NaN", np.isnan(a))
print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
