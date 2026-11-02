"""Carte nationale des nappes : recadrage des couches mondiales (scripts/build_nappes_mondiales.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_nappes_mondiales as N  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


# Grille ASCII au pas de 1° couvrant 40-54°E, 30-10°S ; valeur = 100 x ligne + colonne, ligne 0 au nord
rows, cols = 20, 14
vals = [[100 * r + c for c in range(cols)] for r in range(rows)]
vals[5][5] = -9999
txt = "ncols 14\nnrows 20\nxllcorner 40\nyllcorner -30\ncellsize 1\nNODATA_value -9999\n" + \
      "\n".join(" ".join(str(v) for v in row) for row in vals)
a, west, north, res = N.crop_ascii_grid(txt, (43.0, -26.0, 51.0, -11.5))
check("grille ASCII : mailles dont le centre est dans l'emprise, bords compris (15 x 8)", a.shape == (15, 8), str(a.shape))
check("grille ASCII : coin nord-ouest recadré (43°E, 11°S)", (west, north) == (43.0, -11.0))
check("grille ASCII : nord en haut, valeur de la maille 43,5°E 11,5°S", a[0, 0] == 100 * 1 + 3)
check("grille ASCII : NODATA devient NaN", np.isnan(a[4, 2]))

df = pd.DataFrame({"Lat": [-18.9, -30.0, -12.0, -18.9], "Lon": [47.5, 47.5, 49.3, 60.0], "Country": ["Madagascar"] * 4})
f = N.filter_points(df, (43.0, -26.0, 51.0, -11.5))
check("points : seuls ceux de l'emprise de Madagascar", len(f) == 2 and set(f.Lat) == {-18.9, -12.0})

check("licences : couches non republiables bien marquées",
      not N.SOURCES["fan"]["republication"] and not N.SOURCES["fluor"]["republication"]
      and all(N.SOURCES[k]["republication"] for k in ("socle", "glhymps", "glim", "salinite")))
check("chaque couche a une citation, une licence, une unité et une résolution",
      all(all(v.get(k) for k in ("citation", "licence", "unite", "resolution", "url")) for v in N.SOURCES.values()))

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
