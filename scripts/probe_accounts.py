"""Vérifie que les comptes NASA Earthdata et Copernicus (CDS, EWDS) fonctionnent, sans jamais afficher les secrets.

Cahier des charges §4 (accès aux données documenté), §14 (services soumis à inscription). Lit EARTHDATA_USER,
EARTHDATA_PASSWORD et CDS_API_KEY dans l'environnement (secrets GitHub). Pour chaque service : une petite requête réelle,
puis « OK » ou « ÉCHEC » avec la cause probable.
Usage : python scripts/probe_accounts.py
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import requests

IMERG_DIR = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDL.07/2026/09/"


class EarthdataSession(requests.Session):
    """Garde l'authentification lors de la redirection vers urs.earthdata.nasa.gov (et seulement là)."""

    def rebuild_auth(self, prepared_request, response):
        host = requests.utils.urlparse(prepared_request.url).hostname
        if "Authorization" in prepared_request.headers and host not in ("urs.earthdata.nasa.gov",) \
                and requests.utils.urlparse(response.request.url).hostname != host:
            del prepared_request.headers["Authorization"]


def earthdata() -> str:
    user, pw = os.environ.get("EARTHDATA_USER"), os.environ.get("EARTHDATA_PASSWORD")
    if not user or not pw:
        return "ÉCHEC : secrets EARTHDATA_USER / EARTHDATA_PASSWORD absents"
    listing = requests.get(IMERG_DIR, timeout=120).text
    files = sorted(set(re.findall(r'href="(3B-DAY-L[^"]+\.nc4)"', listing)))
    if not files:
        return "ÉCHEC : liste des fichiers IMERG introuvable (structure du serveur changée ?)"
    s = EarthdataSession()
    s.auth = (user, pw)
    r = s.get(IMERG_DIR + files[0], timeout=300, stream=True)
    head = next(r.iter_content(4096), b"")
    if r.status_code == 200 and (head[:4] == b"\x89HDF" or head[:3] == b"CDF"):
        return f"OK : fichier IMERG journalier lu ({files[0]})"
    if r.status_code == 401:
        return "ÉCHEC : identifiant ou mot de passe refusé (HTTP 401)"
    if r.status_code == 403 or b"approve" in head.lower() or b"authorize" in head.lower():
        return "ÉCHEC : application « NASA GESDISC DATA ARCHIVE » non approuvée dans le profil Earthdata (HTTP %d)" % r.status_code
    return f"ÉCHEC : réponse inattendue (HTTP {r.status_code})"


def copernicus(url: str, dataset: str, request: dict) -> str:
    key = os.environ.get("CDS_API_KEY")
    if not key:
        return "ÉCHEC : secret CDS_API_KEY absent"
    try:
        import cdsapi
    except ImportError:
        return "ÉCHEC : bibliothèque cdsapi non installée"
    out = Path(tempfile.mkdtemp()) / "test.grib"
    try:
        cdsapi.Client(url=url, key=key, quiet=True, progress=False, timeout=600).retrieve(dataset, request, str(out))
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "licen" in msg.lower() or "terms" in msg.lower():
            return "ÉCHEC : licence du jeu de données non acceptée (page du jeu de données, « Terms of use » -> Accept)"
        if "401" in msg or "authentication" in msg.lower() or "token" in msg.lower():
            return "ÉCHEC : clé API refusée"
        return f"ÉCHEC : {type(e).__name__} : {msg[:200]}"
    return f"OK : {dataset} téléchargé ({out.stat().st_size} octets)"


def main() -> None:
    print("NASA Earthdata (GPM IMERG) :", earthdata(), flush=True)
    print("Copernicus CDS (prévision saisonnière) :", copernicus(
        "https://cds.climate.copernicus.eu/api", "seasonal-monthly-single-levels",
        {"originating_centre": "ecmwf", "system": "51", "variable": ["total_precipitation"], "product_type": ["monthly_mean"],
         "year": ["2016"], "month": ["10"], "leadtime_month": ["1"], "area": [-12, 44, -13, 45], "data_format": "grib"}), flush=True)
    print("Copernicus EWDS (prévision de crue GloFAS) :", copernicus(
        "https://ewds.climate.copernicus.eu/api", "cems-glofas-forecast",
        {"system_version": ["operational"], "hydrological_model": ["lisflood"], "product_type": ["control_forecast"],
         "variable": "river_discharge_in_the_last_24_hours", "year": ["2026"], "month": ["10"], "day": ["01"],
         "leadtime_hour": ["24"], "area": [-18.8, 47.4, -19.0, 47.6], "data_format": "grib2", "download_format": "unarchived"}), flush=True)


if __name__ == "__main__":
    main()
