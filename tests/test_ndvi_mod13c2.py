"""NDVI MOD13C2 pour H-C6 (scripts/build_ndvi_mod13c2.py) : noms de variables, lecture OPeNDAP, moyennes par maille."""
import sys
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_ndvi_mod13c2 as N  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


dds = """Dataset {
    Int16 CMG_0_05_Deg_Monthly_NDVI[YDim = 3600][XDim = 7200];
    UInt8 CMG_0_05_Deg_Monthly_pixel_reliability[YDim = 3600][XDim = 7200];
} f.hdf;"""
check("variables trouvées par mots-clés", N.find_var(dds, "ndvi") == "CMG_0_05_Deg_Monthly_NDVI"
      and N.find_var(dds, "reliability") == "CMG_0_05_Deg_Monthly_pixel_reliability")
txt = "Dataset: f\nCMG_0_05_Deg_Monthly_NDVI.CMG_0_05_Deg_Monthly_NDVI[0], 5000, 6000\nCMG_0_05_Deg_Monthly_NDVI[1], 7000, -3000\n"
g = N.parse_ascii_grid(txt, "CMG_0_05_Deg_Monthly_NDVI")
check("lecture ASCII 2D (avec ou sans préfixe)", g.shape == (2, 2) and g[1, 0] == 7000)

h, w = N.ROW1 - N.ROW0 + 1, N.COL1 - N.COL0 + 1
nd = np.full((h, w), 0.5)
nd[:, :5] = np.nan
m = N.cell_means(nd, [47.0, 42.85], [-18.0, -18.0])
check("moyenne de maille ; maille dont les pixels sont tous manquants -> NaN", m[0] == 0.5 and np.isnan(m[1]))


class R:
    def __init__(self, code, text=""):
        self.status_code, self.text = code, text


class S:
    def __init__(self, seq):
        self.seq = list(seq)

    def get(self, url, timeout=None):
        x = self.seq.pop(0)
        if isinstance(x, Exception):
            raise x
        return x


waits = []
t = N.fetch(S([R(503), requests.ConnectionError(), R(200, "ok")]), "u", sleep=waits.append)
check("attente croissante sur 503 et coupure", t == "ok" and waits == [60, 120])

dmr = '<Dataset><Int16 name="CMG_0_05_Deg_Monthly_NDVI"><Dim/></Int16><UInt8 name="CMG_0_05_Deg_Monthly_pixel_reliability"/></Dataset>'
check("variables trouvées dans la description DAP4", N.find_var_dmr(dmr, "ndvi") == "CMG_0_05_Deg_Monthly_NDVI")
waits = []
check("400 : pas de nouvel essai", N.fetch(S([R(400, "bad")]), "u", sleep=waits.append) is None and waits == [])

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
