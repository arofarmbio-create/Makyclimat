"""Protocole M3 (validation/protocole_nappes_mgmerl.md), étape 1 : indices du système aux sites des dataloggers MGMERL.

Pour chaque site de inputs/mgmerl/mgmerl_dataloggers_ht_analytics_sites.csv, à la maille CHIRPS (0,05°) du site :
pluie mensuelle, SPI-1 à SPI-24 et recharge12_z, calculés avec exactement les fonctions de production
(build_soilwater.rain_series, static_props, et0_grid ; soilwater_core.run_balance, spi, monthly_standardized).
Les niveaux de nappe eux-mêmes ne sont pas lus ici (fichiers bruts MGMERL gardés hors git, traités par
validate_nappes_mgmerl.py sur le poste local).
Sortie : data/<pays>/nappes_sites_indices.csv (site, mois, pluie_mm, spi1..spi24, recharge12_z).
Usage : python scripts/build_nappes_sites.py --country mdg
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

import build_soilwater as B
import soilwater_core as C
from common import ROOT, country_data_dir, grid_dir, load_config, load_grid

SITES = ROOT / "inputs" / "mgmerl" / "mgmerl_dataloggers_ht_analytics_sites.csv"
NMAX = 24


def site_cells(lats, lons, grid, valid):
    """Maille (ligne, colonne) de chaque site ; maille non valide (mer, sol inconnu) -> maille valide la plus proche."""
    rows = np.clip(np.floor((grid["lat0"] - np.asarray(lats)) / grid["res"]).astype(int), 0, grid["h"] - 1)
    cols = np.clip(np.floor((np.asarray(lons) - grid["lon0"]) / grid["res"]).astype(int), 0, grid["w"] - 1)
    vr, vc = np.nonzero(valid)
    out = []
    for r, c in zip(rows, cols):
        if valid[r, c]:
            out.append((int(r), int(c), 0.0))
        else:
            k = int(np.argmin((vr - r) ** 2 + (vc - c) ** 2))
            out.append((int(vr[k]), int(vc[k]), float(np.hypot(vr[k] - r, vc[k] - c)) * grid["res"]))
    return out


def site_indices(P, pet, whc, cn2, month0=11):
    """P (T, N) pluie mensuelle ; pet (12, N) ; whc, cn2 (N,). Retourne {spi1..spiNMAX, recharge12_z} en (T, N)."""
    out = {f"spi{n}": C.spi(P, n, month0) for n in range(1, NMAX + 1)}
    _, _, X, _ = C.run_balance(P, pet, whc, month0=month0, cn2=cn2)
    out["recharge12_z"] = C.monthly_standardized(C.rolling_sum(X, 12), month0)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    cfg = load_config(args.country)
    ms = load_grid(grid_dir(args.country) / "monthly_series.npz")
    h, w = ms["arr"].shape[-2:]
    grid = {"lon0": float(ms["lon0"]), "lat0": float(ms["lat0"]), "res": float(ms["res"]), "h": int(h), "w": int(w)}
    rd = {"soil": B.read_soilgrids, "landcover": B.read_worldcover, "et0": B.read_et0_points, "chirps": B.read_chirps_month}
    land = np.isfinite(np.asarray(ms["arr"][-1, 0], dtype="float32"))
    props = B.static_props(grid, rd, grid_dir(args.country) / "soilprops.npz")
    et0 = B.et0_grid(grid, land, rd, grid_dir(args.country) / "et0_cache.json", 150)
    rain = B.rain_series(grid, cfg, args.country, rd["chirps"])
    if props is None or et0 is None or rain is None:
        raise SystemExit("propriétés du sol, ET0 ou pluie indisponibles (voir build_soilwater)")
    P, labels = rain
    valid = land & np.isfinite(props["whc"]) & np.isfinite(et0[0]) & (props["whc"] > 0)
    sites = pd.read_csv(SITES, dtype={"code": str}).dropna(subset=["lat", "lon"])
    cells = site_cells(sites.lat, sites.lon, grid, valid)
    rr, cc = np.array([c[0] for c in cells]), np.array([c[1] for c in cells])
    Ps = np.nan_to_num(P[:, rr, cc], nan=0.0).astype("float64")
    pet = np.stack([et0[m][rr, cc] for m in range(12)]).astype("float64")
    ind = site_indices(Ps, pet, props["whc"][rr, cc].astype("float64"), props["cn2"][rr, cc].astype("float64"))
    frames = []
    for i, s in enumerate(sites.itertuples()):
        d = pd.DataFrame({"site": s.site, "mois": labels, "pluie_mm": np.round(Ps[:, i], 1)})
        for k, v in ind.items():
            d[k] = np.round(v[:, i], 3)
        d.insert(2, "decalage_maille_deg", round(cells[i][2], 3))
        frames.append(d)
    out = country_data_dir(args.country) / "nappes_sites_indices.csv"
    pd.concat(frames).to_csv(out, index=False)
    print(f"{out.name} : {len(sites)} sites, {labels[0]} à {labels[-1]} ({len(labels)} mois)")


if __name__ == "__main__":
    main()
