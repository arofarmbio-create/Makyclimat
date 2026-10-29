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
check("SPEI-3 : NaN pour les 2 premiers mois", np.isnan(z3[:2]).all() and np.isfinite(z3[2:]).mean() > 0.95,
      f"NaN au début : {np.isnan(z3[:2]).tolist()} ; part finie ensuite {np.isfinite(z3[2:]).mean():.3f}")
a, b, g = C.glo_lmoments(rng.normal(0, 1, 5))
check("logistique généralisée : échantillon trop court -> NaN", np.isnan(a))
xs = -rng.gamma(2.0, 30.0, 200)                                 # asymétrie négative (bilan borné vers le haut)
xi, al, k = C.glo_lmoments(xs)
F = C.glo_cdf(np.sort(xs), xi, al, k)
emp = (np.arange(1, 201) - 0.44) / 200.12
check("logistique généralisée : asymétrie négative ajustée (écart max à la répartition empirique < 0,08)",
      np.isfinite(xi) and np.max(np.abs(F - emp)) < 0.08, f"k = {k:.2f}, écart {np.max(np.abs(F - emp)):.3f}")
import pandas as pd  # noqa: E402

import build_drought_series as BD  # noqa: E402

lat, lon = np.array([-18.0, -18.1, -18.2]), np.array([47.0, 47.1, 47.2])
valid = np.ones((3, 3), bool)
valid[1, 1] = False                                          # maille centrale manquante (mer, nuage)
u = pd.DataFrame({"level": [4, 4], "lat": [-18.1, -18.0], "lon": [47.1, 47.0], "area_km2": [1.0, 2.0], "adm2": ["D1", "D1"]})
ii, jj, w, d = BD.leaf_index(u, lat, lon, valid)
check("maille la plus proche : maille du centroïde si valide, sinon voisine valide",
      (ii[1], jj[1]) == (0, 0) and valid[ii[0], jj[0]] and max(abs(ii[0] - 1), abs(jj[0] - 1)) == 1)
f = np.array([[1.0, 0, 0], [0, 0, 0], [0, 0, 0]])
f[ii[0], jj[0]] = 4.0
check("moyenne du district pondérée par la surface", abs(BD.district_means(f, (ii, jj, w, d))["D1"] - (4 * 1 + 1 * 2) / 3) < 1e-9)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
