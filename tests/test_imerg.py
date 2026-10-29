"""Teste la lecture des réponses OPeNDAP d'IMERG (build_imerg_pilot.py), sans réseau. Usage : python tests/test_imerg.py"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_imerg_pilot as B  # noqa: E402

TXT = """Dataset: 3B-HHR.MS.MRG.3IMERG.20220124-S000000-E002959.0000.V07B.HDF5
precipitation[0][0], 0, 0.5, -9999.9
precipitation[0][1], 1.34, 2, 3
"""
g = B.parse_ascii(TXT, (2262, 2263, 696, 698))
ok = g.shape == (3, 2) and g[1, 0] == 0.5 and np.isnan(g[2, 0]) and abs(g[0, 1] - 1.34) < 1e-6
print(("OK    " if ok else "ÉCHEC ") + "réponse ASCII OPeNDAP -> grille [lat, lon], valeurs négatives = manquantes")
try:
    B.parse_ascii(TXT, (2262, 2264, 696, 698))
    ok2 = False
except ValueError:
    ok2 = True
print(("OK    " if ok2 else "ÉCHEC ") + "grille de taille inattendue -> erreur (pas de décalage silencieux)")
import validate_imerg_pluvial as V  # noqa: E402

P = np.zeros((96, 2), dtype="float32")
P[10:16, 0] = 2.0                         # 2 mm/h pendant 3 h, le premier jour, maille 0
P[60, 1] = np.nan                         # un pas manquant le deuxième jour, maille 1
d1, d3 = V.daily_max(P, 1), V.daily_max(P, 3)
ok3 = d1.shape == (2, 2) and d1[0, 0] == 2.0 and d3[0, 0] == 6.0 and d3[1, 0] == 0.0
print(("OK    " if ok3 else "ÉCHEC ") + "cumul glissant : 2 mm/h pendant 3 h -> 2 mm en 1 h, 6 mm en 3 h")
l2, l5 = V.loso_levels(np.array([[1.0], [2.0], [3.0], [100.0]]), 3)
ok4 = l2[0] == 2.0 and l5[0] < 3.0
print(("OK    " if ok4 else "ÉCHEC ") + "seuils sans la saison testée (la saison extrême exclue)")
sys.exit(0 if ok and ok2 and ok3 and ok4 else 1)
