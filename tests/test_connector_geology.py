"""Tests du connecteur géologie/aquifère (mock complet : aucun appel réseau)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from connector_geology import PRODUCTIVITY, compute, productivity_code


def test_productivity_code_parses_hgcomb():
    assert productivity_code("B-L") == "L"
    assert productivity_code("CSF-VH") == "VH"
    assert productivity_code("") is None
    assert productivity_code(None) is None
    assert productivity_code("B-ZZ") is None   # code inconnu -> ignoré, pas de valeur inventée


def test_all_productivity_classes_have_rank_and_yield():
    for code, (pct, yld) in PRODUCTIVITY.items():
        assert 0 <= pct <= 100
        assert yld >= 0


def test_compute_samples_points_in_polygons():
    import geopandas as gpd
    from shapely.geometry import box

    # deux polygones : un socle peu productif à l'ouest, un sédimentaire très productif à l'est
    g = gpd.GeoDataFrame({"HGComb": ["B-L", "U-VH"]}, geometry=[box(40, -20, 45, -15), box(45, -20, 50, -15)], crs=4326)
    leaves = pd.DataFrame({"pcode": ["A", "B", "C"], "lon": [42.0, 47.0, 70.0], "lat": [-17.0, -17.0, -17.0]})
    out = compute(g, leaves)
    piv = out.pivot_table(index="pcode", columns="indicateur", values="valeur")
    assert piv.loc["A", "aquifer_productivity_pct"] < piv.loc["B", "aquifer_productivity_pct"]
    assert "C" not in piv.index   # hors des deux polygones -> pas de valeur inventée


if __name__ == "__main__":
    test_productivity_code_parses_hgcomb()
    test_all_productivity_classes_have_rank_and_yield()
    test_compute_samples_points_in_polygons()
    print("OK : tests connector_geology")
