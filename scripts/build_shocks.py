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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--max-km", type=float, default=300.0)
    args = ap.parse_args()
    from chirps_daily import days_between, leaf_series
    from validate_events import fetch_ibtracs, footprint, project, rain_features
    full = load_config(args.country)
    bbox = full["map"]["bbox"]
    units = read_units(args.country)
    leaves = units[units.level == 4].reset_index(drop=True)
    ev = pd.read_csv(VAL_DIR / "evenements.csv")
    annual = None
    p = grid_dir(args.country) / "rx3_annual.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        if (z["codes"].astype(str) == leaves.pcode.values).all():
            annual = z["rx3"]
    from scipy.spatial import cKDTree
    d_all = fetch_ibtracs()
    LX, LY = project(leaves.lon.values, leaves.lat.values)
    tree = cKDTree(np.c_[LX, LY])
    sampler, out, summ = None, [], []
    from chirps_daily import roll3_max
    for _, e in ev[ev.type == "cyclone"].iterrows():
        yr = int(str(e.date_debut)[:4])
        g = d_all[(d_all.nom == e.nom) & (d_all.time.dt.year.isin([yr, yr + 1]))]
        if g.empty:
            print("trajectoire introuvable", e.id)
            continue
        g = g[g.SID == g.SID.iloc[0]].reset_index(drop=True)
        x, y = project(g.LON.values, g.LAT.values)
        dist, _ = tree.query(np.c_[x, y])
        near = g[dist <= 400]
        if near.empty:
            continue
        gg = g[(g.time >= near.time.min() - pd.Timedelta(hours=12)) & (g.time <= near.time.max() + pd.Timedelta(hours=12))].reset_index(drop=True)
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
            print("pluie indisponible", e.id, ex)
        keep = (dmin <= args.max_km) | (cls > 0)
        df = pd.DataFrame({"evenement": e.id, "pcode": leaves.pcode.values, "vent_classe_kt": cls, "dist_min_km": np.round(dmin, 1),
                           "date_passage": pd.to_datetime(when).strftime("%Y-%m-%d"), "rx3_mm": np.round(rx3, 0), "periode_retour_ans": np.round(rp, 1)})[keep]
        out.append(df)
        pop = leaves["pop"].fillna(0).values
        summ.append({"evenement": e.id, "nom": e.nom, "fokontany_concernes": int(keep.sum()),
                     **{f"pop_vent_{k}kt": int(pop[cls >= k].sum()) for k in (34, 50, 64)},
                     "fokontany_vent_64kt": int((cls >= 64).sum()), "rayons_manquants": f"{miss}/{n34}"})
        print(f"{e.id}: {keep.sum()} fokontany, vent>=34: {(cls >= 34).sum()}, >=64: {(cls >= 64).sum()}, pluie={'oui' if np.isfinite(rx3).any() else 'non'}")
    VAL_DIR.mkdir(exist_ok=True)
    pd.concat(out).to_csv(VAL_DIR / "chocs_cyclones_fokontany.csv", index=False)
    pd.DataFrame(summ).to_csv(VAL_DIR / "chocs_cyclones_resume.csv", index=False)
    print(pd.DataFrame(summ).to_string())


if __name__ == "__main__":
    main()
