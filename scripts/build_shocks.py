"""Indicateurs de CHOC au format JIAF 2.0 (IASC), pour chaque fokontany : intensité, proximité, tendance.

Le manuel JIAF 2 (Tableau de référence 1) demande, pour chaque zone, l'intensité et la proximité des « dangers naturels » et des
« chocs agroécologiques », avec la tendance (stable / en hausse / en baisse). Il donne comme seuls exemples de mesure la catégorie du
cyclone et les millimètres de pluie. MakyClimat les calcule au niveau le plus fin avec des mesures normalisées, reproductibles partout :

  CYCLONE
    vent_classe_kt   plus fort rayon de vent publié (JTWC via IBTrACS, 4 quadrants, interpolé) qui a atteint le fokontany :
                     0 = aucun, 34 = tempête tropicale, 50 = vent fort, 64 = force cyclone (échelle Saffir-Simpson / RSMC La Réunion).
                     Un fokontany est « atteint » si une position (interpolée) a son rayon de vent couvrant le centroïde.
    dist_min_km      distance minimale entre le centroïde et la trajectoire (proximité, km)
    date_passage     date du passage au plus près (proximité dans le temps ; la tendance se lit en comparant les passages successifs)
    rx3_mm           cumul maximal de pluie sur 3 jours (CHIRPS) pendant le passage
    periode_retour   période de retour LOCALE (ans) de ce cumul, d'après les maxima annuels 2006-2020 du fokontany
Le même format sert d'autres aléas (sécheresse : SPI de l'OMM ; crue : débit/période de retour) : voir le brouillon docs/JIAF.md.

Limites : exposition au vent publié, pas dégâts ; rayons de vent absents pour une partie des positions (valeur médiane du système utilisée
pour 34 kt, sinon pas de classe 50/64) ; la proximité est mesurée au centroïde ; la pluie n'est pas spatialisée finement (CHIRPS 0,05 deg).
Usage : python scripts/build_shocks.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

from common import DATA_DIR, grid_dir, load_config, read_units

VAL_DIR = DATA_DIR.parent / "validation"
CLASSES = {0: "aucun vent de tempête", 34: "tempête tropicale (≥ 34 kt)", 50: "vent fort (≥ 50 kt)", 64: "force cyclone (≥ 64 kt)"}


def wind_class(cov: dict) -> np.ndarray:
    """Classe de vent la plus forte atteinte : 0, 34, 50 ou 64 kt."""
    out = np.zeros(len(cov[34]), dtype=int)
    for k in (34, 50, 64):
        out[cov[k]] = k
    return out


def _quad_cols(k):
    return [f"USA_R{k}_{q}" for q in ("NE", "SE", "SW", "NW")]


def fit_ratios(d: pd.DataFrame):
    """Rapport empirique R50/R34 et R64/R34 en fonction du vent maximal (kt, 1 min), appris sur les positions où le JTWC a publié les rayons :
    log(R_k / R34) = a + b * vent, par régression des moindres carrés sur toutes les paires quadrant/position à rayons > 0.
    Retourne {k: (a, b, écart-type résiduel, n)}."""
    out = {}
    v = pd.to_numeric(d["USA_WIND"], errors="coerce").values
    r34 = np.column_stack([pd.to_numeric(d[c], errors="coerce").values for c in _quad_cols(34)])
    for k in (50, 64):
        rk = np.column_stack([pd.to_numeric(d[c], errors="coerce").values for c in _quad_cols(k)])
        m = np.isfinite(rk) & np.isfinite(r34) & (rk > 0) & (r34 > 0) & np.isfinite(v)[:, None]
        vv = np.repeat(v[:, None], 4, axis=1)[m]
        y = np.log(rk[m] / r34[m])
        A = np.c_[np.ones(len(vv)), vv]
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        out[k] = (float(coef[0]), float(coef[1]), float(np.std(y - A @ coef)), int(len(vv)))
    return out


def fill_radii(g: pd.DataFrame, ratios: dict) -> tuple[pd.DataFrame, int]:
    """Complète R50/R64 absents (aucun quadrant publié) quand le vent maximal atteint ce seuil, avec le rapport empirique à R34.
    Le rayon estimé ne dépasse jamais R34. Retourne (tableau complété, nombre de positions complétées)."""
    g = g.copy()
    n = 0
    v = pd.to_numeric(g["USA_WIND"], errors="coerce").values
    r34 = np.column_stack([pd.to_numeric(g[c], errors="coerce").values for c in _quad_cols(34)])
    for k in (50, 64):
        cols = _quad_cols(k)
        rk = np.column_stack([pd.to_numeric(g[c], errors="coerce").values for c in cols])
        miss = ~np.isfinite(rk).any(axis=1) & np.isfinite(v) & (v >= k) & np.isfinite(r34).any(axis=1)
        a, b, _, _ = ratios[k]
        est = np.minimum(r34 * np.exp(a + b * v[:, None]), r34)
        if k == 64:                                     # R64 <= R50 (valeurs déjà complétées ou publiées)
            r50 = np.column_stack([pd.to_numeric(g[c], errors="coerce").values for c in _quad_cols(50)])
            est = np.where(np.isfinite(r50), np.minimum(est, r50), est)
        for j, c in enumerate(cols):
            col = pd.to_numeric(g[c], errors="coerce").values.copy()
            col[miss] = est[miss, j]
            g[c] = col
        n += int(miss.sum())
    return g, n


def track_distance(xc, yc, tt, X, Y, substeps=6):
    """Distance minimale (km) de chaque point (X, Y) à la trajectoire polygonale (xc, yc) et instant du passage au plus près.
    tt : instants (datetime64) des positions ; l'instant est interpolé linéairement le long du segment."""
    best = np.full(len(X), np.inf)
    when = np.zeros(len(X), dtype="datetime64[s]")
    t = tt.astype("datetime64[s]").astype("int64")
    for i in range(len(xc) - 1):
        for f in np.linspace(0, 1, substeps, endpoint=False):
            x0, y0 = xc[i] * (1 - f) + xc[i + 1] * f, yc[i] * (1 - f) + yc[i + 1] * f
            d = np.hypot(X - x0, Y - y0)
            m = d < best
            best[m] = d[m]
            when[m] = np.int64(t[i] * (1 - f) + t[i + 1] * f).astype("datetime64[s]")
    d = np.hypot(X - xc[-1], Y - yc[-1])
    m = d < best
    best[m] = d[m]
    when[m] = t[-1].astype("datetime64[s]")
    return best, when


def analyse(g, leaves, LX, LY, tree, ratios, bbox, annual, sampler, label, max_km=300.0):
    """Une trajectoire (positions IBTrACS) -> tableau par fokontany ; (None, sampler) si le système n'approche pas le territoire."""
    from chirps_daily import days_between, leaf_series, roll3_max
    from validate_events import footprint, project
    x, y = project(g.LON.values, g.LAT.values)
    dist, _ = tree.query(np.c_[x, y])
    near = g[dist <= 400]
    if near.empty:
        return None, sampler, {}
    gg = g[(g.time >= near.time.min() - pd.Timedelta(hours=12)) & (g.time <= near.time.max() + pd.Timedelta(hours=12))].reset_index(drop=True)
    gg, filled = fill_radii(gg, ratios)
    cov, miss, n34 = footprint(gg, leaves.lon.values, leaves.lat.values)
    cls = wind_class(cov)
    xc, yc = project(gg.LON.values, gg.LAT.values)
    dmin, when = track_distance(xc, yc, gg.time.values, LX, LY)
    rx3 = rp = np.full(len(leaves), np.nan)
    try:
        days = days_between(near.time.min().date() - dt.timedelta(days=1), near.time.max().date() + dt.timedelta(days=1))
        v, sampler = leaf_series(days, bbox, leaves.lon.values, leaves.lat.values, sampler)
        if np.isnan(v).all(axis=1).any():
            raise RuntimeError("jour de pluie absent")
        rx3 = roll3_max(v)
        if annual is not None:
            N = annual.shape[0]
            rp = (N + 1) / (1 + (annual >= rx3[None, :]).sum(axis=0))
    except Exception as ex:  # noqa: BLE001
        print("pluie indisponible", label, ex)
    keep = (dmin <= max_km) | (cls > 0)
    df = pd.DataFrame({"evenement": label, "pcode": leaves.pcode.values, "vent_classe_kt": cls, "dist_min_km": np.round(dmin, 1),
                       "date_passage": pd.to_datetime(when).strftime("%Y-%m-%d"), "rx3_mm": np.round(rx3, 0), "periode_retour_ans": np.round(rp, 1)})[keep]
    info = {"miss": miss, "n34": n34, "filled": filled, "n_keep": int(keep.sum()), "cls": cls, "rx3_ok": bool(np.isfinite(rx3).any())}
    return df, sampler, info


def rollup(leaves: pd.DataFrame, df: pd.DataFrame, today: str, source: str) -> pd.DataFrame:
    """Valeurs au fokontany, puis cumul vers commune, district et région : vent max, distance min, période de retour max, nombre de systèmes."""
    a = df.groupby("pcode").agg(choc_cyc_vent_kt=("vent_classe_kt", "max"), choc_cyc_dist_km=("dist_min_km", "min"),
                                choc_cyc_retour_ans=("periode_retour_ans", "max"), choc_cyc_nb=("evenement", "nunique"))
    a["choc_cyc_dernier_jours"] = (pd.Timestamp(today) - pd.to_datetime(df.groupby("pcode")["date_passage"].max())).dt.days
    t = leaves[["pcode", "adm1", "adm2", "adm3"]].merge(a, left_on="pcode", right_index=True, how="inner")
    ops = {"choc_cyc_vent_kt": "max", "choc_cyc_dist_km": "min", "choc_cyc_retour_ans": "max", "choc_cyc_nb": "max", "choc_cyc_dernier_jours": "min"}
    parts = [a.reset_index()]
    for col in ("adm3", "adm2", "adm1"):
        parts.append(t.groupby(col).agg(ops).reset_index().rename(columns={col: "pcode"}))
    allv = pd.concat(parts).drop_duplicates("pcode")
    m = allv.melt(id_vars="pcode", var_name="indicateur", value_name="valeur").dropna()
    m["date"], m["source"] = today, source
    return m[["pcode", "indicateur", "valeur", "date", "source"]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--max-km", type=float, default=300.0)
    ap.add_argument("--recent", action="store_true", help="systèmes des 12 derniers mois -> data/<pays>/external/chocs.csv (pour le site)")
    args = ap.parse_args()
    from common import country_data_dir
    from scipy.spatial import cKDTree
    from validate_events import fetch_ibtracs, project
    full = load_config(args.country)
    bbox = full["map"]["bbox"]
    units = read_units(args.country)
    leaves = units[units.level == 4].reset_index(drop=True)
    annual = None
    p = grid_dir(args.country) / "rx3_annual.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        if (z["codes"].astype(str) == leaves.pcode.values).all():
            annual = z["rx3"]
    d_all = fetch_ibtracs(since=2000)
    ratios = fit_ratios(d_all)
    for k, (a, b, sd, n) in ratios.items():
        print(f"rapport R{k}/R34 = exp({a:.3f} + {b:.4f} x vent), écart-type résiduel {sd:.2f} (log), n = {n}")
    LX, LY = project(leaves.lon.values, leaves.lat.values)
    tree = cKDTree(np.c_[LX, LY])
    sampler, out, summ = None, [], []
    pop = leaves["pop"].fillna(0).values
    if args.recent:
        since = pd.Timestamp.today() - pd.Timedelta(days=365)
        recent = d_all[d_all.time >= since]
        systems = [(f"{r.nom}-{r.time.year}", d_all[d_all.SID == sid].reset_index(drop=True)) for sid, r in recent.groupby("SID").first().iterrows()]
    else:
        ev = pd.read_csv(VAL_DIR / "evenements.csv")
        systems = []
        for _, e in ev[ev.type == "cyclone"].iterrows():
            yr = int(str(e.date_debut)[:4])
            g = d_all[(d_all.nom == e.nom) & (d_all.time.dt.year.isin([yr, yr + 1]))]
            if g.empty:
                print("trajectoire introuvable", e.id)
                continue
            systems.append((e.id, g[g.SID == g.SID.iloc[0]].reset_index(drop=True)))
    for label, g in systems:
        df, sampler, info = analyse(g, leaves, LX, LY, tree, ratios, bbox, annual, sampler, label, args.max_km)
        if df is None:
            continue
        out.append(df)
        cls = info["cls"]
        summ.append({"evenement": label, "fokontany_concernes": info["n_keep"], **{f"pop_vent_{k}kt": int(pop[cls >= k].sum()) for k in (34, 50, 64)},
                     "fokontany_vent_64kt": int((cls >= 64).sum()), "rayons_manquants": f"{info['miss']}/{info['n34']}", "positions_R50_R64_estimees": info["filled"]})
        print(f"{label}: {info['n_keep']} fokontany, vent>=34: {(cls >= 34).sum()}, >=64: {(cls >= 64).sum()}, pluie={'oui' if info['rx3_ok'] else 'non'}")
    if args.recent:
        ed = country_data_dir(args.country) / "external"
        ed.mkdir(parents=True, exist_ok=True)
        today = dt.date.today().isoformat()
        src = "IBTrACS (rayons de vent JTWC, R50/R64 manquants estimés), CHIRPS journalier : indicateurs de choc au format JIAF, 12 derniers mois"
        if out:
            rollup(leaves, pd.concat(out), today, src).to_csv(ed / "chocs.csv", index=False)
        else:
            (ed / "chocs.csv").write_text("pcode,indicateur,valeur,date,source\n")
        print(f"{len(out)} système(s) des 12 derniers mois")
        return
    VAL_DIR.mkdir(exist_ok=True)
    pd.concat(out).to_csv(VAL_DIR / "chocs_cyclones_fokontany.csv", index=False)
    pd.DataFrame(summ).to_csv(VAL_DIR / "chocs_cyclones_resume.csv", index=False)
    print(pd.DataFrame(summ).to_string())


if __name__ == "__main__":
    main()
