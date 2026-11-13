"""Accueil du tableau de bord (porteur, 13/11/2026) : quatre questions, pour quelqu'un qui ne connaît pas le projet.

1. Est-ce que ça tourne ? (voyant)  2. Qu'est-ce qu'on attend de moi ?  3. Où en est la thèse ? (par grand thème)
4. Qu'est-ce qui a changé depuis ma dernière visite ?
Tout vient des sources existantes (pilotage/fil.yml, COORDINATION.md, surveillant, evenements.jsonl) : aucune donnée en
plus à tenir. Pas de code d'étape à l'écran : des titres en clair.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import yaml

import fil

SITUATION = fil.ROOT / "pilotage" / "situation.yml"
DEPOT = "https://github.com/arofarmbio-create/Makyclimat/blob/main/"
FICHIER = re.compile(r"(?:validation|scripts|docs|coordination|tests|data)/[\w./-]+\.(?:md|py|csv|yml|yaml|json|txt)")

ECHELLE = ["aucune", "provisoire", "exploratoire", "soutenue", "confirmee"]
LIBELLE_FIAB = {"aucune": "aucune", "provisoire": "provisoire", "exploratoire": "exploratoire", "soutenue": "soutenue",
                "confirmee": "confirmée"}
VERBES = {"fait": "Terminé", "en_cours": "Commencé", "a_relire": "En relecture", "decision": "À trancher",
          "valide": "Validé par vous", "clos": "Fermé", "pret": "Prêt", "en_attente": "En attente"}


def _rang(f: str | None) -> int:
    return ECHELLE.index(f) if f in ECHELLE else 0


def voyant(stop: bool, instance: dict | None, en_cours: dict, fil_: dict, aujourd_hui: date | None = None) -> dict:
    jour = aujourd_hui or date.today()
    actives = [e for e in fil.etapes(fil_) if e.get("etat") == "en_cours"]
    notes = [] if fil.disponible("codex") else ["Codex mis de côté (limite d'usage) : Claude travaille seul."]
    if stop:
        return {"couleur": "rouge", "phrase": "Arrêté par vous (STOP)", "detail": "Plus rien ne part tant que vous "
                "n'avez pas touché « Reprise ».", "stop": True, "notes": notes}
    if not instance:
        return {"couleur": "orange", "phrase": "Le moteur est à l'arrêt", "detail": "La boucle le relance d'elle-même "
                "dans les 10 minutes.", "stop": False, "notes": notes}
    if en_cours:
        detail = actives[0].get("quoi") if actives else (en_cours.get("sujet") or "une tâche")
        return {"couleur": "vert", "phrase": "Le système travaille", "detail": f"En ce moment : {detail}",
                "stop": False, "notes": notes}
    prochaine = fil.prochaine(fil_, jour)
    if jour < fil.FIN_PAUSE:
        detail = f"Pause des calculs de recherche jusqu'au lundi {fil.FIN_PAUSE:%d/%m} (votre décision)."
    elif prochaine:
        detail = f"Prochaine étape : {prochaine.get('quoi')}"
    else:
        detail = "Rien de prêt : les étapes attendent des données ou vos décisions."
    return {"couleur": "vert", "phrase": "Le système est en veille", "detail": detail, "stop": False, "notes": notes}


def contributions(fil_: dict, refs: set[str]) -> dict:
    """Ce qu'une action débloque : les étapes non finies qui dépendent de `refs` (données ou étapes), regroupées par
    grand thème avec le titre de leurs objectifs (porteur, 13/11 : dire à quoi sert chaque action)."""
    themes_noms = {t["id"]: t["nom"] for t in fil_.get("themes", [])}
    objectifs = {o["id"]: o for o in fil_.get("objectifs", [])}
    par_theme: dict[str, list[str]] = {}
    debloquees = []
    for e in fil.etapes(fil_):
        if e.get("etat") in fil.FINIS or not refs & set(e.get("depend_de", []) + e.get("donnees", [])):
            continue
        o = objectifs.get(e["_groupe"])
        if not o:
            continue
        debloquees.append(e.get("quoi", ""))
        titres = par_theme.setdefault(themes_noms.get(o.get("theme"), "Autre"), [])
        titre = o.get("titre") or o.get("nom", "")
        if titre not in titres:
            titres.append(titre)
    return {"themes": [{"theme": t, "objectifs": v} for t, v in par_theme.items()], "etapes": debloquees}


def vous_attend(fil_: dict, decisions: list[dict]) -> list[dict]:
    titres = {o["id"]: o.get("titre") or o.get("nom", "") for o in fil_.get("objectifs", [])}
    titres.update({d["id"]: d.get("objet", "") for d in fil_.get("demarches", [])})
    p = fil.pour_porteur(fil_)
    apporte = {g["id"]: g.get("apporte", "") for g in fil_.get("demarches", []) + fil_.get("objectifs", [])}
    donnees_de = {}
    for d in fil_.get("donnees", []):
        if d.get("demarche"):
            donnees_de.setdefault(d["demarche"], set()).add(d["id"])
    sortie = [{"type": "valider", "id": e["id"], "titre": f"Valider : {e.get('quoi', '')}",
               "detail": titres.get(e["_groupe"], "") + (f" — livrable : {e['preuve']}" if e.get("preuve") else ""),
               "apporte": "Votre accord autorise le calcul que ce protocole fixe.",
               "contribue": contributions(fil_, {e["id"]})}
              for e in p["valider"]]
    sortie += [{"type": "decision", "cle": d["cle"], "titre": d["objet"], "detail": d.get("detail", "")[:400]}
               for d in decisions]
    sortie += [{"type": "faire", "id": e["id"], "titre": titres.get(e["_groupe"]) or e.get("quoi", ""),
                "detail": e.get("quoi", "") + (f" — {e['prochaine_action']}" if e.get("prochaine_action") else ""),
                "apporte": e.get("apporte") or apporte.get(e["_groupe"], ""),
                "contribue": contributions(fil_, donnees_de.get(e["_groupe"], set()) | {e["id"]})}
               for e in p["faire"]]
    return sortie


def _cle(texte: str) -> str:
    return re.sub(r"[^0-9a-z]", "", str(texte).split(" — ")[0].lower())


def situation_par_ref(chemin: Path | None = None) -> dict:
    """Entrées de pilotage/situation.yml indexées par leur référence (« R-47 », « E1 — Relief »…), pour relier chaque
    résultat d'un thème à sa preuve et à ce qui reste (porteur, 13/11 : une seule page par thème)."""
    try:
        d = yaml.safe_load((chemin or SITUATION).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return {_cle(e.get("nom", "")): e for sec in ("these", "makyclimat") for e in d.get(sec) or [] if isinstance(e, dict)}


def preuves(texte: str) -> list[dict]:
    """Fichiers du dépôt cités dans une preuve, avec leur lien GitHub (dépôt public)."""
    return [{"chemin": c, "lien": DEPOT + c} for c in dict.fromkeys(FICHIER.findall(str(texte or "")))]


def page_theme(fil_: dict, theme_id: str, objs: list[dict], etapes: list[dict], situation: dict,
               actions: list[dict], nom_theme: str) -> dict:
    donnees = {d["id"]: d for d in fil_.get("donnees", [])}
    demarches = {d["id"]: d.get("objet", "") for d in fil_.get("demarches", [])}
    resultats, vus = [], set()
    for o in objs:
        for r in o.get("resultats", []):
            if r.get("ref") in vus:
                continue
            vus.add(r.get("ref"))
            sit = situation.get(_cle(r.get("ref", ""))) or {}
            resultats.append({"ref": r.get("ref", ""), "verdict": r.get("verdict", ""),
                              "fiabilite": LIBELLE_FIAB.get(r.get("fiabilite"), "aucune"),
                              "rang": _rang(r.get("fiabilite")), "objectif": o.get("titre") or o.get("nom", ""),
                              "titre": sit.get("nom", ""), "reste": sit.get("reste", ""),
                              "preuves": preuves(sit.get("preuve", ""))})
    resultats.sort(key=lambda r: -r["rang"])
    refs = []
    for e in etapes:
        for r in e.get("depend_de", []) + e.get("donnees", []):
            if r in donnees and r not in refs:
                refs.append(r)
    liste_donnees = [{"nom": donnees[r].get("nom", r), "etat": donnees[r].get("etat", ""),
                      "couverture": donnees[r].get("couverture") or donnees[r].get("couverture_visee", ""),
                      "manque": donnees[r].get("manque", ""),
                      "obtenue_par": demarches.get(donnees[r].get("demarche"), "") or donnees[r].get("qui", "")}
                     for r in refs]
    liste_donnees.sort(key=lambda d: d["etat"] == "disponible")
    chemins = []
    for o in objs:
        ids = {e["id"] for e in etapes if e["_groupe"] == o["id"]}
        chemins.append({"titre": o.get("titre") or o.get("nom", ""), "visee": LIBELLE_FIAB.get(o.get("fiabilite_visee"), ""),
                        "etapes": [{"id": e["id"], "quoi": e.get("quoi", ""), "qui": e.get("qui", ""),
                                    "etat": e.get("etat", ""), "libelle": VERBES.get(e.get("etat"), e.get("etat", "")),
                                    "depend_de": [x for x in e.get("depend_de", []) if x in ids],
                                    "bloquant": " ; ".join(f"{donnees[x].get('nom', x)} ({donnees[x].get('etat')})"
                                                           for x in e.get("depend_de", [])
                                                           if x in donnees and donnees[x].get("etat") != "disponible"),
                                    "autorisation": e.get("autorisation") == "porteur"}
                                   for e in etapes if e["_groupe"] == o["id"]]})
    return {"resultats": resultats, "donnees": liste_donnees, "chemins": chemins,
            "actions": [a for a in actions if any(c["theme"] == nom_theme for c in a.get("contribue", {}).get("themes", []))]}


def themes(fil_: dict, actions: list[dict] | None = None) -> list[dict]:
    situation = situation_par_ref()
    donnees = {d["id"]: d for d in fil_.get("donnees", [])}
    pretes = {e["id"] for e in fil.pretes(fil_)}
    sortie = []
    for t in fil_.get("themes", []):
        if t.get("coulisses"):
            continue
        objs = [o for o in fil_.get("objectifs", []) if o.get("theme") == t["id"]]
        if not objs:
            continue
        etapes = [e for e in fil.etapes(fil_) if e["_groupe"] in {o["id"] for o in objs}]
        resultats = [r for o in objs for r in o.get("resultats", [])]
        manque, vus = [], set()
        for e in etapes:
            if e.get("etat") in fil.FINIS:
                continue
            for r in e.get("depend_de", []) + e.get("donnees", []):
                d = donnees.get(r)
                if d and d.get("etat") in ("manquante", "licence") and r not in vus:
                    vus.add(r)
                    manque.append(d.get("nom", r))
        suivante = next((e for e in sorted(etapes, key=lambda e: e["_priorite"])
                         if e["id"] in pretes and e.get("qui") in fil.AUTONOMES), None)
        compte = {}
        for r in resultats:
            compte[r.get("fiabilite", "aucune")] = compte.get(r.get("fiabilite", "aucune"), 0) + 1
        sortie.append({
            "page": page_theme(fil_, t["id"], objs, etapes, situation, actions or [], t["nom"]),
            "id": t["id"], "nom": t["nom"], "dit": t.get("dit", ""),
            "faites": sum(e.get("etat") in fil.FINIS for e in etapes), "total": len(etapes),
            "meilleure": LIBELLE_FIAB[max((r.get("fiabilite", "aucune") for r in resultats), key=_rang, default="aucune")],
            "rang": max((_rang(r.get("fiabilite")) for r in resultats), default=0),
            "resultats_par_fiabilite": {LIBELLE_FIAB[k]: v for k, v in sorted(compte.items(), key=lambda kv: -_rang(kv[0]))},
            "manque": manque[:4], "prochaine": suivante.get("quoi") if suivante else "",
            "en_cours": [e.get("quoi", "") for e in etapes if e.get("etat") in fil.ACTIFS],
            "objectifs": [{"titre": o.get("titre") or o.get("nom", ""), "visee": LIBELLE_FIAB.get(o.get("fiabilite_visee"), ""),
                           "resultats": [{"ref": r.get("ref", ""), "verdict": r.get("verdict", ""),
                                          "fiabilite": LIBELLE_FIAB.get(r.get("fiabilite"), "aucune")}
                                         for r in o.get("resultats", [])],
                           "etapes": [{"quoi": e.get("quoi", ""), "etat": VERBES.get(e.get("etat"), e.get("etat", "")),
                                       "qui": e.get("qui", ""), "brut": e.get("etat", "")}
                                      for e in etapes if e["_groupe"] == o["id"]]}
                          for o in objs]})
    return sortie


def evenements(fil_: dict, n: int = 40) -> list[dict]:
    theme_de = {o["id"]: o.get("theme") for o in fil_.get("objectifs", [])}
    noms = {t["id"]: t["nom"] for t in fil_.get("themes", [])}
    try:
        lignes = fil.EVENEMENTS.read_text(encoding="utf-8").splitlines()[-400:]
    except OSError:
        return []
    sortie = []
    for ligne in reversed(lignes):
        try:
            ev = json.loads(ligne)
        except ValueError:
            continue
        theme = theme_de.get(ev.get("groupe"))
        if theme == "systeme":
            continue
        sortie.append({"quand": ev.get("quand", ""), "texte": f"{VERBES.get(ev.get('etat'), ev.get('etat'))} : {ev.get('quoi', '')}",
                       "theme": noms.get(theme, "Démarches" if str(ev.get("groupe", "")).startswith("X-") else "")})
        if len(sortie) >= n:
            break
    return sortie


def construire(stop: bool, instance: dict | None, en_cours: dict, decisions: list[dict]) -> dict:
    f = fil.charger()
    attend = vous_attend(f, decisions)
    return {"voyant": voyant(stop, instance, en_cours, f), "attend": attend,
            "themes": themes(f, attend), "evenements": evenements(f)}
