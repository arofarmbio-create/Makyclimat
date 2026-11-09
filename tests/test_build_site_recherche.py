"""Données des pages Nappes et Preuves (scripts/build_site_recherche.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_site_recherche as B  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    FAILS += 0 if cond else 1


check("statut réussi", B.classe_statut("✅ H1") == "ok")
check("statut échec ou fermé", B.classe_statut("❌ non démontré") == "ko" and B.classe_statut("⬛ fermé") == "ko")
check("statut partiel", B.classe_statut("⚠️ dépend du dépôt") == "partiel" and B.classe_statut("🟡 piste") == "partiel")
check("statut en attente", B.classe_statut("⏳") == "attente")
reg = B.registre()
check("registre lu (au moins 40 méthodes)", len(reg) >= 40, str(len(reg)))
check("colonne Statut repérée par l'en-tête (R-01)", "✅" in reg.get("R-01", ("", "", ""))[1], reg.get("R-01", ("", "?"))[1][:40])
check("modules du site rattachés à des méthodes existantes", all(i in reg for _, _, ids, _ in B.MODULES for i in ids))
print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
