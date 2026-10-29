"""Pluie récente par dékade, depuis le dernier mois CHIRPS définitif, comparée à la même période des années de référence.

Cahier des charges §5 (anomalies observées depuis le début de l'année hydrologique). Sert d'état initial aux modèles
(§8, §9) : c'est la pluie déjà tombée avant que la prévision ne prenne le relais.

Données : CHIRPS v2.0 décadaire (CHC/UCSB, 0,05°). Pour chaque dékade, le fichier définitif (Afrique) s'il existe,
sinon le fichier provisoire (« prelim », mondial, révisé environ 3 semaines plus tard). Référence : mêmes dékades,
fichiers définitifs, années rainfall.baseline_years (1991-2020).
Indicateurs par fokontany, commune, district, région :
  pluie_recente_mm   cumul de la période (mm)
  pluie_recente_pct  % de la normale de la période (vide si la normale < rainfall.min_normal_mm au prorata des dékades)
  pluie_recente_rang rang centile parmi les années de référence (0 = plus sec que toutes, 100 = plus humide que toutes)
Limites : estimation satellitaire, pas une observation de station ; données provisoires révisables ; début de saison :
un % de la normale sur peu de mm est instable, d'où le rang centile en complément.
Sorties : data/<pays>/external/recent_rain.csv, docs/data/<pays>/recent_rain.json, validation/pluie_recente_regions.csv,
cache data/<pays>/grids/dekad_ref_<mm><d>.npz (pluie des années de référence, recalculée une seule fois par dékade).
Usage : python scripts/update_recent_rain.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from chirps import fetch_array, read_crop
from common import DATA_DIR, country_data_dir, country_docs_dir, grid_dir, load_config, load_grid, read_units, sample_grid, save_grid, write_json

PRELIM_URL = "https://data.chc.ucsb.edu/products/CHIRPS/v2.0/prelim/global_dekad/tifs/chirps-v2.0.{y}.{m:02d}.{d}.tif"
SOURCE = "CHIRPS v2.0 décadaire (CHC/UCSB), définitif ou provisoire ; référence {b0}-{b1} (MakyClimat)"


def url_exists(url: str) -> bool:
    import requests
    try:
        return requests.head(url, timeout=60, allow_redirects=True).status_code == 200
    except requests.RequestException:
        return False


def read_prelim(url: str, bbox):
    """Lecture fenêtrée du GeoTIFF mondial provisoire, sans le télécharger en entier."""
    return read_crop("/vsicurl/" + url, bbox)


def next_month(y: int, m: int):
    return (y + 1, 1) if m == 12 else (y, m + 1)


def window_dekads(cfg: dict, today: dt.date, exists):
    """Dékades à cumuler : du premier jour suivant le dernier mois définitif disponible jusqu'à la dernière dékade publiée.
    Retourne [(année, mois, dékade, 'définitif'|'provisoire'), ...]."""
    r = cfg["rainfall"]
    y, m = today.year, today.month
    for _ in range(6):                                      # dernier mois définitif disponible (au plus 6 mois en arrière)
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
        if exists(r["monthly_url"].format(y=y, m=m)):
            break
    else:
        return []
    out = []
    y, m = next_month(y, m)
    while dt.date(y, m, 1) <= today:
        for d in (1, 2, 3):
            if exists(r["dekad_url"].format(y=y, m=m, d=d)):
                out.append((y, m, d, "définitif"))
            elif exists(PRELIM_URL.format(y=y, m=m, d=d)):
                out.append((y, m, d, "provisoire"))
            else:
                return out
        y, m = next_month(y, m)
    return out


def reference(cfg: dict, country: str, m: int, d: int, read_final):
    """Pluie de la dékade (m, d) pour chaque année de référence, (Y, h, w), mise en cache."""
    b0, b1 = cfg["rainfall"]["baseline_years"]
    path = grid_dir(country) / f"dekad_ref_{m:02d}{d}.npz"
    if path.exists():
        g = load_grid(path)
        if int(g["b0"]) == b0 and int(g["b1"]) == b1:
            return g["arr"].astype("float32"), (float(g["lon0"]), float(g["lat0"]), float(g["res"]))
    arrs, geo = [], None
    for y in range(b0, b1 + 1):
        r = read_final(cfg["rainfall"]["dekad_url"].format(y=y, m=m, d=d), cfg["map"]["bbox"])
        if r is None:
            raise RuntimeError(f"dékade de référence absente : {y}-{m:02d}-{d}")
        arrs.append(r[0])
        geo = geo or r[1:]
    h = min(a.shape[0] for a in arrs)
    w = min(a.shape[1] for a in arrs)
    arr = np.stack([a[:h, :w] for a in arrs])
    save_grid(path, arr=arr.astype("float16"), lon0=np.array(geo[0]), lat0=np.array(geo[1]), res=np.array(geo[2]),
              b0=np.array(b0), b1=np.array(b1))
    return arr, geo


def compute(cur: np.ndarray, ref: np.ndarray, min_normal: float):
    """cur (h, w) cumul actuel ; ref (Y, h, w) cumuls des années de référence -> (normale, % de la normale, rang centile)."""
    normal = np.nanmean(ref, axis=0)
    pct = np.where(normal >= min_normal, 100.0 * cur / np.maximum(normal, 1e-9), np.nan)
    n = np.sum(np.isfinite(ref), axis=0)
    below = np.sum(ref < cur[None], axis=0) + 0.5 * np.sum(ref == cur[None], axis=0)
    rank = np.where((n >= 20) & np.isfinite(cur), 100.0 * below / np.maximum(n, 1), np.nan)
    return normal, pct, rank


def main(country="mdg", today=None, exists=url_exists, read_final=fetch_array, read_prov=read_prelim):
    from build_soilwater import zone_means
    cfg = load_config(country)
    today = today or dt.date.today()
    bbox = cfg["map"]["bbox"]
    dek = window_dekads(cfg, today, exists)
    out_json = country_docs_dir(country) / "recent_rain.json"
    if not dek:
        write_json(out_json, {"generated": today.isoformat(), "dekads": [], "note": "aucune dékade publiée après le dernier mois définitif"})
        print("Pluie récente : aucune dékade à cumuler")
        return None
    cur = ref = geo = None
    for (y, m, d, kind) in dek:
        if kind == "définitif":
            url = cfg["rainfall"]["dekad_url"].format(y=y, m=m, d=d)
            r = read_final(url, bbox)
        else:
            url = PRELIM_URL.format(y=y, m=m, d=d)
            r = read_prov(url, bbox)
        if r is None:
            raise RuntimeError(f"dékade annoncée mais illisible : {url}")
        a, g = r[0], r[1:]
        rf, rgeo = reference(cfg, country, m, d, read_final)
        h, w = min(a.shape[0], rf.shape[1]), min(a.shape[1], rf.shape[2])
        if cur is None:
            cur, ref, geo = a[:h, :w].astype("float64"), rf[:, :h, :w].astype("float64"), rgeo
        else:
            h, w = min(h, cur.shape[0]), min(w, cur.shape[1])
            cur, ref = cur[:h, :w] + a[:h, :w], ref[:, :h, :w] + rf[:, :h, :w]
    min_normal = float(cfg["rainfall"].get("min_normal_mm", 25)) * len(dek) / 3.0
    normal, pct, rank = compute(cur, ref, min_normal)
    units = read_units(country)
    leaves = units[units.level == 4].reset_index(drop=True)
    lon0, lat0, res = geo
    lv = {k: sample_grid(v, lon0, lat0, res, leaves.lon.to_numpy(), leaves.lat.to_numpy())
          for k, v in (("pluie_recente_mm", cur), ("pluie_recente_normale_mm", normal), ("pluie_recente_pct", pct), ("pluie_recente_rang", rank))}
    zm = zone_means(units, lv)
    date = today.isoformat()
    b0, b1 = cfg["rainfall"]["baseline_years"]
    rows = [(pc, k, round(float(v[i]), 1), date) for k, v in lv.items() for i, pc in enumerate(leaves.pcode) if np.isfinite(v[i])]
    rows += [(pc, k, round(v, 1), date) for pc, dd in zm.items() for k, v in dd.items() if np.isfinite(v)]
    ext = pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur", "date"])
    ext["source"] = SOURCE.format(b0=b0, b1=b1)
    ed = country_data_dir(country) / "external"
    ed.mkdir(parents=True, exist_ok=True)
    ext.to_csv(ed / "recent_rain.csv", index=False)
    first, last = dek[0], dek[-1]
    end_day = {1: 10, 2: 20, 3: (dt.date(*next_month(last[0], last[1]), 1) - dt.timedelta(days=1)).day}[last[2]]
    period = {"from": f"{first[0]}-{first[1]:02d}-01", "to": f"{last[0]}-{last[1]:02d}-{end_day:02d}"}
    reg = units[units.level == 1]
    recs = [{"debut": period["from"], "fin": period["to"], "adm1": pc, "nom": nm,
             "pluie_mm": round(zm[pc]["pluie_recente_mm"], 1), "normale_mm": round(zm[pc]["pluie_recente_normale_mm"], 1),
             "pct_normale": None if not np.isfinite(zm[pc]["pluie_recente_pct"]) else round(zm[pc]["pluie_recente_pct"]),
             "rang_centile": round(zm[pc]["pluie_recente_rang"])}
            for pc, nm in zip(reg.pcode, reg.name) if pc in zm]
    vd = DATA_DIR.parent / "validation"
    vd.mkdir(exist_ok=True)
    if country != "demo":
        pd.DataFrame(recs).to_csv(vd / "pluie_recente_regions.csv", index=False)
    write_json(out_json, {"generated": date, "period": period, "baseline": [b0, b1],
                          "dekads": [{"y": y, "m": m, "d": d, "type": k} for (y, m, d, k) in dek],
                          "n_provisoires": sum(k == "provisoire" for *_, k in dek), "regions": recs})
    print(f"Pluie récente du {period['from']} au {period['to']} ({len(dek)} dékades, "
          f"{sum(k == 'provisoire' for *_, k in dek)} provisoires) : {len(recs)} régions")
    return {"dekads": dek, "period": period, "regions": recs, "cur": cur, "pct": pct, "rank": rank}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    main(ap.parse_args().country)
