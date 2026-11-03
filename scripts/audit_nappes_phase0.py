"""Phase 0 du protocole-cadre « eaux souterraines » (validation/protocole_cadre_eaux_souterraines.md, section 3) :
audit des données de niveau statique et référence S0 avec les critères fixés.

1. Diagramme de flux : relevés lus, contrôlés, avec valeur de Fan, situés dans un fokontany, dans une région d'au
   moins 10 forages.
2. Densité des forages par région (nombre, part, forages pour 1 000 km²) ; dates et saisons des relevés.
3. Référence S0 (Fan seule, krigeage, hybride ; réglages de H-C2), validation par région entière :
   - critère 1 : erreur médiane absolue moyennée par région ;
   - critère 2 : erreur médiane absolue des forages à plus de 50 km du forage d'apprentissage le plus proche ;
   - intervalles de confiance à 95 % par rééchantillonnage des régions (2 000 tirages) ;
   - couverture de l'intervalle de 80 % de l'hybride par région et par classe de distance ; biais moyen.
Sorties : validation/nappes_phase0_audit.md et CSV (statistiques agrégées seulement ; valeurs de Fan non publiées).
Usage : python scripts/audit_nappes_phase0.py --country mdg [--couches DOSSIER]
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

import validate_nappes_hc1 as H1
import validate_nappes_hc2 as H2
import validate_nappes_hc2b as H2b
from common import ROOT, country_data_dir, locate_points, read_units

FAR_KM, N_BOOT, SEED = 50.0, 2000, 0
METHODS = ("fan", "krigeage", "hybride")
WET = (11, 12, 1, 2, 3, 4)


def s0_predictions(df: pd.DataFrame, hybrid=H2.hybrid_predict, krige=H2.kriging_predict) -> pd.DataFrame:
    """Prédictions de chaque forage quand sa région entière (au moins 10 forages) est laissée de côté."""
    out = []
    for r, g in df.groupby("region"):
        if len(g) < H2b.MIN_REGION:
            continue
        tr = df[df.region != r]
        ph, lo, hi = hybrid(tr, g)
        pk = krige(tr, g)
        obs = g.mesure_m.to_numpy()
        out.append(pd.DataFrame({"region": r, "mesure_m": obs, "dist_km": H2b.nearest_km(g.lat.to_numpy(), g.lon.to_numpy(),
                                 tr.lat.to_numpy(), tr.lon.to_numpy()), "pred_fan": g.fan_m.to_numpy(), "pred_krigeage": pk,
                                 "pred_hybride": ph, "bas_hybride": lo, "haut_hybride": hi}))
    p = pd.concat(out, ignore_index=True)
    for m in METHODS:
        p[f"err_{m}"] = np.abs(p[f"pred_{m}"] - p.mesure_m)
    return p


def criterion1(p: pd.DataFrame, m: str, regions=None) -> float:
    """Moyenne, sur les régions, de l'erreur médiane absolue de la méthode m."""
    g = p.groupby("region")[f"err_{m}"].median()
    return float(g.loc[regions].mean() if regions is not None else g.mean())


def criterion2(p: pd.DataFrame, m: str, regions=None) -> float:
    q = p if regions is None else pd.concat([p[p.region == r] for r in regions])
    q = q[q.dist_km > FAR_KM]
    return float(q[f"err_{m}"].median()) if len(q) else float("nan")


def bootstrap(p: pd.DataFrame, fn, m: str, n=N_BOOT, seed=SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    regs = p.region.unique()
    vals = [fn(p, m, list(rng.choice(regs, size=len(regs), replace=True))) for _ in range(n)]
    return float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))


def coverage(p: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    inside = (p.mesure_m >= p.bas_hybride) & (p.mesure_m <= p.haut_hybride)
    q = p.assign(dedans=inside)
    by_reg = q.groupby("region").agg(forages=("dedans", "size"), couverture=("dedans", "mean")).reset_index()
    rows = []
    for lo, hi, lab in H2b.BANDS:
        g = q[(q.dist_km >= lo) & (q.dist_km < hi)]
        if len(g):
            rows.append({"distance": lab, "forages": len(g), "couverture": float(g.dedans.mean()),
                         **{f"erreur_{m}": float(g[f"err_{m}"].median()) for m in METHODS}})
    return by_reg, pd.DataFrame(rows)


def flow(n_read, n_qc, n_fan, n_reg, n_reg10) -> list[tuple[str, int]]:
    return [("Relevés lus (tableau MGMERL complet, extrait le 03/11/2026)", n_read), ("Après contrôle (0-200 m, à Madagascar, doublons)", n_qc),
            ("Avec une valeur de la carte de Fan", n_fan), ("Situés dans un fokontany (région connue)", n_reg),
            ("Dans une région d'au moins 10 forages (validation par région)", n_reg10)]


def report(fl, dens, seasons, crit, cov_r, cov_d) -> str:
    L = ["# Phase 0 : audit des forages et référence S0 (module eaux souterraines)", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/audit_nappes_phase0.py`, selon "
         "`validation/protocole_cadre_eaux_souterraines.md` (section 3, critères fixés avant le calcul). Forages : MGMERL ; "
         "carte mondiale : Fan et al. (2017), valeurs non republiées. Analyse exploratoire (forages déjà utilisés en H-C1 à H-C2b).", "",
         "## 1. Diagramme de flux des données", ""]
    for i, (lab, n) in enumerate(fl):
        L.append(f"{'↓ ' if i else ''}**{n}** : {lab}")
        L.append("")
    L += ["## 2. Densité des forages par région", "",
          "| Région | Forages | Part | Forages pour 1 000 km² |", "|---|---|---|---|"]
    for r in dens.itertuples():
        L.append(f"| {r.region} | {r.forages} | {r.part:.1%} | {r.densite:.2f} |")
    L += ["", "## 3. Dates et saisons des relevés", "", seasons, "",
          "## 4. Référence S0 (validation par région entière)", "",
          "| Méthode | Critère 1 : erreur moyennée par région (m) [IC 95 %] | Critère 2 : erreur à plus de 50 km (m) [IC 95 %] | Biais moyen (m) |",
          "|---|---|---|---|"]
    for m, lab in (("fan", "Carte de Fan seule"), ("krigeage", "Krigeage"), ("hybride", "Hybride (forêt de quantiles)")):
        c = crit[m]
        L.append(f"| {lab} | {c['c1']:.2f} [{c['c1_ic'][0]:.2f} ; {c['c1_ic'][1]:.2f}] | {c['c2']:.2f} [{c['c2_ic'][0]:.2f} ; "
                 f"{c['c2_ic'][1]:.2f}] | {c['biais']:+.2f} |")
    L += ["", "Avec 8 régions, les intervalles de confiance sont larges : ils mesurent ce que la phase 0 permet de conclure.", "",
          "## 5. Couverture de l'intervalle de 80 % de l'hybride", "",
          "| Région | Forages | Couverture |", "|---|---|---|"]
    for r in cov_r.itertuples():
        L.append(f"| {r.region} | {r.forages} | {r.couverture:.0%} |")
    L += ["", "| Distance au forage d'apprentissage le plus proche | Forages | Couverture | Erreur Fan (m) | Erreur krigeage (m) | Erreur hybride (m) |",
          "|---|---|---|---|---|---|"]
    for r in cov_d.itertuples():
        L.append(f"| {r.distance} | {r.forages} | {r.couverture:.0%} | {r.erreur_fan:.1f} | {r.erreur_krigeage:.1f} | {r.erreur_hybride:.1f} |")
    return "\n".join(L) + "\n"


def load_sites(country, couches):
    """Forages contrôlés avec leurs variables, leur région et le décompte du diagramme de flux."""
    src = country_data_dir(country) / "mgmerl_raw" / "complet_2026-11-03" / "mgmerl_niveau_statique_complet.csv"
    n_read = len(pd.read_csv(src))
    pts = H1.load_points(src)
    df = H2.point_features(country, pts, couches)
    pc = locate_points(country, df.lon.tolist(), df.lat.tolist())
    geo = pd.read_csv(country_data_dir(country) / "external" / "geology.csv")
    prod = geo[geo.indicateur == "aquifer_productivity_pct"].set_index("pcode").valeur
    df["productivite"] = [float(prod[c]) if c in prod.index else np.nan for c in pc]
    u = read_units(country)
    reg = u[u.level == 1].set_index("pcode")
    adm1 = u[u.level == 4].set_index("pcode").adm1
    df["region"] = [reg.name.get(adm1.get(c, ""), "inconnue") for c in pc]
    n_fan = int(np.isfinite(df.fan_m).sum())
    df = df[np.isfinite(df.fan_m)]
    n_reg = int((df.region != "inconnue").sum())
    df = df[df.region != "inconnue"].reset_index(drop=True)
    return df, pts, n_read, n_fan, n_reg, reg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--couches", default=None)
    args = ap.parse_args()
    couches = Path(args.couches) if args.couches else country_data_dir(args.country) / "nappes_mondiales"
    df, pts, n_read, n_fan, n_reg, reg = load_sites(args.country, couches)
    counts = df.region.value_counts()
    n_reg10 = int(counts[counts >= H2b.MIN_REGION].sum())
    area = reg.set_index("name").area_km2
    dens = pd.DataFrame({"region": counts.index, "forages": counts.values})
    dens["part"] = dens.forages / dens.forages.sum()
    dens["densite"] = [n / area.get(r, np.nan) * 1000 for r, n in zip(dens.region, dens.forages)]
    d = pts.date.dropna()
    wet = d.dt.month.isin(WET)
    seasons = (f"Relevés datés de {d.min():%m/%Y} à {d.max():%m/%Y}. Par année : "
               + ", ".join(f"{y} : {n}" for y, n in d.dt.year.value_counts().sort_index().items())
               + f". Saison des pluies (novembre à avril) : {int(wet.sum())} ; saison sèche : {int((~wet).sum())}.")
    p = s0_predictions(df)
    crit = {}
    for m in METHODS:
        crit[m] = {"c1": criterion1(p, m), "c1_ic": bootstrap(p, criterion1, m), "c2": criterion2(p, m),
                   "c2_ic": bootstrap(p, criterion2, m), "biais": float((p[f"pred_{m}"] - p.mesure_m).mean())}
    cov_r, cov_d = coverage(p)
    fl = flow(n_read, len(pts), n_fan, n_reg, n_reg10)
    vd = ROOT / "validation"
    (vd / "nappes_phase0_audit.md").write_text(report(fl, dens, seasons, crit, cov_r, cov_d), encoding="utf-8")
    dens.round(4).to_csv(vd / "nappes_phase0_densite.csv", index=False)
    pd.DataFrame([{"methode": m, **{k: v for k, v in c.items() if not k.endswith("_ic")},
                   "c1_ic_bas": c["c1_ic"][0], "c1_ic_haut": c["c1_ic"][1], "c2_ic_bas": c["c2_ic"][0],
                   "c2_ic_haut": c["c2_ic"][1]} for m, c in crit.items()]).round(3).to_csv(vd / "nappes_phase0_s0.csv", index=False)
    cov_d.round(3).to_csv(vd / "nappes_phase0_couverture.csv", index=False)
    print("Phase 0 : rapport écrit dans validation/nappes_phase0_audit.md")


if __name__ == "__main__":
    main()
