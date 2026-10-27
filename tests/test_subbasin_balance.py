"""Tests de l'agrégation du bilan hydrique par sous-bassin versant (mécanique de pondération, pas de réseau)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_subbasin_balance import aggregate


def test_aggregate_area_weighted_mean():
    leaves = pd.DataFrame({"pcode": ["A", "B", "C"], "area_km2": [10.0, 90.0, 50.0]})
    lk = pd.DataFrame({"pcode": ["A", "B", "C"], "subbasin": [1, 1, 2]})
    long = pd.DataFrame({
        "pcode": ["A", "B", "C"],
        "indicateur": ["recharge12_mm", "recharge12_mm", "recharge12_mm"],
        "valeur": [0.0, 100.0, 50.0],
    })
    out = aggregate(long, lk, leaves)
    assert "1" in out and "2" in out
    # sous-bassin 1 : A (10 km², 0 mm) + B (90 km², 100 mm) -> moyenne pondérée proche de 90
    assert abs(out["1"]["recharge12_mm"] - 90.0) < 1e-6
    assert out["2"]["recharge12_mm"] == 50.0
    assert out["1"]["n_fokontany"] == 2


def test_aggregate_skips_fokontany_without_subbasin():
    leaves = pd.DataFrame({"pcode": ["A", "B"], "area_km2": [10.0, 10.0]})
    lk = pd.DataFrame({"pcode": ["A", "B"], "subbasin": [0, 1]})   # A : pas de sous-bassin (zone de mer/hors MNT)
    long = pd.DataFrame({"pcode": ["A", "B"], "indicateur": ["recharge12_mm"] * 2, "valeur": [10.0, 20.0]})
    out = aggregate(long, lk, leaves)
    assert "0" not in out
    assert out["1"]["recharge12_mm"] == 20.0


def test_aggregate_handles_missing_indicator_for_some_fokontany():
    leaves = pd.DataFrame({"pcode": ["A", "B"], "area_km2": [10.0, 10.0]})
    lk = pd.DataFrame({"pcode": ["A", "B"], "subbasin": [1, 1]})
    long = pd.DataFrame({"pcode": ["A"], "indicateur": ["water_table_depth_m"], "valeur": [12.0]})
    out = aggregate(long, lk, leaves)
    assert out["1"]["water_table_depth_m"] == 12.0   # moyenne sur le seul fokontany disponible, pas une valeur inventée pour B


if __name__ == "__main__":
    test_aggregate_area_weighted_mean()
    test_aggregate_skips_fokontany_without_subbasin()
    test_aggregate_handles_missing_indicator_for_some_fokontany()
    print("OK : tests build_subbasin_balance")
