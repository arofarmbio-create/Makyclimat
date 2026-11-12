"""Expérience E1 (validation/protocole_e1_fusion_pluie.md) : fusion contrôlée de CHIRPS, IMERG Late et ERA5-Land.

Étapes, toutes fixées par le protocole avant calcul :
  1. pluie journalière des trois sources sur la grille commune de 0,1° (build_e1_sources.py, release « e1-pluie ») ;
  2. cumuls par pentade (5 jours ; la dernière pentade de l'année prend les jours restants) ; pentade manquante si un
     de ses jours manque ;
  3. triple collocation étendue (McColl et al. 2014) par maille, sur les pentades de novembre à avril de la période
     d'apprentissage 2001-2015, après mise à l'échelle de chaque source sur CHIRPS (moyenne et écart-type par mois du
     calendrier) ;
  4. fusion C = moyenne pondérée par 1 / variance d'erreur (poids renormalisés si une source manque ; poids égaux si la
     triple collocation donne une variance négative ou indéfinie) ; B = moyenne simple des sources brutes ;
  5. meilleure source seule = plus faible variance d'erreur médiane sur l'apprentissage ;
  6. évaluation sur les stations GSOD (drapeaux D, F, G seulement ; pentade gardée si ses 5 jours sont valides ; station
     gardée si au moins 100 pentades valides en test 2016-2025) : KGE (critère principal), MAE, RMSE, biais,
     corrélation ; tests du signe H1-E1 (C contre la meilleure source) et H1-E1b (C contre B).
Sorties : validation/e1_fusion_pluie.md, validation/e1_stations.csv, data/<pays>/e1/e1_tc.npz (cartes d'erreur).
Usage : python scripts/validate_e1.py --country mdg [--e1-dir data/mdg/e1]
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from build_e1_sources import LATS, LONS, NX, NY
from common import ROOT, country_data_dir, save_grid

SOURCES = ("chirps", "imerg", "era5")
TRAIN, TEST = (2001, 2015), (2016, 2025)
WET_MONTHS = (11, 12, 1, 2, 3, 4)
GOOD_FLAGS = set("DFG")
MIN_TC_SAMPLES = 30
MIN_STATION_PENTADS = 100


# ---------------- pentades ----------------
def pentad_index(dates: pd.DatetimeIndex) -> np.ndarray:
    """Numéro de pentade dans l'année (0..72) ; la 73e prend les jours restants (5 ou 6)."""
    return np.minimum((dates.dayofyear.to_numpy() - 1) // 5, 72)


def to_pentads(dates: pd.DatetimeIndex, x: np.ndarray):
    """x (jours, ...) -> (étiquettes année*100 + pentade, mois du milieu, sommes (pentades, ...)) ; NaN si un jour manque."""
    key = dates.year.to_numpy() * 100 + pentad_index(dates)
    keys = np.unique(key)
    out = np.full((len(keys),) + x.shape[1:], np.nan, dtype="float64")
    month = np.zeros(len(keys), dtype=int)
    for i, k in enumerate(keys):
        sel = key == k
        block = x[sel]
        out[i] = np.where(np.isfinite(block).all(axis=0), np.nansum(block, axis=0), np.nan)
        month[i] = dates[sel][len(block) // 2].month
    return keys, month, out


# ---------------- triple collocation ----------------
def triple_collocation(x, y, z):
    """Triple collocation étendue (McColl et al. 2014). x, y, z : (n, cellules). Retourne (variances d'erreur (3, cellules),
    corrélations au carré avec le signal vrai (3, cellules)) ; NaN si moins de MIN_TC_SAMPLES valeurs communes."""
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    n = ok.sum(axis=0)
    def cov(a, b):
        am = np.where(ok, a, 0).sum(0) / np.maximum(n, 1)
        bm = np.where(ok, b, 0).sum(0) / np.maximum(n, 1)
        return np.where(ok, (a - am) * (b - bm), 0).sum(0) / np.maximum(n - 1, 1)
    qxx, qyy, qzz = cov(x, x), cov(y, y), cov(z, z)
    qxy, qxz, qyz = cov(x, y), cov(x, z), cov(y, z)
    with np.errstate(divide="ignore", invalid="ignore"):
        ev = np.stack([qxx - qxy * qxz / qyz, qyy - qxy * qyz / qxz, qzz - qxz * qyz / qxy])
        r2 = np.stack([qxy * qxz / (qxx * qyz), qxy * qyz / (qyy * qxz), qxz * qyz / (qzz * qxy)])
    bad = n < MIN_TC_SAMPLES
    ev[:, bad] = np.nan
    r2[:, bad] = np.nan
    return ev, r2


# ---------------- mise à l'échelle et fusion ----------------
def rescale_to_ref(src, ref, month, train):
    """Ramène src à la moyenne et à l'écart-type de ref, par mois du calendrier, estimés sur train (bool par pentade)."""
    out = np.full(src.shape, np.nan)
    for m in range(1, 13):
        k = month == m
        kt = k & train
        if not kt.any():
            continue
        ms, ss = np.nanmean(src[kt], axis=0), np.nanstd(src[kt], axis=0)
        mr, sr = np.nanmean(ref[kt], axis=0), np.nanstd(ref[kt], axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(ss > 0, (src[k] - ms) / ss, 0.0)
        out[k] = np.maximum(mr + z * sr, 0.0)
    return out


def tc_weights(ev):
    """Poids 1 / variance d'erreur, normalisés ; poids égaux là où une variance est négative ou indéfinie."""
    bad = ~np.all(np.isfinite(ev) & (ev > 0), axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        w = 1.0 / ev
    w[:, bad] = 1.0
    return w / w.sum(axis=0, keepdims=True), int(bad.sum())


def merge(series, weights):
    """Moyenne pondérée de séries (k, n, cellules) ; poids renormalisés quand une source manque."""
    s = np.asarray(series)
    w = np.broadcast_to(weights[:, None, :], s.shape)
    ok = np.isfinite(s)
    ws = np.where(ok, w, 0).sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(ws > 0, np.where(ok, s * w, 0).sum(0) / ws, np.nan)


# ---------------- stations ----------------
def station_pentads(df: pd.DataFrame) -> pd.Series:
    """Relevés d'une station GSOD -> cumuls par pentade, seulement si les 5 (ou 6) jours ont un drapeau D, F ou G."""
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.drop_duplicates("date").set_index("date").sort_index()
    good = d["drapeau"].astype(str).str.strip().isin(GOOD_FLAGS) & d["pluie_mm"].notna()
    full = pd.date_range(d.index.min(), d.index.max(), freq="D")
    v = d["pluie_mm"].where(good).reindex(full)
    keys, _, sums = to_pentads(full, v.to_numpy()[:, None])
    return pd.Series(sums[:, 0], index=keys)


def kge(sim, obs):
    ok = np.isfinite(sim) & np.isfinite(obs)
    if ok.sum() < 10 or np.std(obs[ok]) == 0 or np.mean(obs[ok]) == 0:
        return np.nan
    s, o = sim[ok], obs[ok]
    r = np.corrcoef(s, o)[0, 1] if np.std(s) > 0 else 0.0
    return 1 - np.sqrt((r - 1) ** 2 + (np.std(s) / np.std(o) - 1) ** 2 + (np.mean(s) / np.mean(o) - 1) ** 2)


def scores(sim, obs):
    ok = np.isfinite(sim) & np.isfinite(obs)
    s, o = sim[ok], obs[ok]
    return {"kge": kge(sim, obs), "mae": float(np.mean(np.abs(s - o))) if ok.any() else np.nan,
            "rmse": float(np.sqrt(np.mean((s - o) ** 2))) if ok.any() else np.nan,
            "biais": float(np.mean(s - o)) if ok.any() else np.nan,
            "r": float(np.corrcoef(s, o)[0, 1]) if ok.sum() > 2 and np.std(s) > 0 and np.std(o) > 0 else np.nan, "n": int(ok.sum())}


def sign_test(wins: int, n: int) -> float:
    from scipy import stats
    return float(stats.binomtest(wins, n, 0.5, alternative="greater").pvalue) if n else float("nan")


def cell_of(lat, lon):
    return int(np.argmin(np.abs(LATS - lat))), int(np.argmin(np.abs(LONS - lon)))


# ---------------- chargement ----------------
def load_daily(e1_dir, src, years):
    days, arrs = [], []
    for y in years:
        f = e1_dir / f"{src}_{y}.npz"
        if not f.exists():
            continue
        z = np.load(f, allow_pickle=False)
        start = dt.date.fromisoformat(str(z["start"]))
        n = z["pluie"].shape[0]
        days.append(pd.date_range(start, periods=n, freq="D"))
        arrs.append(z["pluie"].astype("float32"))
    if not arrs:
        return None, None
    return days[0].append(days[1:]) if len(days) > 1 else days[0], np.concatenate(arrs)


def analyse(daily: dict, gsod: pd.DataFrame | None):
    """daily : {source: (dates, (jours, NY, NX))} sur des dates identiques. Retourne un dictionnaire de résultats."""
    dates = daily[SOURCES[0]][0]
    keys = month = None
    P = {}
    for s in SOURCES:
        keys, month, p = to_pentads(dates, daily[s][1].reshape(len(dates), -1))
        P[s] = p
    year = keys // 100
    train = (year >= TRAIN[0]) & (year <= TRAIN[1])
    test = (year >= TEST[0]) & (year <= TEST[1])
    wet = np.isin(month, WET_MONTHS)
    R = {s: (P[s] if s == "chirps" else rescale_to_ref(P[s], P["chirps"], month, train)) for s in SOURCES}
    k = train & wet
    ev, r2 = triple_collocation(R["chirps"][k], R["imerg"][k], R["era5"][k])
    w, n_equal = tc_weights(ev)
    C = merge([R[s] for s in SOURCES], w)
    Bm = merge([P[s] for s in SOURCES], np.ones_like(w))
    med = {s: float(np.nanmedian(ev[i])) for i, s in enumerate(SOURCES)}
    best = min(med, key=med.get)
    res = {"keys": keys, "test": test, "ev": ev, "r2": r2, "weights": w, "equal_weight_cells": n_equal,
           "median_ev": med, "best": best, "products": {**{s: P[s] for s in SOURCES}, "B": Bm, "C": C}}
    rows = []
    if gsod is not None and len(gsod):
        for sid, g in gsod.groupby("station"):
            sp = station_pentads(g)
            obs = sp.reindex(keys).to_numpy()
            obs_t = np.where(test, obs, np.nan)
            if np.isfinite(obs_t).sum() < MIN_STATION_PENTADS:
                continue
            i, j = cell_of(float(g.lat.iloc[0]), float(g.lon.iloc[0]))
            row = {"station": sid, "nom": g["nom"].iloc[0], "lat": g.lat.iloc[0], "lon": g.lon.iloc[0], "pentades_test": int(np.isfinite(obs_t).sum())}
            for name, arr in res["products"].items():
                sc = scores(arr[:, i * NX + j], obs_t)
                for kk, vv in sc.items():
                    row[f"{kk}_{name}"] = vv
            rows.append(row)
    st = pd.DataFrame(rows)
    res["stations"] = st
    if len(st):
        ok1 = st[["kge_C", f"kge_{best}"]].dropna()
        ok2 = st[["kge_C", "kge_B"]].dropna()
        w1, w2 = int((ok1.kge_C > ok1[f"kge_{best}"]).sum()), int((ok2.kge_C > ok2.kge_B).sum())
        res["H1-E1"] = (w1, len(ok1), sign_test(w1, len(ok1)))
        res["H1-E1b"] = (w2, len(ok2), sign_test(w2, len(ok2)))
    return res


def report(res, years_used) -> str:
    f = lambda x: "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else (f"{x:.2f}" if isinstance(x, float) else str(x))
    L = ["# E1 : fusion contrôlée des sources de pluie", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_e1.py`, selon `validation/protocole_e1_fusion_pluie.md` "
         f"(fixé avant les calculs). Années disponibles : {years_used}.", "",
         "## Triple collocation (apprentissage 2001-2015, pentades de novembre à avril)", "",
         "| Source | Variance d'erreur médiane (mm² par pentade) | Corrélation médiane avec la pluie vraie (r) |", "|---|---|---|"]
    for i, s in enumerate(SOURCES):
        L.append(f"| {s} | {f(res['median_ev'][s])} | {f(float(np.sqrt(np.nanmedian(res['r2'][i]))))} |")
    L += ["", f"Meilleure source seule (fixée sur l'apprentissage) : **{res['best']}**. Mailles avec poids égaux "
          f"(variance négative ou indéfinie) : {res['equal_weight_cells']}.", ""]
    st = res["stations"]
    L += ["## Stations GSOD (test 2016-2025, pentades)", ""]
    if not len(st):
        L.append("Aucune station n'a assez de pentades valides en période de test.")
    else:
        L += ["| Hypothèse | Stations favorables | Stations | p (test du signe) | Conclusion |", "|---|---|---|---|---|"]
        for h, lab in (("H1-E1", f"KGE(C) > KGE({res['best']})"), ("H1-E1b", "KGE(C) > KGE(B)")):
            w, n, p = res[h]
            L.append(f"| {h} : {lab} | {w} | {n} | {f(p)} | {'soutenue (5 %)' if n and p < 0.05 else 'non soutenue'} |")
        L += ["", "| Station | Pentades | KGE CHIRPS | KGE IMERG | KGE ERA5-Land | KGE B | KGE C |", "|---|---|---|---|---|---|---|"]
        for r in st.itertuples():
            L.append(f"| {r.nom} | {r.pentades_test} | {f(r.kge_chirps)} | {f(r.kge_imerg)} | {f(r.kge_era5)} | {f(r.kge_B)} | {f(r.kge_C)} |")
        L += ["", "Rappel (protocole §7) : CHIRPS intègre des stations GTS, probablement en partie celles-ci ; la "
              "comparaison aux stations le favorise, ainsi que C."]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--e1-dir", default=None)
    args = ap.parse_args()
    e1_dir = country_data_dir(args.country) / "e1" if args.e1_dir is None else ROOT / args.e1_dir
    years = list(range(TRAIN[0], TEST[1] + 1))
    daily = {s: load_daily(e1_dir, s, years) for s in SOURCES}
    missing = [s for s, (d, _) in daily.items() if d is None]
    if missing:
        raise SystemExit(f"sources absentes : {missing} (téléchargement par l'agent, release e1-pluie)")
    common = daily[SOURCES[0]][0]
    for s in SOURCES[1:]:
        common = common.intersection(daily[s][0])
    aligned = {}
    for s, (d, a) in daily.items():
        idx = d.get_indexer(common)
        aligned[s] = (common, a[idx])
    gp = e1_dir / "gsod.csv"
    gsod = pd.read_csv(gp) if gp.exists() else None
    res = analyse(aligned, gsod)
    years_used = f"{common.min().year}-{common.max().year} ({len(common)} jours communs)"
    vd = ROOT / "validation"
    (vd / "e1_fusion_pluie.md").write_text(report(res, years_used), encoding="utf-8")
    res["stations"].to_csv(vd / "e1_stations.csv", index=False)
    save_grid(e1_dir / "e1_tc.npz", variance_erreur=res["ev"].reshape(3, NY, NX).astype("float32"),
              r2=res["r2"].reshape(3, NY, NX).astype("float32"), poids=res["weights"].reshape(3, NY, NX).astype("float32"),
              sources=np.array(SOURCES), lat=LATS, lon=LONS)
    print(f"E1 : meilleure source seule {res['best']}, H1-E1 {res.get('H1-E1')}, H1-E1b {res.get('H1-E1b')}")


if __name__ == "__main__":
    main()
