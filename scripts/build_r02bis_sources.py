"""Protocole R-02 bis (validation/protocole_r02bis_echelle_alea.md) : pluie IMERG demi-horaire et rafales ERA5 sur
les 7 activations Copernicus EMS de R-02, pendant la fenêtre de chaque cyclone.

Fenêtre : du premier jour où le centre IBTrACS (docs/data/<pays>/cyclones.json, une position toutes les 6 h depuis la
date de début) passe à moins de 500 km d'un fokontany jusqu'à 2 jours après le dernier, avec un jour de marge avant
(les heures exactes ne sont pas dans le fichier des trajectoires).
Emprise IMERG : enveloppe des communes évaluées pour l'activation (validation/ems_communes_oof.csv), plus 0,25°.
Parties (une à la fois, au rythme des fournisseurs, voir validation/etat_telechargements.md) :
  --part fenetres : écrit validation/r02bis_fenetres.csv (aucun téléchargement) ;
  --part imerg --event EMSRxxx : IMERG V07 Final demi-horaire (GES DISC), requêtes séquentielles ;
  --part rafales --event EMSRxxx : rafale instantanée à 10 m d'ERA5 (Copernicus, une demande), emprise de Madagascar ;
    collecte reprenable : la demande survit à l'arrêt du job et est reprise au lancement suivant (code 75 si en file).
Sorties : data/<pays>/r02bis/imerg_<EMSR>.npz, rafales_<EMSR>.npz (rangées dans une release GitHub).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import tempfile
import time
import urllib.parse
from pathlib import Path

import numpy as np
import pandas as pd

from common import ROOT, country_data_dir, country_docs_dir, read_units, save_grid

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


CDS = "https://cds.climate.copernicus.eu/api/retrieve/v1"
ECHECS = {"failed", "dismissed", "rejected", "deleted"}
EN_ATTENTE = 75                                         # code de sortie : demande toujours en file à l'échéance


def requete_rafales(w) -> dict:
    days = pd.date_range(w.debut, w.fin)
    return {"product_type": ["reanalysis"], "variable": ["instantaneous_10m_wind_gust"],
            "year": sorted({str(d.year) for d in days}), "month": sorted({f"{d.month:02d}" for d in days}),
            "day": sorted({f"{d.day:02d}" for d in days}), "time": [f"{h:02d}:00" for h in range(24)],
            "area": MDG, "data_format": "netcdf", "download_format": "unarchived"}


def statut(session, entetes, job) -> tuple[str, dict]:
    r = session.get(f"{CDS}/jobs/{job}", headers=entetes, timeout=60)
    if r.status_code == 404:
        return "deleted", {}
    r.raise_for_status()
    d = r.json()
    return d.get("status", "?"), d


def demande_reprenable(session, entetes, jeu, requete, fichier: Path, delai_s: float, publier=None, pause=60,
                       horloge=time.monotonic, dormir=time.sleep) -> str | None:
    """Collecte reprenable (R-40, 12/11/2026 : EMSR564 resté en file chez Copernicus au-delà des 5 h 40 du job).
    Reprend la demande notée dans `fichier` si elle porte sur la même requête et n'a pas échoué, sinon en soumet une
    et note son identifiant (publié aussitôt par `publier`, pour survivre à l'arrêt du job). Suit son état jusqu'à
    l'échéance. Renvoie l'adresse du résultat, ou None si la demande est encore en file : elle reste vivante chez
    Copernicus et la tâche suivante la reprend sans en soumettre une autre."""
    job = None
    if fichier.exists():
        note = json.loads(fichier.read_text(encoding="utf-8"))
        if note.get("jeu") == jeu and note.get("requete") == requete:
            etat, _ = statut(session, entetes, note["jobID"])
            if etat in ECHECS:
                print(f"  demande notée {note['jobID']} : {etat}, nouvelle soumission", flush=True)
            else:
                job = note["jobID"]
                print(f"  reprise de la demande {job} (soumise {note.get('soumise')}, état {etat})", flush=True)
    if job is None:
        r = session.post(f"{CDS}/processes/{jeu}/execution", json={"inputs": requete}, headers=entetes, timeout=120)
        if r.status_code >= 400:
            raise RuntimeError(f"{jeu} refusé : {r.text[:800]}")
        job = r.json()["jobID"]
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(json.dumps({"jeu": jeu, "requete": requete, "jobID": job,
                                       "soumise": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  demande soumise : {job}", flush=True)
        if publier:
            publier(fichier)
    t0, dernier, vu = horloge(), None, None
    while True:
        etat, d = statut(session, entetes, job)
        if etat != vu or horloge() - dernier >= 1800:              # suivi visible (le client était muet)
            print(f"  {dt.datetime.now(dt.timezone.utc):%H:%M} UTC : demande {job} {etat}", flush=True)
            vu, dernier = etat, horloge()
        if etat == "successful":
            r = session.get(f"{CDS}/jobs/{job}/results", headers=entetes, timeout=60)
            r.raise_for_status()
            return urllib.parse.urljoin(f"{CDS}/jobs/{job}/results", r.json()["asset"]["value"]["href"])
        if etat in ECHECS:
            raise RuntimeError(f"demande {job} : {etat} {json.dumps(d, ensure_ascii=False)[:800]}")
        if horloge() - t0 >= delai_s:
            return None
        dormir(pause)


def part_rafales(country, w, delai_min: float = 320, publier=None) -> bool:
    import requests
    import xarray as xr
    dossier = country_data_dir(country) / "r02bis"
    session, entetes = requests.Session(), {"PRIVATE-TOKEN": os.environ["CDS_API_KEY"]}
    href = demande_reprenable(session, entetes, "reanalysis-era5-single-levels", requete_rafales(w),
                              dossier / f"rafales_{w.evenement}.demande.json", delai_min * 60, publier=publier)
    if href is None:
        print(f"::warning::{w.evenement} : demande Copernicus toujours en file après {delai_min:.0f} min ; "
              "elle reste vivante et sera reprise au prochain lancement", flush=True)
        return False
    f = Path(tempfile.mkdtemp()) / "gust.nc"
    meme_hote = urllib.parse.urlsplit(href).netloc == urllib.parse.urlsplit(CDS).netloc
    with session.get(href, stream=True, timeout=600, headers=entetes if meme_hote else None) as r:
        r.raise_for_status()
        with open(f, "wb") as out:
            for bloc in r.iter_content(1 << 20):
                out.write(bloc)
    ds = xr.open_dataset(f)
    tname = "valid_time" if "valid_time" in ds.dims else "time"
    ds = ds.sel({tname: (ds[tname] >= np.datetime64(str(w.debut))) & (ds[tname] < np.datetime64(str(w.fin + dt.timedelta(days=1))))})
    g = ds["i10fg"].transpose(tname, "latitude", "longitude")
    path = dossier / f"rafales_{w.evenement}.npz"
    path.parent.mkdir(exist_ok=True)
    save_grid(path, rafale_ms=g.values.astype("float16"), heures=np.array([str(t)[:13] for t in g[tname].values]),
              lat=g.latitude.values.astype("float32"), lon=g.longitude.values.astype("float32"),
              source=np.array("ERA5 instantaneous_10m_wind_gust (Copernicus), horaire, 0,25°"))
    print(f"{path.name} : {g.shape[0]} heures, rafale max {float(np.nanmax(g.values)):.1f} m/s")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--part", required=True, choices=["fenetres", "imerg", "rafales"])
    ap.add_argument("--event")
    ap.add_argument("--delai-min", type=float, default=320, help="rafales : attente maximale avant de rendre la main")
    ap.add_argument("--publier-demande", metavar="TAG", help="rafales : release où noter la demande dès sa soumission")
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
    if args.part == "imerg":
        part_imerg(args.country, row)
        return
    publier = None
    if args.publier_demande:
        import subprocess
        publier = lambda p: subprocess.run(["gh", "release", "upload", args.publier_demande, str(p), "--clobber"],
                                           check=True)
    if not part_rafales(args.country, row, args.delai_min, publier):
        raise SystemExit(EN_ATTENTE)


if __name__ == "__main__":
    main()
