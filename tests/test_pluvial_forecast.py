"""Teste le ruissellement prévu à 7 jours (update_pluvial_forecast.py) sur la prévision simulée du pays démo (sans réseau).

Usage : python tests/make_synthetic.py && python tests/test_pluvial_forecast.py
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update_pluvial_forecast as U  # noqa: E402
from common import country_data_dir, country_docs_dir, read_units  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


leaves = read_units("demo").query("level == 4").reset_index(drop=True)
n = len(leaves)
rx3 = np.tile(np.linspace(40, 100, 15)[:, None], (1, n))          # maxima saisonniers sur 3 j : 40 à 100 mm
cn2 = np.full(n, 85.0)
# prévision simulée (tests/make_synthetic.py), aujourd'hui 21/02/2026 : 130 mm le 23/02 au nord (lat > -16,5), 140 mm le 02/03
# au centre-est (jour 10, hors des 7 jours), 3 mm/j ailleurs, rien au sud (lat < -24)
out = U.main("demo", today=dt.date(2026, 2, 21), rx3=rx3, cn2=cn2)
north = (leaves.lat > -16.5 + 0.13).to_numpy()
centre_est = ((leaves.lat > -21.0 + 0.13) & (leaves.lat < -18.5 - 0.13) & (leaves.lon > 46.5 + 0.13)).to_numpy()
check("pluie de 130 mm dans les 7 jours au nord -> alerte (retour 5 ans) partout au nord", north.any() and (out["level"][north] == 2).all(),
      f"{int((out['level'][north] == 2).sum())}/{int(north.sum())}")
check("pluie du jour 10 (centre-est) hors horizon de 7 jours -> aucun niveau", centre_est.any() and (out["level"][centre_est] == 0).all())
elsewhere = (leaves.lat < -16.5 - 0.13).to_numpy()                # hors du nord et de sa bande de bord (mailles voisines)
check("3 mm/j ailleurs -> aucun niveau", (out["level"][elsewhere] == 0).all())
ext = pd.read_csv(country_data_dir("demo") / "external" / "pluvial_forecast.csv", dtype={"pcode": str})
check("indicateurs écrits par fokontany et par zone", {"ruiss_prevu_mm", "ruiss_prevu_niveau", "ruiss_prevu_part_pct"} <= set(ext.indicateur)
      and ext[ext.indicateur == "ruiss_prevu_part_pct"].pcode.nunique() > 3)
j = json.load(open(country_docs_dir("demo") / "pluvial_forecast.json", encoding="utf-8"))
check("JSON marqué expérimental, 7 jours, seuils par région", j["experimental"] and len(j["days"]) == 7 and all("q2_mm" in r for r in j["regions"]))
old = U.main("demo", today=dt.date(2025, 1, 1), rx3=rx3, cn2=cn2)
check("date absente de la prévision : rien calculé, pas d'erreur", old is None)

print(f"\n{FAILS} ÉCHEC(S)" if FAILS else "\nTous les tests passent")
sys.exit(1 if FAILS else 0)
