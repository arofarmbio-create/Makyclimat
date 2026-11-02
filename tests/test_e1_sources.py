"""E1 : grille commune et lecteurs des sources de pluie (scripts/build_e1_sources.py)."""
import datetime as dt
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_e1_sources as E  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


check("grille commune 80 x 145 mailles, centres 43,05°E / 25,95°S à 50,95°E / 11,55°S",
      (E.NX, E.NY) == (80, 145) and np.allclose([E.LONS[0], E.LATS[0], E.LONS[-1], E.LATS[-1]],
                                                [43.05, -25.95, 50.95, -11.55], atol=1e-4))
check("indices IMERG du coin sud-ouest alignés sur la grille commune",
      math.isclose(-179.95 + 0.1 * E.I0, 43.05, abs_tol=1e-6) and math.isclose(-89.95 + 0.1 * E.J0, -25.95, abs_tol=1e-6))

# CHIRPS : grille 0,05° nord en haut, avec une marge d'une maille autour de l'emprise
rows, cols = 2 * E.NY + 2, 2 * E.NX + 2
c = np.repeat(np.arange(rows, dtype="float32")[:, None], cols, axis=1)      # valeur = n° de ligne (0 = nord)
c[1:3, 1:3] = [[np.nan, np.nan], [np.nan, 4.0]]                           # bloc nord-ouest : une seule maille valide
c[-3:-1, -3:-1] = np.nan                                                    # bloc sud-est : mer
g = E.block_mean_005(c, 42.95, -11.45)
check("CHIRPS -> 0,1° : forme et sud en bas", g.shape == (E.NY, E.NX) and g[0, 1] > g[-1, 1])
check("CHIRPS -> 0,1° : moyenne des 4 mailles (lignes 289 et 290 -> 289,5 au sud)", math.isclose(g[0, 1], 289.5))
check("CHIRPS -> 0,1° : maille côtière = moyenne des mailles valides seulement", g[-1, 0] == 4.0)
check("CHIRPS -> 0,1° : maille entièrement en mer = manquante", np.isnan(g[0, -1]))

# ERA5-Land : centres sur les bords de la grille commune (146 x 81)
e = np.zeros((E.NY + 1, E.NX + 1), "float32")
e[0, 0], e[1, 0], e[0, 1], e[1, 1] = 1, 2, 3, 6
e[5, 5] = -1
ge = E.corner_mean_01(e)
check("ERA5-Land -> grille commune : moyenne des 4 voisines", ge.shape == (E.NY, E.NX) and math.isclose(ge[0, 0], 3.0))
check("valeur négative traitée comme manquante (pas comme 0)", math.isclose(ge[4, 4], 0.0) and math.isclose(ge[5, 5], 0.0))
check("valeur au-dessus de 1 000 mm/jour rejetée", np.isnan(E.clean(np.array([1200.0]))[0]))

# IMERG : réponse OPeNDAP precipitation[0][lon][lat]
lines = ["Dataset {...}", "precipitation[time=1][lon=80][lat=145]"]
for i in range(E.NX):
    lines.append(f"precipitation[0][{i}], " + ", ".join(str(i + j / 1000) for j in range(E.NY)))
gi = E.parse_imerg_ascii("\n".join(lines))
check("IMERG : transposition lon/lat -> [lat, lon]", gi.shape == (E.NY, E.NX) and math.isclose(gi[3, 2], 2.003, abs_tol=1e-5))

# GSOD
txt = ('"STATION","DATE","PRCP","PRCP_ATTRIBUTES"\n"67083099999","2015-01-01"," 1.00","G"\n'
       '"67083099999","2015-01-02","99.99"," "\n"67083099999","2015-01-03"," 0.00","I"\n')
r = E.parse_gsod(txt)
check("GSOD : pouces -> mm, 99,99 -> manquant, drapeau conservé",
      r[0] == ("2015-01-01", 25.4, "G") and np.isnan(r[1][1]) and r[2] == ("2015-01-03", 0.0, "I"))

# Forme réelle des fichiers journaliers (sonde du 02/11/2026) : variable de type Grid
lines = ["Dataset: 3B-DAY-L.MS.MRG.3IMERG.20150115-S000000-E235959.V07B.nc4",
         "precipitation.lat, " + ", ".join(str(-25.95 + 0.1 * j) for j in range(E.NY))]
for i in range(E.NX):
    lines.append(f"precipitation.precipitation[precipitation.time=12793][precipitation.lon={43.05 + 0.1 * i:.2f}], "
                 + ", ".join(str(i + j / 1000) for j in range(E.NY)))
gg = E.parse_imerg_ascii("\n".join(lines))
check("IMERG journalier (forme Grid réelle) : lu, ligne des latitudes ignorée", math.isclose(gg[3, 2], 2.003, abs_tol=1e-5))
try:
    E.parse_imerg_ascii("réponse inattendue")
    check("format inattendu : erreur explicite", False)
except ValueError:
    check("format inattendu : erreur explicite", True)

d = E.year_days(2026, dt.date(2026, 11, 2))
check("année en cours : jusqu'à hier", d[0] == dt.date(2026, 1, 1) and d[-1] == dt.date(2026, 11, 1))
check("année passée complète", len(E.year_days(2024, dt.date(2026, 11, 2))) == 366)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
