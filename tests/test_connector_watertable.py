"""Tests du connecteur profondeur de nappe (MGMERL — mesures réelles, plus proche voisin, aucun appel réseau)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from connector_watertable import assign_nearest, load_mgmerl, compute


def make_fake_mgmerl_csv(tmp_path) -> Path:
    # 3 points réels fictifs : deux proches l'un de l'autre (même "ID unique" relevé deux fois,
    # on doit garder le plus récent), un isolé loin de tout fokontany de test.
    rows = [
        {"Nom": "Forage A", "ID unique": "1", "Type de point d'eau": "Forage",
         "Coordonnées GPS": "-19.00, 47.00", "Niveau statique d'eau": "5.0", "Date du rapport": "Jan 1, 2025 10:00 AM"},
        {"Nom": "Forage A (relevé suivant)", "ID unique": "1", "Type de point d'eau": "Forage",
         "Coordonnées GPS": "-19.00, 47.00", "Niveau statique d'eau": "8.0", "Date du rapport": "Jun 1, 2026 10:00 AM"},
        {"Nom": "Forage B isolé", "ID unique": "2", "Type de point d'eau": "Forage",
         "Coordonnées GPS": "-25.00, 50.00", "Niveau statique d'eau": "20.0", "Date du rapport": "Jan 1, 2025 10:00 AM"},
    ]
    p = tmp_path / "mgmerl_niveau_statique.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_load_mgmerl_keeps_most_recent_report_per_point(tmp_path):
    csv_path = make_fake_mgmerl_csv(tmp_path)
    df = load_mgmerl(csv_path)
    assert len(df) == 2  # dédoublonné : forage A (2 relevés) + forage B
    row_a = df[df["ID unique"] == 1].iloc[0]
    assert row_a["valeur"] == 8.0  # le relevé le plus récent (juin 2026), pas celui de janvier 2025


def test_assign_nearest_respects_max_distance():
    points = pd.DataFrame({"lon": [47.00, 50.00], "lat": [-19.00, -25.00], "valeur": [8.0, 20.0]})
    leaves = pd.DataFrame({
        "pcode": ["proche", "loin"],
        "lon": [47.01, 48.50],   # "proche" à ~1km du point (47,-19) ; "loin" à des centaines de km des deux points
        "lat": [-19.01, -19.00],
    })
    out = assign_nearest(points, leaves, max_dist_km=15.0)
    assert set(out.pcode) == {"proche"}  # "loin" ne reçoit aucune valeur (hors seuil), pas une valeur inventée
    assert out.iloc[0].valeur == 8.0


def test_compute_end_to_end(tmp_path):
    csv_path = make_fake_mgmerl_csv(tmp_path)
    leaves = pd.DataFrame({"pcode": ["x"], "lon": [47.00], "lat": [-19.00]})
    out = compute(leaves, mgmerl_path=csv_path)
    assert len(out) == 1
    assert out.iloc[0].indicateur == "water_table_depth_m"
    assert out.iloc[0].valeur == 8.0


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        test_load_mgmerl_keeps_most_recent_report_per_point(tmp)
        test_compute_end_to_end(tmp)
    test_assign_nearest_respects_max_distance()
    print("OK : tests connector_watertable (MGMERL)")
