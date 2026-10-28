"""Ruissellement prévu à 7 jours (indicateur EXPÉRIMENTAL d'inondation pluviale), par fokontany.

Cahier des charges §7.A (inondations pluviales et crues éclair), §9 (horizon 0-7 jours), §11 (les niveaux sont des
propositions, pas des alertes officielles). Méthode validée sur le périmètre pilote d'Antananarivo
(validation/crues_pluviales_validation.md : 3 inondations documentées sur 3, mais seulement 2 épisodes indépendants).
Pour chaque jour des 7 prochains jours : pluie sur 3 jours (prévision Open-Meteo de data/<pays>/grids/forecast.npz, qui
contient aussi les jours passés), ruissellement SCS-CN avec le CN du fokontany (infiltration urbaine faible mais non nulle,
CN ~92 en ville) ajusté selon la pluie des 5 jours précédents (règle NRCS), comparé aux seuils communs de SA RÉGION :
ruissellement de retour 2 ans (vigilance) et 5 ans (alerte), calculés sur les maxima saisonniers 2006-2020 (rx3_annual.npz).
Produit séparé des 5 aléas de l'alerte à 7 jours (early_warning.py), dont les seuils sont à valider avec les services :
il n'en modifie aucun niveau.
Limites : pluie prévue par un modèle météo (biais possible par rapport à CHIRPS, sur lequel les seuils sont calculés) ;
pas d'intensité horaire, ni de drainage, digues ou pompage ; validé sur un seul périmètre et 2 épisodes indépendants.
Sorties : data/<pays>/external/pluvial_forecast.csv (indicateurs lus par compute_metrics), docs/data/<pays>/pluvial_forecast.json.
Usage : python scripts/update_pluvial_forecast.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import country_data_dir, country_docs_dir, grid_dir, load_config, load_grid, read_units, write_json
from openmeteo import cell_key
from validate_pluvial import amc_cn, runoff_levels
import soilwater_core as C

HORIZON = 7
SOURCE = ("EXPÉRIMENTAL : ruissellement SCS-CN de la pluie prévue (Open-Meteo), seuils régionaux de retour 2 et 5 ans "
          "(CHIRPS 2006-2020) ; validé sur Antananarivo seulement (2 épisodes indépendants). Pas une alerte officielle.")


def forecast_rain(country, leaves, today, max_age_days):
    """Pluie journalière prévue par fokontany (N, T), dates, indice du jour ; None si la prévision est absente ou périmée."""
    path = grid_dir(country) / "forecast.npz"
    if not path.exists():
        return None
    z = load_grid(path)
    dates = [str(x) for x in z["dates"]]
    fetched = dt.datetime.fromisoformat(str(z["fetched_at"]))
    if (dt.datetime.now(dt.timezone.utc) - fetched).days > max_age_days and today == dt.date.today():
        return None
    if today.isoformat() not in dates:
        return None
    res = float(z["res"])
    kx, ky = cell_key(leaves.lon.to_numpy(), leaves.lat.to_numpy(), res)
    cell_of = {(int(round(a / res)), int(round(b / res))): i for i, (a, b) in enumerate(zip(z["lon"], z["lat"]))}
    idx = np.array([cell_of.get((int(a), int(b)), -1) for a, b in zip(kx, ky)])
    if (idx < 0).any():
        return None
    return np.asarray(z["precipitation_sum"][idx], dtype="float64"), dates, dates.index(today.isoformat()), str(z["fetched_at"])


def compute(P: np.ndarray, t0: int, cn2: np.ndarray, q2: np.ndarray, q5: np.ndarray, horizon=HORIZON):
    """P (N, T) pluie journalière ; jours t0..t0+horizon-1 -> ruissellement max (mm), rapport max au seuil 2 ans,
    niveau (0 aucun, 1 vigilance >= retour 2 ans, 2 alerte >= retour 5 ans), jour du maximum (indice)."""
    N, T = P.shape
    Pz = np.nan_to_num(P, nan=0.0)
    best_q, best_r, best_t = np.zeros(N), np.zeros(N), np.full(N, -1)
    for t in range(t0, min(t0 + horizon, T)):
        if t < 7:
            continue                                                   # pas assez de jours passés pour l'humidité antérieure
        p3 = Pz[:, t] + Pz[:, t - 1] + Pz[:, t - 2]
        p5 = Pz[:, t - 7:t - 2].sum(axis=1)
        q = C.scs_runoff(p3, amc_cn(cn2, p5[None, :])[0])
        r = q / q2
        better = r > best_r
        best_q, best_r, best_t = np.where(better, q, best_q), np.where(better, r, best_r), np.where(better, t, best_t)
    level = np.where(best_q >= q5, 2, np.where(best_q >= q2, 1, 0))
    return best_q, best_r, level, best_t


def main(country="mdg", today=None, rx3=None, cn2=None):
    cfg = load_config(country)
    today = today or dt.date.today()
    units = read_units(country)
    leaves = units[units.level == 4].reset_index(drop=True)
    out_json = country_docs_dir(country) / "pluvial_forecast.json"
    fr = forecast_rain(country, leaves, today, cfg.get("forecast", {}).get("max_age_days", 3))
    if fr is None:
        write_json(out_json, {"available": False, "generated": today.isoformat(), "note": "prévision absente ou périmée"})
        print("Ruissellement prévu : prévision absente ou périmée, rien calculé")
        return None
    P, dates, t0, fetched = fr
    if rx3 is None:
        z = np.load(grid_dir(country) / "rx3_annual.npz", allow_pickle=True)
        if list(z["codes"]) != list(leaves.pcode):
            raise SystemExit("rx3_annual.npz ne correspond pas aux fokontany actuels : relancer build_rx3_clim.py")
        rx3 = z["rx3"]
    if cn2 is None:
        sw = pd.read_csv(country_data_dir(country) / "external" / "soilwater.csv", dtype={"pcode": str})
        cn2 = leaves.pcode.map(sw[sw.indicateur == "cn2"].set_index("pcode").valeur).to_numpy(dtype="float64")
    cn2 = np.asarray(cn2, dtype="float64")
    cn2 = np.where(np.isfinite(cn2), cn2, np.nanmedian(cn2))
    q2, q5, thr = np.full(len(leaves), np.nan), np.full(len(leaves), np.nan), {}
    for reg, ix in leaves.groupby("adm1").indices.items():            # seuils communs par région (cf. périmètre pilote)
        a, b = runoff_levels(rx3[:, ix], cn2[ix])
        q2[ix], q5[ix], thr[reg] = a, b, {"q2_mm": round(a, 1), "q5_mm": round(b, 1)}
    q, r, lvl, tmax = compute(P, t0, cn2, q2, q5)
    rows = []
    date = today.isoformat()
    for i, pc in enumerate(leaves.pcode):
        rows += [(pc, "ruiss_prevu_mm", round(float(q[i]), 1), date), (pc, "ruiss_prevu_niveau", int(lvl[i]), date)]
    for key in ("adm1", "adm2", "adm3"):
        for pc, ix in leaves.groupby(key).indices.items():
            if pc:
                rows += [(pc, "ruiss_prevu_niveau", int(lvl[ix].max()), date),
                         (pc, "ruiss_prevu_part_pct", round(100.0 * float(np.mean(lvl[ix] >= 1)), 1), date)]
    ext = pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur", "date"]).assign(source=SOURCE)
    ed = country_data_dir(country) / "external"
    ed.mkdir(parents=True, exist_ok=True)
    ext.to_csv(ed / "pluvial_forecast.csv", index=False)
    names = dict(zip(units.pcode, units.name))
    reg = [{"adm1": pc, "nom": names.get(pc, pc), "niveau_max": int(lvl[ix].max()),
            "part_fokontany_vigilance_pct": round(100.0 * float(np.mean(lvl[ix] >= 1)), 1), **thr[pc]}
           for pc, ix in leaves.groupby("adm1").indices.items()]
    write_json(out_json, {"available": True, "experimental": True, "generated": date, "forecast_fetched_at": fetched,
                          "days": dates[t0:t0 + HORIZON], "regions": reg,
                          "method": "Ruissellement SCS-CN de la pluie prévue sur 3 jours ; CN du fokontany ajusté selon les 5 jours précédents ; "
                                    "seuils régionaux de retour 2 ans (vigilance) et 5 ans (alerte).",
                          "validation": "Périmètre d'Antananarivo seulement : 3 inondations documentées sur 3 détectées, mais 2 épisodes indépendants. "
                                        "Voir validation/crues_pluviales_validation.md.",
                          "warning": "Indicateur expérimental, pas une alerte officielle : les alertes de Météo Madagascar et du BNGRC priment."})
    n1, n2 = int((lvl >= 1).sum()), int((lvl >= 2).sum())
    print(f"Ruissellement prévu ({dates[t0]} + {HORIZON} j) : {n1} fokontany en vigilance ou plus, dont {n2} en alerte (expérimental)")
    return {"q": q, "ratio": r, "level": lvl, "day": tmax, "regions": reg}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    main(ap.parse_args().country)
