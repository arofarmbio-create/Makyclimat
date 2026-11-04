"""Bassins hydrogéologiques (écoulement sur la surface de la nappe) comparés aux bassins de surface
(validation/protocole_bassins_hydrogeologiques.md, fixé avant le calcul).

Charge h = altitude GLO-90 (0,005°) − profondeur du niveau statique (carte v2, fokontany le plus proche). Même chaîne
que build_hydro.process : la mer et la pente viennent du terrain, l'écoulement suit h. Mailles divergentes : bassin
différent dans les deux découpages (bassin hydrogéologique apparié au bassin de surface le plus recouvrant).
Lancé sur GitHub (workflow 28). Sorties : validation/bassins_hydrogeologiques.md, inputs/hydrogeologie/divergence_bassins.csv.
Usage : python scripts/bassins_hydrogeologiques.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

import build_hydro as BH
from common import ROOT, country_data_dir, load_config, read_units

FLAT_PCT = 2.0


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


def depth_raster(shape, lon0, lat0, res, lon, lat, depth) -> np.ndarray:
    from scipy.spatial import cKDTree
    h, w = shape
    xs = lon0 + (np.arange(w) + 0.5) * res
    ys = lat0 - (np.arange(h) + 0.5) * res
    tree = cKDTree(np.c_[lon, lat])
    out = np.empty(shape, dtype="float32")
    for i in range(0, h, 200):                     # par bandes (mémoire)
        X, Y = np.meshgrid(xs, ys[i:i + 200])
        _, j = tree.query(np.c_[X.ravel(), Y.ravel()])
        out[i:i + 200] = np.asarray(depth)[j].reshape(X.shape)
    return out


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
    fk = units[units.level == 4][["pcode", "lon", "lat", "adm1"]]
    c = pd.read_csv(country_data_dir(args.country) / "external" / "nappes_carte.csv", dtype={"pcode": str})
    d = c[c.indicateur == "niveau_statique_m"].set_index("pcode").valeur
    fk = fk.assign(depth=fk.pcode.map(d)).dropna(subset=["depth"])
    depth = depth_raster(dem.shape, lon0, lat0, res, fk.lon.to_numpy(), fk.lat.to_numpy(), fk.depth.to_numpy())
    P_sf = BH.process(dem, lon0, lat0, res, hcfg, dem_min)
    head = dem_min - depth
    P_gw = BH.process(dem, lon0, lat0, res, hcfg, head)
    land = ~P_sf["sea"]
    lab_sf, lab_gw = P_sf["lab_main"].reshape(dem.shape), P_gw["lab_main"].reshape(dem.shape)
    r = divergence(lab_gw, lab_sf, land, P_sf["slope"])
    # par bassin de surface (bassins d'au moins 500 km² : mailles « big » de process)
    per = pd.DataFrame({"bassin": lab_sf[land], "div": r["div"][land]}).groupby("bassin")["div"].agg(["size", "mean"]).reset_index()
    per.columns = ["bassin_surface", "mailles", "part_divergente"]
    per = per[per.mailles >= 20000].sort_values("part_divergente", ascending=False)
    out = ROOT / "inputs" / "hydrogeologie"
    out.mkdir(parents=True, exist_ok=True)
    per.round(4).to_csv(out / "divergence_bassins.csv", index=False)
    L = ["# Bassins hydrogéologiques et bassins de surface", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/bassins_hydrogeologiques.py` (workflow 28), selon "
         "`validation/protocole_bassins_hydrogeologiques.md` (fixé avant le calcul). Terrain : Copernicus GLO-90 à 0,005° ; "
         "profondeur : carte du niveau statique v2.", "",
         f"- Mailles terrestres dans un bassin différent : **{r['part_divergente']:.1%}**. **H-B1 {'soutenue' if r['H_B1'] else 'non soutenue'}** "
         "(règle : au plus 5 %).",
         f"- Taux de divergence : pente < 2 % : {r['taux_plat']:.1%} ; pente ≥ 2 % : {r['taux_pente']:.1%}. "
         f"**H-B2 {'soutenue' if r['H_B2'] else 'non soutenue'}** (règle : au moins deux fois plus en zone plate).", "",
         "## Bassins de surface les plus concernés (au moins 20 000 mailles, environ 500 km²)", "",
         "| Bassin de surface (étiquette de calcul) | Mailles | Part divergente |", "|---|---|---|"]
    for x in per.head(15).itertuples():
        L.append(f"| {x.bassin_surface} | {x.mailles} | {x.part_divergente:.1%} |")
    L += ["", "Limite : la charge dépend de la profondeur estimée (approximative hors du Grand Sud) ; un écart indique un passage "
          "possible de l'eau souterraine entre bassins, pas un flux mesuré.", ""]
    (ROOT / "validation" / "bassins_hydrogeologiques.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Divergence {r['part_divergente']:.1%} ; plat {r['taux_plat']:.1%} ; pente {r['taux_pente']:.1%}")


if __name__ == "__main__":
    main()
