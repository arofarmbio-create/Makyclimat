"""Trajectoires de cyclones tropicaux (IBTrACS, bassin océan Indien Sud) et exposition historique par zone.

Source : IBTrACS v04r01 (NOAA/NCEI ; Knapp et al. 2010), « best track » combinant les centres officiels (RSMC La Réunion, JTWC...).
Les saisons récentes sont provisoires jusqu'à leur révision. Vent : vent soutenu sur 10 min du centre officiel (WMO_WIND) ; à défaut,
vent sur 1 min du JTWC multiplié par 0,93 (facteur de conversion recommandé par l'OMM, Harper et al. 2010). Échelle d'intensité :
celle du RSMC La Réunion (dépression < 34 kt, tempête modérée 34-47, forte 48-63, cyclone tropical 64-89, intense 90-115, très intense >= 116).

Sorties :
  docs/data/<pays>/cyclones.json         trajectoires (une position toutes les 6 h) des systèmes depuis `since`, pour la couche carte
  data/<pays>/external/cyclones.csv      indicateurs par zone (cyc_nb_100km, cyc_vent_max_kt), écrits à tous les niveaux
Indicateurs (période depuis `since`) :
  cyc_nb_100km    nombre de systèmes passés à moins de `radius_km` km du centre de la zone avec un vent d'au moins `min_kt` kt
  cyc_vent_max_kt vent maximal (kt, 10 min) d'un système passé à moins de `radius_km` km
Limites : c'est une PROXIMITÉ au centre du système, pas un champ de vent ni des dégâts (les rayons de vent n'existent que pour une partie des systèmes) ;
la proximité est mesurée au centroïde de chaque fokontany ; pour une commune, un district ou une région, un système compte s'il a touché au moins
un de ses fokontany.
Usage : python scripts/build_cyclones.py --country mdg
"""
from __future__ import annotations

import argparse
import datetime as dt
import io

import numpy as np
import pandas as pd
import requests

from common import country_data_dir, country_docs_dir, load_config, read_units, write_json

URL = ("https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/"
       "ibtracs.SI.list.v04r01.csv")
SCALE = [(34, "Dépression"), (48, "Tempête tropicale modérée"), (64, "Forte tempête tropicale"), (90, "Cyclone tropical"),
         (116, "Cyclone tropical intense"), (10 ** 9, "Cyclone tropical très intense")]
USECOLS = ["SID", "SEASON", "NAME", "ISO_TIME", "NATURE", "LAT", "LON", "WMO_WIND", "USA_WIND", "TRACK_TYPE"]
KM_LAT = 110.57
KM_LON0 = 111.32


def category(kt: float) -> str:
    for lim, name in SCALE:
        if kt < lim:
            return name
    return SCALE[-1][1]


def fetch() -> pd.DataFrame:
    r = requests.get(URL, timeout=600, headers={"User-Agent": "MakyClimat (recherche doctorale)"})
    r.raise_for_status()
    return pd.read_csv(io.BytesIO(r.content), skiprows=[1], usecols=USECOLS, low_memory=False)


def clean(df: pd.DataFrame, since: int, bbox) -> pd.DataFrame:
    """Positions toutes les 6 h, numériques, avec vent 10 min (kt) ; systèmes passés dans l'emprise depuis `since`."""
    d = df.copy()
    d["time"] = pd.to_datetime(d["ISO_TIME"], errors="coerce")
    for c in ("LAT", "LON", "WMO_WIND", "USA_WIND"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["time", "LAT", "LON"])
    d = d[(d.SEASON.astype(int) >= since) & (d.time.dt.hour % 6 == 0) & (d.time.dt.minute == 0)]
    d["kt"] = d["WMO_WIND"].where(d["WMO_WIND"] > 0, 0.93 * d["USA_WIND"].where(d["USA_WIND"] > 0))
    lon0, lat0, lon1, lat1 = bbox
    m = (d.LON >= lon0) & (d.LON <= lon1) & (d.LAT >= lat0) & (d.LAT <= lat1)
    inside = m.groupby(d.SID).any()
    d = d[d.SID.isin(inside[inside].index)]
    return d.sort_values(["SID", "time"]).reset_index(drop=True)


def densify(lon, lat, kt, step_km=10.0):
    """Positions interpolées tous les ~step_km km (vent interpolé entre positions connues)."""
    x = (lon - 47.0) * KM_LON0 * np.cos(np.deg2rad(-19.0))
    y = lat * KM_LAT
    seg = np.hypot(np.diff(x), np.diff(y))
    n = np.maximum(1, np.ceil(seg / step_km).astype(int))
    t = np.concatenate([[0.0], np.cumsum(n)])
    tt = np.arange(int(t[-1]) + 1)
    xi, yi = np.interp(tt, t, x), np.interp(tt, t, y)
    ok = np.isfinite(kt)
    ki = np.interp(tt, t[ok], kt[ok]) if ok.any() else np.full(len(tt), np.nan)
    return xi, yi, ki


def exposure(storms: pd.DataFrame, units: pd.DataFrame, radius_km: float, min_kt: float):
    """Par fokontany : nombre de systèmes >= min_kt à moins de radius_km, vent maximal ; puis cumul vers les niveaux supérieurs."""
    from scipy.spatial import cKDTree
    leaves = units[units.level == 4].reset_index(drop=True)
    ux = (leaves.lon.values - 47.0) * KM_LON0 * np.cos(np.deg2rad(-19.0))
    uy = leaves.lat.values * KM_LAT
    tree = cKDTree(np.c_[ux, uy])
    n = len(leaves)
    keys = {1: "adm1", 2: "adm2", 3: "adm3"}
    gid, ng = {}, {}
    for lv, col in keys.items():
        codes, inv = np.unique(leaves[col].values, return_inverse=True)
        gid[lv], ng[lv] = inv, codes
    cnt_leaf = np.zeros(n, dtype=int)
    wmax_leaf = np.zeros(n)
    cnt_grp = {lv: np.zeros(len(ng[lv]), dtype=int) for lv in keys}
    wmax_grp = {lv: np.zeros(len(ng[lv])) for lv in keys}
    near_min = {}
    for sid, g in storms.groupby("SID"):
        xi, yi, ki = densify(g.LON.values, g.LAT.values, g.kt.values)
        w = np.full(n, -1.0)
        lists = tree.query_ball_point(np.c_[xi, yi], r=radius_km)
        for k, lst in zip(ki, lists):
            if len(lst):
                idx = np.asarray(lst)
                w[idx] = np.maximum(w[idx], 0.0 if not np.isfinite(k) else k)
        hit = w >= min_kt
        cnt_leaf += hit
        wmax_leaf = np.maximum(wmax_leaf, np.where(w >= 0, w, 0))
        for lv in keys:
            any_hit = np.bincount(gid[lv][hit], minlength=len(ng[lv])) > 0
            cnt_grp[lv] += any_hit
            np.maximum.at(wmax_grp[lv], gid[lv], np.where(w >= 0, w, 0))
    rows = {}
    for pc, c, w in zip(leaves.pcode, cnt_leaf, wmax_leaf):
        rows[pc] = (int(c), int(round(w)))
    for lv in keys:
        for pc, c, w in zip(ng[lv], cnt_grp[lv], wmax_grp[lv]):
            rows[pc] = (int(c), int(round(w)))
    return rows


def build_rows(rows: dict, source: str) -> pd.DataFrame:
    data = []
    for pc, (c, w) in rows.items():
        data.append((pc, "cyc_nb_100km", c))
        data.append((pc, "cyc_vent_max_kt", w))
    df = pd.DataFrame(data, columns=["pcode", "indicateur", "valeur"])
    df["date"] = dt.date.today().isoformat()
    df["source"] = source
    return df


def tracks_json(storms: pd.DataFrame, near: dict, generated: str, since: int) -> dict:
    out = []
    for sid, g in storms.groupby("SID", sort=False):
        k = g.kt.values
        mx = float(np.nanmax(k)) if np.isfinite(k).any() else 0.0
        name = str(g.NAME.iloc[0])
        out.append({"id": sid, "name": "" if name in ("NOT_NAMED", "nan") else name.title(), "season": int(g.SEASON.iloc[0]),
                    "max_kt": int(round(mx)), "cat": category(mx), "prov": bool((g.TRACK_TYPE == "PROVISIONAL").any()),
                    "start": g.time.iloc[0].strftime("%Y-%m-%d"), "end": g.time.iloc[-1].strftime("%Y-%m-%d"), "near_km": near.get(sid),
                    "p": [[round(float(a), 2), round(float(b), 2), int(round(c)) if np.isfinite(c) else None] for a, b, c in zip(g.LON, g.LAT, k)]})
    out.sort(key=lambda s: (s["season"], s["start"]))
    return {"generated": generated, "since": since, "scale": [[lim if lim < 10 ** 9 else None, nm] for lim, nm in SCALE], "storms": out}


def nearest_unit_km(storms: pd.DataFrame, units: pd.DataFrame) -> dict:
    from scipy.spatial import cKDTree
    leaves = units[units.level == 4]
    tree = cKDTree(np.c_[(leaves.lon.values - 47.0) * KM_LON0 * np.cos(np.deg2rad(-19.0)), leaves.lat.values * KM_LAT])
    near = {}
    for sid, g in storms.groupby("SID"):
        xi, yi, _ = densify(g.LON.values, g.LAT.values, g.kt.values)
        d, _ = tree.query(np.c_[xi, yi])
        near[sid] = int(round(float(d.min())))
    return near


def run(country: str, raw: pd.DataFrame | None = None) -> dict:
    cfg = {**{"since": 1980, "radius_km": 100, "min_kt": 34, "bbox": [38.0, -30.0, 58.0, -6.0]}, **load_config(country).get("cyclones", {})}
    units = read_units(country)
    d = clean(fetch() if raw is None else raw, int(cfg["since"]), cfg["bbox"])
    src = "IBTrACS v04r01 (NOAA/NCEI) : trajectoires officielles ; proximité au centre du système, pas un champ de vent"
    rows = exposure(d, units, float(cfg["radius_km"]), float(cfg["min_kt"]))
    near = nearest_unit_km(d, units)
    gen = dt.date.today().isoformat()
    ext = country_data_dir(country) / "external"
    ext.mkdir(parents=True, exist_ok=True)
    build_rows(rows, src).to_csv(ext / "cyclones.csv", index=False)
    write_json(country_docs_dir(country) / "cyclones.json", tracks_json(d, near, gen, int(cfg["since"])))
    print(f"Cyclones : {d.SID.nunique()} systèmes depuis {cfg['since']}, {sum(1 for v in near.values() if v <= 100)} passés à moins de 100 km de Madagascar ; dernière position {d.time.max()}")
    return {"rows": rows, "near": near, "n": d.SID.nunique()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    args = ap.parse_args()
    if args.country != "mdg":
        print("Cyclones : seul Madagascar est configuré.")
        return
    run(args.country)


if __name__ == "__main__":
    main()
