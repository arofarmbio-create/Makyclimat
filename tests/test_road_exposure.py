import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import numpy as np
from build_road_exposure import densify, accumulate, seg_km

def test_densify_length():
    pts, w = densify([(47.0, -19.0), (47.0, -18.9), (47.1, -18.9)], 0.25)
    L = seg_km(47.0, -19.0, 47.0, -18.9) + seg_km(47.0, -18.9, 47.1, -18.9)
    assert abs(w.sum() - L) < 1e-6 and (w <= 0.26).all() and len(pts) > 40

def test_accumulate():
    h, w, res, lon0, lat0 = 4, 4, 0.1, 47.0, -19.0
    ids = np.zeros((h, w), int); ids[:, :2] = 1; ids[:, 2:] = 2
    hand = np.full((h, w), 20.0, "float32"); hand[:, 0] = 2.0          # colonne 0 : zone basse
    sea = np.zeros((h, w), bool); sea[3, 3] = True
    pts = np.array([[47.05, -19.05], [47.15, -19.05], [47.25, -19.05], [47.35, -19.35], [46.0, -19.0]])
    wts = np.array([1.0, 1.0, 2.0, 5.0, 9.0])
    tot, low = accumulate(pts, wts, ids, hand, sea, lon0, lat0, res, 3)
    assert tot.tolist() == [0.0, 2.0, 2.0] and low.tolist() == [0.0, 1.0, 0.0]     # mer et hors grille ignorés

if __name__ == "__main__":
    test_densify_length(); test_accumulate(); print("ok")
