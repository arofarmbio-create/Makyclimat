"""Tests de la mécanique du score de potentiel pour point d'eau (pas une validation de sa justesse :
voir validation/groundwater_limites.md pour ce que cet indice NE peut PAS prouver — aucune donnée réelle
de forage n'existe pour le calibrer)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_groundwater import compute, pct_rank


def test_pct_rank_basic():
    s = pd.Series([10, 20, 30, 40])
    r = pct_rank(s)
    assert r.iloc[0] < r.iloc[-1]          # monotone croissant
    assert abs(r.iloc[-1] - 1.0) < 1e-9    # le plus grand -> rang 1.0


def test_pct_rank_keeps_nan():
    s = pd.Series([10.0, None, 30.0])
    r = pct_rank(s)
    assert r.isna().iloc[1]


def test_compute_scores_0_100_and_ranks_correctly():
    leaves = pd.DataFrame({"pcode": ["A", "B", "C"]})
    # hydro : A a la pente la plus faible (meilleur), B la plus forte (pire)
    hydro = pd.DataFrame({
        "pcode": ["A", "A", "B", "B", "C", "C"],
        "indicateur": ["hand_lt15_pct", "slope_mean_pct"] * 3,
        "valeur": [80, 5, 20, 40, 50, 20],
    })
    soilwater = pd.DataFrame({
        "pcode": ["A", "A", "B", "B", "C", "C"],
        "indicateur": ["recharge12_z", "whc_mm"] * 3,
        "valeur": [2.0, 150, -1.0, 50, 0.0, 100],
    })
    out = compute(hydro, soilwater, leaves)
    assert set(out.pcode) == {"A", "B", "C"}
    assert (out.valeur >= 0).all() and (out.valeur <= 100).all()
    # A a la meilleure recharge, le HAND le plus favorable et la pente la plus faible -> meilleur score
    a = out.set_index("pcode").loc["A", "valeur"]
    b = out.set_index("pcode").loc["B", "valeur"]
    assert a > b


def test_compute_drops_fokontany_with_too_few_criteria():
    leaves = pd.DataFrame({"pcode": ["A"]})
    hydro = pd.DataFrame({"pcode": [], "indicateur": [], "valeur": []})
    soilwater = pd.DataFrame({"pcode": [], "indicateur": [], "valeur": []})
    out = compute(hydro, soilwater, leaves)
    assert len(out) == 0   # aucun critère disponible -> rien publié plutôt qu'une valeur inventée


def test_compute_uses_geology_and_watertable_when_present():
    leaves = pd.DataFrame({"pcode": ["A", "B"]})
    hydro = pd.DataFrame({"pcode": ["A", "A", "B", "B"], "indicateur": ["hand_lt15_pct", "slope_mean_pct"] * 2, "valeur": [50, 20, 50, 20]})
    soilwater = pd.DataFrame({"pcode": ["A", "A", "B", "B"], "indicateur": ["recharge12_z", "whc_mm"] * 2, "valeur": [0.0, 100, 0.0, 100]})
    # A : aquifère très productif, nappe peu profonde (favorable) ; B : l'inverse. Mêmes autres critères -> A doit gagner.
    geology = pd.DataFrame({"pcode": ["A", "B"], "indicateur": "aquifer_productivity_pct", "valeur": [95, 10]})
    watertable = pd.DataFrame({"pcode": ["A", "B"], "indicateur": "water_table_depth_m", "valeur": [3.0, 60.0]})
    out = compute(hydro, soilwater, leaves, geology, watertable)
    a = out.set_index("pcode").loc["A", "valeur"]
    b = out.set_index("pcode").loc["B", "valeur"]
    assert a > b


if __name__ == "__main__":
    test_pct_rank_basic()
    test_pct_rank_keeps_nan()
    test_compute_scores_0_100_and_ranks_correctly()
    test_compute_drops_fokontany_with_too_few_criteria()
    test_compute_uses_geology_and_watertable_when_present()
    print("OK : tests build_groundwater")
