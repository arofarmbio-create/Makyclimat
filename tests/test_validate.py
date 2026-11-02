"""Âge des données de pluie dans le contrôle qualité (scripts/validate.py)."""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate as V  # noqa: E402

FAILS = 0
D = dt.date


def check(name, cond, extra=""):
    global FAILS
    print(("OK    " if cond else "ÉCHEC ") + name + (" — " + extra if extra else ""))
    if not cond:
        FAILS += 1


check("2 novembre, repli sur la saison précédente (30 avril) : âge compté depuis le 1er novembre",
      V.rain_age_days(D(2026, 4, 30), D(2026, 11, 2), 11) == 1)
check("toujours rien de la nouvelle saison mi-janvier : 80 jours, au-delà du seuil de 75",
      V.rain_age_days(D(2026, 4, 30), D(2027, 1, 20), 11) == 80)
check("en pleine saison : âge ordinaire", V.rain_age_days(D(2027, 1, 10), D(2027, 2, 1), 11) == 22)

print(f"\n{FAILS} échec(s)")
sys.exit(1 if FAILS else 0)
