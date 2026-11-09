"""Projections NEX-GDDP-CMIP6 v2.0 (NASA NEX / NCCS) agrégées au mois et par région de Madagascar (expérience E6,
validation/protocole_cmip6.md, section 9).

Accès (vérifié le 09/11/2026 dans la documentation NCCS et le catalogue THREDDS, sans télécharger de données) :
service NetcdfSubset (NCSS) du serveur THREDDS de la NCCS, sans compte :
  https://ds.nccs.nasa.gov/thredds/ncss/grid/AMES/NEX/GDDP-CMIP6/<modele>/<scenario>/<membre>/<var>/
      <var>_day_<modele>_<scenario>_<membre>_<grille>_<annee>_v2.0.nc?var=<var>&north=..&south=..&west=..&east=..
      &horizStride=1&temporal=all&accept=netcdf3&addLatLon=true
Un fichier par variable et par année (journalier, 0,25°). Le même fichier entier est sur AWS S3 (s3://nex-gddp-cmip6,
accès anonyme), mais il pèse environ 220 Mo par année et par variable (le découpage interne est d'un jour x globe
entier) : le sous-ensemble NCSS de l'emprise (environ 58 x 32 mailles, 2 à 3 Mo) est retenu.

Agrégation : pr (kg m-2 s-1) x 86 400 -> mm/jour, somme sur les jours du mois -> mm/mois ; tas et tasmax (K) - 273,15
-> °C, moyenne des jours du mois. Calendrier du modèle respecté (standard, 365 jours, 360 jours). Puis moyenne
régionale pondérée par la surface des fokontany (valeur de la maille qui contient le centroïde, voisine valide sur la
côte), même méthode que build_teleconnections.region_series, réutilisée telle quelle.

Licence : l'attribut global cmip6_license de chaque réponse est relu et consigné ; arrêt si la licence n'est pas
CC0, CC BY ou CC BY-SA (data/mdg/cmip6_modeles.json donne les sources).

Rythme : une requête à la fois, 3 essais au plus espacés de 30 s, 2 s entre deux fichiers.

Usage : python scripts/build_cmip6_nexgddp.py --probe [--modele ACCESS-CM2 --annee 2014 --variable pr]
        python scripts/build_cmip6_nexgddp.py --modele ACCESS-CM2 --scenario historical   (1981-2014 par défaut)
        python scripts/build_cmip6_nexgddp.py --modele ACCESS-CM2 --scenario ssp585       (2015-2100)
Sortie : data/mdg/cmip6_nexgddp/<modele>_<scenario>.csv (modele, scenario, region, annee, mois, variable, valeur ;
region = code adm1) et <modele>_<scenario>_meta.json (licences lues, fichiers, calendrier). Hors git : release.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_teleconnections import region_series  # noqa: E402
from common import DATA_DIR, read_units  # noqa: E402

NCSS = "https://ds.nccs.nasa.gov/thredds/ncss/grid/AMES/NEX/GDDP-CMIP6"
VERSION = "v2.0"
BBOX = {"west": 43.0, "east": 51.0, "south": -26.0, "north": -11.5}
VARIABLES = ("pr", "tas", "tasmax")
SCENARIOS = ("historical", "ssp126", "ssp245", "ssp585")
YEARS = {"historical": (1981, 2014), "ssp126": (2015, 2100), "ssp245": (2015, 2100), "ssp585": (2015, 2100)}
LICENCES_OK = ("CC0", "CC-BY 4.0", "CC BY 4.0", "CC-BY-SA 4.0", "CC BY-SA 4.0")
MODELS_JSON = DATA_DIR / "mdg" / "cmip6_modeles.json"
OUT_DIR = DATA_DIR / "mdg" / "cmip6_nexgddp"
TRIES, WAIT, PAUSE = 3, 30, 2
COLUMNS = ["modele", "scenario", "region", "annee", "mois", "variable", "valeur"]

CUM365 = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
CUM366 = np.cumsum([0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])


# --------------------------------------------------------------------------- calculs (testés sans réseau)
def is_leap(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def month_of_day(n_days: int, calendar: str, year: int) -> np.ndarray:
    """Mois (1-12) de chaque pas de temps d'un fichier annuel complet, selon le calendrier du modèle."""
    cal = (calendar or "standard").lower()
    if cal == "360_day":
        expected, cum = 360, np.arange(0, 361, 30)
    elif cal in ("noleap", "365_day"):
        expected, cum = 365, CUM365
    elif cal in ("all_leap", "366_day"):
        expected, cum = 366, CUM366
    elif cal in ("standard", "gregorian", "proleptic_gregorian", "julian"):
        expected, cum = (366, CUM366) if is_leap(year) else (365, CUM365)
    else:
        raise ValueError(f"calendrier inconnu : {calendar}")
    if n_days != expected:
        raise ValueError(f"{n_days} jours pour {year} (calendrier {calendar}, {expected} attendus) : fichier incomplet")
    return np.searchsorted(cum, np.arange(n_days), side="right")


def daily_to_monthly(data: np.ndarray, months: np.ndarray, var: str, units: str) -> np.ndarray:
    """(T, H, W) journalier -> (12, H, W) : pr en mm/mois (somme), tas et tasmax en °C (moyenne)."""
    data = np.asarray(data, dtype="float64")
    out = np.full((12,) + data.shape[1:], np.nan)
    if var == "pr":
        if units.replace(" ", "") not in ("kgm-2s-1", "kg/m2/s", "kgm^-2s^-1"):
            raise ValueError(f"unité de pr inattendue : {units}")
        mmday = data * 86400.0
        for m in range(1, 13):
            sel = mmday[months == m]
            out[m - 1] = np.where(np.isfinite(sel).all(axis=0), np.nansum(sel, axis=0), np.nan)
    else:
        if units.strip() != "K":
            raise ValueError(f"unité de {var} inattendue : {units}")
        for m in range(1, 13):
            sel = data[months == m]
            out[m - 1] = np.where(np.isfinite(sel).all(axis=0), sel.mean(axis=0), np.nan) - 273.15
    return out


def regional_means(monthly: np.ndarray, lat: np.ndarray, lon: np.ndarray, units: pd.DataFrame) -> dict:
    """(12, H, W) sur une grille régulière -> {adm1: 12 valeurs}, moyenne pondérée par la surface des fokontany."""
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    lon = np.where(lon > 180, lon - 360, lon)
    io_ = np.argsort(lon)
    ia = np.argsort(lat)[::-1]                                  # nord -> sud, comme les grilles du projet
    arr = monthly[:, ia][:, :, io_]
    res = float(np.median(np.diff(np.sort(lon)))) if len(lon) > 1 else 0.25
    ms = {"arr": arr[None], "lon0": lon[io_][0] - res / 2, "lat0": lat[ia][0] + res / 2, "res": res}
    return {pc: v[0] for pc, v in region_series(ms, units).items()}


def read_nc3(content: bytes, var: str) -> dict:
    """Lit une réponse NCSS (netCDF-3) : données (T, H, W) masquées, lat, lon, calendrier, unités, attributs globaux."""
    from scipy.io import netcdf_file
    f = netcdf_file(io.BytesIO(content), mmap=False)
    try:
        v = f.variables[var]
        data = np.array(v.data, dtype="float64")
        fill = [float(getattr(v, a)) for a in ("_FillValue", "missing_value") if hasattr(v, a)]
        for fv in fill:
            data[data == fv] = np.nan
        data[np.abs(data) > 1e19] = np.nan
        dec = lambda x: x.decode() if isinstance(x, bytes) else str(x)  # noqa: E731
        t = f.variables["time"]
        out = {"data": data, "lat": np.array(f.variables["lat"].data, float),
               "lon": np.array(f.variables["lon"].data, float),
               "calendar": dec(getattr(t, "calendar", b"standard")), "units": dec(getattr(v, "units", b"")),
               "attrs": {k: dec(a) for k, a in f._attributes.items()}}
    finally:
        f.close()
    return out


def licence_ok(lic: str) -> bool:
    return any(lic.strip().upper().startswith(x.upper()) for x in LICENCES_OK)


# --------------------------------------------------------------------------- accès
def model_info(modele: str) -> dict:
    meta = json.loads(MODELS_JSON.read_text(encoding="utf-8"))
    for m in meta["modeles"]:
        if m["modele"] == modele:
            return m
    raise SystemExit(f"modèle absent de {MODELS_JSON.name} : {modele}")


def ncss_url(modele: str, scenario: str, membre: str, grille: str, var: str, annee: int) -> str:
    fn = f"{var}_day_{modele}_{scenario}_{membre}_{grille}_{annee}_{VERSION}.nc"
    q = (f"var={var}&north={BBOX['north']}&south={BBOX['south']}&west={BBOX['west']}&east={BBOX['east']}"
         "&horizStride=1&temporal=all&accept=netcdf3&addLatLon=true")
    return f"{NCSS}/{modele}/{scenario}/{membre}/{var}/{fn}?{q}"


def fetch(url: str, session=None, sleep=time.sleep) -> bytes:
    """Une requête, 3 essais au plus espacés de 30 s ; erreur explicite au troisième échec."""
    if session is None:
        import requests
        session = requests.Session()
    s = session
    last = None
    for k in range(TRIES):
        try:
            r = s.get(url, timeout=300)
            if r.status_code == 200 and r.content[:3] == b"CDF":
                return r.content
            last = f"HTTP {r.status_code}, {len(r.content)} octets, début {r.content[:60]!r}"
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
        print(f"  essai {k + 1}/{TRIES} échoué : {last}", flush=True)
        if k < TRIES - 1:
            sleep(WAIT)
    raise RuntimeError(f"échec après {TRIES} essais : {url} ({last})")


def process_file(modele, scenario, membre, grille, var, annee, units, session=None):
    nc = read_nc3(fetch(ncss_url(modele, scenario, membre, grille, var, annee), session), var)
    lic = nc["attrs"].get("cmip6_license", "").strip()
    if not lic:
        lic = "absente de la réponse NCSS"
        print(f"  attention : cmip6_license non recopiée ({modele} {scenario} {var} {annee})", flush=True)
    elif not licence_ok(lic):
        raise SystemExit(f"licence non admise dans {modele} {scenario} {var} {annee} : « {lic} » ; arrêt")
    months = month_of_day(nc["data"].shape[0], nc["calendar"], annee)
    monthly = daily_to_monthly(nc["data"], months, var, nc["units"])
    reg = regional_means(monthly, nc["lat"], nc["lon"], units)
    rows = [{"modele": modele, "scenario": scenario, "region": pc, "annee": annee, "mois": m + 1, "variable": var,
             "valeur": round(float(v[m]), 3)} for pc, v in sorted(reg.items()) for m in range(12)]
    info = {"licence": lic, "calendrier": nc["calendar"], "version": nc["attrs"].get("version", ""),
            "forme": list(nc["data"].shape), "lat": [float(nc["lat"].min()), float(nc["lat"].max())],
            "lon": [float(nc["lon"].min()), float(nc["lon"].max())]}
    return rows, info


def run(modele, scenario, debut, fin, variables, out_dir=OUT_DIR):
    info_m = model_info(modele)
    membre, grille = info_m["membre"], info_m["grille_source"]
    units = read_units("mdg")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv, metaf = out_dir / f"{modele}_{scenario}.csv", out_dir / f"{modele}_{scenario}_meta.json"
    done = pd.read_csv(csv) if csv.exists() else pd.DataFrame(columns=COLUMNS)
    have = set(zip(done.variable, done.annee.astype(int))) if len(done) else set()
    meta = json.loads(metaf.read_text(encoding="utf-8")) if metaf.exists() else {"fichiers": {}}
    import requests
    s = requests.Session()
    for var in variables:
        for annee in range(debut, fin + 1):
            if (var, annee) in have:
                continue
            rows, info = process_file(modele, scenario, membre, grille, var, annee, units, s)
            pd.DataFrame(rows, columns=COLUMNS).to_csv(csv, mode="a", header=not csv.exists(), index=False)
            meta["fichiers"][f"{var}/{annee}"] = info
            meta.update({"modele": modele, "scenario": scenario, "membre": membre, "grille_source": grille,
                         "jeu": f"NEX-GDDP-CMIP6 {VERSION}", "emprise": BBOX, "maj": dt.datetime.utcnow().isoformat()})
            metaf.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{modele} {scenario} {var} {annee} : licence {info['licence']}, calendrier {info['calendrier']}",
                  flush=True)
            time.sleep(PAUSE)
    lic = sorted({v["licence"] for v in meta["fichiers"].values()})
    print(f"Terminé : {csv} ; licences lues : {lic}")


def probe(modele, annee, var):
    info_m = model_info(modele)
    scen = "historical" if annee <= 2014 else "ssp245"
    url = ncss_url(modele, scen, info_m["membre"], info_m["grille_source"], var, annee)
    print("URL :", url)
    rows, info = process_file(modele, scen, info_m["membre"], info_m["grille_source"], var, annee, read_units("mdg"))
    print(json.dumps(info, ensure_ascii=False))
    df = pd.DataFrame(rows, columns=COLUMNS)
    print(df.groupby("region").valeur.agg(["min", "max"]).round(1).head(30).to_string())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / f"sonde_{modele}_{var}_{annee}.csv", index=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--modele", default="ACCESS-CM2")
    ap.add_argument("--scenario", choices=SCENARIOS, default="historical")
    ap.add_argument("--debut", type=int)
    ap.add_argument("--fin", type=int)
    ap.add_argument("--variables", default=",".join(VARIABLES))
    ap.add_argument("--probe", action="store_true", help="un modèle, une année, une variable")
    ap.add_argument("--annee", type=int, default=2014)
    ap.add_argument("--variable", default="pr", choices=VARIABLES)
    a = ap.parse_args()
    if a.probe:
        probe(a.modele, a.annee, a.variable)
        return
    d0, d1 = YEARS[a.scenario]
    run(a.modele, a.scenario, a.debut or d0, a.fin or d1, [v for v in a.variables.split(",") if v])


if __name__ == "__main__":
    main()
