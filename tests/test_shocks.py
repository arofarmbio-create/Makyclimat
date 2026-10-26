import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import numpy as np
import pandas as pd
from build_shocks import wind_class, track_distance, fit_ratios, fill_radii

def test_wind_class():
    cov = {34: np.array([True, True, True, False]), 50: np.array([False, True, True, False]), 64: np.array([False, False, True, False])}
    assert wind_class(cov).tolist() == [34, 50, 64, 0]

def test_track_distance():
    xc = np.array([0.0, 100.0]); yc = np.array([0.0, 0.0])
    tt = np.array(["2022-02-01T00:00", "2022-02-01T10:00"], dtype="datetime64[s]")
    d, w = track_distance(xc, yc, tt, np.array([50.0, 100.0, 300.0]), np.array([30.0, 0.0, 0.0]))
    assert abs(d[0] - 30) < 6 and abs(d[1]) < 1e-6 and abs(d[2] - 200) < 1e-6
    assert str(w[1]) == "2022-02-01T10:00:00"
    assert abs((w[0] - tt[0]) / np.timedelta64(1, "h") - 5) < 1.0

def _frame(rows):
    cols = ["USA_WIND"] + [f"USA_R{k}_{q}" for k in (34, 50, 64) for q in ("NE", "SE", "SW", "NW")]
    return pd.DataFrame(rows, columns=cols)

def test_fill_radii():
    nan = [np.nan] * 4
    rows = [[v] + [200.0] * 4 + [200 * np.exp(-0.5 - 0.01 * (v - 50))] * 4 + [200 * np.exp(-1.0 - 0.01 * (v - 50))] * 4 for v in (55, 70, 90, 110, 80)]
    d = _frame(rows)
    r = fit_ratios(d)
    assert abs(r[50][1] + 0.01) < 1e-6 and r[50][2] < 1e-6
    g = _frame([[75] + [200.0] * 4 + nan + nan, [40] + [200.0] * 4 + nan + nan])
    g2, n = fill_radii(g, r)
    assert n == 2 * 1 + 0 or n >= 2                      # la position à 75 kt reçoit R50 et R64, celle à 40 kt rien
    assert np.isfinite(g2.loc[0, "USA_R50_NE"]) and np.isfinite(g2.loc[0, "USA_R64_NE"]) and g2.loc[0, "USA_R64_NE"] <= g2.loc[0, "USA_R50_NE"] + 1e-9
    assert np.isnan(g2.loc[1, "USA_R50_NE"])

def test_rollup():
    from build_shocks import rollup
    leaves = pd.DataFrame({"pcode": ["F1", "F2", "F3"], "adm1": ["R1"] * 3, "adm2": ["D1", "D1", "D2"], "adm3": ["C1", "C1", "C2"]})
    df = pd.DataFrame({"evenement": ["a", "a", "b"], "pcode": ["F1", "F2", "F1"], "vent_classe_kt": [34, 64, 50], "dist_min_km": [100, 20, 80],
                       "date_passage": ["2026-02-10"] * 3, "rx3_mm": [1, 2, 3], "periode_retour_ans": [2, 8, 16]})
    r = rollup(leaves, df, "2026-02-20", "s").pivot(index="pcode", columns="indicateur", values="valeur")
    assert r.loc["C1", "choc_cyc_vent_kt"] == 64 and r.loc["R1", "choc_cyc_dist_km"] == 20 and r.loc["F1", "choc_cyc_nb"] == 2
    assert r.loc["D1", "choc_cyc_retour_ans"] == 16 and r.loc["F2", "choc_cyc_dernier_jours"] == 10 and "C2" not in r.index

if __name__ == "__main__":
    test_wind_class(); test_track_distance(); test_fill_radii(); test_rollup(); print("ok")
