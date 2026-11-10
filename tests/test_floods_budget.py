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

    def muette(url, params=None, timeout=None, stream=False):
        vus.append(timeout)
        h.sleep(sum(timeout))                              # connexion puis attente de réponse, chacune à son délai
        raise F.om.requests.Timeout("pas de réponse")

    F.om.requests.get = muette
    echeance = h.t + 300
    try:
        F.om.get_json("u", {}, retries=4, pause=5.0, deadline=echeance)
        raise AssertionError("aurait dû s'arrêter")
    except RuntimeError as e:
        assert "budget de temps épuisé" in str(e), e
    assert h.t <= echeance + 1, f"échéance dépassée de {h.t - echeance:.0f} s"
    assert vus[0] == (30.0, 120.0) and sum(vus[-1]) < 150, vus   # le dernier essai n'a reçu que le temps restant


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


class ReponseLente:
    """Réponse 200 envoyée par petits morceaux : chacun arrive avant le délai d'inactivité, la durée totale est longue."""
    status_code = 200

    def __init__(self, h, morceaux, pas):
        self.h, self.morceaux, self.pas, self.fermee = h, morceaux, pas, False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.fermee = True

    def raise_for_status(self):
        pass

    def close(self):
        self.fermee = True

    def iter_content(self, chunk_size=1):
        for m in self.morceaux:
            self.h.sleep(self.pas)
            yield m


@avec_horloge
def test_reponse_progressive_bornee(h):
    """Relecture Codex : une réponse qui arrive goutte à goutte ne doit pas dépasser l'échéance (le timeout ne la bornait pas)."""
    corps = b'[{"daily": {"time": [], "river_discharge": []}}]'
    F.om.requests.get = lambda url, params=None, timeout=None, stream=False: ReponseLente(h, [corps[i:i + 4] for i in range(0, len(corps), 4)], 30)
    echeance = h.t + 100                                  # 13 morceaux × 30 s = 390 s : bien au-delà de l'échéance
    try:
        F.om.get_json("u", {}, deadline=echeance)
        raise AssertionError("réponse acceptée après l'échéance")
    except RuntimeError as e:
        assert "pendant la réception" in str(e), e
    assert h.t <= echeance + 30, f"dépassement de {h.t - echeance:.0f} s (au plus un morceau)"
    F.om.requests.get = lambda url, params=None, timeout=None, stream=False: ReponseLente(h, [corps], 1)
    assert F.om.get_json("u", {}, deadline=h.t + 100) == [{"daily": {"time": [], "river_discharge": []}}]


@avec_horloge
def test_prevision_echeance_pendant_le_dernier_lot(h):
    """Relecture Codex : la prévision dont le dernier lot finit après l'échéance n'est pas renvoyée (donc pas enregistrée)."""
    communes = pd.DataFrame({"pcode": [f"P{i}" for i in range(80)], "lat": -19.0, "lon": 47.0})
    rapide = faux_get_json()

    def get_json(url, params, **kw):
        h.sleep(100)                                      # 2 lots de 40 communes, 100 s chacun
        return rapide(url, params)

    F.om.get_json = get_json
    try:
        F.forecast(communes, {"forecast_days": 3}, deadline=h.t + 150)
        raise AssertionError("prévision tardive renvoyée")
    except RuntimeError as e:
        assert "dernier lot de la prévision" in str(e), e
    dates, q = F.forecast(communes, {"forecast_days": 3}, deadline=h.t + 1000)
    assert q.shape == (80, 3)


def test_lecture_bloquee_coupee_par_la_garde():
    """Relecture Codex : un serveur qui n'envoie plus rien pendant la réception bloque la lecture sans délai d'inactivité
    atteint. La garde doit fermer la connexion à l'échéance (horloge réelle, échéance à 0,5 s)."""
    import threading

    class Bloquee:
        status_code = 200

        def __init__(self):
            self.fermee = threading.Event()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.fermee.set()

        def raise_for_status(self):
            pass

        def close(self):
            self.fermee.set()

        def iter_content(self, chunk_size=1):
            yield b"[{"
            if not self.fermee.wait(30):                 # bloqué jusqu'à la fermeture par la garde (30 s si elle échoue)
                yield b"}]"
                return
            raise ConnectionError("connexion fermée pendant la lecture")

    original = F.om.requests.get
    F.om.requests.get = lambda url, params=None, timeout=None, stream=False: Bloquee()
    t0 = time.monotonic()
    try:
        F.om.get_json("u", {}, deadline=t0 + 0.5)
        raise AssertionError("lecture bloquée acceptée")
    except RuntimeError as e:
        assert "pendant la réception" in str(e), e
    finally:
        F.om.requests.get = original
    duree = time.monotonic() - t0
    assert duree < 2, f"la garde n'a pas coupé la lecture ({duree:.1f} s)"


@avec_horloge
def test_erreur_400_progressive_non_lue(h):
    """Relecture Codex : sous échéance, une réponse 400 au corps envoyé lentement ne doit pas être lue (ni dépasser le budget)."""
    class Erreur400(ReponseLente):
        status_code = 400

        @property
        def text(self):
            return b"".join(self.iter_content()).decode()

    F.om.requests.get = lambda url, params=None, timeout=None, stream=False: Erreur400(h, [b"x"] * 100, 30)
    echeance = h.t + 100
    try:
        F.om.get_json("u", {}, deadline=echeance)
        raise AssertionError("une erreur 400 aurait dû être levée")
    except ValueError as e:
        assert str(e) == "HTTP 400", e
    assert h.t <= echeance, f"corps d'erreur lu : {h.t - echeance:.0f} s au-delà de l'échéance"


if __name__ == "__main__":
    test_budget_epuise_arrete_l_ensemble()
    test_requete_lente_bornee_par_l_echeance()
    test_echeance_pendant_le_dernier_lot()
    test_reponse_progressive_bornee()
    test_prevision_echeance_pendant_le_dernier_lot()
    test_lecture_bloquee_coupee_par_la_garde()
    test_erreur_400_progressive_non_lue()
    print("OK : budget des débits GloFAS")
