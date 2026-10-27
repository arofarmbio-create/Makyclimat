"""Tests de la logique de filtrage des activations Copernicus EMS « quasi temps réel » (sans réseau,
l'API est simulée). Ne teste pas l'extraction des couches vectorielles (deja couverte par
validate_fokontany.py et ses tests)."""
import datetime as dt
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import connector_ems_live as el  # noqa: E402


def _resp(payload):
    r = MagicMock()
    r.raise_for_status = lambda: None
    r.json.return_value = payload
    return r


def test_filters_by_country_and_keeps_open_activation():
    now = dt.datetime.now(dt.timezone.utc)
    page = {"results": [
        {"code": "EMSR999", "countries": ["Madagascar"], "closed": False,
         "activationTime": (now - dt.timedelta(days=200)).isoformat()},  # vieille mais toujours ouverte -> gardée
        {"code": "EMSR998", "countries": ["Kenya"], "closed": False,
         "activationTime": now.isoformat()},  # mauvais pays -> écartée
    ], "next": None}
    session = MagicMock()
    session.get.return_value = _resp(page)
    out = el.list_madagascar_activations(session)
    assert [a["code"] for a in out] == ["EMSR999"]


def test_excludes_old_closed_activation():
    now = dt.datetime.now(dt.timezone.utc)
    page = {"results": [
        {"code": "EMSR001", "countries": ["Madagascar"], "closed": True,
         "activationTime": (now - dt.timedelta(days=200)).isoformat()},  # fermée et ancienne -> écartée (va dans l'historique validé)
        {"code": "EMSR002", "countries": ["Madagascar"], "closed": True,
         "activationTime": (now - dt.timedelta(days=5)).isoformat()},  # fermée mais récente -> gardée (encore "quasi temps réel")
    ], "next": None}
    session = MagicMock()
    session.get.return_value = _resp(page)
    out = el.list_madagascar_activations(session)
    assert [a["code"] for a in out] == ["EMSR002"]


def test_follows_pagination():
    page1 = {"results": [{"code": "A", "countries": ["Madagascar"], "closed": False, "activationTime": None}], "next": "PAGE2"}
    page2 = {"results": [{"code": "B", "countries": ["Madagascar"], "closed": False, "activationTime": None}], "next": None}
    session = MagicMock()
    session.get.side_effect = [_resp(page1), _resp(page2)]
    out = el.list_madagascar_activations(session)
    assert {a["code"] for a in out} == {"A", "B"}


if __name__ == "__main__":
    test_filters_by_country_and_keeps_open_activation()
    test_excludes_old_closed_activation()
    test_follows_pagination()
    print("OK : tests connector_ems_live")
