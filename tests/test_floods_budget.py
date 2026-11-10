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


class Horloge:
    """Horloge simulée : les requêtes lentes et les attentes avancent le temps sans attendre réellement."""
    def __init__(self):
        self.t = 1000.0

    def monotonic(self):
        return self.t

    def sleep(self, s):
        self.t += s


def avec_horloge(fonction):
    def enveloppe():
        h = Horloge()
        originaux = time.monotonic, time.sleep, F.om.requests.get, F.om.get_json
        time.monotonic, time.sleep = h.monotonic, h.sleep
        try:
            fonction(h)
        finally:
            time.monotonic, time.sleep, F.om.requests.get, F.om.get_json = originaux
    return enveloppe


@avec_horloge
def test_requete_lente_bornee_par_l_echeance(h):
    """API muette : chaque requête attend son délai complet. L'échéance (5 min) doit être tenue, nouvel essai compris."""
    vus = []

    def muette(url, params=None, timeout=None):
        vus.append(timeout)
        h.sleep(timeout)
        raise F.om.requests.Timeout("pas de réponse")

    F.om.requests.get = muette
    echeance = h.t + 300
    try:
        F.om.get_json("u", {}, retries=4, pause=5.0, deadline=echeance)
        raise AssertionError("aurait dû s'arrêter")
    except RuntimeError as e:
        assert "budget de temps épuisé" in str(e), e
    assert h.t <= echeance + 1, f"échéance dépassée de {h.t - echeance:.0f} s"
    assert vus[0] == 120 and vus[-1] < 120, vus          # le dernier essai n'a reçu que le temps restant


@avec_horloge
def test_echeance_pendant_le_dernier_lot(h):
    """Le dernier lot se termine après l'échéance : l'ensemble n'est pas renvoyé (donc pas enregistré)."""
    th = pd.DataFrame({"pcode": [f"P{i}" for i in range(30)], "lat": -19.0, "lon": 47.0, "q2": 100.0})
    lent = faux_get_json()

    def get_json(url, params, **kw):
        h.sleep(100)                                      # chaque lot dure 100 s
        return lent(url, params)

    F.om.get_json = get_json
    try:                                                  # 3 lots, échéance à 250 s : expire pendant le 3e et dernier lot
        F.ensemble(th, {"flood": {"min_q2_m3s": 1.0}}, deadline=h.t + 250)
        raise AssertionError("l'ensemble dépassant l'échéance a été renvoyé")
    except RuntimeError as e:
        assert "dernier lot" in str(e), e


if __name__ == "__main__":
    test_budget_epuise_arrete_l_ensemble()
    test_requete_lente_bornee_par_l_echeance()
    test_echeance_pendant_le_dernier_lot()
    print("OK : budget des débits GloFAS")
