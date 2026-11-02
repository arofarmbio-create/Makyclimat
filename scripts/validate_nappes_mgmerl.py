"""Protocole M3 (validation/protocole_nappes_mgmerl.md), étape 2 : niveaux de nappe MGMERL contre indices du système.

Lit les séries brutes des dataloggers HT Analytics (MGMERL, fichiers gardés hors git dans data/<pays>/mgmerl_raw/),
applique le contrôle qualité fixé à l'avance (section 4), calcule les anomalies mensuelles de niveau (section 5) et
les corrélations de Spearman avec SPI-1..24 et recharge12_z (data/<pays>/nappes_sites_indices.csv, produit par
build_nappes_sites.py). Tests du signe H-N1 et H-N2 (section 6).
Sorties : validation/nappes_mgmerl.md, validation/nappes_mgmerl_sites.csv (résultats agrégés par site seulement).
Données de niveaux de nappe : MGMERL (HT Analytics, UNICEF).
Usage : python scripts/validate_nappes_mgmerl.py --country mdg [--raw data/mdg/mgmerl_raw/ht_analytics_csv_2025-06]
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import os

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir

LEVEL_MIN, LEVEL_MAX = -60.0, 0.0          # règle 1 (m)
SPIKE_M = 2.0                              # règle 2 : écart à la médiane glissante sur 7 jours
JUMP_M, JUMP_DAYS = 3.0, 7                 # règle 3 : saut durable de la médiane journalière
EC_MAX_MS = 20.0                           # règle 4 (mS/cm)
MIN_DAYS_MONTH, MIN_MONTHS = 10, 24        # règles 5 et 6
MIN_PAIRS = 12                             # paires mensuelles minimales pour une corrélation
NMAX = 24
ATTRIBUTION = "Données de niveaux de nappe : MGMERL (HT Analytics, UNICEF)"


def load_ht_csv(path) -> pd.DataFrame:
    """Fichier HT Analytics : Station;Date;Time;Température;Level in m;Conductivity in mS/cm (décimales à virgule)."""
    d = pd.read_csv(path, sep=";", encoding="utf-8-sig", decimal=",")
    t = pd.to_datetime(d["Date"].astype(str) + " " + d["Time"].astype(str), format="%d.%m.%Y %H:%M:%S", errors="coerce")
    return pd.DataFrame({"t": t, "level": pd.to_numeric(d["Level in m"], errors="coerce"),
                         "ec": pd.to_numeric(d["Conductivity in mS/cm"], errors="coerce")}).dropna(subset=["t"]).sort_values("t")


def qc(df: pd.DataFrame):
    """Règles 1 à 4 du protocole. Retourne (série nettoyée, décomptes)."""
    d = df.copy().reset_index(drop=True)
    n = {"mesures": len(d)}
    bad = (d.level > LEVEL_MAX) | (d.level < LEVEL_MIN)
    n["hors_bornes"] = int(bad.sum())
    d.loc[bad, "level"] = np.nan
    med = d.set_index("t").level.rolling("7D", center=True, min_periods=1).median().to_numpy()
    spike = (d.level - med).abs() > SPIKE_M
    n["pics"] = int(spike.sum())
    d.loc[spike, "level"] = np.nan
    # règle 3 : sauts durables de la médiane journalière -> segments, on garde le plus long
    x = d.dropna(subset=["level"])
    day = x.groupby(x.t.dt.floor("D"))["level"].median()
    seg = pd.Series(0, index=day.index)
    k, cuts = 0, 0
    vals = day.to_numpy()
    for i in range(1, len(vals)):
        if abs(vals[i] - vals[i - 1]) > JUMP_M:
            after = vals[i:i + JUMP_DAYS]
            if len(after) >= JUMP_DAYS and np.all(np.abs(after - vals[i]) <= JUMP_M):
                k, cuts = k + 1, cuts + 1
        seg.iloc[i] = k
    n["coupures"] = cuts
    if len(seg):
        best = seg.value_counts().idxmax()
        keep_days = set(seg.index[seg == best])
        outside = ~d.t.dt.floor("D").isin(keep_days)
        n["hors_segment"] = int((outside & d.level.notna()).sum())
        d.loc[outside, "level"] = np.nan
    else:
        n["hors_segment"] = 0
    ec_bad = (d.ec <= 0) | (d.ec > EC_MAX_MS)
    n["conductivite_rejetee"] = int(ec_bad.sum())
    d.loc[ec_bad, "ec"] = np.nan
    n["niveaux_gardes"] = int(d.level.notna().sum())
    return d, n


def monthly(d: pd.DataFrame) -> pd.DataFrame:
    """Moyenne mensuelle (règle 5 : au moins MIN_DAYS_MONTH jours avec une mesure valide)."""
    x = d.set_index("t")
    days = x.level.dropna().groupby(x.level.dropna().index.to_period("M")).apply(lambda s: s.index.normalize().nunique())
    lv = x.level.groupby(x.index.to_period("M")).mean()
    ec = x.ec.groupby(x.index.to_period("M")).mean()
    m = pd.DataFrame({"level": lv, "ec_us": ec * 1000.0, "jours": days}).fillna({"jours": 0})
    m.loc[m.jours < MIN_DAYS_MONTH, ["level", "ec_us"]] = np.nan
    return m.dropna(subset=["level"])


def anomalies(m: pd.DataFrame) -> pd.Series:
    """Niveau mensuel moins la moyenne du même mois du calendrier sur la période du site (section 5)."""
    cal = m.index.month
    return m.level - m.level.groupby(cal).transform("mean")


def spearman(a, b):
    from scipy import stats
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < MIN_PAIRS:
        return np.nan, int(ok.sum())
    return float(stats.spearmanr(a[ok], b[ok]).correlation), int(ok.sum())


def sign_test(wins: int, n: int) -> float:
    """p-valeur unilatérale du test du signe (H0 : P(succès) = 1/2)."""
    from scipy import stats
    return float(stats.binomtest(wins, n, 0.5, alternative="greater").pvalue) if n else float("nan")


def analyse_site(name, raw, ind):
    d, counts = qc(raw)
    m = monthly(d)
    res = {"site": name, **counts, "mois_valides": len(m)}
    if len(m):
        res.update(debut=str(m.index.min()), fin=str(m.index.max()), niveau_median_m=round(float(m.level.median()), 2),
                   ce_mediane_us=round(float(m.ec_us.median()), 0) if m.ec_us.notna().any() else np.nan)
    res["retenu"] = len(m) >= MIN_MONTHS
    if not res["retenu"] or ind is None or ind.empty:
        return res
    an = anomalies(m)
    j = pd.DataFrame({"an": an, "lev": m.level, "ec": m.ec_us})
    j.index = j.index.astype(str)
    j = j.join(ind.set_index("mois"), how="left")
    for col in [f"spi{n}" for n in range(1, NMAX + 1)] + ["recharge12_z"]:
        res[f"r_{col}"], res[f"n_{col}"] = spearman(j.an.to_numpy(float), j[col].to_numpy(float))
    res["r_sgi_spi12"], _ = spearman(j.lev.to_numpy(float), j.spi12.to_numpy(float))     # secondaire : cycle compris
    rs = [res[f"r_spi{n}"] for n in range(1, NMAX + 1)]
    if np.isfinite(rs).any():
        res["n_etoile"] = int(np.nanargmax(rs)) + 1
        res["r_n_etoile"] = round(float(np.nanmax(rs)), 3)
    res["r_ce_niveau"], res["n_ce"] = spearman(j.ec.to_numpy(float), j.an.to_numpy(float))
    w = j.loc[(j.index >= "2019-07") & (j.index <= "2022-06")]
    if w.lev.notna().sum() >= 12 and w.spi12.notna().any():
        res["mois_niveau_min_2019_22"] = w.lev.idxmin()
        res["mois_spi12_min_2019_22"] = w.spi12.idxmin()
        a, b = pd.Period(res["mois_niveau_min_2019_22"], "M"), pd.Period(res["mois_spi12_min_2019_22"], "M")
        res["decalage_mois"] = (a - b).n
    return res


def tests(df: pd.DataFrame) -> dict:
    k = df[df.retenu & df.r_spi12.notna()] if "r_spi12" in df else df.iloc[0:0]
    n1, w1 = len(k), int((k.r_spi12 > 0).sum()) if len(k) else 0
    k2 = k[k.r_recharge12_z.notna()] if len(k) else k
    n2, w2 = len(k2), int((k2.r_recharge12_z > k2.r_spi12).sum()) if len(k2) else 0
    return {"H-N1": (w1, n1, sign_test(w1, n1)), "H-N2": (w2, n2, sign_test(w2, n2))}


def report(df: pd.DataFrame, t: dict, raw_dir: str) -> str:
    f = lambda x: "—" if (x is None or (isinstance(x, float) and np.isnan(x))) else (f"{x:.2f}" if isinstance(x, float) else str(x))
    L = ["# Niveaux de nappe MGMERL contre indices du système (protocole M3)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_nappes_mgmerl.py`, selon "
         "`validation/protocole_nappes_mgmerl.md` (fixé avant les calculs). " + ATTRIBUTION + ".", "",
         f"Séries brutes : `{raw_dir}` (hors git). Indices : `data/mdg/nappes_sites_indices.csv`.", "",
         "## Hypothèses fixées à l'avance", "", "| Hypothèse | Sites favorables | Sites testés | p (test du signe unilatéral) | Conclusion |",
         "|---|---|---|---|---|"]
    for h, lab in (("H-N1", "r(SPI-12) > 0"), ("H-N2", "r(recharge12_z) > r(SPI-12)")):
        w, n, p = t[h]
        concl = "soutenue (5 %)" if n and p < 0.05 else ("non testable" if not n else "non soutenue")
        L.append(f"| {h} : {lab} | {w} | {n} | {f(p)} | {concl} |")
    L += ["", "## Par site", "", "| Site | Mois valides | Retenu | r(SPI-12) | r(recharge12_z) | n* | r(n*) | r(CE, niveau) | Décalage sécheresse 2019-2022 (mois) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        g = lambda k: getattr(r, k, np.nan)
        L.append(f"| {r.site} | {g('mois_valides')} | {'oui' if r.retenu else 'non'} | {f(g('r_spi12'))} | {f(g('r_recharge12_z'))} | "
                 f"{f(g('n_etoile'))} | {f(g('r_n_etoile'))} | {f(g('r_ce_niveau'))} | {f(g('decalage_mois'))} |")
    L += ["", "## Contrôle qualité (règles de la section 4)", "",
          "| Site | Mesures | Hors bornes | Pics | Coupures | Hors segment gardé | Conductivité rejetée |", "|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        L.append(f"| {r.site} | {r.mesures} | {r.hors_bornes} | {r.pics} | {r.coupures} | {r.hors_segment} | {r.conductivite_rejetee} |")
    L += ["", "n* : durée de cumul du SPI la mieux corrélée (descriptif, jamais une performance). Corrélations de Spearman sur "
          "les anomalies mensuelles de niveau (cycle saisonnier retiré).", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--raw", default=None)
    args = ap.parse_args()
    raw_dir = args.raw or str(country_data_dir(args.country) / "mgmerl_raw" / "ht_analytics_csv_2025-06")
    files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    if not files:
        raise SystemExit(f"aucune série dans {raw_dir} (téléchargement manuel depuis MGMERL, voir le protocole)")
    ip = country_data_dir(args.country) / "nappes_sites_indices.csv"
    ind_all = pd.read_csv(ip) if ip.exists() else pd.DataFrame(columns=["site", "mois"])
    rows = []
    for fp in files:
        name = os.path.splitext(os.path.basename(fp))[0]
        rows.append(analyse_site(name, load_ht_csv(fp), ind_all[ind_all.site == name]))
    df = pd.DataFrame(rows)
    t = tests(df)
    vd = ROOT / "validation"
    df.round(3).to_csv(vd / "nappes_mgmerl_sites.csv", index=False)
    rel = os.path.relpath(raw_dir, ROOT).replace("\\", "/")
    (vd / "nappes_mgmerl.md").write_text(report(df, t, rel), encoding="utf-8")
    for h, (w, n, p) in t.items():
        print(f"{h} : {w}/{n} sites favorables, p = {p:.3f}")


if __name__ == "__main__":
    main()
