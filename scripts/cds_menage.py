"""Ménage de la file Copernicus (CDS) du compte : liste les demandes en attente ou en cours et annule celles qui sont
orphelines (en attente depuis plus de --age-min minutes, tous jeux confondus).

Pourquoi (02/11/2026) : une demande C3S restée en file près de 5 heures, laissée par une tâche annulée, faisait
refuser toutes les demandes ERA5-Land du compte (« Maximum number queued requests »), alors que la file ERA5-Land
du compte était vide. Les demandes en cours de calcul (« running ») ne sont jamais annulées, ni celles passées par
--garder (12/11/2026 : collecte reprenable des rafales R-40, la demande en file est reprise par le lancement suivant).
Relecture Codex du 12/11 (14:55) : toutes les demandes notées (--garder-notes, notes rafales_*.demande.json de toutes
les activations) sont épargnées, pas seulement celle de l'activation courante ; une note illisible arrête tout (code 3)
au lieu d'être prise pour une absence.
Usage : python scripts/cds_menage.py [--age-min 30] [--garder ID ...] [--garder-notes DOSSIER] [--liste-seulement]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

import requests

BASE = "https://cds.climate.copernicus.eu/api"


def stale_jobs(jobs: list[dict], now: dt.datetime, age_min: float, garder=()) -> list[dict]:
    """Demandes « accepted » (en file, pas encore calculées) plus anciennes que age_min minutes, hors `garder`."""
    out = []
    for j in jobs:
        if j.get("jobID") in garder:
            continue
        try:
            created = dt.datetime.fromisoformat(str(j.get("created", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if created.tzinfo is None:                   # Copernicus date ses demandes sans fuseau, en UTC (run 43216795187)
            created = created.replace(tzinfo=dt.timezone.utc)
        if j.get("status") == "accepted" and (now - created).total_seconds() / 60 > age_min:
            out.append(j)
    return out


def ids_notes(dossier) -> set[str]:
    """Identifiants des demandes notées dans un dossier (*.demande.json). Une note illisible lève ValueError."""
    ids = set()
    for f in sorted(Path(dossier).glob("*.demande.json")):
        try:
            ids.add(str(json.loads(f.read_text(encoding="utf-8"))["jobID"]))
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise ValueError(f"note illisible : {f.name} ({e})") from e
    return ids


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--age-min", type=float, default=30)
    ap.add_argument("--garder", nargs="*", default=[], help="identifiants de demandes à ne jamais annuler")
    ap.add_argument("--garder-notes", help="dossier des notes *.demande.json dont les demandes sont à épargner")
    ap.add_argument("--liste-seulement", action="store_true")
    args = ap.parse_args()
    garder = set(args.garder)
    if args.garder_notes:
        try:
            garder |= ids_notes(args.garder_notes)
        except ValueError as e:
            print(f"::error::{e} : ménage annulé", flush=True)
            sys.exit(3)
        print(f"{len(garder)} demande(s) notée(s) épargnée(s)")
    h = {"PRIVATE-TOKEN": os.environ["CDS_API_KEY"]}
    r = requests.get(f"{BASE}/retrieve/v1/jobs", params={"status": ["accepted", "running"], "limit": 100}, headers=h, timeout=60)
    r.raise_for_status()
    jobs = r.json().get("jobs", [])
    now = dt.datetime.now(dt.timezone.utc)
    print(f"{len(jobs)} demande(s) en file ou en cours :")
    for j in jobs:
        print(f"  {j.get('processID')} : {j.get('status')}, créée {j.get('created')}")
    if args.liste_seulement:
        return
    for j in stale_jobs(jobs, now, args.age_min, garder):
        d = requests.delete(f"{BASE}/retrieve/v1/jobs/{j['jobID']}", headers=h, timeout=60)
        print(f"  annulée : {j.get('processID')} (HTTP {d.status_code})")


if __name__ == "__main__":
    main()
