"""Validation sur événements réels : nos indicateurs auraient-ils désigné les régions que les rapports disent touchées ?

Pour chaque cyclone documenté (validation/zones_touchees.csv, avec source), on calcule par région :
  - vent maximal du système (IBTrACS, kt) à moins de R km d'un fokontany de la région, pour plusieurs rayons R ;
  - pluie CHIRPS journalière : cumul maximal sur 3 jours (rx3, mm) et sa part de la normale mensuelle, au 90e centile des fokontany ;
puis on compare à la liste des régions touchées (rapports OCHA/IFRC) :
  - AUC : probabilité qu'une région documentée soit mieux classée qu'une région non citée (0,5 = hasard, 1 = parfait) ;
  - règles d'alerte simples : détection (POD) et fausses alertes (FAR) ;
  - choix du seuil en « laisser un événement de côté » (le seuil est choisi sans voir l'événement testé).
Limites : les listes de régions des rapports sont partielles (une région non citée n'est pas forcément épargnée) : l'AUC est donc
prudente et la FAR est un majorant. Peu d'événements : résultats indicatifs, pas des garanties.
Usage : python scripts/validate_events.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools

import numpy as np
import pandas as pd

from common import DATA_DIR, country_docs_dir, grid_dir, load_config, load_grid, read_units, sample_grid, write_json

VAL_DIR = DATA_DIR.parent / "validation"
RADII = (50, 100, 150, 200)
RX3_T = (50, 75, 100, 150, 200)
FRAC_T = (0.15, 0.25, 0.4)
WIND_T = 34


def auc(score: np.ndarray, pos: np.ndarray) -> float:
    """Aire sous la courbe ROC (Mann-Whitney) ; NaN s'il manque une classe."""
    s = np.asarray(score, float)
    p = np.asarray(pos, bool)
    if p.sum() == 0 or (~p).sum() == 0:
        return float("nan")
    from scipy.stats import rankdata
    r = rankdata(s)
    return float((r[p].sum() - p.sum() * (p.sum() + 1) / 2) / (p.sum() * (~p).sum()))


def rules() -> dict:
    """Règles candidates : nom -> fonction(feat_row_df) -> booléens."""
    out = {}
    for R in RADII:
        out[f"vent>=34kt à {R} km"] = lambda f, R=R: f[f"wind{R}"] >= WIND_T
    for T in RX3_T:
        out[f"pluie 3 j >= {T} mm"] = lambda f, T=T: f["rx3"] >= T
    for T in FRAC_T:
        out[f"pluie 3 j >= {int(T*100)} % de la normale du mois"] = lambda f, T=T: f["frac3"] >= T
    for R, T in itertools.product(RADII, RX3_T):
        out[f"vent>=34kt à {R} km OU pluie 3 j >= {T} mm"] = lambda f, R=R, T=T: (f[f"wind{R}"] >= WIND_T) | (f["rx3"] >= T)
    return out


def confusion(flag: pd.Series, pos: pd.Series):
    tp = int((flag & pos).sum()); fp = int((flag & ~pos).sum()); fn = int((~flag & pos).sum())
    pod = tp / (tp + fn) if tp + fn else float("nan")
    far = fp / (tp + fp) if tp + fp else float("nan")
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return tp, fp, fn, pod, far, f1


def evaluate(feat: pd.DataFrame) -> dict:
    """feat : une ligne par (evenement, region) avec colonnes wind50..200, rx3, frac3, pos (bool). Retourne résultats."""
    res = {"events": [], "rules": [], "loeo": []}
    for ev, g in feat.groupby("evenement"):
        row = {"evenement": ev, "n_regions": int(len(g)), "n_documentees": int(g.pos.sum())}
        for c in ["wind100", "wind200", "rx3", "frac3"]:
            row[f"auc_{c}"] = auc(g[c].values, g.pos.values)
        # classement combiné : moyenne des rangs vent 150 km et pluie
        rk = g[["wind150", "rx3"]].rank(pct=True).mean(axis=1)
        row["auc_combine"] = auc(rk.values, g.pos.values)
        res["events"].append(row)
    R = rules()
    names = list(R)
    for nm in names:
        tp = fp = fn = 0
        for ev, g in feat.groupby("evenement"):
            a, b, c, *_ = confusion(R[nm](g), g.pos)
            tp += a; fp += b; fn += c
        pod = tp / (tp + fn) if tp + fn else float("nan")
        far = fp / (tp + fp) if tp + fp else float("nan")
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        res["rules"].append({"regle": nm, "tp": tp, "fp": fp, "fn": fn, "pod": pod, "far": far, "f1": f1})
    evs = sorted(feat.evenement.unique())
    for held in evs:
        train = feat[feat.evenement != held]
        best, bf = None, -1.0
        for nm in names:
            tp = fp = fn = 0
            for ev, g in train.groupby("evenement"):
                a, b, c, *_ = confusion(R[nm](g), g.pos); tp += a; fp += b; fn += c
            f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
            if f1 > bf:
                best, bf = nm, f1
        g = feat[feat.evenement == held]
        tp, fp, fn, pod, far, f1 = confusion(R[best](g), g.pos)
        res["loeo"].append({"evenement": held, "regle_choisie": best, "tp": tp, "fp": fp, "fn": fn, "pod": pod, "far": far, "f1": f1})
    return res


def storm_features(sid: str, d: pd.DataFrame, units: pd.DataFrame, rain: dict | None):
    """Entités par région pour un système. d = positions de ce système ; rain = dict(days, grid) ou None."""
    from build_cyclones import exposure
    leaves = units[units.level == 4]
    feats = {}
    for R in RADII:
        rows = exposure(d, units, float(R), 1.0)
        for pc, (_, w) in rows.items():
            if len(pc) == 4:
                feats.setdefault(pc, {})[f"wind{R}"] = float(w)
    if rain is not None:
        v = rain["leaf"]                     # (jours, feuilles)
        n = v.shape[0]
        roll = np.stack([v[i:i + 3].sum(axis=0) for i in range(max(1, n - 2))]) if n >= 3 else v.sum(axis=0, keepdims=True)
        rx3 = np.nanmax(roll, axis=0)
        frac = rx3 / np.maximum(rain["norm"], 1.0)
        for pc, idx in leaves.groupby("adm1").indices.items():
            feats.setdefault(pc, {})["rx3"] = float(np.nanpercentile(rx3[idx], 90))
            feats[pc]["frac3"] = float(np.nanpercentile(frac[idx], 90))
    return feats


def fetch_rain(cfg, units, days):
    """Pluie CHIRPS journalière aux fokontany pour une liste de dates ; None si indisponible."""
    from chirps import fetch_array
    leaves = units[units.level == 4]
    url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_daily/tifs/p05/{y}/chirps-v2.0.{y}.{m:02d}.{d:02d}.tif.gz"
    clim = load_grid(grid_dir(cfg["slug"]) / "clim_monthly.npz")
    out = []
    for day in days:
        res = fetch_array(url.format(y=day.year, m=day.month, d=day.day), cfg["bbox"])
        if res is None:
            print("  pluie absente", day)
            return None
        arr, lon0, lat0, r = res
        out.append(sample_grid(arr, lon0, lat0, r, leaves.lon.values, leaves.lat.values))
    mid = days[len(days) // 2]
    norm = sample_grid(clim["clim"][mid.month - 1], float(clim["lon0"]), float(clim["lat0"]), float(clim["res"]), leaves.lon.values, leaves.lat.values)
    return {"leaf": np.vstack(out), "norm": norm}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    from build_cyclones import KM_LAT, KM_LON0, clean, densify, fetch
    from scipy.spatial import cKDTree
    full = load_config(args.country)
    cfg = {"slug": args.country, "bbox": full["map"]["bbox"]}
    units = read_units(args.country)
    ev = pd.read_csv(VAL_DIR / "evenements.csv")
    truth = pd.read_csv(VAL_DIR / "zones_touchees.csv")
    names = dict(zip(units[units.level == 1].name, units[units.level == 1].pcode))
    d_all = clean(fetch(), 2016, [38.0, -30.0, 58.0, -6.0])
    d_all["nom"] = d_all.NAME.astype(str).str.title()
    leaves = units[units.level == 4]
    tree = cKDTree(np.c_[(leaves.lon.values - 47.0) * KM_LON0 * np.cos(np.deg2rad(-19.0)), leaves.lat.values * KM_LAT])
    rows = []
    for _, e in ev[ev.type == "cyclone"].iterrows():
        t = truth[truth.evenement == e.id]
        if t.empty:
            continue
        nom = e.nom
        yr = int(str(e.date_debut)[:4])
        g = d_all[(d_all.nom == nom) & (d_all.time.dt.year.isin([yr, yr + 1, yr - 1]))]
        if g.empty:
            print("trajectoire introuvable", e.id)
            continue
        g = g[g.SID == g.SID.iloc[0]]
        x = (g.LON.values - 47.0) * KM_LON0 * np.cos(np.deg2rad(-19.0)); y = g.LAT.values * KM_LAT
        dist, _ = tree.query(np.c_[x, y])
        near = g[dist <= 400]
        if near.empty:
            continue
        d0 = near.time.min().date() - dt.timedelta(days=1)
        d1 = near.time.max().date() + dt.timedelta(days=1)
        days = [d0 + dt.timedelta(days=i) for i in range((d1 - d0).days + 1)]
        try:
            rain = fetch_rain(cfg, units, days)
        except Exception as ex:  # noqa: BLE001
            print("pluie indisponible", e.id, ex)
            rain = None
        f = storm_features(g.SID.iloc[0], g, units, rain)
        pos = {names[r] for r in t.region if r in names}
        for pc, vals in f.items():
            rows.append({"evenement": e.id, "region": pc, "pos": pc in pos, **vals})
        print(f"{e.id}: fenêtre {d0}..{d1}, pluie={'oui' if rain else 'non'}")
    feat = pd.DataFrame(rows).fillna(0.0)
    for c in ["rx3", "frac3"]:
        if c not in feat:
            feat[c] = 0.0
    res = evaluate(feat)
    nm = dict(zip(units[units.level == 1].pcode, units[units.level == 1].name))
    feat["nom_region"] = feat.region.map(nm)
    VAL_DIR.mkdir(exist_ok=True)
    feat.to_csv(VAL_DIR / "cyclones_indicateurs_par_region.csv", index=False)
    pd.DataFrame(res["events"]).to_csv(VAL_DIR / "cyclones_auc_par_evenement.csv", index=False)
    pd.DataFrame(res["rules"]).sort_values("f1", ascending=False).to_csv(VAL_DIR / "cyclones_regles.csv", index=False)
    pd.DataFrame(res["loeo"]).to_csv(VAL_DIR / "cyclones_laisser_un_de_cote.csv", index=False)
    write_json(country_docs_dir(args.country) / "validation.json", {"generated": dt.date.today().isoformat(), "cyclones": res,
               "notes": ["Listes de régions touchées partielles (rapports OCHA/IFRC) : AUC prudente, fausses alertes majorées.",
                         "Peu d'événements : résultats indicatifs."]})
    print(pd.DataFrame(res["events"]).round(2).to_string())
    print(pd.DataFrame(res["loeo"]).round(2).to_string())


if __name__ == "__main__":
    main()
