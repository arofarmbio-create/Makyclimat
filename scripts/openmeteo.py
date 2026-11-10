"""Appels à l'API gratuite Open-Meteo (usage non commercial, sans clé) : prévision météo et débits de rivière (GloFAS).

Les coordonnées sont envoyées par lots. En cas d'erreur temporaire (429, 5xx), nouvel essai avec attente croissante.
https://open-meteo.com/en/docs   https://open-meteo.com/en/docs/flood-api
"""
from __future__ import annotations

import threading
import time

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
DAILY_VARS = ["precipitation_sum", "temperature_2m_max", "temperature_2m_min", "wind_gusts_10m_max", "wind_speed_10m_max",
              "et0_fao_evapotranspiration"]


def _appel(url: str, params: dict, timeout: float, avec_corps_400: bool):
    """Une requête complète (statut et corps). Renvoie (genre, valeur) au lieu de lever, pour passer d'un fil à l'autre."""
    try:
        r = requests.get(url, params=params, timeout=timeout)
        if r.status_code in (429, 500, 502, 503, 504):
            return "reessai", f"HTTP {r.status_code}"
        if r.status_code == 400:
            return "erreur400", f"HTTP 400 : {r.text[:200]}" if avec_corps_400 else "HTTP 400"
        r.raise_for_status()
        return "ok", r.json()
    except requests.RequestException as e:      # y compris JSON illisible (requests.JSONDecodeError)
        return "reessai", type(e).__name__
    except ValueError:
        return "reessai", "réponse JSON illisible"


def get_json(url: str, params: dict, retries: int = 5, pause: float = 1.0, deadline: float | None = None):
    """deadline (time.monotonic) : échéance stricte sur la durée totale, nouveaux essais et attentes compris.
    Sous échéance, chaque requête tourne dans un fil séparé que l'appelant abandonne à l'échéance : ni une réponse
    envoyée goutte à goutte, ni une lecture bloquée, ni un corps d'erreur lent ne peuvent la dépasser (le timeout de
    Requests ne borne que l'inactivité ; fermer la connexion depuis un autre fil peut attendre le verrou du lecteur :
    relectures Codex du 10/11/2026). Le fil abandonné finit seul à son délai d'inactivité (fil démon)."""
    last = None

    def reste() -> float:
        return float("inf") if deadline is None else deadline - time.monotonic()

    for attempt in range(retries):
        if reste() <= 0:
            raise RuntimeError(f"Open-Meteo : budget de temps épuisé ({last or 'avant la requête'})")
        if deadline is None:
            genre, valeur = _appel(url, params, 120.0, True)
        else:
            boite = []
            fil = threading.Thread(target=lambda: boite.append(_appel(url, params, max(0.1, min(120.0, reste())), False)),
                                   daemon=True)
            fil.start()
            fil.join(max(0.0, reste()))
            if not boite or reste() <= 0:
                raise RuntimeError("Open-Meteo : budget de temps épuisé pendant la requête (requête abandonnée)")
            genre, valeur = boite[0]
        if genre == "ok":
            return valeur
        if genre == "erreur400":
            raise ValueError(valeur)
        last = valeur
        if attempt + 1 == retries:
            break
        attente = pause * (2 ** attempt) + 2
        if attente >= reste():
            raise RuntimeError(f"Open-Meteo : budget de temps épuisé ({last})")
        print(f"  Open-Meteo {last} : nouvel essai dans {attente:.0f} s ({attempt + 1}/{retries})", flush=True)
        time.sleep(attente)
    raise RuntimeError(f"Open-Meteo : échec après {retries} essais ({last})")


def as_list(payload) -> list[dict]:
    """Une seule position = un objet, plusieurs = une liste."""
    return payload if isinstance(payload, list) else [payload]


def batches(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def cell_key(lon, lat, res):
    """Indice entier de la maille de prévision contenant un point (centres des mailles = multiples de res)."""
    import numpy as np
    return np.round(np.asarray(lon) / res).astype(int), np.round(np.asarray(lat) / res).astype(int)
