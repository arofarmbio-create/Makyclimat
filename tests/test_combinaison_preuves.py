"""Combinaison des preuves (scripts/combinaison_preuves.py)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import combinaison_preuves as C  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    FAILS += 0 if cond else 1


check("Stouffer : deux lignes égales de même poids", np.isclose(C.stouffer([(1.0, 4), (1.0, 4)]), np.sqrt(2)))
check("Stouffer : poids √n", C.stouffer([(2.0, 100), (0.0, 1)]) > 1.9)
check("Wilcoxon : tout positif → z positif", C.z_wilcoxon([1, 2, 3, 4, 5, 6])[0] > 1.5)
check("Wilcoxon : trop peu d'unités → nan", np.isnan(C.z_wilcoxon([1, 2])[0]))
check("verdict établi", C.verdict(2.5, [(2.0, 10), (1.5, 10)]) == "établi")
check("contradiction forte empêche « établi »", C.verdict(2.5, [(4.0, 10), (-2.0, 10)]).startswith("non établi"))
check("indice", C.verdict(1.2, [(1.2, 10)]) == "indice")
print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
