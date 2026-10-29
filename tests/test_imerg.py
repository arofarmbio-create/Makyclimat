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
sys.exit(0 if ok and ok2 else 1)
