"""Test de la mémoire hydrique du sous-sol (THMS) dans le Grand Sud (validation/protocole_thms_test_sud.md, fixé avant
le calcul ; idée du porteur du projet).

Modèle journalier : réservoir de sol (capacité Smax, ETR = ET0 × stock / Smax, surplus = infiltration I) ; recharge =
somme de M réservoirs linéaires (poids w_j, temps T_j, T_1 < T_2 < T_3) ; nappe : dh/dt = R/Sy − (h − h0)/τd.
Calage sur les 60 % premiers de chaque série (KGE, évolution différentielle), validation sur les 40 % suivants.
H-M1 : le M choisi par l'AIC du calage bat M = 1 en validation sur au moins 9 sites sur 12.
Mise en œuvre : Smax pris dans une grille fixe (8 valeurs) pour que le calage reste rapide (réservoirs linéaires calculés
par filtrage récursif).
Sorties : validation/thms_test_sud.md et thms_test_sud_sites.csv (agrégés, sans séries).
Usage : python scripts/thms_test_sud.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

import numpy as np
import pandas as pd
from scipy import optimize, signal, stats

import recharge_fluctuation as RF
import validate_e1 as E
import validate_nappes_mgmerl as N
from common import ROOT, country_data_dir, grid_dir

SMAX_GRID = (25.0, 50.0, 75.0, 100.0, 150.0, 200.0, 300.0, 400.0)
SY = {"Basement": (0.01, 0.05), "Sedimentary": (0.05, 0.15), "Unconsolidated": (0.05, 0.15)}
T_BOUNDS, TAUD_BOUNDS = (1.0, 3000.0), (5.0, 3000.0)
CAL_SHARE, WARMUP_DAYS, SEED = 0.6, 365, 0


# ---------------- modèle ----------------
def soil_infiltration(P: np.ndarray, ET0: np.ndarray, smax: float) -> np.ndarray:
    """Réservoir de sol : ETR = ET0 × S / Smax ; I = surplus au-delà de Smax (mm/jour)."""
    s, out = smax / 2, np.zeros(len(P))
    for t in range(len(P)):
        s = max(s + P[t] - ET0[t] * s / smax, 0.0)
        if s > smax:
            out[t], s = s - smax, smax
    return out


def linear_reservoir(x: np.ndarray, T: float) -> np.ndarray:
    """Réponse exponentielle exp(−τ/T)/T discrétisée : y_t = a y_{t−1} + (1 − a) x_t, a = exp(−1/T)."""
    a = np.exp(-1.0 / T)
    return signal.lfilter([1 - a], [1, -a], x)


def simulate(I: np.ndarray, w, T, sy: float, taud: float, h0: float) -> np.ndarray:
    """Niveau (m) : h_t − h0 = (1 − 1/τd)(h_{t−1} − h0) + R_t / Sy, R en m/jour."""
    R = sum(wj * linear_reservoir(I, Tj) for wj, Tj in zip(w, T)) / 1000.0
    b = 1.0 - 1.0 / taud
    return h0 + signal.lfilter([1.0 / sy], [1, -b], R)


def kge(sim, obs) -> float:
    ok = np.isfinite(sim) & np.isfinite(obs)
    if ok.sum() < 30 or np.std(obs[ok]) == 0 or np.std(sim[ok]) == 0:
        return float("nan")
    s, o = sim[ok], obs[ok]
    r = np.corrcoef(s, o)[0, 1]
    return float(1 - np.sqrt((r - 1) ** 2 + (np.std(s) / np.std(o) - 1) ** 2 + (np.mean(s) / np.mean(o) - 1) ** 2))


def unpack(x, M):
    """x = [i_smax, w_1..w_M, logT_1..logT_M (incréments), sy, log τd, h0] ; poids renormalisés si Σ > 1."""
    ism = int(np.clip(round(x[0]), 0, len(SMAX_GRID) - 1))
    w = np.asarray(x[1:1 + M])
    if w.sum() > 1:
        w = w / w.sum()
    inc = np.exp(np.asarray(x[1 + M:1 + 2 * M]))
    T = np.clip(np.cumsum(inc), *T_BOUNDS)                 # T_1 < T_2 < T_3 par construction
    return ism, w, T, x[1 + 2 * M], np.exp(x[2 + 2 * M]), x[3 + 2 * M]


def fit(Is: dict, obs: np.ndarray, cal: np.ndarray, M: int, sy_bounds, seed=SEED):
    """Calage par évolution différentielle (KGE sur les jours de calage). Retourne (paramètres, KGE calage, AIC)."""
    o_lo, o_hi = np.nanmin(obs[cal]), np.nanmax(obs[cal])
    bounds = ([(0, len(SMAX_GRID) - 1)] + [(0.0, 1.0)] * M + [(0.0, np.log(T_BOUNDS[1]))] * M
              + [sy_bounds, (np.log(TAUD_BOUNDS[0]), np.log(TAUD_BOUNDS[1])), (o_lo - 10, o_hi + 10)])

    def loss(x):
        ism, w, T, sy, taud, h0 = unpack(x, M)
        sim = simulate(Is[ism], w, T, sy, taud, h0)
        k = kge(sim[cal], obs[cal])
        return 10.0 if not np.isfinite(k) else 1 - k

    res = optimize.differential_evolution(loss, bounds, seed=seed, maxiter=150, popsize=12, tol=1e-6, polish=False)
    ism, w, T, sy, taud, h0 = unpack(res.x, M)
    sim = simulate(Is[ism], w, T, sy, taud, h0)
    e = (sim - obs)[cal]
    e = e[np.isfinite(e)]
    aic = len(e) * np.log(np.mean(e ** 2) + 1e-12) + 2 * len(bounds)
    return {"x": res.x, "smax": SMAX_GRID[ism], "w": w, "T": T, "sy": sy, "taud": taud, "h0": h0}, 1 - res.fun, aic, sim


def sign_test(wins: int, n: int) -> float:
    return float(stats.binomtest(wins, n, 0.5, alternative="greater").pvalue) if n else float("nan")


# ---------------- données ----------------
def daily_level(d: pd.DataFrame) -> pd.Series:
    clean, _ = N.qc(d)
    return clean.set_index("t").level.dropna().resample("D").mean()


def et0_daily(dates: pd.DatetimeIndex, lat, lon, cache: dict) -> np.ndarray:
    keys = [k for k in cache if not k.startswith("_") and cache[k]]
    k = min(keys, key=lambda s: (float(s.split(",")[0]) - lon) ** 2 + (float(s.split(",")[1]) - lat) ** 2)
    clim = np.asarray(cache[k], float)
    return clim[dates.month - 1] / dates.days_in_month.to_numpy()


def rain_daily(dates: pd.DatetimeIndex, lat, lon, e1_dir) -> np.ndarray:
    i, j = E.cell_of(lat, lon)
    out = pd.Series(np.nan, index=dates)
    for y in sorted(set(dates.year)):
        d, a = E.load_daily(e1_dir, "chirps", [y])
        if d is None:
            continue
        s = pd.Series(a[:, i, j].astype(float), index=d)
        out.loc[out.index.intersection(s.index)] = s.reindex(out.index.intersection(s.index)).to_numpy()
    return out.to_numpy()


def report(tab: pd.DataFrame, t1) -> str:
    L = ["# Test THMS (mémoire hydrique du sous-sol) dans le Grand Sud", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/thms_test_sud.py`, selon `validation/protocole_thms_test_sud.md` "
         "(fixé avant le calcul ; idée du porteur du projet). Niveaux : MGMERL (HT) et Carrière et al. 2021 (GROSoM) ; pluie CHIRPS ; "
         "ET0 Open-Meteo (ERA5-Land). Calage sur les 60 % premiers jours de chaque série, validation sur les 40 % suivants.", "",
         "| Site | Aquifère | Jours (calage / validation) | M choisi (AIC) | KGE validation M = 1 | KGE validation M choisi | Poids rapide w1 | T1 (jours) |",
         "|---|---|---|---|---|---|---|---|"]
    for r in tab.itertuples():
        L.append(f"| {r.site} | {r.aquifere} | {r.n_cal} / {r.n_val} | {r.M_aic} | {r.kge_val_M1:.2f} | {r.kge_val_Maic:.2f} | {r.w1:.2f} | {r.T1:.0f} |")
    L += ["", f"**H-M1** : le modèle choisi par l'AIC bat la mémoire unique en validation sur {t1[0]} sites sur {t1[1]} "
          f"(règle : au moins 9 sur 12 ; test du signe p = {t1[2]:.3f}). **{'Soutenue' if t1[0] >= 9 and t1[2] < 0.05 else 'Non soutenue'}**.",
          f"Sites où l'AIC garde une seule mémoire : {int((tab.M_aic == 1).sum())} (égalité, comptée comme non-victoire).", "",
          "H-M2 et H-M3 (exploratoires) : voir les colonnes w1 et T1 selon l'aquifère ; aucune conclusion confirmatoire.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cdir = country_data_dir(args.country)
    sites = pd.read_csv(ROOT / "validation" / "recharge_fluctuation_sites.csv")
    sites = sites[sites.retenu.astype(str) == "True"]
    coords = pd.read_csv(ROOT / "inputs" / "mgmerl" / "mgmerl_dataloggers_ht_analytics_sites.csv")
    gro = pd.read_csv(cdir / "nappes_mondiales" / "grosom" / "puits_grosom.csv")
    ll = {**{r.site.lower(): (r.lat, r.lon) for r in coords.itertuples()}, **{r.nom.lower(): (r.lat, r.lon) for r in gro.itertuples()}}
    ht = {k[1].lower(): v for k, v in RF.load_ht(cdir / "mgmerl_raw" / "complet_2026-11-03" / "niveaux_autres_tableaux"
                                                 / "mgmerl_piezometres_ht_lectures_complet.csv").items()}
    gr = {k.lower(): v[0] for k, v in RF.load_grosom(cdir / "nappes_mondiales" / "grosom").items()}
    cache = json.loads((grid_dir(args.country) / "et0_cache.json").read_text())
    rows = []
    for s in sites.itertuples():
        raw = ht.get(s.site.lower(), gr.get(s.site.lower()))
        if raw is None:
            continue
        lv = daily_level(raw)
        lv = lv[lv.index <= "2025-12-31"]
        dates = pd.date_range(lv.index.min() - pd.Timedelta(days=WARMUP_DAYS), lv.index.max(), freq="D")
        lat, lon = ll[s.site.lower()]
        P = np.nan_to_num(rain_daily(dates, lat, lon, cdir / "e1"), nan=0.0)
        ET0 = et0_daily(dates, lat, lon, cache)
        obs = lv.reindex(dates).to_numpy()
        valid = np.where(np.isfinite(obs))[0]
        valid = valid[valid >= WARMUP_DAYS]
        cut = valid[int(len(valid) * CAL_SHARE)]
        cal = np.zeros(len(dates), bool)
        cal[valid[valid < cut]] = True
        val = np.zeros(len(dates), bool)
        val[valid[valid >= cut]] = True
        Is = [soil_infiltration(P, ET0, sm) for sm in SMAX_GRID]
        grp = "Basement" if s.groupe == "Basement" else "Sedimentary"
        res = {}
        for M in (1, 2, 3):
            p, k_cal, aic, sim = fit(Is, obs, cal, M, SY[grp])
            res[M] = (p, k_cal, aic, kge(sim[val], obs[val]))
        m_aic = min(res, key=lambda m: res[m][2])
        pa = res[m_aic][0]
        rows.append({"site": s.site, "aquifere": s.groupe, "n_cal": int(cal.sum()), "n_val": int(val.sum()), "M_aic": m_aic,
                     "kge_val_M1": res[1][3], "kge_val_M2": res[2][3], "kge_val_M3": res[3][3], "kge_val_Maic": res[m_aic][3],
                     "w1": float(pa["w"][0]), "T1": float(pa["T"][0]), "smax": pa["smax"], "sy": float(pa["sy"]), "taud": float(pa["taud"])})
        print(f"THMS {s.site} : M = {m_aic}, KGE validation {res[1][3]:.2f} -> {res[m_aic][3]:.2f}", flush=True)
    tab = pd.DataFrame(rows)
    wins = int(((tab.M_aic > 1) & (tab.kge_val_Maic > tab.kge_val_M1)).sum())
    t1 = (wins, len(tab), sign_test(wins, len(tab)))
    vd = ROOT / "validation"
    (vd / "thms_test_sud.md").write_text(report(tab, t1), encoding="utf-8")
    tab.round(3).to_csv(vd / "thms_test_sud_sites.csv", index=False)
    print(f"THMS : H-M1 {wins}/{len(tab)} (p = {t1[2]:.3f})")


if __name__ == "__main__":
    main()
