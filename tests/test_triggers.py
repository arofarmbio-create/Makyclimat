"""Tests de la confusion/couverture utilisées pour calibrer les déclencheurs d'action anticipée."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_triggers import confusion, events_covered, scan


def test_confusion_basic():
    import numpy as np
    flag = np.array([True, True, False, False])
    pos = np.array([True, False, True, False])
    c = confusion(flag, pos)
    assert c["tp"] == 1 and c["fp"] == 1 and c["fn"] == 1 and c["tn"] == 1
    assert abs(c["pod"] - 0.5) < 1e-9
    assert abs(c["far"] - 0.5) < 1e-9


def test_confusion_perfect():
    import numpy as np
    flag = np.array([True, False, True, False])
    pos = np.array([True, False, True, False])
    c = confusion(flag, pos)
    assert c["pod"] == 1.0 and c["far"] == 0.0


def test_events_covered_counts_at_least_one_hit_per_event():
    df = pd.DataFrame({
        "evenement": ["a", "a", "b", "b", "c"],
        "pos":       [True, False, True, True, False],
    })
    # "a" : la région touchée (ligne 0) est signalée -> couvert
    # "b" : aucune des deux régions touchées n'est signalée -> pas couvert
    # "c" : pas d'impact documenté -> ignoré (ni couvert ni comptabilisé)
    flag = [True, False, False, False, True]
    n_cov, n_tot = events_covered(df, flag)
    assert n_tot == 2  # a et b ont au moins une région touchée
    assert n_cov == 1  # seul a est couvert


def test_scan_monotonic_pod_decreases_as_threshold_rises():
    df = pd.DataFrame({
        "evenement": ["a"] * 5,
        "pos":       [True, True, True, False, False],
        "x":         [0.1, 0.3, 0.5, 0.2, 0.6],
    })
    rows = scan(df, "x", [0.0, 0.4], lambda t: str(t))
    assert rows[0]["pod"] >= rows[1]["pod"]  # seuil plus bas -> détecte au moins autant


if __name__ == "__main__":
    import inspect
    mod = sys.modules[__name__]
    fails = 0
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith("test_"):
            try:
                fn()
                print(f"OK    {name}")
            except AssertionError as e:
                fails += 1
                print(f"ÉCHEC {name} : {e}")
    if fails:
        raise SystemExit(f"{fails} test(s) en échec")
    print("Tous les tests des déclencheurs passent.")
