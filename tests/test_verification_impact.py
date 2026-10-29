"""Teste les scores de la vérification par l'impact (validate_reforecast_impact.py) et le parseur DesInventar, sans réseau.

Usage : python tests/test_verification_impact.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import connector_desinventar as DI  # noqa: E402
import update_floods as UF  # noqa: E402
import validate_reforecast_impact as V  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


o = np.array([0, 0, 0, 1, 1])
check("AUC : prévision parfaite = 1", V.auc([0.1, 0.2, 0.3, 0.8, 0.9], o) == 1.0)
check("AUC : prévision constante = 0,5", V.auc([0.5] * 5, o) == 0.5)
check("AUC : une seule classe -> NaN", np.isnan(V.auc([0.1, 0.9], [1, 1])))
check("Brier : parfait = 0, inverse = 1", V.brier(o, o) == 0 and V.brier(1 - o, o) == 1)
c = V.contingency([0.9, 0.9, 0.1, 0.9, 0.1], o, 0.5)
check("table de contingence : 1 détection, 2 fausses alertes, 1 raté", (c["h"], c["fa"], c["mi"], c["cn"]) == (1, 2, 1, 1)
      and abs(c["far"] - 2 / 3) < 1e-9 and c["pod"] == 0.5)
v, t = V.rev([0.1, 0.2, 0.3, 0.8, 0.9], o, 0.3, V.PROB_LEVELS)
check("valeur économique : prévision parfaite = 1", abs(v - 1) < 1e-9, f"{v} au seuil {t}")
v0, _ = V.rev([0.5] * 5, o, 0.3, [0.4])
check("valeur économique : toujours alerter quand coût/perte < fréquence = climatologie (0)", abs(v0) < 1e-9, str(v0))
check("saisons : novembre et avril -> saison commencée en novembre ; juillet hors saison",
      V.season_of(dt.date(2017, 11, 3)) == 2017 and V.season_of(dt.date(2018, 4, 30)) == 2017 and V.season_of(dt.date(2018, 7, 1)) is None)
x = np.random.default_rng(1).gumbel(50, 10, 30)
ref = UF.gumbel_levels(x, periods=(5,))[5]
check("Gumbel identique à celui des seuils du site (update_floods.py)", abs(V.gumbel_q(x.mean(), x.std(ddof=1), 5) - ref) < 1e-6)
M = np.tile(x[:24, None, None], (1, 1, 2)).astype("float32")
M[:10, 0, 1] = np.nan                                       # deuxième maille : 14 saisons seulement
seasons = np.arange(1999, 2023)
q = V.loso_thresholds(M, seasons, 2005, 5)
xx = np.delete(x[:24], 6)
check("seuils sans la saison testée (2005) ; NaN si moins de 15 saisons",
      abs(q[0, 0] - V.gumbel_q(xx.mean(), xx.std(ddof=1), 5)) < 1e-3 and np.isnan(q[0, 1]))

xml = b"""<?xml version="1.0" encoding="UTF-8"?><DESINVENTAR><fichas>
<TR><serial>1</serial><evento>CYCLONES</evento><level0>23</level0><level1>23209</level1><fechano>2012</fechano><fechames>2</fechames><fechadia>26</fechadia><afectados>56</afectados><vivdest>-1</vivdest><fuentes>BNGRC</fuentes></TR>
<TR><serial>2</serial><evento>INONDATION</evento><level0>11</level0><level1>11101</level1><fechano>2015</fechano><fechames>1</fechames><fechadia>0</fechadia><afectados>10</afectados></TR>
<TR><serial>3</serial><evento>\xef\xbf\xbdPID\xef\xbf\xbdMIE</evento><level0>11</level0><level1>00</level1><fechano>2010</fechano></TR>
</fichas></DESINVENTAR>"""
r = DI.parse(xml, "MG", {"MG26209", "MG11118", "MG11119", "MG27209x"}, {"MG11101": ["MG11118", "MG11119"]})
check("DesInventar : région renommée rapprochée par le numéro de district (23209 -> 26209)", r[1]["adm2_actuel"] == "MG26209", str(r[1]))
check("DesInventar : district découpé -> plusieurs districts actuels ; jour 0 -> date vide",
      r[2]["adm2_actuel"] == "MG11118;MG11119" and r[2]["date"] == "" and r[2]["type"] == "inondation", str(r[2]))
check("DesInventar : -1 = non renseigné ; niveau district « 00 » ignoré ; autre type conservé",
      r[1]["maisons_detruites"] == "" and r[0]["adm2"] == "" and r[0]["type"] == "autre")

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
