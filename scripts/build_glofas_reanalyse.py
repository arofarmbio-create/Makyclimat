"""R-21 bis, section 5 : collecte uniquement, aucun score scientifique.

API vérifiée le 12/11/2026 : https://confluence.ecmwf.int/spaces/CEMS/pages/699325478
et https://confluence.ecmwf.int/spaces/CEMS/pages/242067432 (exemple GloFAS).
Une saison s commence en novembre s et finit en avril s+1. Les sélecteurs
year/month/day font un produit cartésien : une demande contient donc aussi
des jours hors fenêtre, éliminés avant écriture du NPZ (25/11–05/04 inclus).
Schéma : dates ISO (jour de validité), lat/lon (maille), q float32 (jour, maille), m³/s.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import urllib.parse

import numpy as np

BASE = "https://ewds.climate.copernicus.eu/api/retrieve/v1"
JEU = "cems-glofas-historical"
TAG = "glofas-reanalyse-v4"
EN_ATTENTE = 75
ECHECS = {"failed", "dismissed", "rejected", "deleted"}


def saisons(texte):
    mots = texte.split()
    if not mots or any(not re.fullmatch(r"20(?:0[3-9]|1[0-6])", s) for s in mots):
        raise ValueError("Saisons admises : 2003 à 2016, séparées par des espaces")
    return sorted(set(map(int, mots)))


def dates_saison(saison):
    saisons(str(saison))
    return np.arange(np.datetime64(f"{saison}-11-25"), np.datetime64(f"{saison+1}-04-06"))


def requete(saison):
    dates_saison(saison)
    return {"system_version": ["version_4_0"], "hydrological_model": ["lisflood"],
            "product_type": ["consolidated"], "timespan": "time_mean",
            "variable": ["average_river_discharge_in_the_last_24_hours"],
            "year": [str(saison), str(saison+1)], "month": ["01", "02", "03", "04", "11", "12"],
            "day": [f"{j:02d}" for j in range(1, 32)],
            "area": [-11.5, 43.0, -26.0, 51.0], "data_format": "netcdf",
            "download_format": "unarchived"}


def lire_note(path):
    note = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(note.get("jobID"), str) or not re.fullmatch(r"[\w-]+", note["jobID"]):
        raise ValueError(f"Note illisible : {path}")
    return note


def statut(session, entetes, job, essais=5, dormir=time.sleep):
    # Erreur 5xx passagère d'EWDS (run 43236237171, saison 2006, 12/11) : on réessaie avant d'abandonner.
    for essai in range(essais):
        r = session.get(f"{BASE}/jobs/{job}", headers=entetes, timeout=60)
        if r.status_code < 500 or essai == essais - 1:
            break
        dormir(30 * (essai + 1))
    if r.status_code == 404:
        return "deleted"
    r.raise_for_status()
    etat = r.json()["status"]
    if etat not in ECHECS | {"accepted", "running", "successful"}:
        raise ValueError(f"État EWDS inconnu : {etat}")
    return etat


def demande_reprenable(session, entetes, demande, fichier, delai_s, publier=None,
                       pause=60, horloge=time.monotonic, dormir=time.sleep):
    """Même cycle que R-40 ; une note incompatible arrête avant toute soumission."""
    job = None
    if fichier.exists():
        note = lire_note(fichier)
        if note.get("jeu") != JEU or note.get("requete") != demande:
            raise ValueError("Note incompatible avec la requête : intervention nécessaire")
        if statut(session, entetes, note["jobID"]) not in ECHECS:
            job = note["jobID"]
    if job is None:
        r = session.post(f"{BASE}/processes/{JEU}/execution", json={"inputs": demande},
                         headers=entetes, timeout=120)
        r.raise_for_status()
        job = r.json()["jobID"]
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(json.dumps({"jeu": JEU, "requete": demande, "jobID": job,
                           "soumise": dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2), encoding="utf-8")
    # Republier aussi à la reprise : une publication précédente peut avoir échoué.
    if publier:
        publier(fichier)
    debut = horloge()
    while True:
        etat = statut(session, entetes, job)
        print(f"EWDS {job} : {etat}", flush=True)
        if etat == "successful":
            r = session.get(f"{BASE}/jobs/{job}/results", headers=entetes, timeout=60)
            r.raise_for_status()
            return urllib.parse.urljoin(f"{BASE}/jobs/{job}/results", r.json()["asset"]["value"]["href"])
        if etat in ECHECS:
            raise RuntimeError(f"EWDS {job} : {etat}")
        if horloge() - debut >= delai_s:
            return None
        dormir(min(pause, delai_s - (horloge() - debut)))


def menage(session, entetes, dossier, courante, now=None):
    """Épargne toutes les notes ; ne touche qu'aux demandes orphelines de ce jeu.

    Refuse une nouvelle collecte si une autre demande EWDS est encore active,
    y compris une autre saison notée après un retour 75 de la matrice.
    """
    if not dossier.is_dir():
        raise ValueError("Dossier des notes absent : restaurer la release avant le ménage")
    notes = [lire_note(p) for p in sorted(dossier.glob("*.demande.json"))]
    garder = {n["jobID"] for n in notes}
    propre = lire_note(courante)["jobID"] if courante.exists() else None
    r = session.get(f"{BASE}/jobs", params={"status": ["accepted", "running"], "limit": 100},
                    headers=entetes, timeout=60)
    r.raise_for_status()
    data = r.json()
    jobs = data["jobs"]
    if len(jobs) >= 100 or any(l.get("rel") == "next" for l in data.get("links", [])):
        raise RuntimeError("Inventaire EWDS incomplet : arrêt avant ménage")
    now = now or dt.datetime.now(dt.timezone.utc)
    libre = True
    for j in jobs:
        ident = j["jobID"]
        if ident == propre:
            continue
        ancien = dt.datetime.fromisoformat(j["created"].replace("Z", "+00:00"))
        if (ident not in garder and j.get("processID") == JEU and j["status"] == "accepted"
                and (now - ancien).total_seconds() >= 1800):
            r = session.delete(f"{BASE}/jobs/{ident}", headers=entetes, timeout=60)
            r.raise_for_status()
        else:
            libre = False
    return libre


def mailles(dossier):
    """Union des seules coordonnées publiées, sans seuil nouveau ni interpolation."""
    points = {}
    fichiers = sorted(dossier.glob("glofas_v4_*.npz"))
    if not fichiers:
        raise ValueError("Aucune reprévision de référence")
    for f in fichiers:
        with np.load(f, allow_pickle=False) as z:
            lat, lon = z["lat"], z["lon"]
            if lat.ndim != 1 or lat.shape != lon.shape or not np.isfinite([lat, lon]).all():
                raise ValueError(f"Coordonnées invalides : {f.name}")
            for a, b in zip(lat, lon):
                points.setdefault((round(float(a), 3), round(float(b), 3)), (a, b))
    if not points:
        raise ValueError("Aucune maille de rivière")
    coords = np.array([points[k] for k in sorted(points)], dtype="float32")
    return coords[:, 0], coords[:, 1]


def extraire(ds, saison, lat, lon):
    import xarray as xr
    # Le nom de la variable dépend de l'API (run 43230289148 du 12/11 : aucun des noms connus). On garde un nom connu
    # s'il est présent, sinon la seule variable spatiale du fichier ; les dimensions de taille 1 (step, surface…)
    # sont retirées. Le contenu du fichier est journalisé pour la traçabilité.
    print("NetCDF EWDS :", {v: dict(ds[v].sizes) for v in ds.data_vars}, flush=True)
    connus = ("dis24", "avg_dis24", "dis", "average_river_discharge_in_the_last_24_hours")
    noms = [v for v in connus if v in ds.data_vars] or [
        v for v in ds.data_vars if {"latitude", "longitude"} <= set(ds[v].dims)]
    if len(noms) != 1:
        raise ValueError(f"Variable de débit absente ou ambiguë : {list(ds.data_vars)}")
    q = ds[noms[0]]
    q = q.squeeze([d for d in q.dims if q.sizes[d] == 1 and d not in ("latitude", "longitude")])
    t = "valid_time" if "valid_time" in q.coords else "time"
    if q[t].ndim != 1:
        raise ValueError("Temps de validité non unidimensionnel")
    tdim = q[t].dims[0]
    if set(q.dims) != {tdim, "latitude", "longitude"}:
        raise ValueError(f"Dimensions inattendues : {q.dims}")
    dates = q[t].values.astype("datetime64[D]")
    attendues = dates_saison(saison)
    idx = np.flatnonzero((dates >= attendues[0]) & (dates <= attendues[-1]))
    idx = idx[np.argsort(dates[idx])]
    if not np.array_equal(dates[idx], attendues):
        raise ValueError("Jours manquants ou doublonnés : sortie refusée")
    axes = []
    for nom, cible in (("latitude", lat), ("longitude", lon)):
        axe = q[nom].values
        if axe.ndim != 1 or len(np.unique(axe)) != len(axe):
            raise ValueError(f"Axe invalide : {nom}")
        indices = np.abs(axe[:, None] - cible).argmin(axis=0)
        if not np.allclose(axe[indices], cible, rtol=0, atol=1e-4):
            raise ValueError(f"Maille R-21 absente de la réanalyse : {nom}")
        axes.append(xr.DataArray(indices, dims="maille"))
    valeurs = q.isel({tdim: idx, "latitude": axes[0], "longitude": axes[1]}).transpose(tdim, "maille").values
    return {"dates": attendues.astype(str), "lat": lat.astype("float32"), "lon": lon.astype("float32"),
            "q": valeurs.astype("float32")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saison", type=int, required=True, choices=range(2003, 2017))
    ap.add_argument("--references", type=Path, required=True)
    ap.add_argument("--sortie", type=Path, default=Path("data/mdg/glofas_reanalyse"))
    ap.add_argument("--notes", type=Path, required=True)
    ap.add_argument("--delai-min", type=float, default=300)
    ap.add_argument("--publier-demande", choices=[TAG])
    args = ap.parse_args()
    if not 0 < args.delai_min <= 300:
        ap.error("Délai attendu entre 0 et 300 minutes")
    import requests
    import xarray as xr
    lat, lon = mailles(args.references)
    args.sortie.mkdir(parents=True, exist_ok=True)
    note = args.notes / f"glofas_reanalyse_{args.saison}.demande.json"
    headers = {"PRIVATE-TOKEN": os.environ["CDS_API_KEY"]}
    with requests.Session() as session:
        if not menage(session, headers, args.notes, note):
            print("::warning::Autre demande EWDS active : aucune soumission")
            return EN_ATTENTE
        publier = None
        if args.publier_demande:
            def publier(p):
                subprocess.run(["gh", "release", "upload", TAG, str(p), "--clobber"], check=True)
        href = demande_reprenable(session, headers, requete(args.saison), note, args.delai_min * 60, publier)
        if href is None:
            print("::warning::Demande conservée pour reprise au prochain lancement")
            return EN_ATTENTE
        # La clé EWDS ne doit jamais accompagner l'URL du stockage externe.
        url = urllib.parse.urlsplit(href)
        if url.scheme != "https":
            raise ValueError("URL de résultat non HTTPS")
        h = headers if url.netloc == urllib.parse.urlsplit(BASE).netloc else {}
        with tempfile.TemporaryDirectory() as tmp:
            brut = Path(tmp) / "debit.nc"
            with session.get(href, headers=h, stream=True, timeout=600, allow_redirects=False) as r:
                r.raise_for_status()
                if r.status_code != 200:
                    raise RuntimeError("Résultat EWDS redirigé : arrêt sans transmettre la clé")
                with brut.open("wb") as f:
                    for bloc in r.iter_content(1 << 20):
                        f.write(bloc)
            with xr.open_dataset(brut) as ds:
                resultat = extraire(ds, args.saison, lat, lon)
            cible = args.sortie / f"glofas_reanalyse_{args.saison}.npz"
            provisoire = cible.with_suffix(".tmp.npz")
            np.savez_compressed(provisoire, **resultat)
            provisoire.replace(cible)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
