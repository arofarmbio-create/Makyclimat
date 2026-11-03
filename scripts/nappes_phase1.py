"""Phase 1 du protocole-cadre « eaux souterraines » (validation/protocole_cadre_eaux_souterraines.md, section 3 et
modification du 03/11/2026) : les conditions de mesure améliorent-elles l'hybride ?

Variables ajoutées à l'hybride S0 : saison du relevé (1 de novembre à avril), SPI-3 et SPI-12 du mois du relevé à la
maille CHIRPS du forage (grilles de scripts/build_spi_grilles.py ; un relevé postérieur à la dernière grille prend le
dernier mois complet). Mêmes forages, réglages, découpage par région, critères et intervalles de confiance que la
phase 0. Règle fixée : variables gardées seulement si les deux critères principaux s'améliorent.
Sorties : validation/nappes_phase1.md et nappes_phase1.csv (statistiques agrégées seulement).
Usage : python scripts/nappes_phase1.py --country mdg [--couches DOSSIER]
"""
from __future__ import annotations

import argparse
import datetime as dt
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

import audit_nappes_phase0 as A
import validate_nappes_hc2 as H2
from common import ROOT, country_data_dir, grid_dir, load_grid

EXTRA = ["saison", "spi3", "spi12"]


def date_features(df: pd.DataFrame, spi: dict) -> pd.DataFrame:
    """Saison et SPI-3, SPI-12 du mois du relevé, à la maille du forage."""
    labels = [str(m) for m in spi["mois"]]
    idx = {m: i for i, m in enumerate(labels)}
    out = df.copy()
    mois = out.date.dt.strftime("%Y-%m")
    k = np.array([idx.get(m, len(labels) - 1 if isinstance(m, str) and m > labels[-1] else -1) for m in mois])
    out["saison"] = out.date.dt.month.isin(A.WET).astype(float).where(out.date.notna())
    g = (float(spi["lon0"]), float(spi["lat0"]), float(spi["res"]))
    for n in (3, 12):
        arr = np.asarray(spi[f"spi{n}"], dtype=float)
        v = np.full(len(out), np.nan)
        for i in np.unique(k[k >= 0]):
            sel = k == i
            v[sel] = H2.grid_sample(arr[i], *g, out.lon.to_numpy()[sel], out.lat.to_numpy()[sel])
        out[f"spi{n}"] = v
    return out


def compare(p0: pd.DataFrame, p1: pd.DataFrame, n=A.N_BOOT, seed=A.SEED) -> dict:
    """Critères de S0 et de S1 (hybride), avec leurs IC et l'IC de l'écart S1 − S0 sur les mêmes tirages de régions."""
    q = p0.assign(err_s1=p1.err_hybride.to_numpy())
    res = {}
    for c, fn in (("c1", A.criterion1), ("c2", A.criterion2)):
        rng = np.random.default_rng(seed)
        regs = q.region.unique()
        d = []
        for _ in range(n):
            r = list(rng.choice(regs, size=len(regs), replace=True))
            d.append(fn(q, "s1", r) - fn(q, "hybride", r))
        res[c] = {"s0": fn(q, "hybride"), "s0_ic": A.bootstrap(q, fn, "hybride", n, seed), "s1": fn(q, "s1"),
                  "s1_ic": A.bootstrap(q, fn, "s1", n, seed), "ecart_ic": (float(np.nanpercentile(d, 2.5)), float(np.nanpercentile(d, 97.5)))}
    return res


def decide(res: dict) -> tuple[bool, bool]:
    """(gardées, démontré) : gardées si les deux critères baissent ; démontré si les deux IC de l'écart sont sous 0."""
    keep = all(res[c]["s1"] < res[c]["s0"] for c in ("c1", "c2"))
    shown = keep and all(res[c]["ecart_ic"][1] < 0 for c in ("c1", "c2"))
    return keep, shown


def report(res, keep, shown, cov0, cov1, n_pts, n_spi, spi_range) -> str:
    verdict = ("**gardées** pour les phases suivantes, amélioration démontrée" if shown else
               "**gardées** (les deux critères baissent), amélioration **non démontrée** (IC de l'écart contient 0)" if keep else
               "**rejetées** : au moins un critère principal ne s'améliore pas")
    L = ["# Phase 1 : conditions de mesure (module eaux souterraines)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/nappes_phase1.py`, selon "
         "`validation/protocole_cadre_eaux_souterraines.md` (section 3, précisions du 03/11/2026 fixées avant le calcul). "
         f"{n_pts} forages MGMERL, validation par région entière (mêmes régions que la phase 0) ; {n_spi} avec un SPI "
         f"(grilles CHIRPS {spi_range}). Analyse exploratoire.", "",
         "Variables ajoutées à l'hybride S0 : saison du relevé, SPI-3 et SPI-12 du mois du relevé à la maille du forage.", "",
         "| Critère | S0 (m) [IC 95 %] | S1 = S0 + conditions de mesure (m) [IC 95 %] | Écart S1 − S0 [IC 95 %] |", "|---|---|---|---|"]
    for c, lab in (("c1", "1 : erreur moyennée par région"), ("c2", "2 : erreur à plus de 50 km")):
        r = res[c]
        L.append(f"| {lab} | {r['s0']:.2f} [{r['s0_ic'][0]:.2f} ; {r['s0_ic'][1]:.2f}] | {r['s1']:.2f} [{r['s1_ic'][0]:.2f} ; "
                 f"{r['s1_ic'][1]:.2f}] | {r['s1'] - r['s0']:+.2f} [{r['ecart_ic'][0]:+.2f} ; {r['ecart_ic'][1]:+.2f}] |")
    L += ["", f"Décision (règle fixée avant le calcul) : variables {verdict}.", "",
          "## Couverture de l'intervalle de 80 % par classe de distance", "",
          "| Distance | Forages | Couverture S0 | Couverture S1 | Erreur S0 (m) | Erreur S1 (m) |", "|---|---|---|---|---|---|"]
    for a, b in zip(cov0.itertuples(), cov1.itertuples()):
        L.append(f"| {a.distance} | {a.forages} | {a.couverture:.0%} | {b.couverture:.0%} | {a.erreur_hybride:.1f} | {b.erreur_hybride:.1f} |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--couches", default=None)
    args = ap.parse_args()
    couches = Path(args.couches) if args.couches else country_data_dir(args.country) / "nappes_mondiales"
    df, *_ = A.load_sites(args.country, couches)
    spi = load_grid(grid_dir(args.country) / "spi_grilles.npz")
    df = date_features(df, spi)
    p0 = A.s0_predictions(df)
    p1 = A.s0_predictions(df, hybrid=partial(H2.hybrid_predict, features=H2.FEATURES + EXTRA))
    res = compare(p0, p1)
    keep, shown = decide(res)
    cov0 = A.coverage(p0)[1]
    cov1 = A.coverage(p1)[1]
    m = [str(x) for x in spi["mois"]]
    n_pts = len(p0)
    vd = ROOT / "validation"
    (vd / "nappes_phase1.md").write_text(report(res, keep, shown, cov0, cov1, n_pts, int(np.isfinite(df.spi3).sum()),
                                                f"{m[0]} à {m[-1]}"), encoding="utf-8")
    pd.DataFrame([{"critere": c, "s0": r["s0"], "s0_ic_bas": r["s0_ic"][0], "s0_ic_haut": r["s0_ic"][1], "s1": r["s1"],
                   "s1_ic_bas": r["s1_ic"][0], "s1_ic_haut": r["s1_ic"][1], "ecart_ic_bas": r["ecart_ic"][0],
                   "ecart_ic_haut": r["ecart_ic"][1]} for c, r in res.items()]).round(3).to_csv(vd / "nappes_phase1.csv", index=False)
    print(f"Phase 1 : variables {'gardées' if keep else 'rejetées'} ; rapport dans validation/nappes_phase1.md")


if __name__ == "__main__":
    main()
