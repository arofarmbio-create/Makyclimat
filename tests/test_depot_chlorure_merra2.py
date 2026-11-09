"""Dépôt de chlorure MERRA-2 (scripts/depot_chlorure_merra2.py), sur données simulées."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import depot_chlorure_merra2 as M  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


check("20 variables de dépôt de sel de mer", len(M.VARS) == 20 and "SSDP001" in M.VARS and "SSSD005" in M.VARS)
check("grille : 43 et 47,5 E, 22,5 et 25,7 S couverts", M.LON[0] <= 43 and M.LON[-1] >= 47.5 and M.LAT[0] <= -25.7
      and M.LAT[-1] >= -22.5)
txt = "Dataset: x\n/SSDP001[0][0], 1e-12, 2e-12\n/SSDP001[0][1], 3e-12, 4e-12\n/SSWT001[0][0], 9, 9\n"
a = M.parse_csv(txt, "SSDP001", (2, 2))
check("lecture CSV DAP4 d'une variable [time][lat][lon]", np.allclose(a, [[1e-12, 2e-12], [3e-12, 4e-12]]))
try:
    M.parse_csv(txt, "SSDP001", (3, 2)); check("forme inattendue refusée", False)
except ValueError:
    check("forme inattendue refusée", True)
check("conversion : 1e-12 kg/m²/s = 31,6 mg/m²/an", np.isclose(1e-12 * M.SEC_AN * 1e6, 31.56, atol=0.01))
t = M.table_scenarios()
check("scénario bas à 10 km = 500 × (0,3 + 1,5 e^-1)", np.isclose(t["bas"]["10 km"], round(500 * (0.3 + 1.5 / np.e))))
check("scénario central à 200 km ≈ 500 × 0,4 × 1,3", abs(t["central"]["200 km"] - 260) < 2)
calls = []


class S:
    def get(self, url, timeout):
        import requests
        calls.append(url)
        raise requests.ConnectionError


pauses = []
r = M.fetch(S(), "u", sleep=pauses.append)
check("fetch : 3 essais, 2 pauses de 30 s, puis None", r is None and len(calls) == 3 and pauses == [30.0, 30.0])

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
