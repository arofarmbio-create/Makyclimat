"""Teste les indicateurs d'inondation pluviale (validate_pluvial.py) avec de FAUSSES pluies (aucun accès réseau).

Usage : python tests/make_synthetic.py && python tests/test_validate_pluvial.py
"""
from __future__ import annotations

import datetime as dt
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import soilwater_core as C  # noqa: E402
import validate_pluvial as P  # noqa: E402
from common import country_data_dir, read_units  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


units = read_units("demo")
th = pd.read_csv(country_data_dir("demo") / "flood_thresholds.csv", dtype={"pcode": str})
leaves = units[(units.level == 4) & units.adm3.isin(set(th.pcode))].reset_index(drop=True)
n = len(leaves)
urban = np.arange(n) < n // 2                         # moitié « urbaine » (CN 92), moitié rurale (CN 70)
cn2 = np.where(urban, 92.0, 70.0)
rx3 = np.tile(np.linspace(60, 120, 15)[:, None], (1, n))   # maxima saisonniers sur 3 j : 60 à 120 mm, médiane 90


def fake(days, lons, lats, bbox):
    """Pluie de fond 8 mm/j (sol en condition II) ; 35 mm/j les 10-12/02/2005 (105 mm sur 3 j) ; 25 mm/j les 15-17/01/2007 (75 mm)."""
    v = np.full((len(days), n), 8.0, dtype="float32")
    for i, d in enumerate(days):
        if dt.date(2005, 2, 10) <= d <= dt.date(2005, 2, 12):
            v[i] = 35.0
        if dt.date(2007, 1, 15) <= d <= dt.date(2007, 1, 17):
            v[i] = 25.0
    return v


region = units.query("level == 1").name.iloc[0]
events = pd.DataFrame([{"id": "test-2005", "type": "inondation", "date_debut": "2005-02-09", "date_fin": "2005-02-12", "zones_citees": region}])
tmp = Path(tempfile.mkdtemp()) / "pluie.npz"
res = P.main("demo", fetch=fake, rx3=rx3, cn2=cn2, today=dt.date(2008, 6, 1), events=events, cache_path=tmp, first_season=2004)
pl, ru = res["ind"]["pluie"], res["ind"]["ruissellement"]
check("pluie : 105 mm sur 3 jours > seuil local de 90 mm -> détecté partout", bool(pl["detection"].detecte_vigilance.iloc[0])
      and pl["detection"].part_2ans.iloc[0] == 1.0, pl["detection"].to_string())
check("pluie : 75 mm (2007) sous le seuil local de 90 mm -> pas d'épisode ; un seul épisode (2005)", len(pl["episodes"]) == 1, pl["episodes"].to_string())
q_u, q_r = C.scs_runoff(75.0, 92.0), C.scs_runoff(75.0, 70.0)
check("SCS-CN : la même pluie ruisselle bien plus en ville (CN 92) qu'en zone rurale (CN 70)", q_u > 3 * q_r, f"{q_u:.1f} mm contre {q_r:.1f} mm")
ep07 = ru["episodes"][pd.to_datetime(ru["episodes"].debut).dt.year == 2007]
check("ruissellement : l'épisode de 2007 dépasse le seuil commun, porté par la moitié urbaine",
      len(ep07) == 1 and 0.4 <= ep07.part_max.iloc[0] <= 0.6, ru["episodes"].to_string())
check("seuils communs du ruissellement : 5 ans >= 2 ans > 0", res["Q5"] >= res["Q2"] > 0, f"{res['Q2']:.1f} / {res['Q5']:.1f}")
p5 = np.array([[10.0], [45.0], [80.0]])
c = P.amc_cn(np.array([80.0]), p5)[:, 0]
check("humidité antérieure : CN sec < CN II < CN humide", c[0] < c[1] == 80.0 < c[2], str(c))
check("cache de pluie journalière écrit", tmp.exists())

print(f"\n{FAILS} ÉCHEC(S)" if FAILS else "\nTous les tests passent")
sys.exit(1 if FAILS else 0)
