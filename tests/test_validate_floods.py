"""Teste la validation du modèle de crue (validate_floods.py) avec de FAUX débits (aucun accès réseau).

Usage : python tests/make_synthetic.py && python tests/test_validate_floods.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate_floods as V  # noqa: E402
from common import country_data_dir, read_units  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


th = pd.read_csv(country_data_dir("demo") / "flood_thresholds.csv", dtype={"pcode": str})   # q2 = 10, q5 = 20
n = len(th)
dates = np.array([str(dt.date(2000, 1, 1) + dt.timedelta(days=i)) for i in range(365 * 11)])
Q = np.full((len(dates), n), 5.0, dtype="float32")
i_ev = np.where(dates == "2005-02-10")[0][0]
Q[i_ev:i_ev + 3, : n // 2] = 30.0                    # inondation documentée : la moitié des communes au-dessus de la crue de 5 ans
i_fa = np.where(dates == "2007-01-15")[0][0]
Q[i_fa:i_fa + 2, : max(1, n // 5)] = 12.0            # épisode non documenté : 20 % des communes au-dessus de la crue de 2 ans
i_dry = np.where(dates == "2008-07-15")[0][0]
Q[i_dry, :n] = 50.0                                   # juillet : hors saison, ignoré dans les épisodes
region = read_units("demo").query("level == 1").name.iloc[0]
events = pd.DataFrame([{"id": "test-2005", "date_debut": "2005-02-09", "date_fin": "2005-02-11", "zones_citees": region}])
res = V.main("demo", history=(dates, Q, np.arange(n)), today=dt.date(2010, 12, 31), events=events)
det = res["detection"]
check("événement documenté détecté en vigilance et en alerte", len(det) == 1 and bool(det.detecte_vigilance.iloc[0]) and bool(det.detecte_alerte.iloc[0]), det.to_string())
check("part des communes au-dessus de la crue de 5 ans ~ 50 %", abs(det.part_communes_q5.iloc[0] - 0.5) < 0.02)
epi = res["episodes"]
check("deux épisodes en saison (le pic de juillet est ignoré)", len(epi) == 2, epi.to_string())
check("un épisode rattaché à l'événement, l'autre sans correspondance",
      sorted(epi.evenement_documente.tolist()) == ["", "test-2005"], str(epi.evenement_documente.tolist()))
check("AUC : 1 si séparation parfaite, 0,5 si aucune", V.auc([3, 4], [1, 2]) == 1.0 and V.auc([1, 1], [1, 1]) == 0.5)

print(f"\n{FAILS} ÉCHEC(S)" if FAILS else "\nTous les tests passent")
sys.exit(1 if FAILS else 0)
