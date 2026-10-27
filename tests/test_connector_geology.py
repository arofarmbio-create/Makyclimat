"""Tests du connecteur géologie/aquifère (mock complet : aucun appel réseau)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from connector_geology import PRODUCTIVITY, compute, productivity_value


def test_productivity_value_parses_single_code_hgcomb():
    assert productivity_value("B-L") == PRODUCTIVITY["L"]
    assert productivity_value("CSF-VH") == PRODUCTIVITY["VH"]
    assert productivity_value("") is None
    assert productivity_value(None) is None
    assert productivity_value("B-ZZ") is None   # code inconnu -> ignoré, pas de valeur inventée


def test_productivity_value_averages_range_hgcomb():
    # le BGS combine parfois deux classes adjacentes en une fourchette, ex. "B-L/LM" : on moyenne
    pct, yld = productivity_value("B-L/LM")
    pct_l, yld_l = PRODUCTIVITY["L"]
    pct_lm, yld_lm = PRODUCTIVITY["LM"]
    assert pct == (pct_l + pct_lm) / 2
    assert yld == (yld_l + yld_lm) / 2
    # une seule des deux classes reconnue -> on utilise celle-là plutôt que de rejeter la ligne
    assert productivity_value("U-LM/ZZ") == PRODUCTIVITY["LM"]
    assert productivity_value("U-ZZ/ZZ") is None   # aucune classe reconnue -> pas de valeur inventée


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
    test_productivity_value_parses_single_code_hgcomb()
    test_productivity_value_averages_range_hgcomb()
    test_all_productivity_classes_have_rank_and_yield()
    test_compute_samples_points_in_polygons()
    print("OK : tests connector_geology")
