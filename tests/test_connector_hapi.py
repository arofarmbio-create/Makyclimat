"""Tests du connecteur HAPI : génération de l'app_identifier, et robustesse face à un échec HTTP
(ne doit jamais planter avec une trace contenant l'app_identifier, ni avec l'ancien exit forcé si le secret
était absent)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import connector_hapi as ch  # noqa: E402


class FakeResp:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._payload = payload or {}

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_get_app_identifier_uses_env_override():
    with patch.dict("os.environ", {"HAPI_APP_IDENTIFIER": "xyz"}):
        assert ch.get_app_identifier() == "xyz"


def test_get_app_identifier_calls_official_endpoint():
    with patch.dict("os.environ", {}, clear=True):
        with patch("connector_hapi.requests.get", return_value=FakeResp(200, {"encoded_app_identifier": "abc123"})) as m:
            assert ch.get_app_identifier() == "abc123"
            assert "encode_app_identifier" in m.call_args[0][0]


def test_fetch_all_403_raises_runtimeerror_without_leaking_params():
    with patch("connector_hapi.requests.get", return_value=FakeResp(403)):
        try:
            ch.fetch_all("/x", {"a": "b"}, "SECRETIDENTIFIER")
            assert False, "devrait lever"
        except RuntimeError as exc:
            msg = str(exc)
            assert "SECRETIDENTIFIER" not in msg
            assert "403" in msg


def test_fetch_all_success_paginates():
    page1 = FakeResp(200, {"data": [{"a": 1}] * 2})
    page2 = FakeResp(200, {"data": []})
    with patch("connector_hapi.requests.get", side_effect=[page1, page2]):
        rows = ch.fetch_all("/x", {}, "id", page=2)
        assert len(rows) == 2


if __name__ == "__main__":
    test_get_app_identifier_uses_env_override()
    test_get_app_identifier_calls_official_endpoint()
    test_fetch_all_403_raises_runtimeerror_without_leaking_params()
    test_fetch_all_success_paginates()
    print("OK : tests connector_hapi")
