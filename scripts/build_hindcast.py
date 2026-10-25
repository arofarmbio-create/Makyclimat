"""Fiabilité mesurée du moteur de scénarios : validation croisée « une saison laissée de côté » sur toutes les saisons passées.

Pour chaque saison passée y et chaque point de départ (0 à 5 mois déjà observés) :
  - pluie finale prévue = pluie observée de y + pluie restante tirée des AUTRES saisons (jamais y) ;
  - on compare à la pluie finale réellement observée.
Mesures (sur un échantillon de points de grille couvrant le pays) :
  - erreur absolue moyenne (MAE) du scénario médian, en points de % de la normale, et gain (« skill ») par rapport à la
    simple climatologie (médiane des autres saisons sans tenir compte de ce qui est déjà tombé) ;
  - couverture de l'intervalle P10–P90 (attendu : 80 %) ;
  - score de Brier de la probabilité d'alerte (pluie finale < seuil « Alerte ») et gain par rapport à la climatologie ;
  - courbe de fiabilité (probabilité annoncée vs fréquence observée) ;
  - MAE selon la phase ENSO de la saison (El Niño, La Niña, neutre).
Sortie : docs/data/<pays>/hindcast.json (affiché dans l'onglet Méthode).
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np

from common import country_docs_dir, grid_dir, load_config, load_grid, write_json


def run(arr, clim, phases, years, alert_below, min_norm, max_points=3000, seed=0):
    """arr (Y,M,N) pluie mensuelle ; clim (M,N) normale mensuelle ; renvoie un dict de résultats."""
    Y, M, N = arr.shape
    norm = clim.sum(axis=0)
    valid = np.isfinite(norm) & (norm > min_norm) & np.isfinite(arr).all(axis=(0, 1))
    idx = np.where(valid)[0]
    if len(idx) > max_points:
        idx = np.random.default_rng(seed).choice(idx, max_points, replace=False)
    a = arr[:, :, idx].astype("float64")
    nrm = norm[idx]
    full = a.sum(axis=1)                                     # (Y,P) pluie de saison
    truth = full / nrm * 100.0
    out = {"n_seasons": int(Y), "n_points": int(len(idx)), "alert_below_pct": float(alert_below), "origins": []}
    ph = np.asarray(phases)
    for k in range(M):                                       # k mois déjà observés
        pred_med = np.full(truth.shape, np.nan)
        lo = np.full(truth.shape, np.nan)
        hi = np.full(truth.shape, np.nan)
        p_alert = np.full(truth.shape, np.nan)
        clim_med = np.full(truth.shape, np.nan)
        p_clim = np.full(truth.shape, np.nan)
        for y in range(Y):
            others = np.arange(Y) != y
            observed = a[y, :k].sum(axis=0)                  # (P,)
            ens = (observed[None, :] + a[others, k:].sum(axis=1)) / nrm[None, :] * 100.0   # (Y-1,P)
            pred_med[y] = np.median(ens, axis=0)
            lo[y], hi[y] = np.quantile(ens, [0.10, 0.90], axis=0)
            p_alert[y] = (ens < alert_below).mean(axis=0)
            base = truth[others]
            clim_med[y] = np.median(base, axis=0)
            p_clim[y] = (base < alert_below).mean(axis=0)
        ev = (truth < alert_below).astype(float)
        mae = float(np.mean(np.abs(pred_med - truth)))
        mae_c = float(np.mean(np.abs(clim_med - truth)))
        brier = float(np.mean((p_alert - ev) ** 2))
        brier_c = float(np.mean((p_clim - ev) ** 2))
        cover = float(np.mean((truth >= lo) & (truth <= hi)))
        bins = np.linspace(0, 1, 6)
        rel = []
        for b0, b1 in zip(bins[:-1], bins[1:]):
            m = (p_alert >= b0) & ((p_alert < b1) if b1 < 1 else (p_alert <= b1))
            if m.sum() >= 30:
                rel.append({"p": round(float(p_alert[m].mean()), 3), "freq": round(float(ev[m].mean()), 3), "n": int(m.sum())})
        by_phase = {}
        for code, name in (("E", "el"), ("L", "la"), ("N", "ne")):
            s = ph == code
            if s.sum() >= 3:
                by_phase[name] = {"n": int(s.sum()), "mae": round(float(np.mean(np.abs(pred_med[s] - truth[s]))), 2),
                                  "bias": round(float(np.mean(pred_med[s] - truth[s])), 2)}
        out["origins"].append({
            "months_observed": k, "mae": round(mae, 2), "mae_climatology": round(mae_c, 2),
            "skill": round(1 - mae / mae_c, 3) if mae_c > 0 else None,
            "coverage_p10_p90": round(cover, 3), "brier": round(brier, 4), "brier_climatology": round(brier_c, 4),
            "brier_skill": round(1 - brier / brier_c, 3) if brier_c > 0 else None,
            "event_rate": round(float(ev.mean()), 3), "reliability": rel, "by_phase": by_phase})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cfg = load_config(args.country)
    ms, cl = load_grid(grid_dir(args.country) / "monthly_series.npz"), load_grid(grid_dir(args.country) / "clim_monthly.npz")
    months = [int(m) for m in ms["months"]]
    arr = ms["arr"].astype("float32")
    Y, M, H, W = arr.shape
    clim = np.stack([cl["clim"][m - 1] for m in months])
    alert = next(r["below_pct"] for r in cfg["alert_levels"] if r["level"] == 3)
    res = run(arr.reshape(Y, M, H * W), clim.reshape(M, H * W), ms["phases"], ms["years"], alert, cfg["rainfall"]["min_normal_mm"])
    res.update({"first_season": int(ms["years"][0]), "last_season": int(ms["years"][-1]), "season_months": months,
                "computed": dt.date.today().isoformat(),
                "method": "validation croisée en laissant de côté chaque saison ; ensemble d'analogues des autres saisons"})
    write_json(country_docs_dir(args.country) / "hindcast.json", res)
    for o in res["origins"]:
        print(f"{o['months_observed']} mois observés : MAE {o['mae']} (climat {o['mae_climatology']}), couverture {o['coverage_p10_p90']}, Brier gain {o['brier_skill']}")


if __name__ == "__main__":
    main()
