"""Validation au niveau fokontany avec les cartes de dégâts Copernicus EMS (satellite) : bâtiments gradés et zones inondées.

Vérité de terrain : pour chaque activation EMS sur un cyclone à Madagascar, les fichiers vectoriels
  - areaOfInterest : zone réellement cartographiée (hors zone = inconnu, jamais compté comme « épargné ») ;
  - builtUpP (produits « grading ») : bâtiments classés Destroyed / Damaged / Possibly damaged / No visible damage ;
  - observedEventA : zones inondées.
Un fokontany est « touché » s'il contient au moins un bâtiment Destroyed ou Damaged, ou si au moins 5 % de sa surface est inondée.
Il est « évalué » si au moins 50 % de sa surface est dans une zone cartographiée (ou s'il est touché).
Modèle : mêmes variables que validate_events (empreinte de vent par quadrants, pluie exceptionnelle locale), mais par fokontany ;
régression logistique évaluée en laissant chaque événement de côté. Puis agrégation à la commune (touchée si un fokontany évalué l'est).
Limites : les cartes EMS couvrent surtout des villes et des zones accessibles aux satellites ; l'imagerie est prise quelques jours après ;
nuages ; classement « possibly damaged » écarté ; l'exposition n'est pas la vulnérabilité.
Usage : python scripts/validate_fokontany.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import io
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from common import DATA_DIR, country_docs_dir, grid_dir, load_config, read_units, write_json
from validate_events import VAL_DIR, auc, confusion, fetch_ibtracs, footprint, loeo, project, train

EVENTS = {"EMSR197": ("Enawo", 2017), "EMSR264": ("Ava", 2018), "EMSR274": ("Eliakim", 2018), "EMSR564": ("Batsirai", 2022),
          "EMSR565": ("Emnati", 2022), "EMSR645": ("Cheneso", 2023), "EMSR652": ("Freddy", 2023)}
H = {"User-Agent": "Mozilla/5.0 MakyClimat (recherche doctorale)"}
AREA_CRS = "EPSG:6933"
COLS = ["cov34", "cov50", "cov64", "lrp", "lratio"]
TERRAIN = ["lhand5", "lhand15", "lslope", "lelev", "lriver", "lpopdens"]


def list_zips(code):
    t = requests.get(f"https://rapidmapping.emergency.copernicus.eu/{code}/", timeout=60, headers=H).text
    return sorted(set(re.findall(r"https://cems-mapping-website[^\"'\s<>]+_vector\.zip", t)))


def fetch_zip(url, dest: Path):
    f = dest / url.split("/")[-1].replace(".zip", "")
    if f.exists():
        return f
    b = requests.get(url, timeout=600, headers=H).content
    f.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(b)).extractall(f)
    return f


def read_layers(code, tmp: Path):
    """Retourne (aoi, floods, buildings) en GeoDataFrames WGS84 (éventuellement vides)."""
    import geopandas as gpd
    urls = list_zips(code)
    with ThreadPoolExecutor(6) as ex:
        dirs = list(ex.map(lambda u: fetch_zip(u, tmp / code), urls))
    aoi, fl, bl = [], [], []
    names = set()
    for d in dirs:
        for shp in glob.glob(f"{d}/**/*.shp", recursive=True):
            nm = Path(shp).name
            names.add(re.sub(r"EMSR\d+_[A-Z0-9]+_[A-Z]+_[A-Za-z0-9]+_", "", nm))
            kind = ("aoi" if re.search(r"areaOfInterest|area_of_interest", nm) else "flood" if re.search(r"observedEvent|observed_event", nm)
                    else "bld" if re.search(r"builtUp[PA]_|built_up_[pa]\.|built_up_[pa]_", nm) else "crisis" if "crisis_information" in nm else None)
            if not kind:
                continue
            try:
                g = gpd.read_file(shp)
            except Exception as e:  # noqa: BLE001
                print("  lecture impossible", nm, e)
                continue
            if g.empty:
                continue
            g = g.to_crs(4326) if g.crs else g.set_crs(4326)
            if kind == "aoi":
                aoi.append(g[["geometry"]])
            elif kind == "flood":
                ev = g.get("event_type", pd.Series([""] * len(g))).astype(str)
                nt = g.get("notation", pd.Series([""] * len(g))).astype(str)
                fl.append(g[ev.str.contains("Flood", case=False) | nt.str.contains("Flood", case=False)][["geometry"]])
            elif kind == "crisis":
                print("  crisis_information :", Path(shp).name[-40:], list(g.columns)[:10], {c: g[c].astype(str).value_counts().head(5).to_dict() for c in g.columns if c.lower().startswith(("dmg", "damage", "event", "obj_desc", "notation"))})
            elif kind == "bld":
                dc = next((c for c in g.columns if c.lower() in ("damage_gra", "dmg_grade", "damage_grade") or "damage" in c.lower()), None)
                if dc is None:
                    print("  built_up sans classe de dégât :", Path(shp).name[-30:], list(g.columns)[:10])
                    continue
                b = g[[dc, "geometry"]].rename(columns={dc: "damage_gra"}).copy()
                b["geometry"] = b.geometry.representative_point()
                bl.append(b)
    if not (aoi or fl or bl):
        print("  couches non reconnues, exemples :", sorted(names)[:12], "; archives :", [u.split("/")[-1] for u in urls[:4]])
    cat = lambda L: gpd.GeoDataFrame(pd.concat(L, ignore_index=True), crs=4326) if L else gpd.GeoDataFrame({"geometry": []}, crs=4326)  # noqa: E731
    return cat(aoi), cat(fl), cat(bl)


def load_fokontany():
    import geopandas as gpd
    parts = [gpd.read_file(f) for f in sorted(glob.glob(str(country_docs_dir("mdg") / "geo" / "adm4" / "*.geojson")))]
    g = pd.concat(parts, ignore_index=True)
    g = gpd.GeoDataFrame(g[["c", "geometry"]].rename(columns={"c": "pcode"}), crs=4326)
    g["area_m2"] = g.to_crs(AREA_CRS).area
    return g


def _valid_union(gdf):
    import shapely
    from shapely.ops import unary_union
    return unary_union([shapely.make_valid(g) for g in gdf.geometry if g is not None and not g.is_empty])


def _inter_area(fp, other):
    """Surface (m²) de l'intersection de chaque polygone de fp avec `other` (uniquement les candidats)."""
    import geopandas as gpd
    out = np.zeros(len(fp))
    idx = fp.sindex.query(other, predicate="intersects")
    if len(idx):
        sub = gpd.GeoSeries(fp.geometry.values[idx], crs=fp.crs)
        out[idx] = sub.intersection(other).area.values
    return out


def truth_for(fok, aoi, fl, bl):
    """DataFrame par fokontany : couverture cartographiée, fraction inondée, bâtiments détruits/endommagés/évalués."""
    import geopandas as gpd
    import shapely
    out = pd.DataFrame({"pcode": fok.pcode.values, "cover": 0.0, "flood_frac": 0.0, "n_dmg": 0, "n_bld": 0})
    fp = fok.to_crs(AREA_CRS)
    fp["geometry"] = [shapely.make_valid(g) for g in fp.geometry]
    if len(aoi):
        a = _valid_union(aoi.to_crs(AREA_CRS))
        out["cover"] = np.clip(_inter_area(fp, a) / fok.area_m2.values, 0, 1)
    if len(fl):
        f = _valid_union(fl.to_crs(AREA_CRS))
        out["flood_frac"] = np.clip(_inter_area(fp, f) / fok.area_m2.values, 0, 1)
    if len(bl):
        j = gpd.sjoin(bl, fok[["pcode", "geometry"]], how="inner", predicate="within")
        j["dmg"] = j.damage_gra.astype(str).str.lower().isin(["destroyed", "damaged"])
        j["ana"] = ~j.damage_gra.astype(str).str.lower().str.contains("not analysed")
        agg = j.groupby("pcode").agg(n_dmg=("dmg", "sum"), n_bld=("ana", "sum"))
        out = out.set_index("pcode")
        out.loc[agg.index, "n_dmg"] = agg.n_dmg.values
        out.loc[agg.index, "n_bld"] = agg.n_bld.values
        out = out.reset_index()
    out["pos"] = (out.n_dmg >= 1) | (out.flood_frac >= 0.05)
    out["evalue"] = (out.cover >= 0.5) | out.pos
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    a = ap.parse_args()
    from chirps_daily import days_between, leaf_series
    from scipy.spatial import cKDTree
    from validate_events import rain_features  # noqa: F401
    bbox = load_config(a.country)["map"]["bbox"]
    units = read_units(a.country)
    leaves = units[units.level == 4].reset_index(drop=True)
    annual = None
    p = grid_dir(a.country) / "rx3_annual.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        if (z["codes"] == leaves.pcode.values).all():
            annual = z["rx3"]
    hy = pd.read_csv(DATA_DIR / a.country / "external" / "hydro.csv")
    hy = hy[hy.pcode.isin(set(leaves.pcode))].pivot_table(index="pcode", columns="indicateur", values="valeur").reset_index()
    ter = leaves[["pcode", "pop", "area_km2"]].merge(hy, on="pcode", how="left")
    ter["lhand5"] = np.log1p(ter.hand_lt5_pct); ter["lhand15"] = np.log1p(ter.hand_lt15_pct)
    ter["lslope"] = np.log1p(ter.slope_mean_pct); ter["lelev"] = np.log1p(ter.elev_mean_m.clip(lower=0))
    ter["lriver"] = np.log1p(ter.river_max_km2); ter["lpopdens"] = np.log1p(ter["pop"].fillna(0) / ter.area_km2.clip(lower=0.01))
    ter = ter[["pcode"] + TERRAIN]
    fok = load_fokontany()
    fok = fok[fok.pcode.isin(set(leaves.pcode))].reset_index(drop=True)
    d_all = fetch_ibtracs()
    LX, LY = project(leaves.lon.values, leaves.lat.values)
    tree = cKDTree(np.c_[LX, LY])
    tmp = Path("/tmp/ems")
    rows, sampler, summary = [], None, []
    for code, (nom, yr) in EVENTS.items():
        try:
            aoi, fl, bl = read_layers(code, tmp)
        except Exception as e:  # noqa: BLE001
            print(code, "lecture impossible :", e)
            continue
        tr = truth_for(fok, aoi, fl, bl)
        print(f"{code} {nom}: zones cartographiées {len(aoi)}, polygones inondés {len(fl)}, bâtiments gradés {len(bl)}, "
              f"fokontany évalués {int(tr.evalue.sum())}, touchés {int(tr.pos.sum())}", flush=True)
        if tr.pos.sum() == 0:
            continue
        g = d_all[(d_all.nom == nom) & (d_all.time.dt.year.isin([yr - 1, yr, yr + 1]))]
        if g.empty:
            print("  trajectoire introuvable")
            continue
        g = g[g.SID == g.SID.iloc[0]].reset_index(drop=True)
        x, y = project(g.LON.values, g.LAT.values)
        dist, _ = tree.query(np.c_[x, y])
        near = g[dist <= 400]
        gg = g[(g.time >= near.time.min() - pd.Timedelta(hours=12)) & (g.time <= near.time.max() + pd.Timedelta(hours=12))].reset_index(drop=True)
        cov, _, _ = footprint(gg, leaves.lon.values, leaves.lat.values)
        days = days_between(near.time.min().date() - dt.timedelta(days=1), near.time.max().date() + dt.timedelta(days=1))
        v, sampler = leaf_series(days, bbox, leaves.lon.values, leaves.lat.values, sampler)
        from chirps_daily import roll3_max
        rx3 = roll3_max(v)
        df = pd.DataFrame({"pcode": leaves.pcode.values, "adm3": leaves.adm3.values, "adm1": leaves.adm1.values,
                           "cov34": cov[34].astype(float), "cov50": cov[50].astype(float), "cov64": cov[64].astype(float), "rx3": rx3})
        if annual is not None:
            N = annual.shape[0]
            df["lrp"] = np.log(np.clip((N + 1) / (1 + (annual >= rx3[None, :]).sum(axis=0)), 1, N + 1))
            df["lratio"] = np.log(np.maximum(rx3 / np.maximum(np.median(annual, axis=0), 1.0), 0.05))
        m = tr.merge(df, on="pcode").merge(ter, on="pcode", how="left")
        m = m[m.evalue].copy()
        m["evenement"] = code
        rows.append(m)
        summary.append({"evenement": code, "nom": nom, "fokontany_evalues": int(len(m)), "fokontany_touches": int(m.pos.sum()),
                        "batiments_gradees": int(len(bl)), "zones_inondees": int(len(fl))})
    feat = pd.concat(rows, ignore_index=True)
    feat["pos"] = feat["pos"].astype(bool)
    VAL_DIR.mkdir(exist_ok=True)
    pd.DataFrame(summary).to_csv(VAL_DIR / "ems_resume.csv", index=False)
    feat = feat.dropna(subset=TERRAIN).reset_index(drop=True)
    feat["pos_inond"] = feat.flood_frac >= 0.05
    feat["pos_bati"] = feat.n_dmg >= 1
    haz = [c for c in COLS if c in feat and feat[c].std() > 0]
    out = {"evenements": summary}
    variants = {"vent et pluie": haz, "terrain seul": TERRAIN, "vent, pluie et terrain": haz + TERRAIN}
    res_f, oof_best, final = {}, None, {}
    for cible, col in [("touche (bâtiment endommagé ou inondé)", "pos"), ("inondé", "pos_inond"), ("bâtiments détruits ou endommagés", "pos_bati")]:
        f = feat.copy()
        f["pos"] = feat[col].astype(bool)
        res_f[cible] = {}
        for name, cols in variants.items():
            r = loeo(f, cols, with_oof=True)
            oof = r.pop("_oof")
            res_f[cible][name] = {"colonnes": cols, "positifs": int(f.pos.sum()), "n": int(len(f)), **r}
            if col == "pos":
                if name == "vent, pluie et terrain":
                    oof_best = oof
                mu, sd, b0, b = train(f[cols].values, f["pos"].values)
                final[name] = {"colonnes": cols, "moyenne": mu.tolist(), "ecart_type": sd.tolist(), "intercept": b0, "coefficients": b.tolist(),
                               "auc_laisser_un_de_cote": res_f[cible][name]["global"]["auc"], "brier": res_f[cible][name]["global"]["brier"],
                               "brier_climato": res_f[cible][name]["global"]["brier_climato"], "n": int(len(f)), "positifs": int(f.pos.sum())}
    feat["pos"] = feat["pos"].astype(bool)
    out["fokontany"] = res_f
    # agrégation à la commune : touchée si un fokontany évalué l'est ; probabilité = maximum
    if oof_best is not None:
        feat["p"] = oof_best
        ok = feat.dropna(subset=["p"])
        com = ok.groupby(["evenement", "adm3"]).agg(pos=("pos", "max"), p=("p", "max"), n=("pos", "size")).reset_index()
        per = []
        for ev, g in com.groupby("evenement"):
            per.append({"evenement": ev, "communes_evaluees": int(len(g)), "communes_touchees": int(g.pos.sum()), "auc": auc(g.p.values, g.pos.values)})
        out["communes"] = {"auc_global": auc(com.p.values, com.pos.values), "par_evenement": per}
        com.to_csv(VAL_DIR / "ems_communes_oof.csv", index=False)
    flat = [{"cible": c, "variante": n, **{k: v for k, v in r["global"].items()}} for c, d in res_f.items() for n, r in d.items()]
    pd.DataFrame(flat).to_csv(VAL_DIR / "ems_modeles_fokontany.csv", index=False)
    pd.DataFrame([{"cible": c, "variante": n, **r} for c, d in res_f.items() for n, v in d.items() for r in v["par_evenement"]]).to_csv(VAL_DIR / "ems_fokontany_par_evenement.csv", index=False)
    out["modele"] = final
    out["generated"] = dt.date.today().isoformat()
    write_json(VAL_DIR / "ems_resultats.json", out)
    print(pd.DataFrame(flat)[["cible", "variante", "auc", "brier", "brier_climato", "pod", "far"]].round(3).to_string())
    first = list(res_f)[0]
    print(pd.DataFrame([{"variante": n, **{k: r[k] for k in ("evenement", "auc", "pod", "far")}} for n, v in res_f[first].items() for r in v["par_evenement"]]).round(2).to_string())
    print(out.get("communes", {}).get("auc_global"), out.get("communes", {}).get("par_evenement"))


if __name__ == "__main__":
    main()
