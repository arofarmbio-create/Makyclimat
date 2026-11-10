"""État GitHub en direct pour le tableau de bord : runs, job et étape en cours, runs bloqués, mois de la release R-21.

Aucun modèle de langage : uniquement `gh` (déjà authentifié sur le PC). Appelé toutes les 20 s par le serveur local ;
quelques requêtes par cycle, très en deçà de la limite de l'API GitHub (5 000 requêtes par heure).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE_R21 = "reprevisions-glofas-v4"
BLOQUE_MIN = 60                  # run non terminé, sans job actif, depuis plus d'une heure : signalé en rouge
JOBS_MAX = 4                     # détail des jobs pour les 4 runs non terminés les plus récents
_verrou = threading.Lock()
_etat: dict = {"runs": [], "release": None, "alertes": [], "maj": None, "erreur": None}
_vus: dict[int, str] = {}        # statut précédent de chaque run, pour annoncer les fins


def gh(*arguments, timeout=30):
    """Sortie JSON de gh, décodée en UTF-8 (indépendamment de la page de code de Windows)."""
    retour = subprocess.run(["gh", *arguments], cwd=ROOT, capture_output=True, timeout=timeout, check=False,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if retour.returncode != 0:
        raise RuntimeError(retour.stderr.decode("utf-8", errors="replace").strip()[:300] or "gh a échoué")
    return json.loads(retour.stdout.decode("utf-8") or "null")


def instant(texte):
    if not texte or texte.startswith("0001"):
        return None
    return datetime.fromisoformat(texte.replace("Z", "+00:00"))


def duree(debut, fin=None):
    if not debut:
        return ""
    secondes = int(((fin or datetime.now(timezone.utc)) - debut).total_seconds())
    h, m = divmod(max(secondes, 0) // 60, 60)
    return f"{h} h {m:02d}" if h else f"{m} min"


def resumer_jobs(jobs):
    """Job et étape en cours, jobs en attente et terminés."""
    actifs, attente, finis = [], 0, {}
    for job in jobs:
        if job["status"] == "in_progress":
            etape = next((s["name"] for s in job.get("steps") or [] if s["status"] == "in_progress"), "")
            actifs.append({"nom": job["name"], "etape": etape, "depuis": duree(instant(job.get("startedAt"))),
                           "url": job.get("url", "")})
        elif job["status"] in ("queued", "waiting", "pending", "requested"):
            attente += 1
        else:
            cle = job.get("conclusion") or job["status"]
            finis[cle] = finis.get(cle, 0) + 1
    return actifs, attente, finis


def lire_release():
    """Mois présents dans la release R-21, groupés par année (glofas_v4_AAAA_MM.npz)."""
    donnees = gh("release", "view", RELEASE_R21, "--json", "assets")
    annees: dict[str, list[int]] = {}
    for asset in donnees.get("assets") or []:
        if m := re.fullmatch(r"glofas_v4_(\d{4})_(\d{2})\.npz", asset["name"]):
            annees.setdefault(m[1], []).append(int(m[2]))
    return {"nom": RELEASE_R21, "mois": sum(len(v) for v in annees.values()),
            "annees": {a: sorted(v) for a, v in sorted(annees.items())}}


ECHECS = ("failure", "cancelled", "timed_out", "startup_failure")
_chemins: dict[int, str] = {}    # identifiant de workflow -> chemin du fichier (.github/workflows/…)


def chemin_workflow(identifiant):
    if identifiant not in _chemins:
        try:
            _chemins.update({w["id"]: w["path"] for w in gh("workflow", "list", "--all", "--json", "id,path")})
        except (RuntimeError, ValueError, subprocess.TimeoutExpired):
            pass
    return _chemins.get(identifiant, "")


def actualiser(avis=None, avec_release=True, echec=None):
    """Interroge GitHub et met l'état en cache. avis(texte) est appelé pour chaque run qui vient de se terminer ;
    echec(run) en plus pour chaque run terminé en échec ou annulé (diagnostic automatique par le responsable)."""
    maintenant = datetime.now(timezone.utc)
    try:
        champs = ("databaseId,workflowName,workflowDatabaseId,displayTitle,status,conclusion,createdAt,startedAt,"
                  "updatedAt,event,url")
        runs = gh("run", "list", "-L", "12", "--json", champs)
        # Un run long (R-21 : plusieurs jours) sort des 12 derniers : on ajoute à part les runs encore actifs ou en file.
        connus = {r["databaseId"] for r in runs}
        actifs = [r for statut in ("in_progress", "queued") for r in gh("run", "list", "-s", statut, "-L", "10", "--json", champs)]
        for r in actifs:
            if r["databaseId"] not in connus:
                connus.add(r["databaseId"])
                runs.append(r)
        # Relecture Codex (10:53) : un run long qui se termine sort des deux listes ; sans cette requête, sa fin
        # (avis, diagnostic d'échec) ne serait jamais vue. On interroge chaque run suivi encore non terminé et absent.
        for identifiant, statut in list(_vus.items()):
            if statut != "completed" and identifiant not in connus:
                try:
                    runs.append(gh("run", "view", str(identifiant), "--json", champs))
                    connus.add(identifiant)
                except (RuntimeError, ValueError, subprocess.TimeoutExpired):
                    pass
        runs = [r for r in runs if r["status"] != "completed"] + sorted(
            (r for r in runs if r["status"] == "completed"), key=lambda r: r["createdAt"], reverse=True)
        sortie, alertes = [], []
        non_finis = [r for r in runs if r["status"] != "completed"][:JOBS_MAX]
        for run in runs:
            ligne = {"id": run["databaseId"], "workflow": run["workflowName"], "titre": run["displayTitle"],
                     "url": run["url"], "evenement": run["event"], "statut": run["status"],
                     "conclusion": run.get("conclusion") or "", "cree": run["createdAt"],
                     "duree": duree(instant(run.get("startedAt") or run["createdAt"]),
                                    instant(run["updatedAt"]) if run["status"] == "completed" else None),
                     "actifs": [], "attente": 0, "finis": {}}
            if run in non_finis:
                try:
                    jobs = gh("run", "view", str(run["databaseId"]), "--json", "jobs").get("jobs") or []
                    ligne["actifs"], ligne["attente"], ligne["finis"] = resumer_jobs(jobs)
                except (RuntimeError, ValueError, subprocess.TimeoutExpired):
                    pass
                for job in jobs if ligne["actifs"] else []:
                    debut = instant(job.get("startedAt")) if job["status"] == "in_progress" else None
                    if debut and (maintenant - debut).total_seconds() > 4 * 3600:
                        alertes.append(f"{run['workflowName']} · {job['name']} : en cours depuis {duree(debut)}, "
                                       f"proche de la limite de 5 h (le job 2010 a été arrêté ainsi le 09/11).")
                age = (maintenant - instant(run["createdAt"])).total_seconds() / 60
                if not ligne["actifs"] and age > BLOQUE_MIN:
                    ligne["bloque"] = True
                    alertes.append(f"{run['workflowName']} : en file depuis {duree(instant(run['createdAt']))} "
                                   f"sans job actif.")
            precedent = _vus.get(run["databaseId"])
            nouveau = run["status"]
            if precedent and precedent != "completed" and run["status"] == "completed":
                if avis:
                    avis(f"GitHub : {run['workflowName'][:60]} — {(run.get('conclusion') or 'terminé')}")
                if echec and run.get("conclusion") in ECHECS:
                    try:
                        transmis = echec({**ligne, "chemin": chemin_workflow(run.get("workflowDatabaseId"))})
                    except Exception as erreur:      # le suivi GitHub ne doit jamais s'arrêter sur un incident d'écriture
                        print("Échec non transmis :", erreur, flush=True)
                        transmis = False
                    if not transmis:                 # relecture Codex : garder le run « non terminé » pour réessayer
                        nouveau = precedent
            _vus[run["databaseId"]] = nouveau
            sortie.append(ligne)
        release = _etat["release"]
        if avec_release:
            try:
                release = lire_release()
            except (RuntimeError, ValueError, subprocess.TimeoutExpired):
                pass
        with _verrou:
            _etat.update(runs=sortie, alertes=alertes, release=release, erreur=None,
                         maj=datetime.now().strftime("%H:%M:%S"))
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as erreur:
        with _verrou:
            _etat.update(erreur=f"GitHub injoignable : {str(erreur)[:200]}", maj=datetime.now().strftime("%H:%M:%S"))


def etat():
    with _verrou:
        return json.loads(json.dumps(_etat))
