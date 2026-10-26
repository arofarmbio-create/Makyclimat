import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import numpy as np
from build_shocks import wind_class, track_distance

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

if __name__ == "__main__":
    test_wind_class(); test_track_distance(); print("ok")
