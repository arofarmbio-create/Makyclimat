"""Alerte précoce zonale : niveaux d'alerte à partir des prévisions des prochains jours.

Niveaux : 0 aucune, 1 vigilance, 2 alerte, 3 alerte maximale. Seuils dans config/countries/<pays>.yml (section alerts) :
PROVISOIRES, à calibrer avec Météo Madagascar et le BNGRC. Les alertes officielles priment toujours.
Aléas : pluie forte, vent fort, chaleur, période sèche prolongée.
"""
from __future__ import annotations

import numpy as np

HAZARDS = ["rain", "wind", "heat", "dry", "flood"]
HAZARD_LABEL = {"rain": "Pluies fortes", "wind": "Vent fort", "heat": "Forte chaleur", "dry": "Période sèche prolongée",
                "flood": "Crue de rivière"}
LEVEL_NAME = ["Aucune alerte", "Vigilance", "Alerte", "Alerte maximale"]


def level_from_thresholds(x, thr):
    """x (N,) ; thr = [seuil1, seuil2, seuil3] croissants -> niveau 0 à 3 (NaN -> 0)."""
    x = np.asarray(x, dtype=float)
    lv = np.zeros(x.shape, dtype=int)
    for k, t in enumerate(thr, start=1):
        lv[np.isfinite(x) & (x >= t)] = k
    return lv


def longest_dry_run(precip, dry_mm=1.0):
    """Plus longue suite de jours consécutifs sous dry_mm. precip (N,T) -> (N,)."""
    dry = np.asarray(precip) < dry_mm
    best = np.zeros(dry.shape[0], dtype=int)
    cur = np.zeros(dry.shape[0], dtype=int)
    for t in range(dry.shape[1]):
        cur = np.where(dry[:, t], cur + 1, 0)
        best = np.maximum(best, cur)
    return best


def compute(precip, tmax, gust, cfg_alerts, in_rain_season: bool, horizon: int = 7):
    """Niveaux d'alerte par aléa sur les `horizon` premiers jours de prévision.

    precip, tmax, gust : tableaux (N, T) des jours de prévision (à partir d'aujourd'hui).
    Retourne dict aléa -> niveaux (N,), et indicateurs chiffrés (pluie max/jour, cumul, tmax max, rafale max, jours secs)."""
    p, tx, g = precip[:, :horizon], tmax[:, :horizon], gust[:, :horizon]
    with np.errstate(invalid="ignore"):
        rain_max = np.nanmax(p, axis=1)
        rain_3d = np.nanmax(np.stack([np.nansum(p[:, i:i + 3], axis=1) for i in range(max(1, p.shape[1] - 2))]), axis=0)
        tmax_max = np.nanmax(tx, axis=1)
        gust_max = np.nanmax(g, axis=1)
    dry_run = longest_dry_run(precip)   # sur toute la prévision (jusqu'à 16 jours)
    rain_lv = np.maximum(level_from_thresholds(rain_max, cfg_alerts["rain_day_mm"]),
                         level_from_thresholds(rain_3d, cfg_alerts["rain_3day_mm"]))
    out = {
        "rain": rain_lv,
        "wind": level_from_thresholds(gust_max, cfg_alerts["gust_kmh"]),
        "heat": level_from_thresholds(tmax_max, cfg_alerts["tmax_c"]),
        "dry": level_from_thresholds(dry_run, cfg_alerts["dry_days"]) if in_rain_season else np.zeros(len(dry_run), dtype=int),
    }
    nums = {"rain_max": rain_max, "rain_3d": rain_3d, "tmax_max": tmax_max, "gust_max": gust_max, "dry_run": dry_run}
    return out, nums
