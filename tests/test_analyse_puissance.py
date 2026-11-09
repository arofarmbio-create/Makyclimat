"""Analyse de puissance (scripts/analyse_puissance.py) : formules de référence."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import analyse_puissance as A  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    FAILS += 0 if cond else 1


check("Spearman rho 0,3 : environ 85 unités", 83 <= A.n_spearman(0.3) <= 87, f"{A.n_spearman(0.3):.1f}")
check("puissance croissante avec n", A.puissance_spearman(0.3, 100) > A.puissance_spearman(0.3, 30))
check("AUC : 4 fois moins d'erreur type demande 16 fois plus de blocs", np.isclose(A.n_auc(0.04, 100, 0.05) / A.n_auc(0.01, 100, 0.05), 16))
check("prospectif : carte parfaite, peu de sites", A.n_prospectif(0.99) < 20)
rng = np.random.default_rng(0)
check("simulation : dispersion nulle → règle toujours remplie", A.sim_correction(6, -0.7, 1e-9, 0.3, rng, nsim=50) == 1.0)
print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
