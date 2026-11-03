"""E1, section 6.3 (validation/protocole_e1_fusion_pluie.md, précisions du 03/11/2026) : chaque version de la pluie
(CHIRPS, IMERG Late, ERA5-Land, B, C) rejouée dans les tests d'impact déjà établis.

1. Inondations pluviales du périmètre pilote : même code que R-09 (validate_pluvial.main), pluie de la version à la
   maille de 0,1° du fokontany ; seuils locaux tirés de la même version sur les saisons 2001-2002 à 2014-2015 ;
   évaluation sur 2016-2017 à 2024-2025 (événements détectés, épisodes sans correspondance, AUC des communes EMS).
2. Sécheresse du Grand Sud : SPI-3 et SPI-12 régionaux (soilwater_core.spi, référence 2001-2025) ; minimum de juillet
   2019 à juin 2023 et rang parmi les régions (1 = la plus sèche), comme R-14.
Descriptif. Seules les mailles de 0,1° qui portent un fokontany sont chargées (mémoire).
Entrées : data/<pays>/e1/{chirps,imerg,era5}_AAAA.npz et e1_tc.npz (release « e1-pluie »).
Sorties : validation/e1_impacts.md et e1_impacts.csv.
Usage : python scripts/validate_e1_impacts.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import soilwater_core as SC
import validate_e1 as E
from common import ROOT, country_data_dir, load_config, read_units

VERSIONS = ("chirps", "imerg", "era5", "B", "C")
GRAND_SUD = ("Androy", "Anosy", "Atsimo Andrefana")
DROUGHT = ("2019-07", "2023-06")
FIRST_TEST_SEASON, LAST_TRAIN_SEASON = 2016, 2014        # saison y = novembre y à avril y+1


# ---------------- versions journalières ----------------
def daily_versions(dates: pd.DatetimeIndex, raw: dict, weights: np.ndarray) -> dict:
    """raw : {source: (jours, cellules)}. B : moyenne simple ; C : sources ramenées aux moments journaliers de CHIRPS par
    mois du calendrier sur 2001-2015, pondérées par les poids de la triple collocation."""
    month = dates.month.to_numpy()
    train = np.asarray((dates.year >= E.TRAIN[0]) & (dates.year <= E.TRAIN[1]))
    R = {s: (raw[s] if s == "chirps" else E.rescale_to_ref(raw[s], raw["chirps"], month, train)) for s in E.SOURCES}
    out = {s: raw[s] for s in E.SOURCES}
    out["B"] = E.merge([raw[s] for s in E.SOURCES], np.ones_like(weights))
    out["C"] = E.merge([R[s] for s in E.SOURCES], weights)
    return out


# ---------------- inondations ----------------
def rx3_seasons(dates: pd.DatetimeIndex, P: np.ndarray, first: int, last: int) -> np.ndarray:
    """Maximum saisonnier (novembre à avril) de la pluie sur 3 jours, saisons first..last ; (saisons, points)."""
    p3 = pd.DataFrame(P, index=dates).rolling(3, min_periods=3).sum()
    rows = []
    for y in range(first, last + 1):
        w = p3.loc[f"{y}-11-01":f"{y + 1}-04-30"]
        rows.append(w.max(axis=0, skipna=True).to_numpy() if len(w) else np.full(P.shape[1], np.nan))
    return np.array(rows)


def flood_scores(country, dates, P_leaf: np.ndarray, workdir: Path) -> dict:
    """Rejoue validate_pluvial.main avec la pluie donnée (jours, fokontany du périmètre, dans l'ordre de validate_pluvial)."""
    import validate_pluvial as VP
    index = {d.date(): i for i, d in enumerate(dates)}

    def fetch(days, lons, lats, bbox):
        return np.array([P_leaf[index[d]] if d in index else np.full(P_leaf.shape[1], np.nan) for d in days])

    rx3 = rx3_seasons(dates, P_leaf, E.TRAIN[0], LAST_TRAIN_SEASON)
    val = workdir / "val"
    val.mkdir(exist_ok=True)
    for f in ("evenements.csv", "evenements_gdacs.csv", "ems_communes_oof.csv"):
        if (VP.VAL / f).exists():
            shutil.copy(VP.VAL / f, val / f)
    old_val, old_md = VP.VAL, VP.write_md
    VP.VAL, VP.write_md = val, (lambda *a, **k: None)
    try:
        res = VP.main(country, fetch=fetch, rx3=rx3, today=dt.date(2025, 6, 1), cache_path=workdir / "cache.npz",
                      first_season=FIRST_TEST_SEASON)
    finally:
        VP.VAL, VP.write_md = old_val, old_md
    o = res["ind"]["pluie"]
    det, epi, ems = o["detection"], o["episodes"], o["ems"]
    none = ((epi.evenement_perimetre == "") & (epi.evenement_ailleurs == "") & (epi.evenement_gdacs == "")) if len(epi) else pd.Series([], dtype=bool)
    return {"evenements": len(det), "detectes": int(det.detecte_vigilance.sum()) if len(det) else 0, "episodes": len(epi),
            "episodes_sans_correspondance": int(none.sum()),
            "auc_ems": ";".join(f"{a:.2f}" for a in ems.auc.dropna()) if len(ems) else "—"}


# ---------------- sécheresse ----------------
def monthly_by_region(dates, P: np.ndarray, cell_region: np.ndarray) -> pd.DataFrame:
    """P (jours, cellules) -> pluie mensuelle moyenne par région (mois, régions) ; mois incomplet -> NaN."""
    df = pd.DataFrame(P, index=dates)
    m = df.resample("MS").sum(min_count=1)
    n_days = df.notna().resample("MS").sum()
    expected = pd.Series(dates.days_in_month, index=dates).resample("MS").first()
    m = m.where(n_days.eq(expected, axis=0))
    regs = sorted(set(cell_region) - {""})
    return pd.DataFrame({r: m.loc[:, cell_region == r].mean(axis=1) for r in regs}, index=m.index.strftime("%Y-%m"))


def drought_ranks(M: pd.DataFrame, n: int, regions=GRAND_SUD, period=DROUGHT, min_mean_mm=None) -> dict:
    """min_mean_mm : seuil de normale minimale de la production (config du pays), comme le SPI publié."""
    z = pd.DataFrame(SC.spi(M.to_numpy(), n, int(M.index[0][5:7]), min_mean_mm=min_mean_mm), index=M.index, columns=M.columns)
    mn = z.loc[period[0]:period[1]].min()
    rank = mn.rank(method="min")
    return {r: (float(mn[r]), int(rank[r])) for r in regions if r in mn.index}


def report(fl: pd.DataFrame, dr: pd.DataFrame, n_regions: int) -> str:
    L = ["# E1, section 6.3 : les versions de la pluie face aux impacts", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_e1_impacts.py`, selon "
         "`validation/protocole_e1_fusion_pluie.md` (précisions du 03/11/2026, fixées avant ce calcul). Descriptif : peu "
         "d'événements, aucun test de signification.", "",
         "## Inondations pluviales du périmètre pilote (pluie sur 3 jours, seuils locaux de 2001-2015, saisons 2016-2017 à 2024-2025)", "",
         "| Version | Événements détectés | Épisodes | Épisodes sans correspondance | AUC des communes EMS |", "|---|---|---|---|---|"]
    for r in fl.itertuples():
        L.append(f"| {r.version} | {r.detectes} / {r.evenements} | {r.episodes} | {r.episodes_sans_correspondance} | {r.auc_ems} |")
    L += ["", f"## Sécheresse du Grand Sud ({DROUGHT[0]} à {DROUGHT[1]}) : SPI minimum et rang parmi {n_regions} régions (1 = la plus sèche)", "",
          "| Version | Indice | " + " | ".join(GRAND_SUD) + " |", "|---|---|" + "---|" * len(GRAND_SUD)]
    for r in dr.itertuples():
        L.append(f"| {r.version} | {r.indice} | " + " | ".join(getattr(r, f"r{i}") for i in range(len(GRAND_SUD))) + " |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    e1 = country_data_dir(args.country) / "e1"
    units = read_units(args.country)
    leaves = units[units.level == 4].reset_index(drop=True)
    names = dict(zip(units.pcode, units.name))
    ii = np.abs(E.LATS[None, :] - leaves.lat.to_numpy()[:, None]).argmin(1)
    jj = np.abs(E.LONS[None, :] - leaves.lon.to_numpy()[:, None]).argmin(1)
    cells, leaf_cell = np.unique(ii * len(E.LONS) + jj, return_inverse=True)      # mailles utiles seulement (mémoire)
    cell_region = np.full(len(cells), "", dtype=object)
    cell_region[leaf_cell] = [names.get(a, "") for a in leaves.adm1]
    years = range(E.TRAIN[0], E.TEST[1] + 1)
    loaded = {s: E.load_daily(e1, s, years) for s in E.SOURCES}
    common = loaded["chirps"][0]
    for s in E.SOURCES[1:]:
        common = common.intersection(loaded[s][0])
    raw = {}
    for s in E.SOURCES:
        d, a = loaded.pop(s)
        raw[s] = a[np.isin(d, common)].reshape(-1, len(E.LATS) * len(E.LONS))[:, cells].astype("float32")
        del a
    tc = np.load(e1 / "e1_tc.npz", allow_pickle=True)
    w = tc["poids"].reshape(len(E.SOURCES), -1)[:, cells].astype(float)
    V = daily_versions(common, raw, w)
    th = pd.read_csv(country_data_dir(args.country) / "flood_thresholds.csv", dtype={"pcode": str})
    pilot = leaves.adm3.isin(set(th[np.isfinite(th.q2)].pcode)).to_numpy()
    min_mm = float(load_config(args.country)["rainfall"].get("min_normal_mm", 25))
    fl, dr = [], []
    for v in VERSIONS:
        print(f"E1 impacts : {v}", flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            fl.append({"version": v, **flood_scores(args.country, common, V[v][:, leaf_cell[pilot]], Path(tmp))})
        M = monthly_by_region(common, V[v], cell_region)
        for n in (3, 12):
            r = drought_ranks(M, n, min_mean_mm=min_mm)
            dr.append({"version": v, "indice": f"SPI-{n}", **{f"r{i}": (f"{r[g][0]:+.2f} (rang {r[g][1]})" if g in r else "—")
                                                               for i, g in enumerate(GRAND_SUD)}})
    fl, dr = pd.DataFrame(fl), pd.DataFrame(dr)
    vd = ROOT / "validation"
    (vd / "e1_impacts.md").write_text(report(fl, dr, int(len(set(cell_region) - {""}))), encoding="utf-8")
    pd.concat([fl, dr], ignore_index=True).to_csv(vd / "e1_impacts.csv", index=False)
    print("E1 impacts : rapport écrit dans validation/e1_impacts.md")


if __name__ == "__main__":
    main()
