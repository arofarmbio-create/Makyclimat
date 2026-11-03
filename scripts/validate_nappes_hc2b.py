"""Test H-C2b du protocole de la carte des nappes (ajout du 02/11/2026) : prédire la profondeur de l'eau dans une
région administrative entière laissée de côté, loin de tout forage d'apprentissage.

Mêmes modèles et réglages que H-C2 (scripts/validate_nappes_hc2.py) ; seul le découpage change : chaque région d'au
moins 10 forages est laissée de côté. H-C2b confirmée si (1) Wilcoxon apparié unilatéral sur les erreurs absolues
hybride < krigeage (5 %) et (2) l'hybride a l'erreur médiane la plus faible dans plus de la moitié des régions.
Sorties : validation/nappes_hc2b.md, validation/nappes_hc2b_regions.csv, validation/nappes_hc2b_distances.csv.
Usage : python scripts/validate_nappes_hc2b.py --country mdg [--couches DOSSIER]
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

import validate_nappes_hc1 as H1
import validate_nappes_hc2 as H2
from common import ROOT, country_data_dir, locate_points, read_units

MIN_REGION = 10
BANDS = [(0, 25, "0-25 km"), (25, 50, "25-50 km"), (50, 100, "50-100 km"), (100, np.inf, "plus de 100 km")]


def nearest_km(lat_a, lon_a, lat_b, lon_b) -> np.ndarray:
    """Distance (km, approximation équirectangulaire) de chaque point A au point B le plus proche."""
    la, lo = np.radians(lat_a)[:, None], np.radians(lon_a)[:, None]
    lb, lob = np.radians(lat_b)[None, :], np.radians(lon_b)[None, :]
    x = (lob - lo) * np.cos((la + lb) / 2)
    return 6371.0 * np.sqrt(x ** 2 + (lb - la) ** 2).min(axis=1)


def region_cv(df: pd.DataFrame, hybrid=H2.hybrid_predict, krige=H2.kriging_predict):
    pts, regs = [], []
    for r, g in df.groupby("region"):
        if len(g) < MIN_REGION:
            continue
        tr = df[df.region != r]
        ph, _, _ = hybrid(tr, g)
        pk = krige(tr, g)
        obs = g.mesure_m.to_numpy()
        d = nearest_km(g.lat.to_numpy(), g.lon.to_numpy(), tr.lat.to_numpy(), tr.lon.to_numpy())
        e = pd.DataFrame({"region": r, "dist_km": d, "err_hybride": np.abs(ph - obs), "err_krigeage": np.abs(pk - obs),
                          "err_fan": np.abs(g.fan_m.to_numpy() - obs)})
        pts.append(e)
        regs.append({"region": r, "forages": len(g), "distance_mediane_km": float(np.median(d)),
                     **{f"erreur_{k}": float(e[f"err_{k}"].median()) for k in ("hybride", "krigeage", "fan")}})
    return pd.concat(pts, ignore_index=True), pd.DataFrame(regs)


def decide(pts: pd.DataFrame, regs: pd.DataFrame) -> dict:
    from scipy import stats
    d = pts.err_hybride - pts.err_krigeage
    p = float(stats.wilcoxon(d, alternative="less").pvalue) if (d != 0).any() else 1.0
    wins = int((regs.erreur_hybride < regs.erreur_krigeage).sum())
    return {"p_wilcoxon": p, "regions_gagnees": wins, "regions": len(regs), "ok": p < 0.05 and wins > len(regs) / 2}


def distance_table(pts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lo, hi, lab in BANDS:
        g = pts[(pts.dist_km >= lo) & (pts.dist_km < hi)]
        if len(g):
            rows.append({"distance": lab, "forages": len(g), **{f"erreur_{k}": float(g[f"err_{k}"].median()) for k in ("hybride", "krigeage", "fan")}})
    return pd.DataFrame(rows)


def report(regs, dist, dec, n_pts) -> str:
    L = ["# H-C2b : prédire la profondeur de l'eau dans une région entière laissée de côté", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_nappes_hc2b.py`, selon `validation/protocole_carte_nappes.md` "
         "(ajout du 02/11/2026, fixé avant le calcul ; conçu après H-C2, sur les mêmes forages : test complémentaire). "
         f"Forages : MGMERL ({n_pts}) ; carte mondiale : Fan et al. (2017), valeurs non republiées.", "",
         "## Par région laissée de côté", "",
         "| Région | Forages | Distance médiane au forage d'apprentissage le plus proche (km) | Erreur hybride (m) | Erreur krigeage (m) | Erreur Fan (m) |",
         "|---|---|---|---|---|---|"]
    for r in regs.itertuples():
        L.append(f"| {r.region} | {r.forages} | {r.distance_mediane_km:.0f} | {r.erreur_hybride:.1f} | {r.erreur_krigeage:.1f} | {r.erreur_fan:.1f} |")
    L += ["", "## Par distance au forage d'apprentissage le plus proche", "",
          "| Distance | Forages | Erreur hybride (m) | Erreur krigeage (m) | Erreur Fan (m) |", "|---|---|---|---|---|"]
    for r in dist.itertuples():
        L.append(f"| {r.distance} | {r.forages} | {r.erreur_hybride:.1f} | {r.erreur_krigeage:.1f} | {r.erreur_fan:.1f} |")
    L += ["", f"Wilcoxon apparié (hybride < krigeage) : p = {dec['p_wilcoxon']:.3f} ; l'hybride fait mieux dans "
          f"{dec['regions_gagnees']} régions sur {dec['regions']}.", "",
          f"**H-C2b {'confirmée' if dec['ok'] else 'non confirmée'}.**", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--couches", default=None)
    args = ap.parse_args()
    couches = Path(args.couches) if args.couches else country_data_dir(args.country) / "nappes_mondiales"
    src = country_data_dir(args.country) / "mgmerl_raw" / "complet_2026-11-03" / "mgmerl_niveau_statique_complet.csv"
    df = H2.point_features(args.country, H1.load_points(src), couches)
    pc = locate_points(args.country, df.lon.tolist(), df.lat.tolist())
    geo = pd.read_csv(country_data_dir(args.country) / "external" / "geology.csv")
    prod = geo[geo.indicateur == "aquifer_productivity_pct"].set_index("pcode").valeur
    df["productivite"] = [float(prod[c]) if c in prod.index else np.nan for c in pc]
    u = read_units(args.country)
    names = u[u.level == 1].set_index("pcode").name
    adm1 = u[u.level == 4].set_index("pcode").adm1
    df["region"] = [names.get(adm1.get(c, ""), "inconnue") for c in pc]
    df = df[np.isfinite(df.fan_m) & (df.region != "inconnue")].reset_index(drop=True)
    pts, regs = region_cv(df)
    dist = distance_table(pts)
    dec = decide(pts, regs)
    text = report(regs, dist, dec, len(df))
    vd = ROOT / "validation"
    (vd / "nappes_hc2b.md").write_text(text, encoding="utf-8")
    regs.round(3).to_csv(vd / "nappes_hc2b_regions.csv", index=False)
    dist.round(3).to_csv(vd / "nappes_hc2b_distances.csv", index=False)
    print(text)


if __name__ == "__main__":
    main()
