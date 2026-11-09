"""Bassins hydrogéologiques (écoulement sur la surface de la nappe) comparés aux bassins de surface
(validation/protocole_bassins_hydrogeologiques.md, fixé avant le calcul ; test H-B2-L ajouté le 09/11/2026).

Charge h = altitude GLO-90 (0,005°) − profondeur du niveau statique (carte v2). Deux variantes de profondeur : fokontany
le plus proche (calcul initial) et moyenne des 8 plus proches pondérée par 1/d² (test H-B2-L, sans marches aux limites).
Même chaîne que build_hydro.process : la mer et la pente viennent du terrain, l'écoulement suit h. Mailles divergentes :
bassin différent dans les deux découpages (bassin hydrogéologique apparié au bassin de surface le plus recouvrant).
Lancé sur GitHub (workflow 28). Sorties : validation/bassins_hydrogeologiques.md, inputs/hydrogeologie/divergence_bassins.csv,
inputs/hydrogeologie/divergence_regions.csv.
Usage : python scripts/bassins_hydrogeologiques.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import json

import numpy as np
import pandas as pd

import build_hydro as BH
from common import ROOT, country_data_dir, load_config, read_units

FLAT_PCT = 2.0
SMALL = "petits bassins côtiers"


def match_labels(lab_gw: np.ndarray, lab_sf: np.ndarray, land: np.ndarray) -> np.ndarray:
    """Pour chaque bassin hydrogéologique, le bassin de surface le plus recouvrant ; renvoie la carte réétiquetée."""
    g, s = lab_gw[land], lab_sf[land]
    df = pd.DataFrame({"g": g, "s": s})
    best = df.groupby(["g", "s"]).size().reset_index(name="n").sort_values("n").drop_duplicates("g", keep="last")
    m = dict(zip(best.g, best.s))
    out = np.zeros_like(lab_sf)
    out[land] = np.array([m.get(x, -1) for x in g])
    return out


def divergence(lab_gw, lab_sf, land, slope) -> dict:
    mapped = match_labels(lab_gw, lab_sf, land)
    div = land & (mapped != lab_sf)
    flat = land & np.isfinite(slope) & (slope < FLAT_PCT)
    steep = land & np.isfinite(slope) & (slope >= FLAT_PCT)
    r_flat = float(div[flat].mean()) if flat.any() else np.nan
    r_steep = float(div[steep].mean()) if steep.any() else np.nan
    return {"div": div, "part_divergente": float(div[land].mean()), "taux_plat": r_flat, "taux_pente": r_steep,
            "H_B1": bool(div[land].mean() <= 0.05), "H_B2": bool(r_steep > 0 and r_flat >= 2 * r_steep) if np.isfinite(r_flat) else False}


def depth_raster(shape, lon0, lat0, res, lon, lat, depth, k: int = 1, return_idx: bool = False):
    """Profondeur par maille : fokontany le plus proche (k=1) ou moyenne des k plus proches pondérée par 1/d²
    (test H-B2-L). Avec return_idx, renvoie aussi l'indice du fokontany le plus proche (pour la région)."""
    from scipy.spatial import cKDTree
    h, w = shape
    xs = lon0 + (np.arange(w) + 0.5) * res
    ys = lat0 - (np.arange(h) + 0.5) * res
    tree = cKDTree(np.c_[lon, lat])
    depth = np.asarray(depth, dtype="float64")
    k = min(k, len(depth))
    out = np.empty(shape, dtype="float32")
    idx = np.empty(shape, dtype="int32") if return_idx else None
    for i in range(0, h, 200):                     # par bandes (mémoire)
        X, Y = np.meshgrid(xs, ys[i:i + 200])
        dist, j = tree.query(np.c_[X.ravel(), Y.ravel()], k=k)
        if k == 1:
            v, j0 = depth[j], j
        else:
            wgt = 1.0 / np.maximum(dist, 1e-9) ** 2
            v, j0 = (depth[j] * wgt).sum(1) / wgt.sum(1), j[:, 0]
        out[i:i + 200] = v.reshape(X.shape)
        if return_idx:
            idx[i:i + 200] = j0.reshape(X.shape)
    return (out, idx) if return_idx else out


def table_by(keys, divs: dict) -> pd.DataFrame:
    """Nombre de mailles et part de mailles divergentes par groupe, pour chaque variante de profondeur."""
    d = pd.DataFrame({"g": np.asarray(keys), **divs})
    return d.groupby("g").agg(mailles=("g", "size"), **{c: (c, "mean") for c in divs}).reset_index()


def ratio(r: dict) -> float:
    return r["taux_plat"] / r["taux_pente"] if r["taux_pente"] > 0 else float("inf")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cfg = load_config(args.country)
    hcfg = cfg.get("hydro", {})
    res = hcfg.get("res_deg", 0.005)
    bbox = hcfg.get("bbox") or cfg["map"]["bbox"]
    dem, lon0, lat0 = BH.read_dem(bbox, res)
    dem_min, _, _ = BH.read_dem(bbox, res, how="min")
    units = read_units(args.country)
    regs = units[units.level == 1]
    reg_name = dict(zip(regs.pcode, regs.name))
    fk = units[units.level == 4][["pcode", "lon", "lat", "adm1"]]
    c = pd.read_csv(country_data_dir(args.country) / "external" / "nappes_carte.csv", dtype={"pcode": str})
    d = c[c.indicateur == "niveau_statique_m"].set_index("pcode").valeur
    fk = fk.assign(depth=fk.pcode.map(d)).dropna(subset=["depth"]).reset_index(drop=True)
    xy = (fk.lon.to_numpy(), fk.lat.to_numpy(), fk.depth.to_numpy())
    dep_nn, idx = depth_raster(dem.shape, lon0, lat0, res, *xy, return_idx=True)
    dep_ls = depth_raster(dem.shape, lon0, lat0, res, *xy, k=8)

    P_sf = BH.process(dem, lon0, lat0, res, hcfg, dem_min)
    land = ~P_sf["sea"]
    lab_sf = P_sf["lab_main"].reshape(dem.shape)
    R = {}
    for key, dep in (("proche", dep_nn), ("lissee", dep_ls)):
        P_gw = BH.process(dem, lon0, lat0, res, hcfg, dem_min - dep)
        R[key] = divergence(P_gw["lab_main"].reshape(dem.shape), lab_sf, land, P_sf["slope"])
        del P_gw
    a, b = R["proche"], R["lissee"]
    divs = {"part_divergente": a["div"][land], "part_divergente_lissee": b["div"][land]}

    # Noms des grands bassins (mêmes identifiants que hydro.npz et basins.geojson) ; 0 = petit bassin côtier
    main_grid = BH.rank_basins(P_sf, res)[0]
    gj = json.loads((ROOT / "docs" / "data" / args.country / "hydro" / "basins.geojson").read_text(encoding="utf-8"))
    names = {int(f["properties"]["id"]): f["properties"]["name"] for f in gj["features"]}
    mid = main_grid[land]
    per = table_by(lab_sf[land], divs).rename(columns={"g": "bassin_surface"})
    ids = pd.DataFrame({"g": lab_sf[land], "id": mid}).groupby("g").id.max()
    per["id"] = per.bassin_surface.map(ids).fillna(0).astype(int)
    per["nom"] = [names.get(i, f"Bassin {i}") if i > 0 else SMALL for i in per.id]
    per = per[per.mailles >= 20000].sort_values("part_divergente", ascending=False)
    size = table_by(np.where(mid > 0, "grands bassins (nommés)", SMALL), divs)
    reg_of_fk = np.array([reg_name.get(x, x) for x in fk.adm1.to_numpy()], dtype=object)
    reg = table_by(reg_of_fk[idx[land]], divs).sort_values("part_divergente", ascending=False)

    out = ROOT / "inputs" / "hydrogeologie"
    out.mkdir(parents=True, exist_ok=True)
    per[["bassin_surface", "id", "nom", "mailles", "part_divergente", "part_divergente_lissee"]].round(4).to_csv(
        out / "divergence_bassins.csv", index=False)
    reg.rename(columns={"g": "region"}).round(4).to_csv(out / "divergence_regions.csv", index=False)

    L = ["# Bassins hydrogéologiques et bassins de surface", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/bassins_hydrogeologiques.py` (workflow 28), selon "
         "`validation/protocole_bassins_hydrogeologiques.md` (fixé avant le calcul ; test H-B2-L ajouté le 09/11/2026, avant "
         "son calcul). Terrain : Copernicus GLO-90 à 0,005° ; profondeur : carte du niveau statique v2.", "",
         "| Profondeur utilisée | Mailles dans un autre bassin | Pente < 2 % | Pente ≥ 2 % | Rapport plat/pente | H-B1 | H-B2 |",
         "|---|---|---|---|---|---|---|"]
    for lab, r in (("fokontany le plus proche (calcul initial)", a), ("lissée : 8 fokontany, 1/d² (test H-B2-L)", b)):
        L.append(f"| {lab} | {r['part_divergente']:.1%} | {r['taux_plat']:.1%} | {r['taux_pente']:.1%} | {ratio(r):.1f} | "
                 f"{'soutenue' if r['H_B1'] else 'non soutenue'} | {'soutenue' if r['H_B2'] else 'non soutenue'} |")
    verdict = "robuste" if b["H_B2"] else "dépendante de la méthode (non présentée comme résultat)"
    L += ["", f"**Test H-B2-L : H-B2 {verdict}** (règle fixée avant le test : rapport plat/pente d'au moins 2 avec la "
          "profondeur lissée).", "",
          "## Par taille de bassin", "", "| Groupe | Mailles | Profondeur la plus proche | Profondeur lissée |", "|---|---|---|---|"]
    for x in size.itertuples():
        L.append(f"| {x.g} | {x.mailles:,} | {x.part_divergente:.1%} | {x.part_divergente_lissee:.1%} |")
    L += ["", "## Par région (région du fokontany le plus proche)", "",
          "| Région | Mailles | Profondeur la plus proche | Profondeur lissée |", "|---|---|---|---|"]
    for x in reg.itertuples():
        L.append(f"| {x.g} | {x.mailles:,} | {x.part_divergente:.1%} | {x.part_divergente_lissee:.1%} |")
    L += ["", "## Bassins de surface les plus concernés (au moins 20 000 mailles, environ 500 km²)", "",
          "| Bassin | Mailles | Profondeur la plus proche | Profondeur lissée |", "|---|---|---|---|"]
    for x in per.head(15).itertuples():
        L.append(f"| {x.nom} (n° {x.id}) | {x.mailles:,} | {x.part_divergente:.1%} | {x.part_divergente_lissee:.1%} |")
    L += ["", "Limite : la charge dépend de la profondeur estimée (approximative hors du Grand Sud) ; un écart indique un passage "
          "possible de l'eau souterraine entre bassins, pas un flux mesuré.", ""]
    (ROOT / "validation" / "bassins_hydrogeologiques.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    for k, r in R.items():
        print(f"{k} : {r['part_divergente']:.1%} ; plat {r['taux_plat']:.1%} ; pente {r['taux_pente']:.1%} ; rapport {ratio(r):.1f}")


if __name__ == "__main__":
    main()
