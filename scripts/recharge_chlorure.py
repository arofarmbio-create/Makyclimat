"""Recharge par bilan de chlorure dans le Grand Sud : test prospectif des recharges figées T2 et T2L
(validation/protocole_recharge_chlorure.md, fixé avant le calcul ; choix du 09/11/2026 notés en section 10 avant toute
lecture des chlorures).

R (mm/an) = D (mg/m²/an) / Cl_n (mg/L), D = P × Cl_p(d) × (1 + s), Cl_p(d) = Cl_i + (Cl_c − Cl_i) × exp(−d / L).
Forages BushProof (Al-Zoubaidy, Monteleone et Bünzli 2023) : chlorure > 0 ; exclus à moins de 5 km de la côte, nitrate
> 50 mg/L, conductivité > 3 000 µS/cm avec Cl < 10 % de la somme des ions majeurs ; doublons retirés. Zones : lien simple
à moins de 20 km, au moins 3 forages ; valeur de zone = médiane de Cl_n ; D au centre de la zone.
H-Cl1 (T2 : Spearman ≥ 0,3, p < 0,05 et écart médian ≤ 0,3), H-Cl2 (T2L : écart médian ≤ 0,7 × celui de T2 dans le
domaine de T2L), H-Cl4 (fluctuation / chlorure entre 1/3 et 3 pour au moins la moitié des sites à moins de 10 km d'une
zone). Une hypothèse n'est soutenue que si elle l'est dans les trois scénarios. H-Cl3 (karst) infaisable.
Données brutes hors dépôt ; sorties agrégées : validation/recharge_chlorure.md.
Usage : python scripts/recharge_chlorure.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir

SCENARIOS = {"bas": (1.8, 0.3, 10.0, 0.0), "central": (2.2, 0.4, 30.0, 0.3), "haut": (5.4, 1.0, 100.0, 0.5)}
COTE_KM, NO3_MAX, EC_MAX, CL_PART, ZONE_KM, MIN_ZONE, SITE_KM = 5.0, 50.0, 3000.0, 0.10, 20.0, 3, 10.0
ION_COLS = ["Na+_mg/l", "K+_mg/l", "Ca++_mg/l", "Mg++_mg/l", "HCO3-_mg/l", "CO3-_mg/l", "SO4--_mg/l", "Cl-_mg/l", "NO3-_mg/l"]


def cl_pluie(d_km, cl_c, cl_i, L) -> np.ndarray:
    return cl_i + (cl_c - cl_i) * np.exp(-np.asarray(d_km, float) / L)


def depot(p_mm, d_km, sc) -> np.ndarray:
    cl_c, cl_i, L, s = sc
    return np.asarray(p_mm, float) * cl_pluie(d_km, cl_c, cl_i, L) * (1 + s)


def filtre(f: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Applique les exclusions fixées ; renvoie les forages gardés et le décompte des exclusions."""
    n = {"avec chlorure positif": len(f)}
    f = f[f.dist_km >= COTE_KM]
    n["après côte (≥ 5 km)"] = len(f)
    f = f[~(pd.to_numeric(f["NO3-_mg/l"], errors="coerce") > NO3_MAX)]
    n["après nitrate (≤ 50 mg/L)"] = len(f)
    ions = f[[c for c in ION_COLS if c in f]].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
    ec = pd.to_numeric(f.get("EC_µ/cm"), errors="coerce")
    autre = (ec > EC_MAX) & (f.cl / ions < CL_PART)
    f = f[~autre.fillna(False)]
    n["après autre source de sels"] = len(f)
    return f, n


def zones(lat, lon, km: float = ZONE_KM) -> np.ndarray:
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components
    from sklearn.neighbors import BallTree
    X = np.radians(np.c_[lat, lon])
    pairs = BallTree(X, metric="haversine").query_radius(X, r=km / 6371.0)
    rows = np.concatenate([np.full(len(p), i) for i, p in enumerate(pairs)])
    cols = np.concatenate(pairs)
    return connected_components(csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(X), len(X))), directed=False)[1]


def ecart(model, ref) -> np.ndarray:
    return np.log10(np.asarray(model, float) / np.asarray(ref, float))


def nearest(lat, lon, plat, plon) -> np.ndarray:
    from sklearn.neighbors import BallTree
    return BallTree(np.radians(np.c_[plat, plon]), metric="haversine").query(
        np.radians(np.c_[np.asarray(lat), np.asarray(lon)]), k=1, return_distance=False)[:, 0]


def distance_cote(lat, lon, zip_path) -> np.ndarray:
    import os
    import tempfile
    import zipfile

    import geopandas as gpd
    with tempfile.TemporaryDirectory() as td:
        zipfile.ZipFile(zip_path).extractall(td)
        shp = [os.path.join(r, f) for r, _, fs in os.walk(td) for f in fs if f.endswith(".shp")][0]
        coast = gpd.read_file(shp, bbox=(42.0, -26.5, 51.0, -11.0)).to_crs("EPSG:32738").geometry.union_all()
    pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs="EPSG:4326").to_crs("EPSG:32738")
    return pts.distance(coast).to_numpy() / 1000.0


def main() -> None:
    import recharge_fluctuation as RF
    from scipy.stats import spearmanr
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cdir = country_data_dir(args.country)
    fs = glob.glob(str(cdir / "bushproof_raw" / "recuperation" / "*Forages*.csv"))
    f = pd.concat([pd.read_csv(x) for x in fs], ignore_index=True)
    f["lat"], f["lon"] = pd.to_numeric(f.Lat_DD, errors="coerce"), pd.to_numeric(f.Long_DD, errors="coerce")
    f["cl"] = pd.to_numeric(f["Cl-_mg/l"], errors="coerce")
    f = f[(f.cl > 0) & f.lat.notna() & f.lon.notna()]
    f = f.assign(_k=f.lat.round(5).astype(str) + f.lon.round(5).astype(str) + f.cl.astype(str)).drop_duplicates("_k").reset_index(drop=True)
    coast_zip = glob.glob(str(cdir / "chlorure_pluie_raw" / "natural_earth" / "*.zip"))[0]
    f["dist_km"] = distance_cote(f.lat, f.lon, coast_zip)
    f, decompte = filtre(f)
    f = f.reset_index(drop=True)
    f["zone"] = zones(f.lat, f.lon)
    z = f.groupby("zone").agg(n=("cl", "size"), cl=("cl", "median"), lat=("lat", "mean"), lon=("lon", "mean")).reset_index()
    z = z[z.n >= MIN_ZONE].reset_index(drop=True)
    z["dist_km"] = distance_cote(z.lat, z.lon, coast_zip)

    hd = ROOT / "inputs" / "hydrogeologie"
    t2l, t2k = pd.read_csv(hd / "recharge_t2l.csv"), pd.read_csv(hd / "recharge_t2k.csv")
    j = nearest(z.lat, z.lon, t2l.lat, t2l.lon)
    z["T2"], z["T2L"], z["dom"] = t2l.T2_mmpa.to_numpy()[j], t2l.T2L_mmpa.to_numpy()[j], t2l.domaine.to_numpy()[j]
    z["P"] = t2k.LTA_P_mmpa.to_numpy()[nearest(z.lat, z.lon, t2k.lat, t2k.lon)]

    res = {}
    for nom, sc in SCENARIOS.items():
        r = depot(z.P, z.dist_km, sc) / z.cl
        z[f"R_{nom}"] = r
        e2, el = ecart(z.T2, r), ecart(z.T2L, r)
        dom = z.dom.eq("dans le domaine").to_numpy()
        rho2, p2 = spearmanr(z.T2, r)
        rhol, pl = spearmanr(z.T2L, r)
        res[nom] = {"R_med": float(np.median(r)), "e_T2": float(np.median(np.abs(e2))), "b_T2": float(np.median(e2)),
                    "e_T2L": float(np.median(np.abs(el))), "b_T2L": float(np.median(el)),
                    "rho_T2": float(rho2), "p_T2": float(p2), "rho_T2L": float(rhol), "p_T2L": float(pl),
                    "e_T2_dom": float(np.median(np.abs(e2[dom]))) if dom.any() else np.nan,
                    "e_T2L_dom": float(np.median(np.abs(el[dom]))) if dom.any() else np.nan, "n_dom": int(dom.sum())}
        o = res[nom]
        o["H1"] = bool(o["rho_T2"] >= 0.3 and o["p_T2"] < 0.05 and o["e_T2"] <= 0.3)
        o["H2"] = bool(o["e_T2L_dom"] <= 0.7 * o["e_T2_dom"])
    sans_objet = all(res[s]["e_T2_dom"] < np.log10(1.5) for s in res)
    h1 = all(res[s]["H1"] for s in res)
    h2 = (not sans_objet) and all(res[s]["H2"] for s in res)

    # H-Cl4 : sites de fluctuation de nappe à moins de 10 km d'un forage d'une zone retenue
    sites = RF.build_sites(cdir)
    sites = sites[sites.retenu.fillna(False).astype(bool)].reset_index(drop=True)
    kept = f[f.zone.isin(z.zone)].reset_index(drop=True)
    from sklearn.neighbors import BallTree
    dd, ii = BallTree(np.radians(kept[["lat", "lon"]].to_numpy()), metric="haversine").query(np.radians(sites[["lat", "lon"]].to_numpy()), k=1)
    sites["d_km"] = dd[:, 0] * 6371.0
    sites["zone"] = kept.zone.to_numpy()[ii[:, 0]]
    proche = sites[sites.d_km <= SITE_KM].copy()
    h4 = {}
    for nom in SCENARIOS:
        rz = proche.zone.map(dict(zip(z.zone, z[f"R_{nom}"])))
        ratio = proche.r_mm / rz
        proche[f"ratio_{nom}"] = ratio
        h4[nom] = (int(((ratio >= 1 / 3) & (ratio <= 3)).sum()), int(ratio.notna().sum()))
    h4_ok = h4["central"][1] > 0 and h4["central"][0] >= h4["central"][1] / 2

    L = ["# Recharge par bilan de chlorure dans le Grand Sud", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/recharge_chlorure.py`, selon `validation/protocole_recharge_chlorure.md` "
         "(fixé avant le calcul ; dépôt de chlorure et filtres fixés le 09/11/2026 avant toute lecture des chlorures). Forages : "
         "Al-Zoubaidy, Monteleone et Bünzli (2023), BushProof / DDC, 1 487 sur 2 880 récupérés (zone ZH10 absente). Chlorure de "
         "la pluie : Kwale, Kenya (Ferrer, Folch et Thomas 2019) et Van Wyk et al. (2011). Calcul local ; données brutes hors dépôt.", "",
         "## Sélection", "", "| Étape | Forages |", "|---|---|"]
    for k, v in decompte.items():
        L.append(f"| {k} | {v} |")
    L += [f"| zones de validation (lien simple à {ZONE_KM:.0f} km, au moins {MIN_ZONE} forages) | {len(z)} zones, {int(z.n.sum())} forages |", "",
          f"Distance médiane des zones à la côte : {z.dist_km.median():.0f} km ; chlorure médian des zones : {z.cl.median():.0f} mg/L "
          f"(de {z.cl.min():.0f} à {z.cl.max():.0f}).", "",
          "## Recharge par chlorure et accord avec les cartes figées", "",
          "Écart = médiane de |log₁₀(modèle / chlorure)| (0,3 = facteur 2) ; biais = médiane de log₁₀(modèle / chlorure) (positif : modèle trop fort).", "",
          "| Scénario | Recharge médiane (mm/an) | T2 : écart | T2 : biais | T2 : Spearman (p) | T2L : écart | T2L : biais | T2L : Spearman (p) | Domaine T2L : écart T2 → T2L ({0} zones) |".format(res["central"]["n_dom"]),
          "|---|---|---|---|---|---|---|---|---|"]
    for nom, o in res.items():
        L.append(f"| {nom} | {o['R_med']:.0f} | {o['e_T2']:.2f} | {o['b_T2']:+.2f} | {o['rho_T2']:+.2f} ({o['p_T2']:.3f}) | {o['e_T2L']:.2f} | "
                 f"{o['b_T2L']:+.2f} | {o['rho_T2L']:+.2f} ({o['p_T2L']:.3f}) | {o['e_T2_dom']:.2f} → {o['e_T2L_dom']:.2f} |")
    L += ["", f"Contrôle préalable : T2 déjà à moins d'un facteur 1,5 dans les trois scénarios ? **{'oui (H-Cl2 sans objet)' if sans_objet else 'non'}**.", "",
          f"- **H-Cl1 {'soutenue' if h1 else 'non soutenue'}** (T2 suit l'ordre des zones et reste à un facteur 2, dans les trois scénarios ; "
          + ", ".join(f"{s} : {'oui' if res[s]['H1'] else 'non'}" for s in res) + ").",
          f"- **H-Cl2 {'soutenue' if h2 else 'non soutenue'}** (T2L réduit l'écart d'au moins 30 % dans son domaine, dans les trois scénarios ; "
          + ", ".join(f"{s} : {'oui' if res[s]['H2'] else 'non'}" for s in res) + ").",
          "- H-Cl3 (karst) : infaisable, aucun forage karstique dans les données récupérées.",
          f"- **H-Cl4 {'soutenue' if h4_ok else 'non soutenue'}** (fluctuation et chlorure dans un facteur 3 pour au moins la moitié des sites, "
          f"scénario central : {h4['central'][0]} sur {h4['central'][1]} ; bas : {h4['bas'][0]} sur {h4['bas'][1]} ; haut : {h4['haut'][0]} sur {h4['haut'][1]}).", "",
          "## Sites de fluctuation de nappe proches d'une zone (H-Cl4)", "",
          "| Site | Source | Distance (km) | Fluctuation (mm/an) | Chlorure, central (mm/an) | Rapport bas / central / haut |", "|---|---|---|---|---|---|"]
    for x in proche.itertuples():
        rc = dict(zip(z.zone, z.R_central)).get(x.zone, np.nan)
        L.append(f"| {x.site} | {x.source} | {x.d_km:.1f} | {x.r_mm:.0f} | {rc:.0f} | "
                 f"{getattr(x, 'ratio_bas'):.2f} / {getattr(x, 'ratio_central'):.2f} / {getattr(x, 'ratio_haut'):.2f} |")
    if proche.empty:
        L.append("| — | — | — | — | — | aucun site à moins de 10 km |")
    L += ["", "## Décision (fixée avant le calcul)", "",
          ("T2L devient la valeur centrale dans son domaine ; l'atlas par sous-bassin est refait." if h2 else
           "T2 reste la valeur centrale ; la recharge par chlorure est publiée comme estimation indépendante du Grand Sud, avec ses trois scénarios."), "",
          "Limites : chlorure d'autres origines (roches marines, évaporites, embruns, pollution) seulement en partie filtré ; "
          "recharge de long terme (décennies) contre années récentes pour la fluctuation ; recharge concentrée mal vue ; base "
          "compilée de qualité hétérogène ; dépôt de chlorure non mesuré à Madagascar (sources kényane et sud-africaine) ; "
          "longueur de décroissance L choisie.", ""]
    (ROOT / "validation" / "recharge_chlorure.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    z.assign(lat=z.lat.round(1), lon=z.lon.round(1)).drop(columns=["zone"]).round(3).to_csv(
        ROOT / "validation" / "recharge_chlorure_zones.csv", index=False)
    print(json.dumps({"H1": h1, "H2": h2, "sans_objet": sans_objet, "H4": h4, "zones": len(z)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
