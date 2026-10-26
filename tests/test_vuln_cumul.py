"""Tests de la mécanique de l'indice de vulnérabilité cumulative (pas une validation de sa justesse :
voir validation/vuln_cumul_limites.md pour ce que cet indice ne peut pas prouver)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_vuln_cumul import HALF_LIFE_DAYS, cumulative_score, recency_weight, spi_severity, wind_severity


def test_recency_weight():
    assert recency_weight(0) == 1.0
    assert abs(recency_weight(HALF_LIFE_DAYS) - 0.5) < 1e-9
    assert recency_weight(-1) == 0.0           # pas de choc "dans le futur"
    assert recency_weight(10**6) == 0.0        # trop ancien : hors fenêtre


def test_wind_severity_monotone():
    assert wind_severity(None) == 0.0
    assert wind_severity(30) == 0.0            # sous le seuil tempête tropicale
    assert wind_severity(34) == 20.0
    assert wind_severity(64) == 65.0
    assert wind_severity(200) == 100.0         # plafonné


def test_spi_severity_thresholds():
    assert spi_severity(0.0) == 0.0            # normal : aucune sévérité
    assert spi_severity(-0.5) == 0.0
    assert spi_severity(-1.0) == 25.0           # seuil OMM "modérément sec"
    assert spi_severity(-1.5) == 55.0           # seuil OMM "sévèrement sec"
    assert spi_severity(-2.0) == 85.0           # seuil OMM "extrêmement sec"
    assert spi_severity(-3.0) <= 100.0          # plafonné


def test_cumulative_score_saturates_not_linear():
    # Deux chocs modérés comptent moins que leur somme simple (épuisement progressif, jamais > 100).
    one = cumulative_score([50.0])
    two = cumulative_score([50.0, 50.0])
    assert one == 50.0
    assert two > one
    assert two < 100.0
    assert cumulative_score([100.0, 100.0, 100.0]) == 100.0
    assert cumulative_score([]) == 0.0


def test_cumulative_score_order_independent():
    a = cumulative_score([30.0, 70.0, 10.0])
    b = cumulative_score([70.0, 10.0, 30.0])
    assert a == b  # le tri interne par sévérité rend le résultat indépendant de l'ordre d'entrée


if __name__ == "__main__":
    import inspect
    mod = sys.modules[__name__]
    fails = 0
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith("test_"):
            try:
                fn()
                print(f"OK    {name}")
            except AssertionError as e:
                fails += 1
                print(f"ÉCHEC {name} : {e}")
    if fails:
        raise SystemExit(f"{fails} test(s) en échec")
    print("Tous les tests de l'indice de vulnérabilité cumulative passent.")
