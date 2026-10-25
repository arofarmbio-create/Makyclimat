"""Prévision saisonnière de pluie : ECMWF SEAS5 (EC46 pour les 46 premiers jours) via l'API saisonnière d'Open-Meteo.

Source : Open-Meteo Seasonal Forecast API (données ECMWF, licence CC-BY 4.0 pour l'utilisation non commerciale). Variables mensuelles :
precipitation_mean (cumul mensuel prévu, moyenne d'ensemble) et precipitation_anomaly (écart à la climatologie du MODÈLE, en mm).

Méthode (documentée pour la thèse) :
  1. écart relatif d'un mois = anomalie / (prévu - anomalie), c'est-à-dire par rapport à la normale du modèle (pas à celle de CHIRPS, pour éviter le biais du modèle) ;
     écart relatif de la saison de pluie (novembre-avril, mois couverts par la prévision) r = somme des anomalies / somme des normales du modèle ;
  2. pluie attendue = normale CHIRPS du district x (1 + r) : correction « delta » multiplicative, usuelle pour la pluie ;
  3. probabilités des trois classes (sec / normal / humide, terciles de la climatologie CHIRPS 1982-aujourd'hui) avec une loi normale centrée sur la pluie attendue
     et d'écart-type égal à celui de la climatologie : p_sec = Phi((T1 - attendu)/sigma), p_humide = 1 - Phi((T2 - attendu)/sigma), T1,2 = moyenne -/+ 0,43 sigma ;
  4. garde-fou : chaque probabilité est bornée à [0,15 ; 0,50], la somme restant égale à 1 (mise à l'échelle par bissection). La moyenne d'ensemble n'est pas calibrée sur la compétence réelle du modèle
     à cet endroit (modérée à Madagascar, surtout liée à El Niño dans le Sud) : une prévision saisonnière ne doit jamais afficher une certitude.
Les régions reçoivent la moyenne des districts pondérée par la surface. Les communes et fokontany reprennent la valeur de leur district.

Sorties :
  data/<pays>/seasonal_auto.csv           pcode, p_sec, p_normal, p_humide, source, date : lu par compute_metrics (scénario « prévision saisonnière ») si
                                          inputs/prevision_saisonniere.csv (prévision officielle fournie à la main) n'existe pas
  data/<pays>/external/seasonal.csv       indicateurs seas_anom_pct, seas_p_sec_pct, seas_p_humide_pct (district, région)
  docs/data/<pays>/seasonal.json          mois, anomalies, probabilités par zone (affichées dans la fiche de la zone)
Usage : python scripts/connector_seasonal.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import time

import numpy as np
import pandas as pd
import requests

from common import country_data_dir, country_docs_dir, grid_dir, load_grid, read_units, sample_grid, write_json

API = "https://seasonal-api.open-meteo.com/v1/seasonal"
SEASON_MONTHS = (11, 12, 1, 2, 3, 4)
SOURCE = "ECMWF SEAS5 / EC46 via Open-Meteo (CC-BY 4.0) ; probabilités MakyClimat (correction delta, terciles CHIRPS) bornées à 15-50 %"
Z_TERCILE = 0.4307   # quantile 2/3 de la loi normale centrée réduite
P_MIN, P_MAX = 0.15, 0.50


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def fetch(lats: list[float], lons: list[float], batch: int = 20) -> list[dict]:
    out = []
    for i in range(0, len(lats), batch):
        la, lo = lats[i:i + batch], lons[i:i + batch]
        for attempt in range(4):
            r = requests.get(API, params={"latitude": ",".join(f"{v:.4f}" for v in la), "longitude": ",".join(f"{v:.4f}" for v in lo),
                                          "monthly": "precipitation_mean,precipitation_anomaly", "timezone": "UTC"},
                             timeout=120, headers={"User-Agent": "MakyClimat (recherche doctorale)"})
            if r.status_code == 200:
                j = r.json()
                out.extend(j if isinstance(j, list) else [j])
                break
            time.sleep(20 * (attempt + 1))
        else:
            raise RuntimeError(f"Open-Meteo saisonnier : HTTP {r.status_code} {r.text[:200]}")
        time.sleep(1.0)
    return out


def season_anomaly(months: list[str], mean: list, anom: list):
    """(écart relatif de la saison, mois retenus, liste des (mois, anomalie mm, écart relatif)) sur les mois novembre-avril couverts."""
    rows = []
    for m, a, v in zip(months, anom, mean):
        if a is None or v is None:
            continue
        mo = int(m[5:7])
        norm = v - a
        rows.append((m[:7], mo, float(a), float(norm)))
    sel = [r for r in rows if r[1] in SEASON_MONTHS]
    if len(sel) < 2 or sum(r[3] for r in sel) <= 0:
        return None, [], rows
    r = sum(x[2] for x in sel) / sum(x[3] for x in sel)
    return r, [x[1] for x in sel], rows


def tercile_probs(r: float, mu: float, sigma: float):
    """(p_sec, p_normal, p_humide) pour une pluie attendue mu(1+r) et une climatologie normale (mu, sigma) ; bornées à [P_MIN, P_MAX]."""
    if not (mu > 0 and sigma > 0):
        return None
    exp = mu * (1.0 + r)
    t1, t2 = mu - Z_TERCILE * sigma, mu + Z_TERCILE * sigma
    ps = phi((t1 - exp) / sigma)
    ph = 1.0 - phi((t2 - exp) / sigma)
    raw = np.array([ps, max(0.0, 1.0 - ps - ph), ph]) + 1e-9
    lo, hi = 1e-12, 1e12       # facteur d'échelle tel que la somme des probabilités bornées vaut 1 (bissection)
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if np.clip(raw * mid, P_MIN, P_MAX).sum() < 1.0:
            lo = mid
        else:
            hi = mid
    p = np.clip(raw * math.sqrt(lo * hi), P_MIN, P_MAX)
    return tuple(float(x) for x in p / p.sum())


def climatology(country: str, units: pd.DataFrame, months_used: list[int]):
    """Moyenne et écart-type (sur les saisons CHIRPS) du cumul des mois donnés, au centroïde de chaque zone."""
    ms = load_grid(grid_dir(country) / "monthly_series.npz")
    idx = [list(ms["months"]).index(m) for m in months_used]
    tot = ms["arr"][:, idx].astype("float64").sum(axis=1)       # (saisons, h, w)
    vals = np.array([sample_grid(tot[k], float(ms["lon0"]), float(ms["lat0"]), float(ms["res"]), units.lon.values, units.lat.values) for k in range(tot.shape[0])])
    return vals.mean(axis=0), vals.std(axis=0, ddof=1)


def run(country: str, forecasts: list[dict] | None = None) -> dict | None:
    units = read_units(country)
    d2 = units[units.level == 2].reset_index(drop=True)
    fc = forecasts if forecasts is not None else fetch(d2.lat.tolist(), d2.lon.tolist())
    parsed = []
    for z in fc:
        mo = z["monthly"]
        parsed.append(season_anomaly(mo["time"], mo["precipitation_mean"], mo["precipitation_anomaly"]))
    ref = next((p for p in parsed if p[0] is not None), None)
    if ref is None:
        print("Prévision saisonnière : moins de deux mois de la saison de pluie couverts, rien d'écrit.")
        return None
    months_used = ref[1]
    mu, sd = climatology(country, d2, months_used)
    today = dt.date.today().isoformat()
    zones, probs = {}, {}
    for i, ((r, _, rows), pc) in enumerate(zip(parsed, d2.pcode)):
        if r is None:
            continue
        p = tercile_probs(r, float(mu[i]), float(sd[i]))
        if p is None:
            continue
        probs[pc] = p
        zones[pc] = {"a": [round(x[2], 1) for x in rows], "r": [round(100 * x[2] / x[3], 1) if x[3] > 0 else None for x in rows], "rs": round(100 * r, 1),
                     "p": [round(100 * x) for x in p]}
    months = [x[0] for x in ref[2]]
    # régions : moyenne pondérée par la surface des districts
    for pc, g in d2.groupby("parent"):
        w = g.area_km2.fillna(0).values
        ok = [c for c in g.pcode if c in zones]
        if not ok or w.sum() <= 0:
            continue
        ww = np.array([float(g.set_index("pcode").area_km2.fillna(0)[c]) for c in ok])
        ww = ww / ww.sum()
        zones[pc] = {"a": [round(float(sum(zones[c]["a"][k] * ww[j] for j, c in enumerate(ok))), 1) for k in range(len(months))],
                     "r": [None if any(zones[c]["r"][k] is None for c in ok) else round(float(sum(zones[c]["r"][k] * ww[j] for j, c in enumerate(ok))), 1) for k in range(len(months))],
                     "rs": round(float(sum(zones[c]["rs"] * ww[j] for j, c in enumerate(ok))), 1),
                     "p": [round(float(sum(zones[c]["p"][k] * ww[j] for j, c in enumerate(ok)))) for k in range(3)]}
        probs[pc] = tuple(float(sum(probs[c][k] * ww[j] for j, c in enumerate(ok))) for k in range(3))
    rows = [(pc, round(p[0], 3), round(p[1], 3), round(p[2], 3), SOURCE, today) for pc, p in probs.items()]
    pd.DataFrame(rows, columns=["pcode", "p_sec", "p_normal", "p_humide", "source", "date"]).to_csv(country_data_dir(country) / "seasonal_auto.csv", index=False)
    ext = []
    for pc, z in zones.items():
        ext += [(pc, "seas_anom_pct", z["rs"]), (pc, "seas_p_sec_pct", z["p"][0]), (pc, "seas_p_humide_pct", z["p"][2])]
    e = pd.DataFrame(ext, columns=["pcode", "indicateur", "valeur"])
    e["date"], e["source"] = today, SOURCE
    (country_data_dir(country) / "external").mkdir(exist_ok=True)
    e.to_csv(country_data_dir(country) / "external" / "seasonal.csv", index=False)
    write_json(country_docs_dir(country) / "seasonal.json", {
        "issued": today, "model": "ECMWF SEAS5 / EC46 via Open-Meteo", "months": months, "season_months": months_used, "source": SOURCE, "z": zones,
        "notes": ["Anomalie = écart à la climatologie du modèle (mm) ; écart en % de cette normale.",
                  "Les probabilités sont bornées à 15-50 % : la moyenne d'ensemble n'est pas calibrée sur la compétence réelle du modèle.",
                  "Les mois hors novembre-avril sont affichés mais ne comptent pas dans la saison."]})
    print(f"Prévision saisonnière : {len(zones)} zones, saison sur les mois {months_used} ; exemple écart saison {next(iter(zones.values()))['rs']} %")
    return {"zones": zones, "probs": probs, "months": months}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    if args.country != "mdg":
        print("Prévision saisonnière : seul Madagascar est configuré.")
        return
    run(args.country)


if __name__ == "__main__":
    main()
