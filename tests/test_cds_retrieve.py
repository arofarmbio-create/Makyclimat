"""Requêtes Copernicus : attente quand la file du compte est pleine (scripts/common.py, cds_retrieve)."""
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import common as C  # noqa: E402

FAILS = 0
FULL = '{"traceback":"Maximum number queued requests for this dataset has been reached."}'


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


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


def error_of(client, **kw):
    try:
        C.cds_retrieve(client, "jeu", {}, "f", pause=0, **kw)
    except RuntimeError as e:
        return str(e)
    return None


c = Client([FULL, FULL])
check("file pleine deux fois puis réussite : trois essais, pas d'erreur", error_of(c) is None and c.calls == 3)
c = Client([FULL] * 10)
e = error_of(c, waits=2)
check("file toujours pleine : abandon après les essais prévus, message du serveur conservé",
      e is not None and "queued requests" in e and c.calls == 3)
c = Client(['{"title":"licence non acceptée"}'])
e = error_of(c)
check("autre refus : erreur immédiate, sans attente", e is not None and "licence" in e and c.calls == 1)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
