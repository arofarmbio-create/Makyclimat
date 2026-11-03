"""Carte nationale du niveau statique, version 1 (validation/protocole_cadre_eaux_souterraines.md, phase 5 et
précisions du 03/11/2026, fixées avant le calcul).

Pour chacun des 17 465 fokontany : profondeur estimée (médiane de l'hybride S0 entraîné sur les 980 forages MGMERL),
intervalle de 80 % élargi selon la distance au forage le plus proche (nappes_intervalle_k.csv), erreur attendue
(erreur médiane de l'hybride dans la classe de distance, validation par région de la phase 0), drapeau
« extrapolation » (variable de terrain hors de l'étendue des forages). Agrégation par commune, district et région.
Niveau de preuve : approximation. La valeur de Fan n'est jamais publiée, seule la prédiction de l'hybride.
Sorties : data/<pays>/external/nappes_carte.csv (format du système : pcode, indicateur, valeur, date, source),
validation/nappes_carte_nationale.md et nappes_carte_regions.csv.
Usage : python scripts/nappes_carte_nationale.py --country mdg [--couches DOSSIER]
"""
from __future__ import annotations

import argparse
import datetime as dt
import gc
from pathlib import Path

import numpy as np
import pandas as pd

import audit_nappes_phase0 as A
import etude_seam as S
import nappes_intervalle as N
import validate_nappes_hc2 as H2
import validate_nappes_hc2b as H2b
from common import ROOT, country_data_dir, read_units

BATCH = 2000
VERSION = "2 (tableau MGMERL complet du 03/11/2026)"
SOURCE = "MakyClimat niveau statique v2 (validation/nappes_carte_nationale.md)"


def expected_error(dist_km, table: pd.DataFrame) -> np.ndarray:
    """Erreur médiane de l'hybride (validation par région) dans la classe de distance de chaque point."""
    e = table.set_index("distance").erreur_hybride
    return np.array([e.get(b, np.nan) for b in N.band_of(dist_km)], dtype=float)


def features_by_batch(country, pts: pd.DataFrame, couches, size=BATCH) -> pd.DataFrame:
    parts = []
    for i in range(0, len(pts), size):
        parts.append(H2.point_features(country, pts.iloc[i:i + size].copy(), couches))
        print(f"variables : {min(i + size, len(pts))} fokontany sur {len(pts)}", flush=True)
        gc.collect()
    return pd.concat(parts, ignore_index=True)


def aggregate(fk: pd.DataFrame, key: str) -> pd.DataFrame:
    """Par unité : médiane de la profondeur et de l'erreur attendue, part des fokontany en extrapolation."""
    return fk.groupby(key).agg(fokontany=("pcode", "size"), profondeur_mediane_m=("profondeur_m", "median"),
                               erreur_attendue_m=("erreur_attendue_m", "median"), part_extrapolation=("extrapolation", "mean"),
                               distance_mediane_km=("distance_km", "median")).reset_index()


def to_external(fk: pd.DataFrame, date: str) -> pd.DataFrame:
    cols = {"profondeur_m": "niveau_statique_m", "bas80_m": "niveau_statique_bas80_m", "haut80_m": "niveau_statique_haut80_m",
            "erreur_attendue_m": "niveau_statique_erreur_attendue_m", "distance_km": "distance_forage_km",
            "extrapolation": "niveau_statique_extrapolation"}
    rows = [pd.DataFrame({"pcode": fk.pcode, "indicateur": ind, "valeur": fk[c].astype(float).round(2)}) for c, ind in cols.items()]
    out = pd.concat(rows, ignore_index=True)
    out = out[np.isfinite(out.valeur)]
    return out.assign(date=date, source=SOURCE)


def report(reg: pd.DataFrame, n_fk: int, n_ok: int, extra_share: float, cmp: dict, train_regions: set, n_train: int, version: str) -> str:
    L = [f"# Carte nationale du niveau statique (version {version})", "",
         f"Générée le {dt.date.today().isoformat()} par `scripts/nappes_carte_nationale.py`, selon "
         "`validation/protocole_cadre_eaux_souterraines.md` (phase 5, précisions du 03/11/2026 fixées avant le calcul). "
         f"Modèle : hybride S0 entraîné sur {n_train} forages MGMERL ; intervalle de 80 % calibré selon la distance. "
         "**Niveau de preuve : approximation**, validée par région entière sur 8 régions ; pas encore de confirmation sur "
         "des forages indépendants (phase 4).", "",
         f"{n_ok} fokontany estimés sur {n_fk} ; {extra_share:.0%} en extrapolation (terrain hors de l'étendue des forages).", "",
         "| Région | Forages d'apprentissage | Fokontany | Profondeur médiane (m) | Erreur attendue (m) | Distance médiane au forage (km) | Part en extrapolation |",
         "|---|---|---|---|---|---|---|"]
    for r in reg.sort_values("region").itertuples():
        L.append(f"| {r.region} | {'oui' if r.region in train_regions else '**aucun**'} | {r.fokontany} | {r.profondeur_mediane_m:.1f} | "
                 f"{r.erreur_attendue_m:.1f} | {r.distance_mediane_km:.0f} | {r.part_extrapolation:.0%} |")
    L += ["", "## Comparaison avec le produit en service (`watertable.csv`, plus proche relevé à 15 km)", "",
          f"Fokontany communs : {cmp['n']} ; écart médian absolu {cmp['ecart']:.1f} m. Sans donnée indépendante, cet écart "
          "ne dit pas lequel est juste (règle fixée avant le calcul).", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--couches", default=None)
    args = ap.parse_args()
    couches = Path(args.couches) if args.couches else country_data_dir(args.country) / "nappes_mondiales"
    train, *_ = A.load_sites(args.country, couches)
    units = read_units(args.country)
    fk = units[units.level == 4][["pcode", "adm1", "adm2", "adm3", "lon", "lat"]].reset_index(drop=True)
    fk = features_by_batch(args.country, fk, couches)
    geo = pd.read_csv(country_data_dir(args.country) / "external" / "geology.csv")
    prod = geo[geo.indicateur == "aquifer_productivity_pct"].set_index("pcode").valeur
    fk["productivite"] = fk.pcode.map(prod).astype(float)
    ok = np.isfinite(fk.fan_m).to_numpy()
    med, lo, hi = H2.hybrid_predict(train, fk[ok])
    fk["pred_hybride"], fk["bas_hybride"], fk["haut_hybride"] = np.nan, np.nan, np.nan
    fk.loc[ok, "pred_hybride"], fk.loc[ok, "bas_hybride"], fk.loc[ok, "haut_hybride"] = med, lo, hi
    fk["dist_km"] = H2b.nearest_km(fk.lat.to_numpy(), fk.lon.to_numpy(), train.lat.to_numpy(), train.lon.to_numpy())
    kk = pd.read_csv(ROOT / "validation" / "nappes_intervalle_k.csv")
    w = N.widen(fk, dict(zip(kk.classe, kk.k)))
    fk["profondeur_m"], fk["bas80_m"], fk["haut80_m"] = w.pred_hybride, w.bas_cal, w.haut_cal
    fk["distance_km"] = fk.dist_km
    fk["erreur_attendue_m"] = expected_error(fk.dist_km, pd.read_csv(ROOT / "validation" / "nappes_phase0_couverture.csv"))
    fk["extrapolation"] = S.outside_share(train, fk).astype(float)
    fk.loc[~ok, ["erreur_attendue_m", "extrapolation"]] = np.nan
    names = dict(zip(units.pcode, units.name))
    fk["region"] = fk.adm1.map(names)
    ext = to_external(fk, dt.date.today().isoformat())
    ext.to_csv(country_data_dir(args.country) / "external" / "nappes_carte.csv", index=False)
    reg = aggregate(fk[ok], "region")
    for key, f in (("adm3", "communes"), ("adm2", "districts")):
        a = aggregate(fk[ok], key)
        a.insert(1, "nom", a[key].map(names))
        a.round(3).to_csv(ROOT / "validation" / f"nappes_carte_{f}.csv", index=False)
    reg.round(3).to_csv(ROOT / "validation" / "nappes_carte_regions.csv", index=False)
    wt = pd.read_csv(country_data_dir(args.country) / "external" / "watertable.csv", dtype={"pcode": str})
    wt = wt[wt.indicateur == "water_table_depth_m"].set_index("pcode").valeur
    both = fk[ok & fk.pcode.isin(wt.index)]
    cmp = {"n": len(both), "ecart": float(np.median(np.abs(both.profondeur_m - both.pcode.map(wt)))) if len(both) else float("nan")}
    train_regions = set(train.region)
    (ROOT / "validation" / "nappes_carte_nationale.md").write_text(
        report(reg, len(fk), int(ok.sum()), float(np.nanmean(fk.extrapolation)), cmp, train_regions, len(train), VERSION), encoding="utf-8")
    print(f"Carte nationale : {int(ok.sum())} fokontany estimés ; rapport dans validation/nappes_carte_nationale.md")


if __name__ == "__main__":
    main()
