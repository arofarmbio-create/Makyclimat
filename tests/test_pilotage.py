"""Pilotage local : décisions du porteur, exécutions autorisées, relectures croisées et lecture des tokens (sans réseau,
sans lancer Claude ni Codex). Travaille sur une copie de COORDINATION.md."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "scripts" / "pilotage"))
import serveur_pilotage as S  # noqa: E402
import surveiller_coordination as C  # noqa: E402

COPIE = """# Coordination

## Tâches

| Tâche | Responsable | État | Preuve ou périmètre | Prochaine action ou condition de fin | Début | Fin |
|---|---|---|---|---|---|---|
| Outil A | Claude | À relire | [Parcours](scripts/pilotage/parcours.py) | Vérifier le rendu. | — | — |
| Outil B | Codex | À relire | `COORDINATION.md` | Suivi seulement. | — | — |

## Messages et décisions en attente

- **10/11/2026 · Claude → porteur du projet · R-21, autoriser la collecte ?** Lots proposés : 2010 mois 2 et 3.
- **10/11/2026 · Codex → porteur du projet · Choisir un seuil.** Deux options.

Réserver cette section aux questions.

## Lancements ponctuels autorisés

- [x] `claude:ancien` Déjà fait.
"""


def _copie():
    dossier = Path(tempfile.mkdtemp())
    chemin = dossier / "COORDINATION.md"
    chemin.write_text(COPIE, encoding="utf-8")
    S.COORD = chemin
    S.tableau_de_bord.generer = lambda: None        # ne pas régénérer le vrai tableau pendant le test
    S.lire_instance = lambda dossier: None
    return chemin


def test_autoriser_cree_decision_et_execution():
    chemin = _copie()
    ligne = next(l for l in COPIE.splitlines() if "autoriser la collecte" in l)
    r = S.decision(C.cle_message(ligne), "autoriser", "D'abord 2010.")
    assert "erreur" not in r and r["surveillant_actif"] is False, r
    texte = chemin.read_text(encoding="utf-8")
    assert "autoriser la collecte ?** Lots" not in texte                     # message retiré
    assert "## Décisions du porteur du projet" in texte and "**Autorisé**" in texte and "D'abord 2010." in texte
    assert texte.index("## Exécutions autorisées") < texte.index("## Lancements ponctuels autorisés")
    demandes = list(C.demandes_claude(texte, False, ("claude", "codex")))
    assert len(demandes) == 1 and demandes[0][0] == "claude" and demandes[0][1].startswith("claude/exec-"), demandes
    assert "D'abord 2010." in demandes[0][2]
    # un second clic sur le même message ne fait rien
    assert "erreur" in S.decision(C.cle_message(ligne), "autoriser", "")


def test_refuser_et_repondre_n_executent_rien():
    chemin = _copie()
    ligne = next(l for l in COPIE.splitlines() if "Choisir un seuil" in l)
    assert "erreur" in S.decision(C.cle_message(ligne), "repondre", "  ")   # réponse vide refusée
    assert "erreur" not in S.decision(C.cle_message(ligne), "repondre", "Prendre l'option 2.")
    texte = chemin.read_text(encoding="utf-8")
    assert "Porteur du projet → Codex · **Réponse** · Choisir un seuil" in texte
    assert "## Exécutions autorisées" not in texte


def test_consigne_codex():
    chemin = _copie()
    assert "erreur" not in S.consigne("codex", "Relire le `workflow` 14\net répondre.")
    texte = chemin.read_text(encoding="utf-8")
    demandes = [d for d in C.demandes_claude(texte, False, ("codex",))]
    assert demandes and demandes[0][0] == "codex" and "`" not in demandes[0][2] and "\n" not in demandes[0][2]
    assert "erreur" in S.consigne("autre", "x")


def test_relecture_croisee_et_economie():
    lignes = COPIE.splitlines()
    a = next(l for l in lignes if l.startswith("| Outil A"))
    b = next(l for l in lignes if l.startswith("| Outil B"))
    assert list(C.relecture_auto(a, "claude")) == []          # Claude ne se relit pas
    (agent, ident, consigne), = C.relecture_auto(a, "codex")
    assert agent == "codex" and ident.startswith("codex/relecture-") and "```diff" in consigne
    assert list(C.relecture_auto(b, "claude")) == []          # suivi seul : pas de relecture
    reformulee = a.replace("Vérifier le rendu.", "Vérifier le rendu, autrement dit.")
    (_, ident2, _), = C.relecture_auto(reformulee, "codex")
    assert ident2 == ident                                     # reformuler la ligne ne relance pas la relecture


def test_lecture_des_tokens_et_fichiers():
    texte, conso = C.lire_sortie("claude", json.dumps({"result": "Verdict : sans blocage", "total_cost_usd": 0.1234,
        "usage": {"input_tokens": 10, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 20000, "output_tokens": 300}}),
        Path("absent"))
    assert texte == "Verdict : sans blocage" and conso == "entrée 21 010 (dont cache 20 000) · sortie 300 · 0.12 $", conso
    dossier = Path(tempfile.mkdtemp())
    (dossier / "r.md").write_text("Avis Codex", encoding="utf-8")
    flux = "\n".join([json.dumps({"type": "thread.started"}),
                      json.dumps({"type": "turn.completed", "usage": {"input_tokens": 5000, "cached_input_tokens": 4000, "output_tokens": 200}})])
    assert C.lire_sortie("codex", flux, dossier / "r.md") == ("Avis Codex", "entrée 5 000 (dont cache 4 000) · sortie 200")
    assert C.nom_fichier("r21-x") == "claude-r21-x.md" and C.nom_fichier("codex/relecture-a") == "codex-relecture-a.md"
    assert C.nom_fichier("claude/exec-1") == "claude-exec-1.md"
    shutil.rmtree(dossier, ignore_errors=True)


if __name__ == "__main__":
    for nom, fonction in list(globals().items()):
        if nom.startswith("test_"):
            fonction()
    print("OK : tests pilotage")
