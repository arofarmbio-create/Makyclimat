"""Modèle THMS (scripts/thms_test_sud.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import thms_test_sud as M  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


P = np.zeros(400)
P[10] = 200.0
I = M.soil_infiltration(P, np.zeros(400), 50.0)
check("sol : surplus d'une pluie de 200 mm sur un sol à moitié plein (25 mm) de capacité 50 mm = 175 mm", abs(I.sum() - 175) < 1e-9)
r = M.linear_reservoir(np.r_[1.0, np.zeros(999)], 10.0)
check("réservoir linéaire : masse conservée et pic au premier jour", abs(r.sum() - 1) < 1e-3 and r.argmax() == 0)
check("réservoir lent : réponse plus étalée", M.linear_reservoir(np.r_[1.0, np.zeros(999)], 100.0)[50] > r[50])
h = M.simulate(np.r_[100.0, np.zeros(999)], [1.0], [1.0], 0.05, 1e9, -10.0)
check("nappe sans drainage : 100 mm × Sy 0,05 -> +2 m", abs(h[-1] - (-8.0)) < 0.02, f"{h[-1]:.3f}")
check("KGE parfait = 1", abs(M.kge(np.arange(100.0) + 5, np.arange(100.0) + 5) - 1) < 1e-12)
ism, w, T, sy, taud, h0 = M.unpack(np.array([3, 0.8, 0.5, 1.0, 2.0, 0.03, 5.0, -10.0]), 2)
check("décodage : poids renormalisés (somme 1,3 > 1) et T1 < T2", abs(w.sum() - 1) < 1e-12 and T[0] < T[1] and M.SMAX_GRID[ism] == 100.0)

# Retrouver une mémoire lente simulée : M = 2 doit caler aussi bien que la vérité
rng = np.random.default_rng(0)
P = rng.gamma(0.3, 20.0, 1500)
ET0 = np.full(1500, 3.0)
Is = [M.soil_infiltration(P, ET0, s) for s in M.SMAX_GRID]
obs = M.simulate(Is[3], [0.3, 0.5], [5.0, 200.0], 0.03, 300.0, -10.0) + rng.normal(0, 0.01, 1500)
cal = np.zeros(1500, bool)
cal[365:1000] = True
p, k, aic, sim = M.fit(Is, obs, cal, 2, (0.01, 0.05))
check("calage sur données simulées : KGE de calage > 0,9", k > 0.9, f"{k:.3f}")

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
