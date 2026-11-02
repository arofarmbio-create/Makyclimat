"""Fonctions communes MakyClimat : chemins, configuration, écriture des limites, utilitaires réseau."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
INPUTS_DIR = ROOT / "inputs"

UNIT_COLUMNS = ["level", "pcode", "name", "parent", "adm1", "adm2", "adm3",
                "lon", "lat", "area_km2", "pop", "pop_year", "pop_source",
                "pop_under5", "pop_under5_year", "pop_under5_source"]


def load_config(slug: str) -> dict:
    with open(CONFIG_DIR / "countries" / f"{slug}.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml(name: str) -> dict:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def country_data_dir(slug: str) -> Path:
    d = DATA_DIR / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def country_docs_dir(slug: str) -> Path:
    d = DOCS_DIR / "data" / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def units_path(slug: str) -> Path:
    return country_data_dir(slug) / "units.csv"


def grid_dir(slug: str) -> Path:
    d = country_data_dir(slug) / "grids"
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_units(slug: str) -> pd.DataFrame:
    return pd.read_csv(units_path(slug), dtype={"pcode": str, "parent": str, "adm1": str, "adm2": str, "adm3": str})


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def round_coords(geom: dict, nd: int = 4) -> dict:
    """Arrondit les coordonnées d'une géométrie GeoJSON pour alléger les fichiers."""
    def rec(c):
        if isinstance(c, (list, tuple)):
            if c and isinstance(c[0], (int, float)):
                return [round(c[0], nd), round(c[1], nd)]
            return [rec(x) for x in c]
        return c
    return {"type": geom["type"], "coordinates": rec(geom["coordinates"])}


def write_boundaries(slug: str, units: list[dict], geoms: dict[str, dict]) -> None:
    """Écrit les fichiers de limites pour le site et la table des unités.

    units : liste de dicts avec les colonnes UNIT_COLUMNS (pop facultatif).
    geoms : pcode -> géométrie GeoJSON (déjà simplifiée).
    Organisation des fichiers :
      docs/data/<slug>/geo/adm1.geojson, adm2.geojson
      docs/data/<slug>/geo/adm3/<adm2>.geojson, adm4/<adm2>.geojson
    """
    out = country_docs_dir(slug) / "geo"
    df = pd.DataFrame(units)
    for c in UNIT_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    df = df[UNIT_COLUMNS]
    df.to_csv(units_path(slug), index=False)

    def feats(sub: pd.DataFrame):
        return [{"type": "Feature",
                 "properties": {"c": r.pcode, "n": r.name, "p": r.parent},
                 "geometry": geoms[r.pcode]} for r in sub.itertuples() if r.pcode in geoms]

    for lv in (1, 2):
        sub = df[df.level == lv]
        write_json(out / f"adm{lv}.geojson", {"type": "FeatureCollection", "features": feats(sub)})
    for lv in (3, 4):
        for adm2, sub in df[df.level == lv].groupby("adm2"):
            write_json(out / f"adm{lv}" / f"{adm2}.geojson", {"type": "FeatureCollection", "features": feats(sub)})

    # Index de recherche : [pcode, nom, niveau, adm1, adm2, adm3]
    idx = [[r.pcode, r.name, int(r.level), r.adm1 if isinstance(r.adm1, str) else "",
            r.adm2 if isinstance(r.adm2, str) else "", r.adm3 if isinstance(r.adm3, str) else ""]
           for r in df.itertuples()]
    write_json(country_docs_dir(slug) / "index.json", idx)


def download(url: str, dest: Path, retries: int = 3, timeout: int = 120) -> bool:
    """Télécharge un fichier. Retourne False en cas d'absence (404), lève l'erreur sinon."""
    import requests
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, stream=True, timeout=timeout)
            if r.status_code == 404:
                return False
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
            return True
        except Exception as e:  # noqa: BLE001
            if attempt == retries:
                raise
            print(f"  nouvelle tentative ({attempt}) pour {url}: {e}")
            # 429 « trop de requêtes » (CHIRPS, 02/11/2026) : attendre vraiment, sinon le serveur continue de refuser
            busy = "429" in str(e)
            time.sleep(min(60 * attempt, 300) if busy else 3 * attempt)
    return False


def cds_cancel_stale(client, dataset: str, max_age_h: float = 6.0, session=None, now=None) -> int:
    """Liste les demandes du compte encore en file chez Copernicus et annule celles de `dataset` en attente depuis
    plus de `max_age_h` heures. Ce sont des demandes orphelines (tâche GitHub annulée ou arrivée à sa limite de temps
    avant la réponse) : elles occupent la file du compte et font refuser les nouvelles (02/11/2026). Les demandes
    récentes, peut-être attendues par une autre tâche en cours, ne sont jamais touchées. Retourne le nombre annulé."""
    import datetime as dt
    import requests
    base, key = getattr(client, "url", "").rstrip("/"), getattr(client, "key", "")
    if not base or not key:
        return 0
    s = session or requests.Session()
    h = {"PRIVATE-TOKEN": key}
    try:
        r = s.get(f"{base}/retrieve/v1/jobs", params={"status": ["accepted", "running"], "limit": 100},
                  headers=h, timeout=60)
        r.raise_for_status()
        jobs = r.json().get("jobs", [])
    except Exception as e:  # noqa: BLE001  (diagnostic seulement : ne doit jamais faire échouer la requête)
        print(f"  liste des demandes Copernicus indisponible : {type(e).__name__}", flush=True)
        return 0
    now = now or dt.datetime.now(dt.timezone.utc)
    mine = [j for j in jobs if j.get("processID") == dataset]
    print(f"  demandes en file chez Copernicus : {len(jobs)} au total, {len(mine)} pour {dataset}", flush=True)
    n = 0
    for j in mine:
        try:
            age = (now - dt.datetime.fromisoformat(str(j.get("created", "")).replace("Z", "+00:00"))).total_seconds() / 3600
        except ValueError:
            continue
        if j.get("status") == "accepted" and age > max_age_h:
            try:
                s.delete(f"{base}/retrieve/v1/jobs/{j['jobID']}", headers=h, timeout=60).raise_for_status()
                n += 1
                print(f"  demande orpheline annulée (en attente depuis {age:.0f} h)", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"  annulation impossible : {type(e).__name__}", flush=True)
    return n


def cds_retrieve(client, dataset: str, request: dict, target, waits: int = 6, pause: int = 900) -> None:
    """Requête Copernicus (CDS, EWDS). Si la file d'attente du jeu est pleine pour ce compte (« Maximum number queued
    requests », vu le 29/10 et le 01/11/2026), attend et réessaie au lieu d'échouer ; toute autre erreur remonte avec
    le message du serveur."""
    import requests
    for attempt in range(waits + 1):
        try:
            client.retrieve(dataset, request, str(target))
            return
        except requests.HTTPError as e:
            msg = e.response.text[:800] if e.response is not None else str(e)
            if "queued requests" in msg and attempt < waits:
                if attempt == 0:
                    cds_cancel_stale(client, dataset)
                print(f"  file d'attente Copernicus pleine ({dataset}), nouvel essai dans {pause // 60} min "
                      f"({attempt + 1}/{waits})", flush=True)
                time.sleep(pause)
                continue
            raise RuntimeError(f"{dataset} refusé : {msg}") from e


def hdx_resources(dataset: str) -> list[dict]:
    """Liste les ressources d'un jeu de données HDX (API CKAN publique)."""
    import requests
    r = requests.get("https://data.humdata.org/api/3/action/package_show",
                     params={"id": dataset}, timeout=60)
    r.raise_for_status()
    return r.json()["result"]["resources"]


# ---------- Grille raster (format npz simple, sans dépendance à rasterio pour l'analyse) ----------

def save_grid(path: Path, **arrays) -> None:
    np.savez_compressed(path, **arrays)


def load_grid(path: Path) -> dict:
    z = np.load(path, allow_pickle=False)
    return {k: z[k] for k in z.files}


def sample_grid(arr: np.ndarray, lon0: float, lat0: float, res: float,
                lons: np.ndarray, lats: np.ndarray, max_ring: int = 4) -> np.ndarray:
    """Valeur de la cellule contenant chaque point ; cherche la cellule valide voisine si NaN (côtes)."""
    h, w = arr.shape[-2:]
    cols = np.floor((lons - lon0) / res).astype(int)
    rows = np.floor((lat0 - lats) / res).astype(int)
    cols = np.clip(cols, 0, w - 1)
    rows = np.clip(rows, 0, h - 1)
    vals = arr[rows, cols].astype(float)
    bad = np.where(~np.isfinite(vals))[0]
    for i in bad:
        r0, c0 = rows[i], cols[i]
        found = np.nan
        for ring in range(1, max_ring + 1):
            r1, r2 = max(r0 - ring, 0), min(r0 + ring + 1, h)
            c1, c2 = max(c0 - ring, 0), min(c0 + ring + 1, w)
            win = arr[r1:r2, c1:c2]
            ok = np.isfinite(win)
            if ok.any():
                rr, cc = np.where(ok)
                d = (rr + r1 - r0) ** 2 + (cc + c1 - c0) ** 2
                j = int(np.argmin(d))
                found = float(win[rr[j], cc[j]])
                break
        vals[i] = found
    return vals


def locate_points(slug: str, lons, lats):
    """Pour chaque point (lon, lat), le code du fokontany qui le contient ('' si aucun). Utilise les limites publiées dans docs/data."""
    import json

    from shapely.geometry import Point, shape
    from shapely.strtree import STRtree

    geo_dir = country_docs_dir(slug) / "geo" / "adm4"
    geoms, codes = [], []
    for f in sorted(geo_dir.glob("*.geojson")):
        for ft in json.loads(f.read_text(encoding="utf-8"))["features"]:
            geoms.append(shape(ft["geometry"]))
            codes.append(ft["properties"]["c"])
    tree = STRtree(geoms)
    pts = [Point(x, y) for x, y in zip(lons, lats)]
    out = [""] * len(pts)
    hit_p, hit_g = tree.query(pts, predicate="within")
    for pi, gi in zip(hit_p, hit_g):
        if not out[pi]:
            out[pi] = codes[gi]
    return out
