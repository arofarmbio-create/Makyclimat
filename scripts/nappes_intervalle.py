"""Calibration de l'intervalle de 80 % du niveau statique selon la distance au forage le plus proche
(validation/protocole_cadre_eaux_souterraines.md, modification du 03/11/2026, avant la phase 5).

Constat de la phase 0 : l'intervalle de l'hybride S0 couvre 84 % des forages à moins de 25 km, 65 % au-delà de 100 km.
Méthode conforme par classe de distance : écart normalisé s de chaque forage prédit hors de sa région ; facteur k =
80e centile de s dans la classe ; intervalle élargi [médiane − k (médiane − bas) ; médiane + k (haut − médiane)].
Validation : k estimé sans la région évaluée, couverture mesurée sur cette région. Critère : 75 à 85 % par classe.
Sorties : validation/nappes_intervalle.md, nappes_intervalle_k.csv (facteurs pour la carte nationale).
Usage : python scripts/nappes_intervalle.py --country mdg [--couches DOSSIER]
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

import audit_nappes_phase0 as A
import validate_nappes_hc2b as H2b
from common import ROOT, country_data_dir

LEVEL, TARGET = 0.80, (0.75, 0.85)


def band_of(dist_km) -> np.ndarray:
    d = np.asarray(dist_km, float)
    out = np.full(d.shape, "", dtype=object)
    for lo, hi, lab in H2b.BANDS:
        out[(d >= lo) & (d < hi)] = lab
    return out


def scores(p: pd.DataFrame) -> np.ndarray:
    """Écart normalisé : 1 = la mesure tombe sur la borne de l'intervalle de 80 % ; > 1 = hors de l'intervalle."""
    up = p.mesure_m >= p.pred_hybride
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(up, (p.mesure_m - p.pred_hybride) / (p.haut_hybride - p.pred_hybride),
                     (p.pred_hybride - p.mesure_m) / (p.pred_hybride - p.bas_hybride))
    return np.where(np.isfinite(s), s, np.where(up, np.where(p.mesure_m > p.pred_hybride, np.inf, 0.0), 0.0))


def factors(p: pd.DataFrame, level=LEVEL) -> dict:
    """k par classe de distance : quantile `level` des écarts normalisés (version finie des petits échantillons)."""
    s, b = scores(p), band_of(p.dist_km)
    out = {}
    for _, _, lab in H2b.BANDS:
        v = np.sort(s[b == lab])
        if len(v):
            out[lab] = float(v[min(len(v) - 1, int(np.ceil(level * (len(v) + 1))) - 1)])
    return out


def widen(p: pd.DataFrame, k: dict) -> pd.DataFrame:
    kk = np.array([k.get(x, np.nan) for x in band_of(p.dist_km)])
    lo = np.maximum(p.pred_hybride - kk * (p.pred_hybride - p.bas_hybride), 0)
    hi = p.pred_hybride + kk * (p.haut_hybride - p.pred_hybride)
    return p.assign(bas_cal=lo, haut_cal=hi, k=kk)


def cross_calibrate(p: pd.DataFrame) -> pd.DataFrame:
    """Pour chaque région : k estimé sur les autres régions, appliqué à celle-ci."""
    return pd.concat([widen(p[p.region == r], factors(p[p.region != r])) for r in p.region.unique()], ignore_index=True)


def summary(q: pd.DataFrame) -> pd.DataFrame:
    q = q.assign(classe=band_of(q.dist_km), avant=(q.mesure_m >= q.bas_hybride) & (q.mesure_m <= q.haut_hybride),
                 apres=(q.mesure_m >= q.bas_cal) & (q.mesure_m <= q.haut_cal),
                 larg_avant=q.haut_hybride - q.bas_hybride, larg_apres=q.haut_cal - q.bas_cal)
    rows = []
    for _, _, lab in H2b.BANDS:
        g = q[q.classe == lab]
        if len(g):
            rows.append({"classe": lab, "forages": len(g), "couverture_avant": g.avant.mean(), "couverture_apres": g.apres.mean(),
                         "largeur_avant_m": g.larg_avant.median(), "largeur_apres_m": g.larg_apres.median()})
    return pd.DataFrame(rows)


def report(tab: pd.DataFrame, by_reg: pd.DataFrame, k_all: dict, ok: bool) -> str:
    L = ["# Intervalle de 80 % du niveau statique, calibré selon la distance aux forages", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/nappes_intervalle.py`, selon "
         "`validation/protocole_cadre_eaux_souterraines.md` (modification du 03/11/2026, fixée avant le calcul). Modèle : "
         "hybride S0, validation par région entière ; facteurs estimés sans la région évaluée.", "",
         "| Distance au forage connu le plus proche | Forages | Couverture avant | Couverture après | Largeur médiane avant (m) | Largeur médiane après (m) |",
         "|---|---|---|---|---|---|"]
    for r in tab.itertuples():
        L.append(f"| {r.classe} | {r.forages} | {r.couverture_avant:.0%} | {r.couverture_apres:.0%} | {r.largeur_avant_m:.1f} | {r.largeur_apres_m:.1f} |")
    L += ["", f"Critère (75 à 85 % dans chaque classe) : **{'atteint' if ok else 'non atteint'}**.", "",
          "| Région | Forages | Couverture avant | Couverture après |", "|---|---|---|---|"]
    for r in by_reg.itertuples():
        L.append(f"| {r.region} | {r.forages} | {r.avant:.0%} | {r.apres:.0%} |")
    L += ["", "Facteurs k retenus pour la carte nationale (toutes régions) : "
          + " ; ".join(f"{c} : {v:.2f}" for c, v in k_all.items()) + " (1 = intervalle inchangé).", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--couches", default=None)
    args = ap.parse_args()
    couches = Path(args.couches) if args.couches else country_data_dir(args.country) / "nappes_mondiales"
    df, *_ = A.load_sites(args.country, couches)
    p = A.s0_predictions(df)
    q = cross_calibrate(p)
    tab = summary(q)
    ok = bool(tab.couverture_apres.between(*TARGET).all())
    ins = lambda lo, hi: (q.mesure_m >= lo) & (q.mesure_m <= hi)
    by_reg = q.assign(avant=ins(q.bas_hybride, q.haut_hybride), apres=ins(q.bas_cal, q.haut_cal)).groupby("region").agg(
        forages=("avant", "size"), avant=("avant", "mean"), apres=("apres", "mean")).reset_index()
    k_all = factors(p)
    vd = ROOT / "validation"
    (vd / "nappes_intervalle.md").write_text(report(tab, by_reg, k_all, ok), encoding="utf-8")
    pd.DataFrame({"classe": list(k_all), "k": list(k_all.values())}).round(3).to_csv(vd / "nappes_intervalle_k.csv", index=False)
    print(f"Intervalle : critère {'atteint' if ok else 'non atteint'} ; rapport dans validation/nappes_intervalle.md")


if __name__ == "__main__":
    main()
