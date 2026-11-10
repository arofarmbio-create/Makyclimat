"""Budget de temps des débits GloFAS (update_floods.py), sans réseau : une API lente ne doit plus bloquer la publication.

Usage : python tests/test_floods_budget.py
"""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update_floods as F  # noqa: E402


def faux_get_json(lent=0.0):
    def get_json(url, params, **kw):
        time.sleep(lent)
        n = len(params["latitude"].split(","))
        jours = [f"2026-11-{j + 1:02d}" for j in range(3)]
        membres = {f"river_discharge_member{m:02d}": [1.0] * 3 for m in range(1, 51)} if params.get("ensemble") else {}
        return [{"daily": {"time": jours, "river_discharge": [1.0] * 3, **membres}} for _ in range(n)]
    return get_json


def test_budget_epuise_arrete_l_ensemble():
    th = pd.DataFrame({"pcode": [f"P{i}" for i in range(40)], "lat": -19.0, "lon": 47.0, "q2": 100.0})
    cfg = {"flood": {"min_q2_m3s": 1.0}}
    original, sommeil = F.om.get_json, time.sleep
    F.om.get_json, F.time.sleep = faux_get_json(0.0), lambda s: None
    try:
        dates, pc, q = F.ensemble(th, cfg, deadline=time.monotonic() + 60)       # budget large : tout est récupéré
        assert q.shape == (51, 40, 3), q.shape
        try:
            F.ensemble(th, cfg, deadline=time.monotonic() - 1)                   # budget épuisé : arrêt avant le 1er lot
            raise AssertionError("l'ensemble aurait dû s'arrêter")
        except RuntimeError as e:
            assert "budget de temps épuisé après 0/40" in str(e), e
    finally:
        F.om.get_json, F.time.sleep = original, sommeil
    assert time.sleep is sommeil


if __name__ == "__main__":
    test_budget_epuise_arrete_l_ensemble()
    print("OK : budget des débits GloFAS")
