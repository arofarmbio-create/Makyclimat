"""NDVI MOD13C2 (MODIS Terra, CMG 0,05°, mensuel, v6.1, NASA LP DAAC) pour la colonne NDVI des covariables H-C6
(protocole carte des nappes) : moyenne 2001-2010 des pixels fiables dans chaque maille BGS de 0,28°.

Accès : service OPeNDAP de la NASA dans le cloud (opendap.earthdata.nasa.gov), compte Earthdata ; seul le
sous-ensemble de Madagascar est demandé (environ 300 x 170 pixels par mois au lieu d'un fichier mondial de 89 Mo).
Une requête à la fois, attente croissante sur 503 et coupures (règles de validation/etat_telechargements.md).
Pixels gardés : fiabilité 0 (bonne) ou 1 (marginale) ; NDVI = valeur brute / 10 000.
Usage : python scripts/build_ndvi_mod13c2.py --probe         (noms des variables d'un mois)
        python scripts/build_ndvi_mod13c2.py --country mdg    (moyenne 2001-2010 et colonne NDVI)
"""
from __future__ import annotations

import argparse
import re
import time

import numpy as np
import pandas as pd
import requests

from common import country_data_dir

COLLECTION = "C2565788914-LPCLOUD"
OPENDAP = "https://opendap.earthdata.nasa.gov/collections/" + COLLECTION + "/granules/"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
RES = 0.05
ROW0, ROW1 = 2022, 2324                     # lignes de 11,1°S à 26,2°S (ligne 0 = 90°N)
COL0, COL1 = 4456, 4624                     # colonnes de 42,8°E à 51,2°E (colonne 0 = 180°O)
BGS_RES = 0.28


def granule_id(year: int, month: int) -> str | None:
    r = requests.get(CMR, params={"short_name": "MOD13C2", "version": "061", "page_size": 5,
                                  "temporal": f"{year}-{month:02d}-01T00:00:00Z,{year}-{month:02d}-02T00:00:00Z"}, timeout=60)
    r.raise_for_status()
    ids = [e["title"] for e in r.json()["feed"]["entry"] if f".A{year}{pd.Timestamp(year, month, 1).dayofyear:03d}." in e["title"]]
    return ids[0] if ids else None


def find_var(dds: str, *words: str) -> str:
    """Nom complet de la première variable du DDS qui contient tous les mots (sans tenir compte de la casse)."""
    names = re.findall(r"(?:Int16|UInt8|Int8|Float32|UInt16)\s+([\w.]+)\[", dds)
    for n in names:
        if all(w.lower() in n.lower() for w in words):
            return n
    raise ValueError(f"variable {words} introuvable parmi {names[:15]}")


def parse_ascii_grid(text: str, var: str) -> np.ndarray:
    """Réponse ASCII OPeNDAP d'un tableau 2D -> tableau (lignes, colonnes)."""
    leaf = var.split(".")[-1]
    rows = [list(map(float, ln.split(",")[1:])) for ln in text.splitlines()
            if re.match(r"^\s*(?:[\w.]*\.)?" + re.escape(leaf) + r"\[\d+\],", ln)]
    if not rows:
        raise ValueError("réponse OPeNDAP sans données")
    return np.array(rows, dtype="float32")


def fetch(s, url: str, tries: int = 6, sleep=time.sleep) -> str | None:
    for k in range(tries):
        try:
            r = s.get(url, timeout=180)
            if r.status_code == 200:
                return r.text
            if r.status_code in (401, 403):
                raise RuntimeError(f"accès refusé (HTTP {r.status_code}) : compte Earthdata")
            why = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            why = type(e).__name__
        print(f"  essai {k + 1} : {why}", flush=True)
        if k + 1 < tries:
            sleep(min(60 * (k + 1), 300))
    return None


def cell_means(ndvi: np.ndarray, lons, lats) -> list[float]:
    """Moyenne des pixels (grille ROW0/COL0, 0,05°) dont le centre est dans chaque maille BGS de 0,28°."""
    plat = 90 - (np.arange(ROW0, ROW1 + 1) + 0.5) * RES
    plon = -180 + (np.arange(COL0, COL1 + 1) + 0.5) * RES
    out = []
    for lo, la in zip(lons, lats):
        r = np.where(np.abs(plat - la) <= BGS_RES / 2)[0]
        c = np.where(np.abs(plon - lo) <= BGS_RES / 2)[0]
        v = ndvi[np.ix_(r, c)]
        out.append(round(float(np.nanmean(v)), 4) if np.isfinite(v).any() else np.nan)
    return out


def main() -> None:
    import build_imerg_pilot as P                       # session Earthdata (redirections URS)
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="mdg")
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()
    s = P.session()
    gid = granule_id(2005, 1)
    dds = fetch(s, OPENDAP + gid + ".dds")
    v_ndvi = find_var(dds, "ndvi")
    v_rel = find_var(dds, "reliability")
    print(f"granule {gid} ; variables : {v_ndvi}, {v_rel}", flush=True)
    if args.probe:
        t = fetch(s, OPENDAP + gid + f".ascii?{v_ndvi}[{ROW0}:{ROW0 + 2}][{COL0}:{COL0 + 2}]")
        print(t[:800] if t else "aucune réponse")
        return
    total = np.zeros((ROW1 - ROW0 + 1, COL1 - COL0 + 1))
    count = np.zeros_like(total)
    got = 0
    for y in range(2001, 2011):
        for m in range(1, 13):
            g = granule_id(y, m)
            sub = f"[{ROW0}:{ROW1}][{COL0}:{COL1}]"
            tn = fetch(s, OPENDAP + g + f".ascii?{v_ndvi}{sub}") if g else None
            tr = fetch(s, OPENDAP + g + f".ascii?{v_rel}{sub}") if g else None
            time.sleep(1.0)
            if tn is None or tr is None:
                print(f"  {y}-{m:02d} : manquant", flush=True)
                continue
            nd, rel = parse_ascii_grid(tn, v_ndvi), parse_ascii_grid(tr, v_rel)
            ok = (nd > -3000) & ((rel == 0) | (rel == 1))
            total += np.where(ok, nd / 10000.0, 0.0); count += ok
            got += 1
            print(f"  {y}-{m:02d} : {int(ok.sum())} pixels fiables", flush=True)
    mean = np.where(count > 0, total / np.maximum(count, 1), np.nan)
    path = country_data_dir(args.country) / "nappes_mondiales" / "covariables_hc6.csv"
    df = pd.read_csv(path)
    df["NDVI"] = cell_means(mean, df.lon, df.lat)
    df["NDVI_source"] = f"MOD13C2 v6.1 (NASA LP DAAC), moyenne 2001-2010 de {got} mois, pixels de fiabilité 0 ou 1"
    df.to_csv(path, index=False)
    print(f"{path.name} : NDVI sur {int(df.NDVI.notna().sum())} mailles ({got} mois sur 120)")


if __name__ == "__main__":
    main()
