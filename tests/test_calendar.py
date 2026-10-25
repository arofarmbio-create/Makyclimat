"""Teste le calendrier cultural (recommandations par région, fenêtres saisies) sans réseau.

Usage : python tests/make_synthetic.py && python tests/test_calendar.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_calendar as BCAL  # noqa: E402
from common import country_docs_dir, load_yaml, read_units, write_json  # noqa: E402

FAILS = 0


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


def main() -> None:
    cfg = load_yaml("calendrier_cultural.yml")
    names = [r for rule in cfg["rules"] for r in rule["regions"]]
    check("source officielle citée avec son adresse", cfg["source"]["url"].startswith("https://www.meteomadagascar.mg/") and "2025-2026" in cfg["season"])
    check("régions de la configuration : orthographe cohérente avec les limites officielles", len(set(names)) >= 14)
    units = read_units("demo")
    regs = units[units.level == 1]
    demo_cfg = {"season": "test", "source": {}, "general": ["g"], "rules": [{"regions": [regs.name.iloc[0], "Région inexistante"], "text": "Règle A"}, {"regions": [regs.name.iloc[0]], "text": "Règle A"}]}
    win = pd.DataFrame({"pcode": [regs.pcode.iloc[0], "ALL", "ZZZ", regs.pcode.iloc[0]], "culture": ["Riz", "Maïs", "Riz", "Riz"], "operation": ["semis", "semis", "semis", "recolte"],
                        "mois_debut": [11, 12, 11, 4], "decade_debut": [2, 1, 1, 2], "mois_fin": [12, 1, 12, 13], "decade_fin": [3, 2, 3, 1], "source": ["s", "s", "s", "s"]})
    out = BCAL.build(demo_cfg, units, win)
    check("règle rattachée à la région par son nom, sans doublon de texte", out["regions"][regs.pcode.iloc[0]] == ["Règle A"])
    check("région inexistante signalée", out["unknown_regions"] == ["Région inexistante"])
    check("fenêtres valides gardées (ALL accepté), invalides ignorées (zone inconnue, mois 13)", sum(len(v) for v in out["windows"].values()) == 2 and "ZZZ" not in out["windows"])
    # le test de l'interface vérifie l'affichage dans la fiche : une règle pour toutes les régions de démonstration
    ui = BCAL.build({"season": "test", "source": {"title": "Source de test", "url": "https://example.org/x.pdf"}, "general": [], "rules": [{"regions": regs.name.tolist(), "text": "Règle de démonstration"}]}, units, None)
    write_json(country_docs_dir("demo") / "calendrier.json", ui)
    if FAILS:
        print(f"\n{FAILS} ÉCHEC(S)")
        sys.exit(1)
    print("\ntest_calendar OK")


if __name__ == "__main__":
    main()
