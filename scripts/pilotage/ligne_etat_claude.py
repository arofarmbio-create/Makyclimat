"""Ligne d'état de Claude Code : affiche contexte et limites d'usage, et les enregistre pour le poste de pilotage.

Claude Code envoie à chaque rafraîchissement un JSON sur l'entrée standard. Champs lus (tolérant aux absences) :
- context_window.context_window_size (fenêtre réelle du modèle) et context_window.used_percentage ;
- rate_limits.five_hour et rate_limits.seven_day : used_percentage, resets_at (secondes Unix ou date ISO).
Écrit pilotage/etat/limites_claude.json (local, ignoré par Git) et, pour contrôle des champs,
pilotage/etat/ligne_etat_brute.json (dernier JSON reçu). Sans modèle, sans réseau, sans dépendance externe.
Branché par « statusLine » dans .claude/settings.local.json (11/11/2026).
"""
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ETAT = ROOT / "pilotage" / "etat"
SORTIE = ETAT / "limites_claude.json"
BRUT = ETAT / "ligne_etat_brute.json"


def nombre(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def date_iso(x) -> str:
    """resets_at en heure locale ISO ; accepte secondes ou millisecondes Unix, ou une chaîne ISO."""
    if isinstance(x, str) and x:
        try:
            return dt.datetime.fromisoformat(x.replace("Z", "+00:00")).astimezone().isoformat(timespec="minutes")
        except ValueError:
            return ""
    v = nombre(x)
    if v is None or v <= 0:
        return ""
    if v > 1e11:                                   # millisecondes
        v /= 1000
    try:
        return dt.datetime.fromtimestamp(v).astimezone().isoformat(timespec="minutes")
    except (OSError, OverflowError, ValueError):
        return ""


def limite(bloc) -> dict:
    bloc = bloc if isinstance(bloc, dict) else {}
    p = nombre(bloc.get("used_percentage"))
    if p is None:
        p = nombre(bloc.get("utilization"))
    return {"pourcent": round(p, 1) if p is not None else None, "remise": date_iso(bloc.get("resets_at"))}


def extraire(ev: dict) -> dict:
    cw = ev.get("context_window") if isinstance(ev.get("context_window"), dict) else {}
    rl = ev.get("rate_limits") if isinstance(ev.get("rate_limits"), dict) else {}
    taille = nombre(cw.get("context_window_size")) or nombre(ev.get("context_window_size"))
    return {"session_id": ev.get("session_id") or "",
            "modele": (ev.get("model") or {}).get("display_name", "") if isinstance(ev.get("model"), dict) else "",
            "fenetre": int(taille) if taille else None,
            "contexte_pourcent": nombre(cw.get("used_percentage")),
            "cinq_heures": limite(rl.get("five_hour")),
            "semaine": limite(rl.get("seven_day")),
            "maj": dt.datetime.now().isoformat(timespec="seconds")}


def ecrire(chemin: Path, d: dict) -> None:
    ETAT.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ETAT, delete=False) as f:
        tmp = Path(f.name)
        json.dump(d, f, ensure_ascii=False)
    try:
        tmp.replace(chemin)
    finally:
        tmp.unlink(missing_ok=True)


def ligne(d: dict) -> str:
    morceaux = []
    if d["modele"]:
        morceaux.append(d["modele"])
    if d["contexte_pourcent"] is not None:
        f = f" / {d['fenetre'] // 1000} k" if d["fenetre"] else ""
        morceaux.append(f"contexte {round(d['contexte_pourcent'])} %{f}")
    for nom, cle in (("5 h", "cinq_heures"), ("semaine", "semaine")):
        b = d[cle]
        if b["pourcent"] is not None:
            r = f" (→ {b['remise'][11:16]})" if cle == "cinq_heures" and b["remise"] else ""
            morceaux.append(f"{nom} {round(b['pourcent'])} %{r}")
    return " · ".join(morceaux) or "MakyClimat"


def main() -> None:
    try:
        ev = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except ValueError:
        ev = {}
    if not isinstance(ev, dict):
        ev = {}
    d = extraire(ev)
    try:
        ecrire(BRUT, ev)
        ecrire(SORTIE, d)
    except OSError:
        pass                                       # la ligne d'état ne doit jamais échouer
    sys.stdout.buffer.write(ligne(d).encode("utf-8"))


if __name__ == "__main__":
    main()
