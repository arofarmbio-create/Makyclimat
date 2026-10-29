"""Pluie demi-horaire GPM IMERG (NASA, V07 « Final ») sur le périmètre pilote, pour les cumuls 1 h / 3 h / 6 h des crues éclair.

Cahier des charges §7.A (cumuls sur 1, 3, 6, 24, 72 heures). Découpage OPeNDAP du serveur GES DISC : seules les mailles
du périmètre (0,1°) sont lues dans chaque fichier demi-horaire global. Compte NASA Earthdata (secrets EARTHDATA_USER,
EARTHDATA_PASSWORD), jamais affiché.
Sortie : data/<pays>/imerg/imerg_<saison>.npz, pluie[pas de 30 min, lat, lon] en mm/h (float16), saison novembre-avril.
Usage : python scripts/build_imerg_pilot.py --country mdg --season 2021          (novembre 2021 - avril 2022)
        python scripts/build_imerg_pilot.py --country mdg --probe 2022-01-24      (teste l'accès sur un fichier)
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import os
import re
import time

import numpy as np
import pandas as pd
import requests

from common import country_data_dir, read_units, save_grid

BASE = "https://gpm1.gesdisc.eosdis.nasa.gov"
COLL = "GPM_L3/GPM_3IMERGHH.07"
RES = 0.1


class EarthdataSession(requests.Session):
    """Garde l'authentification lors de la redirection vers urs.earthdata.nasa.gov (et seulement là)."""

    def rebuild_auth(self, prepared_request, response):
        host = requests.utils.urlparse(prepared_request.url).hostname
        if "Authorization" in prepared_request.headers and host != "urs.earthdata.nasa.gov" \
                and requests.utils.urlparse(response.request.url).hostname != host:
            del prepared_request.headers["Authorization"]


def session() -> EarthdataSession:
    s = EarthdataSession()
    s.auth = (os.environ["EARTHDATA_USER"], os.environ["EARTHDATA_PASSWORD"])
    return s


def pilot_box(country: str):
    """Emprise des fokontany du périmètre pilote (communes avec un seuil de crue), marge d'une maille ; indices IMERG."""
    th = pd.read_csv(country_data_dir(country) / "flood_thresholds.csv", dtype={"pcode": str})
    u = read_units(country)
    lv = u[(u.level == 4) & u.adm3.isin(set(th.pcode))]
    lo0, lo1 = lv.lon.min() - RES, lv.lon.max() + RES
    la0, la1 = lv.lat.min() - RES, lv.lat.max() + RES
    i0, i1 = int((lo0 + 179.95) / RES), int(round((lo1 + 179.95) / RES))      # lon : -179,95 + 0,1 i
    j0, j1 = int((la0 + 89.95) / RES), int(round((la1 + 89.95) / RES))        # lat : -89,95 + 0,1 j
    return i0, i1, j0, j1


def day_files(s, day: dt.date) -> list[str]:
    url = f"{BASE}/data/{COLL}/{day.year}/{day.timetuple().tm_yday:03d}/"
    for k in range(5):
        try:
            r = s.get(url, timeout=120)
            r.raise_for_status()
            return sorted(set(re.findall(r'href="(3B-HHR[^"]+\.HDF5)"', r.text)))
        except requests.RequestException:
            time.sleep(5 * (k + 1))
    raise RuntimeError(f"liste des fichiers inaccessible : {url}")


def subset_url(day: dt.date, fname: str, box) -> str:
    i0, i1, j0, j1 = box
    return (f"{BASE}/opendap/{COLL}/{day.year}/{day.timetuple().tm_yday:03d}/{fname}.ascii?"
            f"precipitation[0:0][{i0}:{i1}][{j0}:{j1}]")


def parse_ascii(text: str, box) -> np.ndarray:
    """Réponse ASCII OPeNDAP -> grille [lat, lon] en mm/h ; NaN pour les valeurs manquantes (< 0)."""
    i0, i1, j0, j1 = box
    body = text.split("---------------------------------------------", 1)[-1]
    rows = [ln for ln in body.splitlines() if ln.startswith("precipitation") or ln.startswith("[0][")]
    vals = [list(map(float, ln.split(",")[1:])) for ln in rows if ln.startswith("[0][")]
    a = np.array(vals, dtype="float32")                                     # lon, lat
    if a.shape != (i1 - i0 + 1, j1 - j0 + 1):
        raise ValueError(f"grille inattendue {a.shape}")
    a[a < 0] = np.nan
    return a.T


def fetch_one(s, day, fname, box):
    for k in range(6):
        try:
            r = s.get(subset_url(day, fname, box), timeout=120)
            if r.status_code == 200:
                return parse_ascii(r.text, box)
            if r.status_code in (401, 403):
                raise RuntimeError(f"accès refusé (HTTP {r.status_code}) : compte Earthdata ou application GES DISC")
        except (requests.RequestException, ValueError):
            pass
        time.sleep(3 * (k + 1))
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--season", type=int, help="année de novembre")
    ap.add_argument("--probe", help="jour à tester (AAAA-MM-JJ)")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    box = pilot_box(args.country)
    s = session()
    if args.probe:
        d = dt.date.fromisoformat(args.probe)
        files = day_files(s, d)
        g = fetch_one(s, d, files[0], box)
        print(f"{len(files)} fichiers le {d} ; grille {None if g is None else g.shape} ; max {None if g is None else np.nanmax(g):.2f} mm/h ; "
              f"URL type : {subset_url(d, files[0], box).split('?')[0][-60:]}")
        return
    days = [dt.date(args.season, 11, 1) + dt.timedelta(days=k) for k in range((dt.date(args.season + 1, 5, 1) - dt.date(args.season, 11, 1)).days)]
    out = country_data_dir(args.country) / "imerg"
    out.mkdir(exist_ok=True)
    path = out / f"imerg_{args.season}.npz"
    if path.exists():
        print(f"{path.name} : déjà présent")
        return
    ny, nx = box[3] - box[2] + 1, box[1] - box[0] + 1
    P = np.full((len(days) * 48, ny, nx), np.nan, dtype="float32")
    t0, missing = time.time(), 0
    for di, d in enumerate(days):
        files = day_files(s, d)
        with cf.ThreadPoolExecutor(args.workers) as ex:
            res = list(ex.map(lambda f: fetch_one(s, d, f, box), files))
        for f, g in zip(files, res):
            k = int(f.split(".")[-3]) // 30                                   # minute de début / 30 (0000..1410)
            if g is None:
                missing += 1
            else:
                P[di * 48 + k] = g
        if di % 30 == 0:
            print(f"  {d} : {time.time() - t0:.0f} s, {missing} fichiers manquants", flush=True)
    save_grid(path, pluie=P.astype("float16"), start=np.array(days[0].isoformat()), step_min=np.array(30),
              lat=np.array([-89.95 + RES * j for j in range(box[2], box[3] + 1)], "float32"),
              lon=np.array([-179.95 + RES * i for i in range(box[0], box[1] + 1)], "float32"), product=np.array(COLL))
    print(f"{path.name} : {len(days)} jours, {ny} x {nx} mailles, {missing} pas manquants sur {len(days) * 48}, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
