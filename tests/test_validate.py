"""Âge des données de pluie dans le contrôle qualité (scripts/validate.py)."""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate as V  # noqa: E402

D = dt.date


def test_repli_debut_de_saison_pas_ancien():
    # 2 novembre : saison précédente jusqu'au 30 avril (repli), âge compté depuis le 1er novembre
    assert V.rain_age_days(D(2026, 4, 30), D(2026, 11, 2), 11) == 1


def test_repli_trop_long_detecte():
    # toujours aucune donnée de la nouvelle saison mi-janvier : 75 jours dépassés
    assert V.rain_age_days(D(2026, 4, 30), D(2027, 1, 20), 11) == 80


def test_age_normal_en_saison():
    assert V.rain_age_days(D(2027, 1, 10), D(2027, 2, 1), 11) == 22
