"""Installe (ou retire avec --retirer) le lancement de pilotage_permanent.cmd à l'ouverture de la session Windows.

À lancer par le porteur lui-même : dépose un petit fichier dans son dossier Démarrage (aucun droit administrateur).
Le BIOS (« redémarrage au retour du courant ») et l'ouverture de session automatique restent à régler à la main.
"""
import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEMARRAGE = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
LANCEUR = DEMARRAGE / "MakyClimat_pilotage.cmd"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--retirer", action="store_true")
    a = ap.parse_args()
    if a.retirer:
        LANCEUR.unlink(missing_ok=True)
        return print("Lancement au démarrage retiré.")
    LANCEUR.write_text(f'@echo off\r\nstart "MakyClimat pilotage" /min cmd /c "{ROOT / "pilotage_permanent.cmd"}"\r\n',
                       encoding="utf-8")
    print(f"Installé : {LANCEUR}")


if __name__ == "__main__":
    main()
