"""Protocole R-02 bis (validation/protocole_r02bis_echelle_alea.md) : pluie IMERG demi-horaire et rafales ERA5 sur
les 7 activations Copernicus EMS de R-02, pendant la fenêtre de chaque cyclone.

Fenêtre : du premier jour où le centre IBTrACS (docs/data/<pays>/cyclones.json, une position toutes les 6 h depuis la
date de début) passe à moins de 500 km d'un fokontany jusqu'à 2 jours après le dernier, avec un jour de marge avant
(les heures exactes ne sont pas dans le fichier des trajectoires).
Emprise IMERG : enveloppe des communes évaluées pour l'activation (validation/ems_communes_oof.csv), plus 0,25°.
Parties (une à la fois, au rythme des fournisseurs, voir validation/etat_telechargements.md) :
  --part fenetres : écrit validation/r02bis_fenetres.csv (aucun téléchargement) ;
  --part imerg --event EMSRxxx : IMERG V07 Final demi-horaire (GES DISC), requêtes séquentielles ;
  --part rafales --event EMSRxxx : rafale instantanée à 10 m d'ERA5 (Copernicus, une demande), emprise de Madagascar.
Sorties : data/<pays>/r02bis/imerg_<EMSR>.npz, rafales_<EMSR>.npz (rangées dans une release GitHub).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

from common import ROOT, cds_retrieve, country_data_dir, country_docs_dir, read_units, save_grid

EVENTS = {"EMSR264": ("Ava", 2018), "EMSR274": ("Eliakim", 2018), "EMSR424": ("Diane", 2020),
          "EMSR564": ("Batsirai", 2022), "EMSR565": ("Emnati", 2022), "EMSR645": ("Cheneso", 2023),
          "EMSR652": ("Freddy", 2023)}
NEAR_KM, AFTER_DAYS, BEFORE_DAYS, MARGIN_DEG = 500.0, 2, 1, 0.25
MDG = [-11.5, 43.0, -26.0, 51.0]                       # N, O, S, E (rafales ERA5)
RES = 0.1


def haversine_km(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, (lon1, lat1, lon2, lat2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def window(points, start: dt.date, land_lon, land_lat):
    """Positions toutes les 6 h depuis `start` -> (premier jour, dernier jour) de la fenêtre, ou None."""
    near = [k for k, p in enumerate(points)
            if np.min(haversine_km(p[0], p[1], land_lon, land_lat)) <= NEAR_KM]
    if not near:
        return None
    t0 = dt.datetime.combine(start, dt.time()) + dt.timedelta(hours=6 * near[0])
    t1 = dt.datetime.combine(start, dt.time()) + dt.timedelta(hours=6 * near[-1])
    return t0.date() - dt.timedelta(days=BEFORE_DAYS), t1.date() + dt.timedelta(days=AFTER_DAYS)


def windows(country: str) -> pd.DataFrame:
    storms = json.load(open(country_docs_dir(country) / "cyclones.json", encoding="utf-8"))["storms"]
    units = read_units(country)
    leaves = units[units.level == 4]
    lon, lat = leaves.lon.to_numpy()[::20], leaves.lat.to_numpy()[::20]      # un fokontany sur 20 suffit à 500 km
    com = pd.read_csv(ROOT / "validation" / "ems_communes_oof.csv", dtype={"adm3": str})
    rows = []
    for ev, (name, season) in EVENTS.items():
        s = next((x for x in storms if x["name"].split(":")[0] == name and int(x["season"]) == season), None)
        if s is None:
            raise SystemExit(f"trajectoire introuvable : {name} {season}")
        pts = json.loads(s["p"]) if isinstance(s["p"], str) else s["p"]
        w = window(pts, dt.date.fromisoformat(s["start"]), lon, lat)
        cu = units[(units.level == 4) & units.adm3.isin(set(com[com.evenement == ev].adm3))]
        rows.append({"evenement": ev, "cyclone": name, "saison": season, "sid": s["id"], "debut": w[0], "fin": w[1],
                     "lon_min": round(cu.lon.min() - MARGIN_DEG, 2), "lon_max": round(cu.lon.max() + MARGIN_DEG, 2),
                     "lat_min": round(cu.lat.min() - MARGIN_DEG, 2), "lat_max": round(cu.lat.max() + MARGIN_DEG, 2),
                     "communes": int(cu.adm3.nunique())})
    return pd.DataFrame(rows)


def imerg_box(lon_min, lon_max, lat_min, lat_max):
    """Indices IMERG (lon : -179,95 + 0,1 i ; lat : -89,95 + 0,1 j) couvrant l'emprise."""
    return (int((lon_min + 179.95) / RES), int(round((lon_max + 179.95) / RES)),
            int((lat_min + 89.95) / RES), int(round((lat_max + 89.95) / RES)))


def part_imerg(country, w):
    import build_imerg_pilot as P
    box = imerg_box(w.lon_min, w.lon_max, w.lat_min, w.lat_max)
    days = pd.date_range(w.debut, w.fin).date
    s = P.session()
    ny, nx = box[3] - box[2] + 1, box[1] - box[0] + 1
    out = np.full((len(days) * 48, ny, nx), np.nan, "float32")
    missing, t0 = 0, time.time()
    for di, d in enumerate(days):
        for f in P.day_files(s, d):                      # séquentiel : GES DISC refuse les requêtes parallèles
            k = int(f.split(".")[-3]) // 30
            g = P.fetch_one(s, d, f, box)
            time.sleep(0.3)
            if g is None:
                missing += 1
            else:
                out[di * 48 + k] = g
        print(f"  {d} : {time.time() - t0:.0f} s, {missing} pas manquants", flush=True)
    path = country_data_dir(country) / "r02bis" / f"imerg_{w.evenement}.npz"
    path.parent.mkdir(exist_ok=True)
    save_grid(path, pluie=out.astype("float16"), start=np.array(str(days[0])), step_min=np.array(30),
              lat=np.array([-89.95 + RES * j for j in range(box[2], box[3] + 1)], "float32"),
              lon=np.array([-179.95 + RES * i for i in range(box[0], box[1] + 1)], "float32"),
              product=np.array(P.COLL), unite=np.array("mm/h"))
    print(f"{path.name} : {len(days)} jours, {missing} pas manquants sur {len(days) * 48}")


def part_rafales(country, w):
    import cdsapi
    import xarray as xr
    c = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=os.environ["CDS_API_KEY"], quiet=True,
                      progress=False, timeout=1800)
    days = pd.date_range(w.debut, w.fin)
    f = Path(tempfile.mkdtemp()) / "gust.nc"
    cds_retrieve(c, "reanalysis-era5-single-levels", {
        "product_type": ["reanalysis"], "variable": ["instantaneous_10m_wind_gust"],
        "year": sorted({str(d.year) for d in days}), "month": sorted({f"{d.month:02d}" for d in days}),
        "day": sorted({f"{d.day:02d}" for d in days}), "time": [f"{h:02d}:00" for h in range(24)],
        "area": MDG, "data_format": "netcdf", "download_format": "unarchived"}, f)
    ds = xr.open_dataset(f)
    tname = "valid_time" if "valid_time" in ds.dims else "time"
    ds = ds.sel({tname: (ds[tname] >= np.datetime64(str(w.debut))) & (ds[tname] < np.datetime64(str(w.fin + dt.timedelta(days=1))))})
    g = ds["i10fg"].transpose(tname, "latitude", "longitude")
    path = country_data_dir(country) / "r02bis" / f"rafales_{w.evenement}.npz"
    path.parent.mkdir(exist_ok=True)
    save_grid(path, rafale_ms=g.values.astype("float16"), heures=np.array([str(t)[:13] for t in g[tname].values]),
              lat=g.latitude.values.astype("float32"), lon=g.longitude.values.astype("float32"),
              source=np.array("ERA5 instantaneous_10m_wind_gust (Copernicus), horaire, 0,25°"))
    print(f"{path.name} : {g.shape[0]} heures, rafale max {float(np.nanmax(g.values)):.1f} m/s")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--part", required=True, choices=["fenetres", "imerg", "rafales"])
    ap.add_argument("--event")
    args = ap.parse_args()
    if args.part == "fenetres":
        w = windows(args.country)
        w.to_csv(ROOT / "validation" / "r02bis_fenetres.csv", index=False)
        print(w.to_string(index=False))
        return
    w = pd.read_csv(ROOT / "validation" / "r02bis_fenetres.csv", parse_dates=["debut", "fin"])
    row = w[w.evenement == args.event].iloc[0]
    row = row.copy()
    row["debut"], row["fin"] = row.debut.date(), row.fin.date()
    (part_imerg if args.part == "imerg" else part_rafales)(args.country, row)


if __name__ == "__main__":
    main()
