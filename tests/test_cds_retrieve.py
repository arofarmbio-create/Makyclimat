"""Requêtes Copernicus : attente quand la file du compte est pleine (scripts/common.py, cds_retrieve)."""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import common as C  # noqa: E402


class Rep:
    def __init__(self, text):
        self.text = text


class Client:
    def __init__(self, errors):
        self.errors, self.calls = list(errors), 0

    def retrieve(self, dataset, request, target):
        self.calls += 1
        if self.errors:
            raise requests.HTTPError("400", response=Rep(self.errors.pop(0)))


FULL = '{"traceback":"Maximum number queued requests for this dataset has been reached."}'


def test_file_pleine_puis_succes():
    c = Client([FULL, FULL])
    C.cds_retrieve(c, "jeu", {}, "f", pause=0)
    assert c.calls == 3


def test_file_toujours_pleine_echoue_avec_message():
    c = Client([FULL] * 10)
    with pytest.raises(RuntimeError, match="queued requests"):
        C.cds_retrieve(c, "jeu", {}, "f", waits=2, pause=0)
    assert c.calls == 3


def test_autre_refus_immediat():
    c = Client(['{"title":"licence non acceptée"}'])
    with pytest.raises(RuntimeError, match="licence"):
        C.cds_retrieve(c, "jeu", {}, "f", pause=0)
    assert c.calls == 1
