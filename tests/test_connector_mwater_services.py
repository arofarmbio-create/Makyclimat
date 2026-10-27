"""Tests du connecteur formations sanitaires mWater (aucun appel réseau)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from connector_mwater_services import compute, load_sante


def make_fake_csv(tmp_path) -> Path:
    rows = [
        {"Name": "CSB2 Test A", "Type": "Primary Health Center",
         "GPS Location (latitude)": "-18.8792", "GPS Location (longitude)": "47.5079",
         "Administrative Region": "Analamanga, Madagascar"},
        {"Name": "CSB2 Test B", "Type": "",
         "GPS Location (latitude)": "", "GPS Location (longitude)": "",  # pas de GPS -> doit être ignoré
         "Administrative Region": "Analamanga, Madagascar"},
    ]
    p = tmp_path / "mwater_sante.csv"
    pd.DataFrame(rows).to_csv(p, index=False, encoding="utf-8-sig")
    return p


def test_load_sante_drops_rows_without_gps(tmp_path):
    csv_path = make_fake_csv(tmp_path)
    df = load_sante(csv_path)
    assert len(df) == 1
    assert df.iloc[0]["lat"] == -18.8792


def test_compute_uses_point_in_polygon_real_boundaries(tmp_path):
    """Un point réel à Antananarivo doit être assigné à un fokontany réel (pcode non vide)."""
    csv_path = make_fake_csv(tmp_path)
    from common import read_units
    units = read_units("mdg")
    leaves = units[units.level == units.level.max()]
    out = compute(leaves, "mdg", path=csv_path)
    assert len(out) == 1
    assert out.iloc[0].indicateur == "mwater_sante"
    assert out.iloc[0].valeur == 1
    assert out.iloc[0].pcode.startswith("MG")


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        test_load_sante_drops_rows_without_gps(tmp)
        test_compute_uses_point_in_polygon_real_boundaries(tmp)
    print("OK : tests connector_mwater_services")
