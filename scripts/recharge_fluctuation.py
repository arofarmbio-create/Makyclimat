"""Recharge mesurée par la fluctuation des nappes dans le Grand Sud (validation/protocole_recharge_fluctuation.md,
fixé avant le calcul) et comparaison à la recharge transférée T2.

Sources : capteurs HT Analytics de MGMERL (2019 à mai 2026, niveau sous repère) et puits GROSoM (Carrière et al. 2021,
cotes ramenées en profondeur). Contrôle qualité de protocole_nappes_mgmerl.md. Recharge = Sy × somme des remontées
de novembre à avril (mensuelle, comme H-C6 ; journalière en sensibilité). Rapport recharge mesurée / T2 par site,
médiane et IC par rééchantillonnage ; règle de correction fixée à l'avance.
Sorties : validation/recharge_fluctuation.md et recharge_fluctuation_sites.csv (agrégés, sans séries).
Usage : python scripts/recharge_fluctuation.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

import validate_nappes_mgmerl as N
import validate_transfert_madagascar as T
from common import ROOT, country_data_dir

WET = (11, 12, 1, 2, 3, 4)
DAILY_RISE_M, MIN_SEASON_DAYS = 0.01, 120
N_BOOT, SEED, SHARE_BELOW = 2000, 0, 0.8


def wtf_daily(d: pd.DataFrame, sy: float) -> float:
    """Recharge (mm/an) par remontées journalières > 1 cm, de novembre à avril ; saisons d'au moins 120 jours valides."""
    day = d.set_index("t").level.dropna().resample("D").mean().dropna()
    if day.empty:
        return np.nan
    rise = day.diff().where(lambda x: x > DAILY_RISE_M, 0.0)
    wet = rise[rise.index.month.isin(WET)]
    season = wet.index.year + (wet.index.month >= 11)
    per = wet.groupby(season).agg(["sum", "count"])
    per = per[per["count"] >= MIN_SEASON_DAYS]
    return float(sy * per["sum"].mean() * 1000) if len(per) else np.nan


def site_recharge(d: pd.DataFrame, group: str) -> dict:
    """d : colonnes t, level (m, négatif sous le repère), ec (mS/cm). Recharge mensuelle et journalière en fourchette."""
    clean, n = N.qc(d)
    m = N.monthly(clean)
    out = {"mesures": n["mesures"], "gardees": n["niveaux_gardes"], "mois": len(m)}
    if len(m) < N.MIN_MONTHS:
        return {**out, "retenu": False}
    lv = m.level.copy()
    lv.index = lv.index.to_timestamp()
    lo, hi = T.SY.get(group, T.SY["Basement"])
    rm = (T.wtf_recharge(lv, lo), T.wtf_recharge(lv, hi))
    rd = (wtf_daily(clean, lo), wtf_daily(clean, hi))
    return {**out, "retenu": bool(np.isfinite(rm[0])), "r_bas": rm[0], "r_haut": rm[1], "r_mm": (rm[0] + rm[1]) / 2,
            "r_jour_bas": rd[0], "r_jour_haut": rd[1], "r_jour_mm": (rd[0] + rd[1]) / 2,
            "debut": str(m.index.min()), "fin": str(m.index.max())}


def ratio_test(ratios, n=N_BOOT, seed=SEED) -> dict:
    r = np.asarray([x for x in ratios if np.isfinite(x)])
    if len(r) == 0:
        return {"n": 0, "mediane": np.nan, "ic": (np.nan, np.nan), "part_sous_1": np.nan, "surestimee": False}
    rng = np.random.default_rng(seed)
    boot = [np.median(rng.choice(r, size=len(r), replace=True)) for _ in range(n)]
    ic = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))
    share = float(np.mean(r < 1))
    return {"n": len(r), "mediane": float(np.median(r)), "ic": ic, "part_sous_1": share,
            "surestimee": bool(share >= SHARE_BELOW and ic[1] < 1)}


def load_ht(path) -> dict:
    d = pd.read_csv(path, dtype={"Site Code": str})
    d["t"] = pd.to_datetime(d["Timestamp"], utc=True, errors="coerce").dt.tz_localize(None)
    d["code"] = pd.to_numeric(d["Site Code"], errors="coerce")
    out = {}
    for (code, name), g in d.dropna(subset=["code"]).groupby(["code", "Site - Nom"]):
        out[(int(code), str(name).strip())] = pd.DataFrame({"t": g.t, "level": pd.to_numeric(g["Water Level (m)"], errors="coerce"),
                                                            "ec": pd.to_numeric(g["Conductivité (uS/cm)"], errors="coerce") / 1000.0}).dropna(subset=["t"]).sort_values("t")
    return out


def load_grosom(folder) -> dict:
    wells = pd.read_csv(folder / "puits_grosom.csv")
    out = {}
    for w in wells.itertuples():
        f = folder / f"{w.nom}.csv"
        if not f.exists():
            continue
        g = pd.read_csv(f)
        out[w.nom] = (pd.DataFrame({"t": pd.to_datetime(g.datetime_utc, errors="coerce"),
                                    "level": pd.to_numeric(g.valeur, errors="coerce") - float(w.altitude_sol_m),
                                    "ec": np.nan}).dropna(subset=["t"]).sort_values("t"), float(w.lat), float(w.lon))
    return out


def nearest_row(df: pd.DataFrame, lat, lon) -> pd.Series:
    return df.iloc[int(np.argmin((df.lat - lat) ** 2 + (df.lon - lon) ** 2))]


def report(tab: pd.DataFrame, t_main: dict, t_day: dict) -> str:
    f = lambda v: "—" if v is None or not np.isfinite(v) else f"{v:.0f}"
    L = ["# Recharge mesurée par la fluctuation des nappes dans le Grand Sud", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/recharge_fluctuation.py`, selon "
         "`validation/protocole_recharge_fluctuation.md` (fixé avant le calcul). Sources : MGMERL (capteurs HT Analytics, "
         "2019-2026) ; Carrière et al. 2021, IGRAC-GGIS (GROSoM). Séries non publiées.", "",
         "| Site | Source | Groupe d'aquifère | Mois valides | Recharge mensuelle (mm/an) [Sy bas ; haut] | Recharge journalière (mm/an) | T2 (mm/an) | Rapport mesurée / T2 |",
         "|---|---|---|---|---|---|---|---|"]
    for r in tab.itertuples():
        if not r.retenu:
            L.append(f"| {r.site} | {r.source} | {r.groupe} | {r.mois} | non retenu (moins de {N.MIN_MONTHS} mois) | — | {f(r.t2_mm)} | — |")
            continue
        L.append(f"| {r.site} | {r.source} | {r.groupe} | {r.mois} | {f(r.r_mm)} [{f(r.r_bas)} ; {f(r.r_haut)}] | {f(r.r_jour_mm)} | {f(r.t2_mm)} | {r.rapport:.2f} |")
    for lab, t in (("principale (pas mensuel)", t_main), ("sensibilité (pas journalier)", t_day)):
        L += ["", f"**Méthode {lab}** : {t['n']} sites ; rapport médian {t['mediane']:.2f} [IC 95 % {t['ic'][0]:.2f} ; {t['ic'][1]:.2f}] ; "
              f"{t['part_sous_1']:.0%} des sites sous 1. T2 jugée **{'surestimée dans le Grand Sud' if t['surestimee'] else 'non démontrée surestimée'}** "
              "(règle : au moins 80 % des sites sous 1 et borne haute de l'IC sous 1)."]
    L += ["", "Limite : sites peu nombreux et concentrés ; la méthode mensuelle manque les remontées brèves (sous-estimation), "
          "la méthode journalière peut compter du bruit de capteur (surestimation).", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cdir = country_data_dir(args.country)
    rt = pd.read_csv(cdir / "nappes_mondiales" / "recharge_transferee.csv")
    sites = pd.read_csv(ROOT / "inputs" / "mgmerl" / "mgmerl_dataloggers_ht_analytics_sites.csv")
    rows = []
    ht = load_ht(cdir / "mgmerl_raw" / "complet_2026-11-03" / "niveaux_autres_tableaux" / "mgmerl_piezometres_ht_lectures_complet.csv")
    for (code, name), d in ht.items():
        s = sites[sites.code == code]
        if s.empty:
            continue
        lat, lon = float(s.lat.iloc[0]), float(s.lon.iloc[0])
        c = nearest_row(rt, lat, lon)
        grp = str(c.Aquifer_group) if pd.notna(c.Aquifer_group) else "Basement"
        rows.append({"site": name, "source": "HT (MGMERL)", "lat": lat, "lon": lon, "groupe": grp, "t2_mm": float(c.T2_mmpa), **site_recharge(d, grp)})
    for name, (d, lat, lon) in load_grosom(cdir / "nappes_mondiales" / "grosom").items():
        c = nearest_row(rt, lat, lon)
        grp = str(c.Aquifer_group) if pd.notna(c.Aquifer_group) else "Sedimentary"
        rows.append({"site": name, "source": "GROSoM", "lat": lat, "lon": lon, "groupe": grp, "t2_mm": float(c.T2_mmpa), **site_recharge(d, grp)})
    tab = pd.DataFrame(rows)
    for col in ("r_mm", "r_jour_mm", "r_bas", "r_haut", "r_jour_bas", "r_jour_haut"):
        if col not in tab:
            tab[col] = np.nan
    tab["rapport"] = tab.r_mm / tab.t2_mm
    tab["rapport_jour"] = tab.r_jour_mm / tab.t2_mm
    ok = tab.retenu.fillna(False).astype(bool)
    t_main, t_day = ratio_test(tab.rapport[ok]), ratio_test(tab.rapport_jour[ok])
    vd = ROOT / "validation"
    (vd / "recharge_fluctuation.md").write_text(report(tab, t_main, t_day), encoding="utf-8")
    tab.drop(columns=["lat", "lon"]).round(3).to_csv(vd / "recharge_fluctuation_sites.csv", index=False)
    print(f"Recharge par fluctuation : {int(ok.sum())} sites retenus ; rapport médian {t_main['mediane']:.2f} ; surestimée : {t_main['surestimee']}")


if __name__ == "__main__":
    main()
