"""Test H-C6 du protocole de la carte des nappes (section 10 et précisions du 02/11/2026) : la recharge transférée
depuis les 134 sites africains du BGS vers Madagascar concorde-t-elle avec les références malgaches indépendantes ?

Version retenue (choisie sur H-C5) : T2, 5 analogues selon la distance de Gower ; T1 (ridge) et T0 (carte BGS) sont
publiées en comparaison. Intervalle de 80 % : prédiction + 10e et 90e centiles des résidus obtenus en laissant un pays
de côté. Domaine d'applicabilité : une maille dont l'analogue le plus proche est plus loin que le 95e centile des
distances au plus proche voisin entre sites africains est marquée « extrapolation ».
Références : (1) Sud de Madagascar 20-100 mm/an (BRGM 2005) ; (2) plateau Mahafaly environ 60 mm/an ; (3) sites de
nappe MGMERL retenus en M3, recharge par fluctuation de nappe R = Sy × remontées de saison des pluies.
Entrées : data/<pays>/nappes_mondiales/covariables_hc6.csv (agent de téléchargement), base BGS (hors git), séries
MGMERL (hors git). Sorties : validation/transfert_recharge_hc6.md, data/<pays>/nappes_mondiales/recharge_transferee.csv.
Usage : python scripts/validate_transfert_madagascar.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import os

import numpy as np
import pandas as pd

import validate_transfert_recharge as T
from common import ROOT, country_data_dir

SOUTH_LAT = -23.0
SY = {"Basement": (0.01, 0.05), "Sedimentary": (0.05, 0.15), "Unconsolidated": (0.05, 0.15)}
LIT_REFS = [("Sud de Madagascar (BRGM 2005, cité par AVSF 2016)", 20.0, 100.0), ("Plateau Mahafaly (profil USAID/Winrock)", 60.0, 60.0)]


def loco_residuals(df: pd.DataFrame) -> dict:
    """Résidus site par site (observé − prédit, log10(R + 1)) en laissant chaque pays de côté, pour T1 et T2."""
    y = T.target(df.Recharge_mmpa)
    r1, r2 = np.full(len(df), np.nan), np.full(len(df), np.nan)
    for c in df.Country.unique():
        te = (df.Country == c).to_numpy()
        tr = ~te
        xtr, xte = T.design(df[tr], df[te])
        r1[te] = y[te] - T.ridge_predict(xtr, y[tr], xte)
        r2[te] = y[te] - T.knn_predict(df[tr], y[tr], df[te])
    return {"T1": r1, "T2": r2}


def nn_threshold(df: pd.DataFrame) -> float:
    """95e centile des distances de Gower au plus proche autre site africain."""
    d = T.gower(df, df)
    np.fill_diagonal(d, np.inf)
    return float(np.percentile(d.min(axis=1), 95))


def predict(df_af: pd.DataFrame, cov: pd.DataFrame, res: dict) -> pd.DataFrame:
    y = T.target(df_af.Recharge_mmpa)
    xtr, xte = T.design(df_af, cov)
    out = cov.copy()
    preds = {"T1": T.ridge_predict(xtr, y, xte), "T2": T.knn_predict(df_af, y, cov)}
    for v, p in preds.items():
        lo, hi = np.nanpercentile(res[v], [10, 90])
        out[f"{v}_mmpa"] = 10 ** p - 1
        out[f"{v}_bas_mmpa"] = np.maximum(10 ** (p + lo) - 1, 0)
        out[f"{v}_haut_mmpa"] = 10 ** (p + hi) - 1
    dmin = T.gower(df_af, cov).min(axis=1)
    out["distance_analogue"] = dmin
    out["extrapolation"] = dmin > nn_threshold(df_af)
    return out


def wtf_recharge(levels: pd.Series, sy: float) -> float:
    """Recharge annuelle moyenne (mm/an) par fluctuation de nappe : Sy × somme des remontées mensuelles de novembre à
    avril (niveau en m, profondeur négative), moyennée sur les saisons complètes."""
    m = levels.dropna()
    if m.empty:
        return np.nan
    rise = m.diff().clip(lower=0)
    wet = rise[rise.index.month.isin([11, 12, 1, 2, 3, 4])]
    season = wet.index.year + (wet.index.month >= 11)
    per = wet.groupby(season).agg(["sum", "count"])
    per = per[per["count"] >= 4]
    return float(sy * per["sum"].mean() * 1000) if len(per) else np.nan


def site_references(country: str, cov: pd.DataFrame) -> list[tuple]:
    import validate_nappes_mgmerl as N
    raw_dir = country_data_dir(country) / "mgmerl_raw" / "ht_analytics_csv_2025-06"
    sites = pd.read_csv(ROOT / "inputs" / "mgmerl" / "mgmerl_dataloggers_ht_analytics_sites.csv")
    refs = []
    for fp in sorted(glob.glob(os.path.join(raw_dir, "*.csv"))):
        name = os.path.splitext(os.path.basename(fp))[0]
        s = sites[sites.site == name]
        if s.empty:
            continue
        d, _ = N.qc(N.load_ht_csv(fp))
        m = N.monthly(d)
        if len(m) < N.MIN_MONTHS:
            continue
        lv = m.level.copy()
        lv.index = lv.index.to_timestamp()
        i = int(np.argmin((cov.lon - float(s.lon.iloc[0])) ** 2 + (cov.lat - float(s.lat.iloc[0])) ** 2))
        grp = cov.Aquifer_group.iloc[i]
        lo, hi = SY.get(grp, SY["Basement"])
        a, b = wtf_recharge(lv, lo), wtf_recharge(lv, hi)
        refs.append((f"Site MGMERL {name} ({grp}, fluctuation de nappe)", a, b, i))
    return refs


def evaluate(pred: pd.DataFrame, version: str, refs: list[tuple]) -> pd.DataFrame:
    rows = []
    south = pred[pred.lat < SOUTH_LAT]
    maha = pred[pred.get("GLG", pd.Series("", index=pred.index)).astype(str).str.contains("Eocene|Éocène|limestone|calcaire", case=False, regex=True)]
    for name, lo, hi in LIT_REFS:
        zone = south if "Sud" in name else maha
        if zone.empty:
            rows.append({"reference": name, "valeur_centrale_mmpa": (lo + hi) / 2, "mailles": 0, "dans_intervalle": np.nan})
            continue
        b, h = zone[f"{version}_bas_mmpa"].median(), zone[f"{version}_haut_mmpa"].median()
        c = (lo + hi) / 2
        rows.append({"reference": name, "valeur_centrale_mmpa": c, "mailles": len(zone), "intervalle_bas": b,
                     "intervalle_haut": h, "prediction_mediane": zone[f"{version}_mmpa"].median(), "dans_intervalle": bool(b <= c <= h)})
    for name, lo, hi, i in refs:
        c = (lo + hi) / 2
        b, h = pred[f"{version}_bas_mmpa"].iloc[i], pred[f"{version}_haut_mmpa"].iloc[i]
        rows.append({"reference": name, "valeur_centrale_mmpa": c, "mailles": 1, "intervalle_bas": b, "intervalle_haut": h,
                     "prediction_mediane": pred[f"{version}_mmpa"].iloc[i], "dans_intervalle": bool(b <= c <= h) if np.isfinite(c) else np.nan})
    return pd.DataFrame(rows)


def report(pred, ev, version) -> str:
    f = lambda x: "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else (f"{x:.0f}" if isinstance(x, float) else str(x))
    ok = ev.dans_intervalle.dropna()
    share = float(ok.mean()) if len(ok) else float("nan")
    L = ["# H-C6 : recharge transférée à Madagascar contre les références malgaches", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_transfert_madagascar.py`, selon "
         "`validation/protocole_carte_nappes.md` (section 10 et précisions du 02/11/2026, fixées avant le calcul). Base "
         "africaine : MacDonald et al. (2021) ; séries de nappe : MGMERL.", "",
         f"Version retenue (choisie sur H-C5) : **{version}**. Mailles : {len(pred)} ; en extrapolation (aucun analogue "
         f"proche) : {int(pred.extrapolation.sum())}.", "",
         "| Carte | Médiane (mm/an) | Grand Sud, au sud de 23°S (mm/an) | Nord (mm/an) |", "|---|---|---|---|"]
    for col, lab in (("recharge_bgs_mmpa", "T0 (carte BGS)"), ("T1_mmpa", "T1 (ridge)"), ("T2_mmpa", "T2 (analogues)")):
        if col in pred:
            L.append(f"| {lab} | {f(pred[col].median())} | {f(pred[pred.lat < SOUTH_LAT][col].median())} | "
                     f"{f(pred[pred.lat >= -20][col].median())} |")
    L += ["", "## Références malgaches", "",
          "| Référence | Valeur centrale | Prédiction | Intervalle de 80 % | Dans l'intervalle |", "|---|---|---|---|---|"]
    for r in ev.itertuples():
        L.append(f"| {r.reference} | {f(r.valeur_centrale_mmpa)} | {f(getattr(r, 'prediction_mediane', np.nan))} | "
                 f"{f(getattr(r, 'intervalle_bas', np.nan))} à {f(getattr(r, 'intervalle_haut', np.nan))} | "
                 f"{'oui' if r.dans_intervalle is True else ('non' if r.dans_intervalle is False else '—')} |")
    L += ["", f"**Part des références dans l'intervalle : {share:.0%} ({int(ok.sum())} sur {len(ok)}). H-C6 "
          f"{'confirmée (seuil de 60 %)' if share >= 0.6 else 'non confirmée'}.** Avec si peu de références, le résultat "
          "reste indicatif.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    base = country_data_dir(args.country)
    af = pd.read_excel(base / "bgs_recharge_raw" / "Recharge_data_Africa_BGS.xlsx", sheet_name="data").dropna(
        subset=["Recharge_mmpa"] + T.NUM + T.CAT_T2)
    cov = pd.read_csv(base / "nappes_mondiales" / "covariables_hc6.csv").dropna(subset=T.NUM + T.CAT_T2).reset_index(drop=True)
    res = loco_residuals(af)
    pred = predict(af, cov, res)
    refs = site_references(args.country, pred)
    ev = evaluate(pred, "T2", refs)
    (ROOT / "validation" / "transfert_recharge_hc6.md").write_text(report(pred, ev, "T2"), encoding="utf-8")
    ev.to_csv(ROOT / "validation" / "transfert_recharge_hc6_references.csv", index=False)
    pred.round(4).to_csv(base / "nappes_mondiales" / "recharge_transferee.csv", index=False)
    print(report(pred, ev, "T2"))


if __name__ == "__main__":
    main()
