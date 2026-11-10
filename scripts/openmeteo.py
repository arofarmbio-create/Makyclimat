"""Appels à l'API gratuite Open-Meteo (usage non commercial, sans clé) : prévision météo et débits de rivière (GloFAS).

Les coordonnées sont envoyées par lots. En cas d'erreur temporaire (429, 5xx), nouvel essai avec attente croissante.
https://open-meteo.com/en/docs   https://open-meteo.com/en/docs/flood-api
"""
from __future__ import annotations

import json
import threading
import time

import requests

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood"
DAILY_VARS = ["precipitation_sum", "temperature_2m_max", "temperature_2m_min", "wind_gusts_10m_max", "wind_speed_10m_max",
              "et0_fao_evapotranspiration"]


def get_json(url: str, params: dict, retries: int = 5, pause: float = 1.0, deadline: float | None = None):
    """deadline (time.monotonic) : échéance stricte sur la durée totale. Délais de connexion et de lecture, attentes et
    réception bornés au temps restant ; la réponse est lue par morceaux et abandonnée si l'échéance passe pendant la
    réception (le timeout de Requests ne borne que l'inactivité, pas la durée totale : relectures Codex du 10/11/2026)."""
    last = None

    def reste() -> float:
        return float("inf") if deadline is None else deadline - time.monotonic()

    for attempt in range(retries):
        if reste() <= 0:
            raise RuntimeError(f"Open-Meteo : budget de temps épuisé ({last or 'avant la requête'})")
        try:
            # Connexion et attente du début de réponse se partagent le temps restant (chacune au plus la moitié).
            delai = 120.0 if deadline is None else (max(0.05, min(30.0, reste() / 2)), max(0.05, min(120.0, reste() / 2)))
            with requests.get(url, params=params, timeout=delai, stream=deadline is not None) as r:
                if r.status_code in (429, 500, 502, 503, 504):
                    last = f"HTTP {r.status_code}"
                elif r.status_code == 400:
                    raise ValueError(f"HTTP 400 : {r.text[:200]}")
                else:
                    r.raise_for_status()
                    if deadline is None:
                        return r.json()
                    morceaux = []
                    garde = threading.Timer(max(0.0, reste()), r.close)   # ferme la connexion à l'échéance, même en pleine attente
                    garde.daemon = True
                    garde.start()
                    try:
                        for morceau in r.iter_content(chunk_size=1 << 16):
                            if reste() <= 0:
                                break
                            morceaux.append(morceau)
                    except Exception:                  # lecture interrompue par la garde ou par le réseau
                        if reste() > 0:
                            raise
                    finally:
                        garde.cancel()
                    if reste() <= 0:
                        raise RuntimeError("Open-Meteo : budget de temps épuisé pendant la réception de la réponse")
                    try:
                        return json.loads(b"".join(morceaux))
                    except ValueError:
                        last = "réponse JSON illisible"
        except requests.RequestException as e:
            last = f"{type(e).__name__}"
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
