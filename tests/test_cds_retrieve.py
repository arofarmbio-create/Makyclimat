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

# Demandes orphelines : seules celles du même jeu, en attente depuis plus de 6 h, sont annulées
import datetime as dt  # noqa: E402

NOW = dt.datetime(2026, 11, 2, 12, tzinfo=dt.timezone.utc)


class Resp:
    def __init__(self, data=None):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class Sess:
    def __init__(self, jobs):
        self.jobs, self.deleted = jobs, []

    def get(self, url, params=None, headers=None, timeout=None):
        return Resp({"jobs": self.jobs})

    def delete(self, url, headers=None, timeout=None):
        self.deleted.append(url.rsplit("/", 1)[1])
        return Resp()


class Cli:
    url, key = "https://cds.example/api", "cle-de-test"


def job(i, ds, status, hours):
    return {"jobID": i, "processID": ds, "status": status, "created": (NOW - dt.timedelta(hours=hours)).isoformat()}


s = Sess([job("a", "era5", "accepted", 30), job("b", "era5", "accepted", 1), job("c", "era5", "running", 30),
          job("d", "autre", "accepted", 30)])
n = C.cds_cancel_stale(Cli(), "era5", session=s, now=NOW)
check("annule seulement la demande ancienne, en attente, du même jeu", n == 1 and s.deleted == ["a"])
check("client sans adresse ni clé : rien n'est tenté", C.cds_cancel_stale(object(), "era5", session=s, now=NOW) == 0)

# Ménage de la file (scripts/cds_menage.py) : seules les demandes en file depuis plus de 30 min, tous jeux confondus
import cds_menage as M  # noqa: E402

jobs = [job("a", "seasonal", "accepted", 5), job("b", "era5", "accepted", 0.2), job("c", "era5", "running", 9)]
st = M.stale_jobs(jobs, NOW, 30)
check("ménage : demande en file depuis 5 h annulée, récente et en cours épargnées", [j["jobID"] for j in st] == ["a"])
check("ménage : demande gardée (collecte reprenable des rafales) jamais annulée",
      M.stale_jobs(jobs, NOW, 30, garder={"a"}) == [])

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
