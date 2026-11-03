"""Test H-C2 du protocole de la carte des nappes (précisions du 02/11/2026) : un modèle hybride (Fan + correction apprise
sur les forages malgaches) prédit-il la profondeur de l'eau mieux que la carte de Fan seule et que le krigeage des
seules mesures, dans des zones qu'il n'a jamais vues ?

Validation par blocs de 1° (au moins 5 forages) ; erreur du bloc = médiane des erreurs absolues (m) ; H-C2 confirmée
si l'hybride bat Fan ET le krigeage dans plus de la moitié des blocs (tests du signe unilatéraux, 5 % chacun).
Entrées : relevé MGMERL du 02/11/2026 (hors git), fan.tif (licence sans republication, jamais publié), couches
mondiales (glim.tif, glhymps.gpkg, socle.tif), relief et pluie du système. Sorties : validation/nappes_hc2.md,
validation/nappes_hc2_blocs.csv (statistiques par bloc seulement).
Usage : python scripts/validate_nappes_hc2.py --country mdg [--couches DOSSIER]
"""
from __future__ import annotations

import argparse
import datetime as dt

import numpy as np
import pandas as pd

import validate_nappes_hc1 as H1
from common import ROOT, country_data_dir, grid_dir, load_grid

N_TREES, MIN_LEAF, MIN_BLOCK = 500, 5, 5
STREAM_ACC = 1000
FEATURES = ["fan_m", "hand", "pente", "log_acc", "dist_riviere_km", "glim", "logk", "porosite", "socle_m", "pluie_mm",
            "altitude_m", "rugosite_m", "productivite"]


# ---------------- variables au point ----------------
def grid_sample(arr, lon0, lat0, res, lons, lats):
    r = np.clip(np.floor((lat0 - np.asarray(lats)) / res).astype(int), 0, arr.shape[0] - 1)
    c = np.clip(np.floor((np.asarray(lons) - lon0) / res).astype(int), 0, arr.shape[1] - 1)
    return np.asarray(arr)[r, c].astype(float)


def stream_distance_km(acc, lon0, lat0, res, lons, lats):
    """Distance (km) au pixel de cours d'eau le plus proche (accumulation ≥ STREAM_ACC)."""
    from scipy import ndimage
    stream = np.asarray(acc, dtype=float) >= STREAM_ACC
    d = ndimage.distance_transform_edt(~stream) * res * 111.0
    return grid_sample(d, lon0, lat0, res, lons, lats)


def point_features(country, pts: pd.DataFrame, couches) -> pd.DataFrame:
    import rasterio
    out = pts.copy()
    lons, lats = pts.lon.to_numpy(), pts.lat.to_numpy()
    out["fan_m"] = H1.fan_depth(H1.sample_raster(couches / "fan.tif", lons, lats))
    h = load_grid(grid_dir(country) / "hydro.npz")
    g = (float(h["lon0"]), float(h["lat0"]), float(h["res"]))
    out["hand"] = grid_sample(h["hand"], *g, lons, lats)
    out["pente"] = grid_sample(h["slope"], *g, lons, lats)
    out["log_acc"] = np.log10(grid_sample(h["acc"], *g, lons, lats) + 1)
    out["dist_riviere_km"] = stream_distance_km(h["acc"], *g, lons, lats)
    out["glim"] = H1.sample_raster(couches / "glim.tif", lons, lats)
    with rasterio.open(couches / "socle.tif") as s:
        v = np.array([x[0] for x in s.sample(zip(lons, lats))], dtype=float)
        if s.nodata is not None:
            v[v == s.nodata] = np.nan
    out["socle_m"] = v / 100.0
    out[["logk", "porosite"]] = glhymps_at(couches / "glhymps.gpkg", lons, lats)
    c = load_grid(grid_dir(country) / "clim_monthly.npz")
    ann = np.nansum(np.asarray(c["clim"], dtype=float), axis=0)
    out["pluie_mm"] = grid_sample(ann, float(c["lon0"]), float(c["lat0"]), float(c["res"]), lons, lats)
    rel = np.load(country_data_dir(country) / "e1" / "relief_01deg.npz")
    keys = {k.lower(): k for k in rel.files}
    la, lo = rel[keys.get("lat", "lat")], rel[keys.get("lon", "lon")]
    ii = np.abs(la[None, :] - lats[:, None]).argmin(1)
    jj = np.abs(lo[None, :] - lons[:, None]).argmin(1)
    alt = rel[next(k for k in rel.files if "alt" in k.lower() and "std" not in k.lower())]
    rug = rel[next(k for k in rel.files if "rug" in k.lower() or "std" in k.lower())]
    out["altitude_m"], out["rugosite_m"] = alt[ii, jj], rug[ii, jj]
    return out


def glhymps_at(path, lons, lats) -> np.ndarray:
    """logK (×100 dans le fichier, ramené à logK) et porosité (×100, ramenée à une fraction) du polygone du point."""
    import geopandas as gpd
    g = gpd.read_file(path)
    cols = {c.lower(): c for c in g.columns}
    kc = next(cols[c] for c in cols if c.startswith("logk_ferr"))
    pc = next(cols[c] for c in cols if c.startswith("porosity"))
    p = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lons, lats), crs="EPSG:4326").to_crs(g.crs)
    j = gpd.sjoin(p, g[[kc, pc, "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    return np.column_stack([j[kc].to_numpy(float) / 100.0, j[pc].to_numpy(float) / 100.0])


# ---------------- modèles ----------------
def hybrid_predict(train: pd.DataFrame, test: pd.DataFrame, seed=0, features=None):
    from quantile_forest import RandomForestQuantileRegressor
    feats = [f for f in (features or FEATURES) if f in train]
    xtr, xte = train[feats].fillna(-999).to_numpy(), test[feats].fillna(-999).to_numpy()
    y = (train.mesure_m - train.fan_m).to_numpy()
    m = RandomForestQuantileRegressor(n_estimators=N_TREES, min_samples_leaf=MIN_LEAF, random_state=seed, n_jobs=-1)
    m.fit(xtr, y)
    q = m.predict(xte, quantiles=[0.1, 0.5, 0.9])
    base = test.fan_m.to_numpy()
    return np.maximum(base + q[:, 1], 0), np.maximum(base + q[:, 0], 0), np.maximum(base + q[:, 2], 0)


def kriging_predict(train: pd.DataFrame, test: pd.DataFrame):
    from pykrige.ok import OrdinaryKriging
    ok = OrdinaryKriging(train.lon.to_numpy(), train.lat.to_numpy(), train.mesure_m.to_numpy(),
                         variogram_model="exponential", coordinates_type="geographic")
    z, _ = ok.execute("points", test.lon.to_numpy(), test.lat.to_numpy())
    return np.maximum(np.asarray(z), 0)


def block_cv(df: pd.DataFrame, hybrid=hybrid_predict, krige=kriging_predict) -> pd.DataFrame:
    df = df.assign(bloc=np.floor(df.lat).astype(int).astype(str) + "/" + np.floor(df.lon).astype(int).astype(str))
    rows = []
    for b, g in df.groupby("bloc"):
        if len(g) < MIN_BLOCK:
            continue
        tr = df[df.bloc != b]
        ph, lo, hi = hybrid(tr, g)
        pk = krige(tr, g)
        obs = g.mesure_m.to_numpy()
        rows.append({"bloc": b, "forages": len(g), "erreur_fan": float(np.median(np.abs(g.fan_m - obs))),
                     "erreur_hybride": float(np.median(np.abs(ph - obs))), "erreur_krigeage": float(np.median(np.abs(pk - obs))),
                     "couverture_80": float(np.mean((obs >= lo) & (obs <= hi)))})
    return pd.DataFrame(rows)


def sign_test(a, b):
    from scipy import stats
    d = np.asarray(a) - np.asarray(b)
    w, n = int((d < 0).sum()), int((d != 0).sum())
    return w, n, float(stats.binomtest(w, n, 0.5, alternative="greater").pvalue) if n else float("nan")


def report(res: pd.DataFrame, n_pts: int) -> tuple[str, bool]:
    w1, n1, p1 = sign_test(res.erreur_hybride, res.erreur_fan)
    w2, n2, p2 = sign_test(res.erreur_hybride, res.erreur_krigeage)
    ok = p1 < 0.05 and p2 < 0.05
    L = ["# H-C2 : modèle hybride de profondeur de l'eau contre la carte mondiale et le krigeage", "",
         f"Généré le {dt.date.today().isoformat()} par `scripts/validate_nappes_hc2.py`, selon "
         "`validation/protocole_carte_nappes.md` (précisions du 02/11/2026, fixées avant le calcul). Forages : MGMERL "
         f"({n_pts} points) ; carte mondiale : Fan et al. (2017), valeurs non republiées.", "",
         f"Validation par blocs de 1° (au moins {MIN_BLOCK} forages) : {len(res)} blocs, chacun prédit sans aucun de ses forages.", "",
         "| Méthode | Erreur absolue médiane entre blocs (m) | Blocs où l'hybride fait mieux | p (signe) |", "|---|---|---|---|",
         f"| Carte de Fan seule | {res.erreur_fan.median():.1f} | {w1} sur {n1} | {p1:.3f} |",
         f"| Krigeage des mesures | {res.erreur_krigeage.median():.1f} | {w2} sur {n2} | {p2:.3f} |",
         f"| **Modèle hybride** | **{res.erreur_hybride.median():.1f}** | — | — |", "",
         f"Couverture médiane de l'intervalle de 80 % de l'hybride : {res.couverture_80.median():.0%} (attendu : 80 %).", "",
         f"**H-C2 {'confirmée' if ok else 'non confirmée'}** (l'hybride doit battre les deux références, p < 0,05 chacune).", "",
         "Limites : forages regroupés autour des projets, surtout dans le Sud ; pas de carte des failles ; niveau statique "
         "ponctuel ; le modèle prédit le niveau de l'eau dans un forage, pas la profondeur à forer."]
    return "\n".join(L) + "\n", ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--couches", default=None, help="dossier contenant fan.tif, glim.tif, glhymps.gpkg, socle.tif")
    args = ap.parse_args()
    from pathlib import Path
    couches = Path(args.couches) if args.couches else country_data_dir(args.country) / "nappes_mondiales"
    src = country_data_dir(args.country) / "mgmerl_raw" / "complet_2026-11-03" / "mgmerl_niveau_statique_complet.csv"
    pts = H1.load_points(src)
    df = point_features(args.country, pts, couches)
    geo = pd.read_csv(country_data_dir(args.country) / "external" / "geology.csv")
    prod = geo[geo.indicateur == "aquifer_productivity_pct"].set_index("pcode").valeur
    from common import locate_points
    pc = locate_points(args.country, df.lon.tolist(), df.lat.tolist())
    df["productivite"] = [float(prod[c]) if c in prod.index else np.nan for c in pc]
    df = df[np.isfinite(df.fan_m)].reset_index(drop=True)
    res = block_cv(df)
    text, _ = report(res, len(df))
    (ROOT / "validation" / "nappes_hc2.md").write_text(text, encoding="utf-8")
    res.round(3).to_csv(ROOT / "validation" / "nappes_hc2_blocs.csv", index=False)
    print(text)


if __name__ == "__main__":
    main()
