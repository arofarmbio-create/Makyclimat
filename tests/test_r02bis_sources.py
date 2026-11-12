"""R-02 bis : fenêtres des cyclones et emprises IMERG (scripts/build_r02bis_sources.py)."""
import datetime as dt
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_r02bis_sources as R  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


land_lon, land_lat = np.array([47.0]), np.array([-19.0])
pts = [[60.0, -19.0, 30], [53.0, -19.0, 60], [50.0, -19.0, 90], [47.5, -19.0, 70], [44.0, -19.0, 40], [38.0, -19.0, 30]]
w = R.window(pts, dt.date(2022, 2, 1), land_lon, land_lat)
# positions toutes les 6 h : à moins de 500 km aux indices 2, 3, 4 (12 h à 24 h après le début)
check("fenêtre : 1 jour avant le premier passage à moins de 500 km, 2 jours après le dernier",
      w == (dt.date(2022, 1, 31), dt.date(2022, 2, 4)))
check("aucun passage à moins de 500 km : pas de fenêtre", R.window([[70.0, -19.0, 30]], dt.date(2022, 2, 1), land_lon, land_lat) is None)
check("distance : 1° de latitude vaut environ 111 km", abs(R.haversine_km(47, -19, 47, -20) - 111.2) < 0.5)
b = R.imerg_box(43.05, 43.25, -25.95, -25.75)
check("emprise IMERG : indices de la grille 0,1°", b == (2230, 2232, 640, 642))

# Collecte reprenable des rafales (12/11/2026, EMSR564 resté en file au-delà de 5 h 40) : fausse API Copernicus
import json  # noqa: E402
import tempfile  # noqa: E402


class Rep:
    def __init__(self, code=200, data=None):
        self.status_code, self.data, self.text = code, data or {}, json.dumps(data or {})

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return self.data


class FausseAPI:
    """Chaque demande suit une liste d'états, un par consultation ; la dernière valeur se répète."""
    def __init__(self, etats=None):
        self.etats, self.soumises = dict(etats or {}), []

    def post(self, url, json=None, headers=None, timeout=None):
        job = f"j{len(self.soumises) + 1}"
        self.soumises.append((url.split("/processes/")[1], json["inputs"]))
        self.etats.setdefault(job, ["accepted"])
        return Rep(201, {"jobID": job})

    def get(self, url, headers=None, timeout=None):
        job, _, suite = url.split("/jobs/")[1].partition("/")
        if job not in self.etats:
            return Rep(404)
        if suite == "results":
            return Rep(200, {"asset": {"value": {"href": f"https://resultat/{job}.nc"}}})
        e = self.etats[job]
        return Rep(200, {"status": e.pop(0) if len(e) > 1 else e[0]})


class Horloge:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def dormir(self, s):
        self.t += s


def collecte(api, fichier, requete, delai=600):
    h, publies = Horloge(), []
    href = R.demande_reprenable(api, {}, "era5", requete, fichier, delai, publier=publies.append, horloge=h,
                                dormir=h.dormir)
    return href, publies


REQ = {"day": ["01"]}
with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "rafales_X.demande.json"
    api = FausseAPI()
    href, publies = collecte(api, f, REQ)
    check("demande encore en file à l'échéance : rien rendu, demande notée et publiée dès la soumission",
          href is None and publies == [f] and json.loads(f.read_text(encoding="utf-8"))["jobID"] == "j1")
    api.etats["j1"] = ["running", "successful"]
    href, publies = collecte(api, f, REQ)
    check("lancement suivant : la même demande est reprise, aucune nouvelle soumission",
          href == "https://resultat/j1.nc" and len(api.soumises) == 1 and publies == [])
    api.etats["j1"] = ["dismissed"]
    api.etats["j2"] = ["successful"]
    href, _ = collecte(api, f, REQ)
    check("demande notée annulée chez Copernicus : nouvelle soumission",
          href == "https://resultat/j2.nc" and len(api.soumises) == 2)
    collecte(api, f, {"day": ["02"]})
    check("requête différente (fenêtre changée) : la note n'est pas réutilisée", len(api.soumises) == 3)
    f.unlink()
    api = FausseAPI({"j1": ["accepted", "failed"]})
    try:
        collecte(api, f, REQ)
        ok = False
    except RuntimeError as e:
        ok = "failed" in str(e)
    check("échec pendant le suivi : erreur visible (la note sera écartée au lancement suivant)", ok)

# Run 43216795187 (12/11/2026) : coupure réseau pendant le suivi d'EMSR565 ; elle est réessayée, pas fatale
class APICoupee(FausseAPI):
    def __init__(self, coupures, etats=None):
        super().__init__(etats)
        self.coupures = coupures

    def get(self, url, headers=None, timeout=None):
        if self.coupures and "/results" not in url:
            self.coupures -= 1
            raise ConnectionError("Remote end closed connection without response")
        return super().get(url, headers, timeout)


with tempfile.TemporaryDirectory() as d:
    f = Path(d) / "rafales_X.demande.json"
    api = APICoupee(2, {"j1": ["running", "successful"]})
    href, _ = collecte(api, f, REQ)
    check("coupures réseau isolées pendant le suivi : réessayées, résultat obtenu",
          href == "https://resultat/j1.nc" and len(api.soumises) == 1)
    f.unlink()
    api = APICoupee(99, {"j1": ["accepted"]})
    try:
        collecte(api, f, REQ)
        ok = False
    except ConnectionError:
        ok = True
    check("coupure durable : erreur après 5 essais", ok and api.coupures == 99 - 5)
check("requête ERA5 : un jour par date de la fenêtre, 24 heures",
      R.requete_rafales(type("W", (), {"debut": dt.date(2022, 1, 31), "fin": dt.date(2022, 2, 2)})())["day"]
      == ["01", "02", "31"])

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
