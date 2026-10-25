"""Appels à l'API gratuite Open-Meteo (usage non commercial, sans clé) : prévision météo et débits de rivière (GloFAS).

Les coordonnées sont envoyées par lots. En cas d'erreur temporaire (429, 5xx), nouvel essai avec attente croissante.
https://open-meteo.com/en/docs   https://open-meteo.com/en/docs/flood-api
"""
from __future__ import annotations

import time

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
DAILY_VARS = ["precipitation_sum", "temperature_2m_max", "temperature_2m_min", "wind_gusts_10m_max", "wind_speed_10m_max",
              "et0_fao_evapotranspiration"]


def get_json(url: str, params: dict, retries: int = 5, pause: float = 1.0):
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                time.sleep(pause * (2 ** attempt) + 2)
                continue
            if r.status_code == 400:
                raise ValueError(f"HTTP 400 : {r.text[:200]}")
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            last = str(e)
            time.sleep(pause * (2 ** attempt) + 2)
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
