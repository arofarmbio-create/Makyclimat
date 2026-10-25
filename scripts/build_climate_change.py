"""Changement climatique et ENSO : séries saisonnières de pluie (CHIRPS, depuis 1981) par zone.

Pour chaque saison des pluies (ex. novembre à avril) depuis 1982 :
  - cumul de pluie et pourcentage de la normale (1991-2020) ;
  - phase ENSO de la saison (ONI NOAA) : El Niño, La Niña ou neutre.
Résultats :
  - tendance de la pluie saisonnière (points de % de la normale par décennie) et sa significativité ;
  - effet moyen d'un El Niño et d'une La Niña sur la pluie de la saison, par zone ;
  - corrélation pluie / ONI ;
  - série historique par région et district (docs/data/<pays>/history.json), avec la phase ENSO de chaque année.
Écrit : data/<pays>/grids/climate_change.npz, data/<pays>/external/climate.csv (lu par compute_metrics),
        docs/data/<pays>/history.json.
Usage : python scripts/build_climate_change.py --country mdg [--start 1981]   (après connector_enso.py)
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

import enso
from chirps import fetch_array
from common import (DATA_DIR, country_data_dir, country_docs_dir, grid_dir, load_config, read_units, sample_grid,
                    save_grid, write_json)

SIGNIF_P = 0.10


def p_two_sided(t: np.ndarray, df: int) -> np.ndarray:
    try:
        from scipy import stats
        return 2 * stats.t.sf(np.abs(t), df)
    except Exception:  # noqa: BLE001  approximation normale si scipy absent
        return np.array([math.erfc(abs(x) / math.sqrt(2)) if np.isfinite(x) else np.nan for x in np.ravel(t)]).reshape(np.shape(t))


def last_complete_season_year(today: dt.date, end_m: int) -> int:
    return today.year if today.month > end_m else today.year - 1


def load_totals(cfg: dict, y_first: int, y_last: int):
    """Cumul de pluie par saison (clé : année de fin de saison). Saison incomplète -> ignorée."""
    s_m, e_m = cfg["rainfall"]["season_start_month"], cfg["rainfall"]["season_end_month"]
    bbox, tmpl = cfg["map"]["bbox"], cfg["rainfall"]["monthly_url"]
    jobs = sorted({ym for y in range(y_first, y_last + 1) for ym in enso.season_months(y, s_m, e_m)})

    def one(ym):
        try:
            return ym, fetch_array(tmpl.format(y=ym[0], m=ym[1]), bbox)
        except Exception as e:  # noqa: BLE001
            print(f"  échec {ym}: {e}")
            return ym, None

    with ThreadPoolExecutor(max_workers=4) as ex:
        got = dict(ex.map(one, jobs))
    geo, totals, monthly = None, {}, {}
    for y in range(y_first, y_last + 1):
        months = enso.season_months(y, s_m, e_m)
        if any(got.get(ym) is None for ym in months):
            print(f"  saison {y} incomplète : ignorée")
            continue
        arrs = []
        for ym in months:
            a, lon0, lat0, step = got[ym]
            geo = geo or (lon0, lat0, step)
            arrs.append(a)
        st = np.stack(arrs)
        tot = st.sum(axis=0)
        tot[np.isnan(st).any(axis=0)] = np.nan
        totals[y] = tot.astype("float32")
        monthly[y] = st.astype("float32")
    return totals, geo, monthly


def analyse(years, totals, oni_by_year, base, min_norm):
    """Retourne les grilles d'analyse."""
    stack = np.stack([totals[y] for y in years])
    bmask = np.array([base[0] <= y <= base[1] for y in years])
    normal = np.nanmean(stack[bmask], axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(normal > min_norm, stack / normal * 100.0, np.nan)
    n = len(years)
    valid = np.isfinite(ratio).all(axis=0)
    x = np.array(years, dtype="float64")
    xc = x - x.mean()
    r0 = np.where(valid, ratio, 0.0)
    ybar = r0.mean(axis=0)
    sxx = (xc ** 2).sum()
    slope = (xc[:, None, None] * (r0 - ybar)).sum(axis=0) / sxx
    resid = r0 - (ybar + slope * xc[:, None, None])
    se = np.sqrt((resid ** 2).sum(axis=0) / max(n - 2, 1) / sxx)
    with np.errstate(invalid="ignore", divide="ignore"):
        tstat = np.where(se > 0, slope / se, 0.0)
    trend_p = np.where(valid, p_two_sided(tstat, n - 2), np.nan)
    trend = np.where(valid, slope * 10.0, np.nan)  # points de % de la normale par décennie

    o = np.array([oni_by_year[y] for y in years])
    ok = np.isfinite(o)
    oc = o[ok] - o[ok].mean()
    rr = r0[ok]
    rc = rr - rr.mean(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = (oc[:, None, None] * rc).sum(axis=0) / np.sqrt((oc ** 2).sum() * (rc ** 2).sum(axis=0))
    corr = np.where(valid & np.isfinite(corr), corr, np.nan)
    ph = np.array([enso.phase_of(v) for v in o])

    def comp(code):
        sel = (ph == code)
        if sel.sum() < 3:
            return np.full(normal.shape, np.nan, dtype="float32"), int(sel.sum())
        return np.where(valid, ratio[sel].mean(axis=0), np.nan).astype("float32"), int(sel.sum())

    el, n_el = comp("E")
    la, n_la = comp("L")
    ne, n_ne = comp("N")
    return dict(ratio=ratio, trend=trend.astype("float32"), trend_p=trend_p.astype("float32"),
                corr=corr.astype("float32"), el=el, la=la, ne=ne, n_el=n_el, n_la=n_la, n_ne=n_ne, phases=ph, oni=o)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--start", type=int, default=1981)
    args = ap.parse_args()
    cfg = load_config(args.country)
    s_m, e_m = cfg["rainfall"]["season_start_month"], cfg["rainfall"]["season_end_month"]
    min_norm = cfg["rainfall"]["min_normal_mm"]
    base = cfg["rainfall"]["baseline_years"]
    oni_path = DATA_DIR / "enso" / "oni.csv"
    if not oni_path.exists():
        raise SystemExit("data/enso/oni.csv absent : lancer d'abord scripts/connector_enso.py")
    oni = pd.read_csv(oni_path)

    y_last = last_complete_season_year(dt.date.today(), e_m)
    y_first = args.start + (1 if s_m > e_m else 0)
    totals, geo, monthly = load_totals(cfg, y_first, y_last)
    oni_by_year = {y: enso.season_oni(oni, y, s_m, e_m) for y in totals}
    years = sorted(y for y in totals if np.isfinite(oni_by_year[y]))
    if len(years) < 25 or geo is None:
        raise SystemExit(f"Pas assez de saisons complètes ({len(years)}) pour analyser le climat.")
    print(f"{len(years)} saisons ({years[0]}-{years[-1]}) ; phases :",
          {c: sum(1 for y in years if enso.phase_of(oni_by_year[y]) == c) for c in "ELN"})
    res = analyse(years, totals, oni_by_year, base, min_norm)
    lon0, lat0, step = geo
    save_grid(grid_dir(args.country) / "climate_change.npz",
              trend=res["trend"], trend_p=res["trend_p"], corr=res["corr"], el=res["el"], la=res["la"], ne=res["ne"],
              years=np.array(years), oni=res["oni"], lon0=np.array(lon0), lat0=np.array(lat0), res=np.array(step))

    # série mensuelle de chaque saison (sert aux scénarios de fin de saison) : float16 pour limiter la taille
    save_grid(grid_dir(args.country) / "monthly_series.npz",
              arr=np.stack([monthly[y] for y in years]).astype("float16"),
              months=np.array([m for _, m in enso.season_months(years[-1], s_m, e_m)]),
              years=np.array(years), phases=np.array(res["phases"]), oni=res["oni"].astype("float32"),
              lon0=np.array(lon0), lat0=np.array(lat0), res=np.array(step))

    units = read_units(args.country)
    leaves = units[units.level == units.level.max()]
    lon, lat = leaves.lon.to_numpy(), leaves.lat.to_numpy()

    def samp(g):
        return sample_grid(g, lon0, lat0, step, lon, lat)

    vals = {"rain_trend_pct_decade": samp(res["trend"]), "enso_el_pct": samp(res["el"]), "enso_la_pct": samp(res["la"]),
            "enso_corr": samp(res["corr"])}
    pv = samp(res["trend_p"])
    vals["rain_trend_signif_share"] = np.where(np.isfinite(pv), np.where(pv < SIGNIF_P, 100.0, 0.0), np.nan)
    date = f"{years[-1]}-{e_m:02d}-28"
    src = f"CHIRPS v2.0 {years[0]}-{years[-1]} ; ONI NOAA"
    rows = []
    for ind, v in vals.items():
        for pc, x in zip(leaves.pcode, v):
            if np.isfinite(x):
                rows.append((pc, ind, round(float(x), 3), date, src))
    dest = country_data_dir(args.country) / "external"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["pcode", "indicateur", "valeur", "date", "source"]).to_csv(dest / "climate.csv", index=False)

    # séries historiques (régions et districts) avec la phase ENSO de chaque saison
    d2 = units[units.level == 2]
    ser = res["ratio"]
    series = {}
    for pc, lo, la_ in zip(d2.pcode, d2.lon, d2.lat):
        v = np.array([sample_grid(ser[i], lon0, lat0, step, np.array([lo]), np.array([la_]))[0] for i in range(len(years))])
        series[pc] = [None if not np.isfinite(x) else int(round(float(x))) for x in v]
    pop = dict(zip(units.pcode, units["pop"].fillna(0)))
    for pc in units[units.level == 1].pcode:
        kids = [k for k in d2[d2.adm1 == pc].pcode if any(x is not None for x in series.get(k, []))]
        row = []
        for i in range(len(years)):
            pts = [(series[k][i], pop.get(k, 0)) for k in kids if series[k][i] is not None]
            w = sum(p for _, p in pts)
            row.append(None if not pts else int(round(sum(v * p for v, p in pts) / w if w > 0 else sum(v for v, _ in pts) / len(pts))))
        series[pc] = row
    write_json(country_docs_dir(args.country) / "history.json", {
        "season": f"{s_m:02d}-{e_m:02d}", "years": years,
        "oni": [round(float(res["oni"][i]), 2) for i in range(len(years))],
        "phases": list(res["phases"]), "counts": {"E": res["n_el"], "L": res["n_la"], "N": res["n_ne"]},
        "baseline": base, "series": series})
    print(f"Écrit : {len(rows)} valeurs au niveau fin, {len(series)} séries ; "
          f"{res['n_el']} saisons El Niño, {res['n_la']} La Niña, {res['n_ne']} neutres.")


if __name__ == "__main__":
    main()
