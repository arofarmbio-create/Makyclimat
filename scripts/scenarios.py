"""Scénarios de fin de saison des pluies : combien de personnes pourraient être touchées, où, avec quelle probabilité.

Méthode (ensemble d'analogues, sans modèle de prévision externe) :
  pluie finale d'une saison = pluie déjà tombée (observée) + pluie restante prise dans chacune des ~43 saisons passées (CHIRPS).
  On obtient ~43 saisons « possibles » par zone, comparées à la normale de la saison complète.
  Scénarios : sec (1 saison sur 10), médiane, humide (1 sur 10), type El Niño (médiane des saisons El Niño passées),
  type La Niña, et « prévision » si une prévision saisonnière officielle est fournie (pondération des années par tercile).
La probabilité d'alerte est la part des saisons analogues qui atteignent le niveau d'alerte.
Ces scénarios décrivent ce qui est arrivé dans le passé dans des situations comparables ; ce n'est pas une prévision météo.
"""
from __future__ import annotations

import calendar
import datetime as dt

import numpy as np

import enso


def target_season(today: dt.date, s_m: int, e_m: int) -> tuple[int, int]:
    """(année de début, année de fin) de la saison en cours ou, hors saison, de la prochaine saison."""
    if s_m > e_m:
        if today.month >= s_m:
            y0 = today.year
        elif today.month <= e_m:
            y0 = today.year - 1
        else:
            y0 = today.year
        return y0, y0 + 1
    return today.year, today.year


def covered_fractions(months: list[tuple[int, int]], season_start: str, through: dt.date | None, start_ym: tuple[int, int]):
    """Part observée de chaque mois de la saison cible (0 si les données ne couvrent pas cette saison)."""
    if through is None or season_start != f"{start_ym[0]}-{start_ym[1]:02d}":
        return [0.0] * len(months)
    out = []
    for y, m in months:
        if (y, m) < (through.year, through.month):
            out.append(1.0)
        elif (y, m) == (through.year, through.month):
            out.append(min(1.0, through.day / calendar.monthrange(y, m)[1]))
        else:
            out.append(0.0)
    return out


def final_pct(act, clim_m, series, covered, min_norm):
    """Pluie finale analogue en % de la normale complète. act (N), clim_m (M,N), series (Y,M,N) -> (Y,N)."""
    rem = 1.0 - np.asarray(covered)[None, :, None]
    total = np.nan_to_num(act)[None, :] + np.nansum(series * rem, axis=1)
    bad = np.isnan(series).all(axis=1)
    norm = np.nansum(clim_m, axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        pct = np.where(norm[None, :] > min_norm, total / norm[None, :] * 100.0, np.nan)
    pct[bad] = np.nan
    return pct, norm


def weighted_quantile(values, weights, q):
    """Quantile pondéré d'un vecteur (valeurs NaN ignorées)."""
    m = np.isfinite(values) & (weights > 0)
    if not m.any():
        return np.nan
    v, w = values[m], weights[m]
    o = np.argsort(v)
    v, w = v[o], w[o]
    c = (np.cumsum(w) - 0.5 * w) / w.sum()
    return float(np.interp(q, c, v))


def tercile_weights(pct, probs):
    """Poids par saison pour une zone : p(tercile) / nombre d'années du tercile. pct (Y,), probs = (p_sec, p_norm, p_hum)."""
    ok = np.isfinite(pct)
    w = np.zeros(len(pct))
    if ok.sum() < 9:
        return np.where(ok, 1.0, 0.0)
    lo, hi = np.nanquantile(pct[ok], [1 / 3, 2 / 3])
    cls = np.where(pct <= lo, 0, np.where(pct <= hi, 1, 2))
    for k in range(3):
        sel = ok & (cls == k)
        if sel.any():
            w[sel] = probs[k] / sel.sum()
    return w


def scenario_values(pct, phases, forecast_probs=None):
    """Retourne dict id -> (N,) pourcentages de fin de saison, plus nombre d'années par phase."""
    out = {
        "sec": np.nanquantile(pct, 0.10, axis=0),
        "med": np.nanquantile(pct, 0.50, axis=0),
        "hum": np.nanquantile(pct, 0.90, axis=0),
    }
    n = {}
    for code, sid in (("E", "el"), ("L", "la")):
        sel = np.asarray(phases) == code
        n[sid] = int(sel.sum())
        out[sid] = np.nanmedian(pct[sel], axis=0) if sel.sum() >= 3 else np.full(pct.shape[1], np.nan)
    if forecast_probs is not None:  # (N,3) probabilités par zone
        res = np.full(pct.shape[1], np.nan)
        for j in range(pct.shape[1]):
            w = tercile_weights(pct[:, j], forecast_probs[j])
            res[j] = weighted_quantile(pct[:, j], w, 0.5)
        out["prev"] = res
    return out, n


def level_array(pct, levels):
    """Version vectorisée de level_from_pct : 0 = pas de donnée, sinon niveau du premier seuil franchi (sévère -> léger)."""
    pct = np.asarray(pct, dtype=float)
    out = np.zeros(pct.shape, dtype=int)
    done = ~np.isfinite(pct)
    for rule in sorted(levels, key=lambda r: -r["level"]):
        hit = (~done) & (pct < rule["below_pct"])
        out[hit] = rule["level"]
        done |= hit
    return out


def rollup_sum(units, leafmask, arr):
    """Somme des valeurs des fokontany vers communes, districts et régions (niveaux 3, 2, 1)."""
    import pandas as pd
    out = np.array(arr, dtype=float).copy()
    leaf = np.asarray(leafmask)
    for lv, key in ((3, "adm3"), (2, "adm2"), (1, "adm1")):
        s = pd.Series(out[leaf]).groupby(units.loc[leaf, key].values).sum()
        m = (units.level == lv).values
        out[m] = units.loc[m, "pcode"].map(s).fillna(0).values
    return out
