"""Teste les probabilités et le score RPSS de la planification à 12 mois (build_planning.py), sans réseau.
Usage : python tests/test_planning.py"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_planning as B  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


p0 = B.tercile_probs(0.0, 1.0)
check("prévision neutre -> ~1/3 chacun", np.allclose(p0, 1 / 3, atol=0.01), str(p0.round(3)))
p = B.tercile_probs(-3.0, 0.5)
check("prévision très sèche -> bornée à 50 % maximum et 15 % minimum, somme 1",
      abs(p.sum() - 1) < 1e-9 and p.max() <= 0.5 + 1e-9 and p.min() >= 0.15 - 1e-9 and p[0] == p.max(), str(p.round(3)))
check("RPS : prévision parfaite = 0", B.rps(np.array([1.0, 0, 0]), 0) == 0)
rng = np.random.default_rng(0)
x = rng.normal(size=45)
y_sig = 0.8 * x + 0.6 * rng.normal(size=45)
y_noise = rng.normal(size=45)
r1, r0 = B.rpss_loo(x[:, None], y_sig), B.rpss_loo(x[:, None], y_noise)
check("RPSS croisé : signal réel > 0, bruit pur <= ~0", r1 > 0 and r0 < 0.05, f"{r1:.3f} / {r0:.3f}")
print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
