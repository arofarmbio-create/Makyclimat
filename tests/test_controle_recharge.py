"""Contrôle de vraisemblance de la recharge (scripts/controle_recharge.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import controle_recharge as C  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


check("climat : P/ETP < 0,5 est aride", list(C.climate([0.2, 0.5, 1.0])) == ["aride", "humide", "humide"])

# 12 sites de socle arides (r de 0,01 à 0,12), 3 sites sédimentaires humides (trop peu : repli)
af = pd.DataFrame({"R": [10.0 * k for k in range(1, 13)] + [300.0, 300.0, 300.0], "P": [1000.0] * 15,
                   "Aridity": [0.3] * 12 + [0.8] * 3, "groupe": ["Basement"] * 12 + ["Sedimentary"] * 3})
tab = C.bounds_table(af)
q10, q90, cl = C.lookup(tab, "Basement", "aride")
check("bornes de classe (quantiles 10 et 90 %)", abs(q10 - np.quantile(np.arange(1, 13) / 100, 0.1)) < 1e-12 and cl == "Basement / aride")
_, _, cl2 = C.lookup(tab, "Sedimentary", "humide")
check("repli sur tous les sites si moins de 10 sites", cl2 == "tous / tous", cl2)
_, _, cl3 = C.lookup(tab, "Unconsolidated", "humide")
check("groupe absent : repli sur tous les sites", cl3 == "tous / tous")

t2c, lo, hi, flag = C.correct([200.0, 5.0, 50.0], [100.0, 1.0, 20.0], [400.0, 10.0, 80.0], [1000.0] * 3, [0.02] * 3, [0.10] * 3)
check("trop haut : ramené à la borne haute", t2c[0] == 100.0 and flag[0] == 1)
check("trop bas : ramené à la borne basse", t2c[1] == 20.0 and flag[1] == -1)
check("dans les bornes : inchangé", t2c[2] == 50.0 and flag[2] == 0)
check("intervalle : partie commune", lo[0] == 100.0 and hi[0] == 100.0 and lo[2] == 20.0 and hi[2] == 80.0)
check("intervalle sans recouvrement : bornes de la classe", lo[1] == 20.0 and hi[1] == 100.0)

st = C.share_table(["a", "a", "b"], [1, 0, -1]).set_index("g")
check("parts hors bornes par groupe", st.loc["a", "au_dessus"] == 0.5 and st.loc["b", "sous_borne"] == 1.0)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
