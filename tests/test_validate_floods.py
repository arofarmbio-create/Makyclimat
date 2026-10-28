"""Teste la validation du modèle de crue (validate_floods.py) avec de FAUX débits (aucun accès réseau).

Usage : python tests/make_synthetic.py && python tests/test_validate_floods.py
"""
from __future__ import annotations

import datetime as dt
import sys
import tempfile
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
pos = {(round(a, 4), round(b, 4)): i for i, (a, b) in enumerate(zip(th.lat, th.lon))}
calls = {"n": 0}


def fake(lat, lon, start, end):
    """Débit 5 m3/s ; inondation documentée du 10 au 12/02/2005 dans la 1re moitié des communes (30 m3/s > crue de 5 ans) ;
    épisode non documenté les 15-16/01/2007 partout (12 m3/s > crue de 2 ans)."""
    calls["n"] += 1
    i = pos[(round(lat, 4), round(lon, 4))]
    days = pd.date_range(start, end).strftime("%Y-%m-%d").tolist()
    v = [5.0] * len(days)
    for k, t in enumerate(days):
        if "2005-02-10" <= t <= "2005-02-12" and i < n // 2:
            v[k] = 30.0
        if t in ("2007-01-15", "2007-01-16"):
            v[k] = 12.0
    return days, v


region = read_units("demo").query("level == 1").name.iloc[0]
events = pd.DataFrame([{"id": "test-2005", "type": "inondation", "date_debut": "2005-02-09", "date_fin": "2005-02-11", "zones_citees": region}])
tmp = Path(tempfile.mkdtemp()) / "cache.json"
res = V.main("demo", fetch=fake, today=dt.date(2008, 6, 1), events=events, pause=0, cache_path=tmp, first_season=2004)
det, epi = res["detection"], res["episodes"]
check("résultat complet (pas de quota)", res["complete"])
check("événement documenté détecté en vigilance et en alerte",
      len(det) == 1 and bool(det.detecte_vigilance.iloc[0]) and bool(det.detecte_alerte.iloc[0]), det.to_string())
check("part des communes au-dessus de la crue de 5 ans ~ 50 %", abs(det.part_communes_q5.iloc[0] - 0.5) < 0.04, str(det.part_communes_q5.iloc[0]))
check("4 saisons parcourues (2004-2005 à 2007-2008)", res["seasons"] == 4, str(res["seasons"]))
check("deux épisodes : l'un rattaché à l'événement, l'autre sans correspondance",
      len(epi) == 2 and sorted(epi.evenement_perimetre.tolist()) == ["", "test-2005"], epi.to_string())
n_calls = calls["n"]
V.main("demo", fetch=fake, today=dt.date(2008, 6, 1), events=events, pause=0, cache_path=tmp, first_season=2004)
check("cache : aucune nouvelle requête au 2e passage", calls["n"] == n_calls, f"{n_calls} puis {calls['n']}")


def quota(lat, lon, start, end):
    raise V.QuotaError("HTTP 429")


r2 = V.main("demo", fetch=quota, today=dt.date(2008, 6, 1), events=events, pause=0,
            cache_path=Path(tempfile.mkdtemp()) / "c.json", first_season=2004)
check("quota atteint : arrêt propre, résultat marqué incomplet", r2 is not None and not r2["complete"] and len(r2["detection"]) == 0)
check("AUC : 1 si séparation parfaite, 0,5 si aucune", V.auc([3, 4], [1, 2]) == 1.0 and V.auc([1, 1], [1, 1]) == 0.5)

print(f"\n{FAILS} ÉCHEC(S)" if FAILS else "\nTous les tests passent")
sys.exit(1 if FAILS else 0)
