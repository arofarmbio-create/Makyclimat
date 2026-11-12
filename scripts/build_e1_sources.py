"""Expérience E1 (validation/protocole_e1_fusion_pluie.md) : pluie journalière de trois sources sur une grille commune
de 0,1°, et relevés des stations synoptiques GSOD.

Sources (période 2001 à aujourd'hui) :
  chirps : CHIRPS v2.0 journalier, 0,05° (CHC/UCSB), moyenne des 4 mailles contenues dans chaque maille de 0,1° ;
  imerg  : GPM IMERG V07 Late journalier, 0,1° (NASA GES DISC, OPeNDAP, compte Earthdata), sans recalage sur pluviomètres ;
  era5   : ERA5-Land, total_precipitation à 00 h UTC du jour J+1 = pluie du jour J (Copernicus CDS), centres décalés
           d'une demi-maille : moyenne des 4 mailles voisines ;
  gsod   : stations GSOD de Madagascar (NOAA NCEI), relevés bruts avec leur drapeau (le contrôle qualité est fait par
           validate_e1.py, jamais ici : les données brutes sont conservées telles quelles).
Grille commune : centres -179,95 + 0,1 i (grille IMERG), 43-51°E, 26-11,5°S ; latitudes croissantes (sud -> nord).
Sortie : data/<pays>/e1/<source>_<année>.npz (pluie[jour, lat, lon] en mm, float32, NaN = manquant), gsod.csv.
Usage : python scripts/build_e1_sources.py --country mdg --source imerg --year 2015
        python scripts/build_e1_sources.py --country mdg --source gsod
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import io
import os
import re
import tempfile
import time
from pathlib import Path

import numpy as np
import requests

from common import cds_retrieve, country_data_dir, load_config, save_grid

RES = 0.1
LON0, LON1, LAT0, LAT1 = 43.0, 51.0, -26.0, -11.5                  # bords de la grille commune
NX, NY = round((LON1 - LON0) / RES), round((LAT1 - LAT0) / RES)    # 80 x 145
LONS = np.round(LON0 + RES / 2 + RES * np.arange(NX), 2).astype("float32")
LATS = np.round(LAT0 + RES / 2 + RES * np.arange(NY), 2).astype("float32")
MAX_DAY_MM = 1000.0                                                # au-dessus du record mondial journalier : erreur

IMERG_BASE = "https://gpm1.gesdisc.eosdis.nasa.gov"
IMERG_COLL = "GPM_L3/GPM_3IMERGDL.07"
I0, J0 = round((LON0 + RES / 2 + 179.95) / RES), round((LAT0 + RES / 2 + 89.95) / RES)   # indices IMERG du coin sud-ouest
CHIRPS_URL = "https://data.chc.ucsb.edu/products/CHIRPS/v2.0/africa_daily/tifs/p05/{y}/chirps-v2.0.{y}.{m:02d}.{d:02d}.tif.gz"
GSOD_URL = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{y}/{sid}.csv"
ISD_HISTORY = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"


def year_days(year: int, today: dt.date) -> list[dt.date]:
    """Jours de l'année jusqu'à hier au plus tard."""
    last = min(dt.date(year, 12, 31), today - dt.timedelta(days=1))
    return [dt.date(year, 1, 1) + dt.timedelta(days=k) for k in range((last - dt.date(year, 1, 1)).days + 1)]


def clean(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype="float32").copy()
    a[(a < 0) | (a > MAX_DAY_MM)] = np.nan
    return a


def block_mean_005(arr: np.ndarray, lon_edge: float, lat_top: float) -> np.ndarray:
    """Grille CHIRPS 0,05° (nord en haut, bord ouest lon_edge, bord nord lat_top) -> grille commune 0,1° (sud en bas).
    Moyenne des mailles valides parmi les 4 ; NaN si aucune (mer)."""
    c0 = round((LON0 - lon_edge) / 0.05)
    r0 = round((lat_top - LAT1) / 0.05)
    a = clean(arr[r0:r0 + 2 * NY, c0:c0 + 2 * NX])
    if a.shape != (2 * NY, 2 * NX):
        raise ValueError(f"emprise CHIRPS insuffisante : {a.shape}")
    b = a.reshape(NY, 2, NX, 2)
    n = np.isfinite(b).sum(axis=(1, 3))
    m = np.where(n > 0, np.nansum(b, axis=(1, 3)) / np.maximum(n, 1), np.nan)
    return clean(m[::-1])


def corner_mean_01(arr: np.ndarray) -> np.ndarray:
    """Grille ERA5-Land 0,1° dont les centres sont sur les bords de la grille commune (NY+1 x NX+1, sud en bas)
    -> moyenne des 4 mailles voisines de chaque centre commun."""
    if arr.shape != (NY + 1, NX + 1):
        raise ValueError(f"grille ERA5-Land inattendue : {arr.shape}")
    arr = clean(arr)                                          # valeur négative = manquante, avant la moyenne
    s = np.stack([arr[:-1, :-1], arr[1:, :-1], arr[:-1, 1:], arr[1:, 1:]])
    with np.errstate(invalid="ignore"):
        n = np.isfinite(s).sum(0)
        out = np.where(n > 0, np.nansum(s, 0) / np.maximum(n, 1), np.nan)
    return clean(out)


# ---------- CHIRPS ----------
def empty_days(pr: np.ndarray) -> list[int]:
    """Indices des jours entièrement vides (aucune maille renseignée)."""
    return [k for k in range(len(pr)) if not np.isfinite(pr[k]).any()]


def chirps_plain_url(url: str) -> str:
    """Adresse du même jour en .tif non compressé (certains mois, comme décembre 2021, ne sont publiés que sous cette
    forme sur le serveur CHC)."""
    return url[:-3] if url.endswith(".tif.gz") else url


def part_chirps(days):
    import gzip
    import shutil

    from chirps import read_crop
    from common import download

    def get(url, dest):
        try:
            return download(url, dest, retries=8)              # CHC très chargé : plus de patience sur les 429
        except Exception as e:  # noqa: BLE001
            if "403" in str(e):                   # jour pas encore publié : CHC répond 403, pas 404 (02/11/2026)
                return False
            raise

    def one(d):
        with tempfile.TemporaryDirectory(prefix="e1c_") as tmp:
            gz, tif = Path(tmp) / "f.tif.gz", Path(tmp) / "f.tif"
            url = CHIRPS_URL.format(y=d.year, m=d.month, d=d.day)
            if get(url, gz):
                with gzip.open(gz, "rb") as fi, open(tif, "wb") as fo:
                    shutil.copyfileobj(fi, fo)
            elif not get(chirps_plain_url(url), tif):   # décembre 2021 : publié en .tif non compressé (03/11/2026)
                return None
            arr, lon0, lat0, _ = read_crop(tif, [LON0 - 0.05, LAT0 - 0.05, LON1 + 0.05, LAT1 + 0.05])
            return block_mean_005(arr, lon0, lat0)

    with cf.ThreadPoolExecutor(1) as ex:                     # CHC refuse (429) même à 2 requêtes simultanées (03/11/2026)
        return list(ex.map(one, days)), "CHIRPS v2.0 journalier, 0,05° -> 0,1° (moyenne 2 x 2)"


# ---------- IMERG Late ----------
def imerg_session():
    from build_imerg_pilot import session
    return session()


def imerg_month_files(s, y: int, m: int) -> dict[dt.date, str]:
    url = f"{IMERG_BASE}/data/{IMERG_COLL}/{y}/{m:02d}/"
    for k in range(8):
        try:
            r = s.get(url, timeout=120)
            if r.status_code == 404:
                return {}
            r.raise_for_status()
            out = {}
            for f in set(re.findall(r'href="(3B-DAY-L[^"]+\.nc4)"', r.text)):
                d = re.search(r"\.(\d{8})-S", f).group(1)
                out[dt.date(int(d[:4]), int(d[4:6]), int(d[6:]))] = f
            return out
        except requests.RequestException:
            time.sleep(30 * (k + 1))
    raise RuntimeError(f"liste IMERG inaccessible : {url}")


DATA_LINE = re.compile(r"^(precipitation\.)?precipitation\[[^\]]+\]\[[^\]]+\],")


def parse_imerg_ascii(text: str) -> np.ndarray:
    """Réponse ASCII OPeNDAP -> grille commune [lat, lon]. Une ligne par longitude ; deux formes acceptées :
    « precipitation[0][12], v, v… » et, pour les fichiers journaliers (variable de type Grid, vu le 02/11/2026),
    « precipitation.precipitation[precipitation.time=…][precipitation.lon=43.05], v, v… »."""
    vals = [list(map(float, ln.split(",")[1:])) for ln in text.splitlines() if DATA_LINE.match(ln)]
    a = np.array(vals, dtype="float32")
    if a.shape != (NX, NY):
        raise ValueError(f"grille IMERG inattendue {a.shape}")
    return clean(a.T)


def probe_imerg(day: dt.date) -> None:
    """Diagnostic rapide d'IMERG Late (un jour) : liste du mois, unité, réponse OPeNDAP et durée."""
    s = imerg_session()
    t0 = time.time()
    files = imerg_month_files(s, day.year, day.month)
    print(f"liste {day:%Y-%m} : {len(files)} fichiers en {time.time() - t0:.1f} s ; exemple : {next(iter(files.values()), None)}")
    f = files.get(day)
    if not f:
        return
    stem = f"{IMERG_BASE}/opendap/{IMERG_COLL}/{day.year}/{day.month:02d}/{f}"
    for suffix in (".das", ".dds", f".ascii?precipitation[0:0][{I0}:{I0 + 2}][{J0}:{J0 + 2}]"):
        t0 = time.time()
        r = s.get(stem + suffix, timeout=120)
        print(f"--- {suffix[:60]} -> HTTP {r.status_code}, {len(r.text)} car., {time.time() - t0:.1f} s")
        print(r.text[:700])
    days = [day + dt.timedelta(days=k) for k in range(12)]
    t0 = time.time()
    got, _ = part_imerg(days)
    print(f"12 jours avec part_imerg : {sum(g is not None for g in got)} obtenus en {time.time() - t0:.0f} s", flush=True)


def part_imerg(days):
    s = imerg_session()
    files = {}
    for y, m in sorted({(d.year, d.month) for d in days}):
        files.update(imerg_month_files(s, y, m))
    units = "?"
    if files:
        f0 = next(iter(files.items()))
        das = s.get(f"{IMERG_BASE}/opendap/{IMERG_COLL}/{f0[0].year}/{f0[0].month:02d}/{f0[1]}.das", timeout=120).text
        mu = re.search(r"precipitation\s*\{[^}]*?units\s+\"([^\"]+)\"", das, re.S)
        units = mu.group(1) if mu else "?"
        print(f"  unité IMERG : {units}", flush=True)
        if units not in ("mm/day", "mm"):
            raise RuntimeError(f"unité IMERG inattendue : {units} (attendu mm/day)")

    out, fails_in_a_row = [], 0
    for d in days:                                       # séquentiel : en parallèle, GES DISC répond 503 puis coupe
        f = files.get(d)                                 # les connexions (sonde du 02/11/2026)
        g = None
        if f is not None:
            url = (f"{IMERG_BASE}/opendap/{IMERG_COLL}/{d.year}/{d.month:02d}/{f}.ascii?"
                   f"precipitation[0:0][{I0}:{I0 + NX - 1}][{J0}:{J0 + NY - 1}]")
            g = fetch_imerg_day(s, url, d)
            time.sleep(PAUSE_S)
        fails_in_a_row = 0 if (g is not None or f is None) else fails_in_a_row + 1
        if fails_in_a_row >= MAX_FAILS_IN_A_ROW:
            raise RuntimeError(f"IMERG : {MAX_FAILS_IN_A_ROW} jours de suite en échec (jusqu'au {d}) ; arrêt pour ne pas "
                               "insister auprès du serveur")
        out.append(g)
    return out, f"IMERG V07 Late journalier ({IMERG_COLL}), 0,1°, unité {units}"


PAUSE_S = 0.5                       # entre deux requêtes IMERG
MAX_FAILS_IN_A_ROW = 10


def fetch_imerg_day(s, url, d, tries=6, sleep=time.sleep):
    """Une journée IMERG. 200 : grille ; 401/403 : erreur ; 503 ou coupure : attente croissante (60 s, 120 s, …
    plafonnée à 300 s) avant un nouvel essai ; None après `tries` essais."""
    for k in range(tries):
        try:
            r = s.get(url, timeout=120)
            if r.status_code == 200:
                return parse_imerg_ascii(r.text)         # un format inattendu lève ValueError : pas de nouvel essai
            if r.status_code in (401, 403):
                raise RuntimeError(f"accès refusé (HTTP {r.status_code}) : compte Earthdata ou application GES DISC")
            why = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            why = type(e).__name__
        print(f"  {d} essai {k + 1} : {why}", flush=True)
        if k + 1 < tries:
            sleep(min(60 * (k + 1), 300))
    return None


# ---------- ERA5-Land ----------
def part_era5(days):
    import cdsapi
    import xarray as xr
    c = cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=os.environ["CDS_API_KEY"], quiet=True,
                      progress=False, timeout=1800)
    area = [LAT1, LON0, LAT0, LON1]                          # N, O, S, E : centres ERA5-Land sur les bords communs
    acc = {}                                                  # date de la valeur de 00 h -> grille (cumul de la veille)
    y, today = days[0].year, dt.date.today()
    # année en cours : mois terminés seulement (ERA5-Land paraît environ 5 jours après) ; 1er janvier suivant si publié
    plan = [(list(range(1, 13)) if y < today.year else list(range(1, today.month)), y)]
    if y + 1 <= today.year:
        plan.append(([1], y + 1))
    for months, yy in plan:
        if not months:
            continue
        f = Path(tempfile.mkdtemp()) / "era5land.nc"
        req = {"variable": ["total_precipitation"], "year": [str(yy)], "month": [f"{m:02d}" for m in months],
               "day": [f"{d:02d}" for d in range(1, 32)], "time": ["00:00"], "area": area,
               "data_format": "netcdf", "download_format": "unarchived"}
        if yy > y:
            req["day"] = ["01"]
        try:
            cds_retrieve(c, "reanalysis-era5-land", req, f)
        except RuntimeError as e:
            if yy > y:                                       # 1er janvier suivant pas encore publié : 31/12 manquant
                print(f"  {yy}-01-01 indisponible : {str(e)[:200]}")
                continue
            raise
        ds = xr.open_dataset(f)
        tname = "valid_time" if "valid_time" in ds.dims else "time"
        v = ds["tp"].transpose(tname, "latitude", "longitude")
        lat = ds.latitude.values
        for t, a in zip(ds[tname].values, v.values):
            a = a[::-1] if lat[0] > lat[-1] else a
            acc[dt.date.fromisoformat(str(t)[:10])] = corner_mean_01(a.astype("float32") * 1000.0)
    return [acc.get(d + dt.timedelta(days=1)) for d in days], \
        "ERA5-Land total_precipitation, valeur de 00 h UTC du lendemain, 0,1° (moyenne des 4 mailles voisines)"


# ---------- GSOD ----------
def gsod_stations() -> list[dict]:
    r = requests.get(ISD_HISTORY, timeout=300)
    r.raise_for_status()
    out = []
    for x in csv.DictReader(io.StringIO(r.content.decode("latin-1"))):
        try:
            lat, lon = float(x["LAT"]), float(x["LON"])
        except ValueError:
            continue
        if x["CTRY"] == "MA" and LAT0 <= lat <= LAT1 and LON0 <= lon <= LON1 and x["END"] >= "20010101":
            out.append({"sid": x["USAF"] + x["WBAN"], "name": x["STATION NAME"].strip(), "lat": lat, "lon": lon})
    return out


def parse_gsod(text: str) -> list[tuple[str, float, str]]:
    """CSV GSOD -> (date, pluie mm ou NaN, drapeau) ; 99.99 = manquant, pouces -> mm."""
    rows = []
    for x in csv.DictReader(io.StringIO(text)):
        p = float(x["PRCP"])
        rows.append((x["DATE"], np.nan if p >= 99.98 else round(p * 25.4, 1), x.get("PRCP_ATTRIBUTES", "").strip()))
    return rows


def part_gsod(out_dir: Path, years):
    st = gsod_stations()
    print(f"  {len(st)} stations GSOD à Madagascar", flush=True)
    path = out_dir / "gsod.csv"
    with open(path, "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["station", "nom", "lat", "lon", "date", "pluie_mm", "drapeau"])
        for x in st:
            n = 0
            for y in years:
                r = requests.get(GSOD_URL.format(y=y, sid=x["sid"]), timeout=120)
                if r.status_code == 404:
                    continue
                r.raise_for_status()
                for d, p, f in parse_gsod(r.text):
                    w.writerow([x["sid"], x["name"], x["lat"], x["lon"], d, "" if np.isnan(p) else p, f])
                    n += 1
            print(f"  {x['sid']} {x['name']} : {n} jours", flush=True)
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--source", required=True, choices=["chirps", "imerg", "era5", "gsod"])
    ap.add_argument("--year", type=int)
    ap.add_argument("--first-year", type=int, default=2001)
    ap.add_argument("--probe", help="diagnostic IMERG sur un jour AAAA-MM-JJ")
    ap.add_argument("--completer", action="store_true",
                    help="repartir du fichier existant et ne télécharger que les jours entièrement vides")
    args = ap.parse_args()
    load_config(args.country)
    out_dir = country_data_dir(args.country) / "e1"
    out_dir.mkdir(exist_ok=True)
    today = dt.date.today()
    if args.probe:
        probe_imerg(dt.date.fromisoformat(args.probe))
        return
    if args.source == "gsod":
        print(f"écrit : {part_gsod(out_dir, range(args.first_year, today.year + 1))}")
        return
    days = year_days(args.year, today)
    t0 = time.time()
    path = out_dir / f"{args.source}_{args.year}.npz"
    part = {"chirps": part_chirps, "imerg": part_imerg, "era5": part_era5}[args.source]
    if args.completer and path.exists():
        old = np.load(path, allow_pickle=False)
        pr = np.full((len(days), NY, NX), np.nan, "float32")
        pr[: min(len(days), len(old["pluie"]))] = old["pluie"][: len(days)]
        todo = empty_days(pr)
        print(f"  {len(todo)} jours entièrement vides à compléter", flush=True)
        grids, desc = part([days[k] for k in todo]) if todo else ([], str(old["source"]))
        for k, g in zip(todo, grids):
            if g is not None:
                pr[k] = g
        missing = len(empty_days(pr))
    else:
        grids, desc = part(days)
        pr = np.full((len(days), NY, NX), np.nan, "float32")
        missing = 0
        for k, g in enumerate(grids):
            if g is None:
                missing += 1
            else:
                pr[k] = g
    if missing == len(days):
        raise SystemExit(f"{args.source} {args.year} : aucun jour obtenu")
    save_grid(path, pluie=pr, start=np.array(days[0].isoformat()), lat=LATS, lon=LONS, source=np.array(desc),
              jours_manquants=np.array(missing), cree=np.array(dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")))
    print(f"{path.name} : {len(days)} jours, {missing} manquants, {NY} x {NX} mailles, "
          f"moyenne {np.nanmean(pr) * 365:.0f} mm/an, {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
