"""Tests du connecteur conductivité électrique (MGMERL — mesures réelles, aucun appel réseau)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from connector_mgmerl_quality import compute, load_conductivity


def make_fake_csv(tmp_path) -> Path:
    rows = [
        {"Nom": "Forage A", "ID unique": "1", "Type": "Forage",
         "Coordonnées GPS": "-19.00, 47.00", "Conductivité électrique (uS/cm)": "3,999"},
        {"Nom": "Forage B", "ID unique": "2", "Type": "Forage",
         "Coordonnées GPS": "-25.00, 50.00", "Conductivité électrique (uS/cm)": "622"},
    ]
    p = tmp_path / "mgmerl_conductivite.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_load_conductivity_parses_thousands_separator(tmp_path):
    csv_path = make_fake_csv(tmp_path)
    df = load_conductivity(csv_path)
    assert len(df) == 2
    row_a = df[df["ID unique"] == 1].iloc[0]
    assert row_a["valeur"] == 3999.0  # "3,999" (virgule = séparateur de milliers) -> 3999, pas 3.999


def test_compute_assigns_conductivity_indicator(tmp_path):
    csv_path = make_fake_csv(tmp_path)
    leaves = pd.DataFrame({"pcode": ["x"], "lon": [47.00], "lat": [-19.00]})
    out = compute(leaves, path=csv_path)
    assert len(out) == 1
    assert out.iloc[0].indicateur == "conductivity_uscm"
    assert out.iloc[0].valeur == 3999.0


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        test_load_conductivity_parses_thousands_separator(tmp)
        test_compute_assigns_conductivity_indicator(tmp)
    print("OK : tests connector_mgmerl_quality")
