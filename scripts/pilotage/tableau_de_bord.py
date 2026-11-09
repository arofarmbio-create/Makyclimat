"""Tableau de bord LOCAL de la thèse et de MakyClimat — aucun modèle, aucun token.

Lit : pilotage/objectifs.yml (objectifs, tâches, blocages, téléchargements), pilotage/etat/agents.jsonl (écrit par
les hooks de Claude Code), validation/journal_recherche.md (verdicts des hypothèses), git et GitHub (gh).
Écrit : pilotage/tableau_de_bord.html (rafraîchissement automatique toutes les 30 s).
Usage : python scripts/pilotage/tableau_de_bord.py            (une fois)
        python scripts/pilotage/tableau_de_bord.py --boucle   (régénère toutes les 30 s ; Ctrl+C pour arrêter)
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PIL = ROOT / "pilotage"
OUT = PIL / "tableau_de_bord.html"
PERIODE_S, GH_PERIODE_S, ARRET_MIN = 30, 300, 15
_gh_cache: dict = {"t": 0.0, "runs": []}

VERDICT = re.compile(r"\*\*(H-[A-Za-z0-9-]+)[^*]*?(non soutenue|soutenue|robuste|non confirmée|non vérifiée)")
SECTION = re.compile(r"^###\s+(.*)")


def run(cmd: list[str], timeout: int = 20) -> str:
    try:
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=timeout).stdout
    except Exception:
        return ""


def lire_objectifs() -> dict:
    try:
        return yaml.safe_load((PIL / "objectifs.yml").read_text(encoding="utf-8")) or {}
    except Exception as e:
        return {"erreur": f"objectifs.yml illisible : {e}"}


def agents() -> tuple[list[dict], list[dict]]:
    """Agents en cours (SubagentStart sans SubagentStop) et derniers lancements (PreToolUse sur Agent)."""
    p = PIL / "etat" / "agents.jsonl"
    rows = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    started, stopped = {}, set()
    for r in rows:
        if r.get("evenement") == "SubagentStart" and r.get("agent_id"):
            started[r["agent_id"]] = r
        elif r.get("evenement") == "SubagentStop" and r.get("agent_id"):
            stopped.add(r["agent_id"])
    en_cours = [r for a, r in started.items() if a not in stopped]
    lancements = [r for r in rows if r.get("evenement") == "PreToolUse"][-8:][::-1]
    fins = {r["agent_id"]: r for r in rows if r.get("evenement") == "SubagentStop" and r.get("agent_id")}
    return en_cours, lancements, list(fins.values())[-5:][::-1]


def hypotheses() -> list[tuple[str, str, str]]:
    """(section du journal, hypothèse, verdict), dans l'ordre du journal ; dernier verdict par hypothèse."""
    p = ROOT / "validation" / "journal_recherche.md"
    out, sec = {}, ""
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = SECTION.match(line)
            if m:
                sec = re.sub(r"\s*\(`.*?`\)", "", m.group(1)).strip()
            for h, v in VERDICT.findall(line):
                out[h] = (sec, h, v)
    return list(out.values())


def github() -> list[dict]:
    if time.time() - _gh_cache["t"] > GH_PERIODE_S:
        txt = run(["gh", "run", "list", "-L", "8", "--json", "displayTitle,workflowName,status,conclusion,createdAt"])
        try:
            _gh_cache["runs"] = json.loads(txt) if txt else []
        except Exception:
            _gh_cache["runs"] = []
        _gh_cache["t"] = time.time()
    return _gh_cache["runs"]


def telechargements(obj: dict) -> list[dict]:
    out = []
    for d in obj.get("telechargements") or []:
        p = ROOT / d.get("chemin", "")
        if p.is_dir():
            fs = [f for f in p.rglob("*") if f.is_file()]
            taille, mtime = sum(f.stat().st_size for f in fs), max((f.stat().st_mtime for f in fs), default=0)
        elif p.exists():
            taille, mtime = p.stat().st_size, p.stat().st_mtime
        else:
            taille, mtime = 0, 0
        att = d.get("taille_attendue")
        age = (time.time() - mtime) / 60 if mtime else None
        if att and taille >= att:
            etat = "fini"
        elif age is None:
            etat = "absent"
        elif age > ARRET_MIN:
            etat = "arrêté"
        else:
            etat = "en cours"
        out.append({"nom": d.get("nom", ""), "taille": taille, "attendue": att, "etat": etat,
                    "maj": dt.datetime.fromtimestamp(mtime).strftime("%d/%m %H:%M") if mtime else "-"})
    return out


def esc(x) -> str:
    return html.escape(str(x))


def mo(n) -> str:
    return f"{n / 1e6:,.0f} Mo".replace(",", " ")


CLASSE = {"fini": "ok", "en_cours": "run", "en cours": "run", "bloque": "ko", "arrêté": "ko", "a_faire": "todo",
          "absent": "todo", "soutenue": "ok", "robuste": "ok", "non soutenue": "ko", "non confirmée": "ko",
          "non vérifiée": "warn", "success": "ok", "failure": "ko", "in_progress": "run", "queued": "todo"}
LIB = {"fini": "fini", "en_cours": "en cours", "bloque": "bloqué", "a_faire": "à faire"}


def carte(titre: str, sous: str = "", etat: str = "") -> str:
    c = CLASSE.get(etat, "todo")
    badge = f'<span class="b {c}">{esc(LIB.get(etat, etat))}</span>' if etat else ""
    return f'<div class="card {c}"><div class="t">{esc(titre)} {badge}</div><div class="s">{esc(sous)}</div></div>'


def page(obj: dict) -> str:
    now = dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    th = obj.get("these") or {}
    taches = obj.get("taches") or []
    en_cours, lancements, fins = agents()
    col = {"toi": [], "claude": [], "agent": [], "github": []}
    for t in taches:
        if t.get("statut") != "fini":
            col.setdefault(t.get("qui", "claude"), []).append(carte(t.get("nom", ""), "", t.get("statut", "")))
    for o in obj.get("objectifs") or []:
        for e in o.get("etapes") or []:
            if e.get("statut") != "fini" and e.get("qui"):
                col.setdefault(e["qui"], []).append(carte(e.get("nom", ""), o.get("nom", ""), e.get("statut", "")))
    for r in en_cours:
        col["agent"].insert(0, carte(f"Agent actif ({r.get('type') or 'agent'})", f"depuis {r.get('quand', '')[11:16]}", "en_cours"))
    for r in lancements:
        col["agent"].append(carte(r.get("description") or "Agent", f"lancé le {r.get('quand', '')[8:10]}/{r.get('quand', '')[5:7]} "
                                  f"à {r.get('quand', '')[11:16]}" + (" (arrière-plan)" if r.get("arriere_plan") else ""), ""))
    for r in fins:
        col["agent"].append(carte(f"Agent terminé ({r.get('type') or 'agent'})", f"à {r.get('quand', '')[11:16]}", "fini"))
    for d in telechargements(obj):
        pct = f" — {100 * d['taille'] / d['attendue']:.0f} %" if d["attendue"] else ""
        col["agent"].append(carte(f"Téléchargement : {d['nom']}", f"{mo(d['taille'])}{pct} ; dernière écriture {d['maj']}", d["etat"]))
    for r in github():
        etat = r.get("conclusion") or r.get("status") or ""
        col["github"].append(carte(r.get("workflowName", ""), f"{r.get('displayTitle', '')[:70]} — {r.get('createdAt', '')[:16].replace('T', ' ')}", etat))
    attente = [l for l in run(["git", "log", "origin/main..HEAD", "--format=%s"]).splitlines() if l]
    if attente:
        col["github"].insert(0, carte(f"{len(attente)} commit(s) pas encore envoyés", attente[0][:80], "bloque"))
    colonnes = "".join(f'<section class="col"><h2>{t}</h2>{"".join(col.get(k, [])) or "<p class=vide>rien</p>"}</section>'
                       for k, t in (("toi", "Toi"), ("claude", "Claude"), ("agent", "Agents et téléchargements"), ("github", "GitHub")))

    objs = ""
    for o in obj.get("objectifs") or []:
        av = int(o.get("avancement", 0))
        et = "".join(f'<li class="{CLASSE.get(e.get("statut"), "todo")}">{esc(e.get("nom"))} '
                     f'<span class="b {CLASSE.get(e.get("statut"), "todo")}">{esc(LIB.get(e.get("statut"), e.get("statut")))}</span></li>'
                     for e in o.get("etapes") or [])
        objs += f'<div class="obj"><div class="t">{esc(o.get("nom"))} <b>{av} %</b></div><div class="bar"><i style="width:{av}%"></i></div><ul>{et}</ul></div>'

    hyp = "".join(f'<tr><td>{esc(s)}</td><td>{esc(h)}</td><td><span class="b {CLASSE.get(v, "todo")}">{esc(v)}</span></td></tr>'
                  for s, h, v in hypotheses()[::-1])
    bloc = "".join(f'<tr><td>{esc(b.get("quoi"))}</td><td>{esc(b.get("effet"))}</td><td>{esc(b.get("qui_peut_debloquer"))}</td></tr>'
                   for b in obj.get("blocages") or [])
    commits = "".join(f"<li>{esc(l)}</li>" for l in run(["git", "log", "-8", "--format=%ad · %s", "--date=format:%d/%m %H:%M"]).splitlines())
    err = f'<p class="ko">{esc(obj["erreur"])}</p>' if obj.get("erreur") else ""

    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="{PERIODE_S}">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Pilotage MakyClimat</title><style>
:root{{--bg:#f6f7f9;--fg:#1d2330;--mut:#667085;--card:#fff;--line:#e3e6eb;--ok:#1a7f4b;--ko:#c0362c;--run:#1f5fbf;--warn:#a96b00;--todo:#667085}}
@media (prefers-color-scheme:dark){{:root{{--bg:#12151b;--fg:#e6e9ef;--mut:#98a2b3;--card:#1b2029;--line:#2b3240;--ok:#4cc38a;--ko:#ff6b5e;--run:#6ea8ff;--warn:#f0b54a;--todo:#98a2b3}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,Segoe UI,sans-serif}}
h1{{font-size:20px;margin:0}} h2{{font-size:15px;margin:0 0 8px}} .mut{{color:var(--mut)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:14px 0}}
.col{{background:transparent}} .card{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--todo);border-radius:8px;padding:8px 10px;margin-bottom:8px}}
.card.ok{{border-left-color:var(--ok)}} .card.ko{{border-left-color:var(--ko)}} .card.run{{border-left-color:var(--run)}} .card.warn{{border-left-color:var(--warn)}}
.t{{font-weight:600}} .s{{color:var(--mut);font-size:12px}} .vide{{color:var(--mut)}}
.b{{font-size:11px;padding:1px 6px;border-radius:9px;border:1px solid currentColor;font-weight:500;white-space:nowrap}}
.b.ok,li.ok{{color:var(--ok)}} .b.ko{{color:var(--ko)}} .b.run{{color:var(--run)}} .b.warn{{color:var(--warn)}} .b.todo{{color:var(--todo)}}
.box{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin-bottom:12px}}
.obj{{margin-bottom:12px}} .bar{{height:8px;background:var(--line);border-radius:4px;overflow:hidden;margin:4px 0}} .bar i{{display:block;height:100%;background:var(--run)}}
ul{{margin:4px 0 0 18px;padding:0}} li{{color:var(--fg)}} table{{width:100%;border-collapse:collapse}} td{{padding:4px 6px;border-top:1px solid var(--line);vertical-align:top}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}} .ko{{color:var(--ko)}}
</style></head><body>
<h1>Pilotage — thèse et MakyClimat</h1>
<div class="mut">{esc(th.get("titre", ""))}</div>
<div><b>Question en cours :</b> {esc(th.get("question_en_cours", ""))}</div>
<div class="mut">Mis à jour le {now} · se rafraîchit toutes les {PERIODE_S} s · aucun token consommé</div>{err}
<div class="grid">{colonnes}</div>
<div class="two"><div class="box"><h2>Objectifs et avancement</h2>{objs}</div>
<div class="box"><h2>Blocages</h2><table>{bloc}</table></div></div>
<div class="two"><div class="box"><h2>Hypothèses (journal de recherche, plus récentes en haut)</h2><table>{hyp}</table></div>
<div class="box"><h2>Dernières actions (git)</h2><ul>{commits}</ul></div></div>
</body></html>"""


def generer() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(page(lire_objectifs()), encoding="utf-8")
    tmp.replace(OUT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boucle", action="store_true")
    a = ap.parse_args()
    generer()
    while a.boucle:
        time.sleep(PERIODE_S)
        try:
            generer()
        except Exception as e:
            print("erreur :", e)


if __name__ == "__main__":
    main()
