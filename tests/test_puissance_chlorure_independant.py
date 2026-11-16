"""Tests de l'analyse de puissance T-H2.1 (scripts/puissance_chlorure_independant.py)."""
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, wilcoxon

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import puissance_chlorure_independant as P  # noqa: E402


def test_wilcoxon_exact_comme_scipy():
    rng = np.random.default_rng(1)
    for n in (5, 8, 12, 20):
        for _ in range(20):
            d = rng.normal(0.2, 1.0, n)
            attendu = wilcoxon(d, alternative="greater", method="exact").pvalue
            assert abs(P.wilcoxon_sup(d) - attendu) < 1e-9


def test_signe_comme_binomtest():
    e = np.array([0.3, 0.1, -0.2, 0.5, 0.4, 0.2, 0.6, -0.1, 0.3, 0.2])
    attendu = binomtest(8, 10, 0.5, alternative="greater").pvalue
    assert abs(P.signe_sup(e) - attendu) < 1e-12


def test_h_i2_invariant_au_niveau_du_depot():
    rng = np.random.default_rng(2)
    r = rng.normal(1.0, 0.4, 15)
    t2 = r + 0.6 + rng.normal(0, 0.4, 15)
    t2l = r + 0.1 + rng.normal(0, 0.1, 15)
    a = P.h_i2(t2, t2l, r)
    b = P.h_i2(t2, t2l, r + 0.5)
    assert a[0] == b[0] and abs(a[1] - b[1]) < 1e-12 and abs(a[2] - b[2]) < 1e-12


def test_reference_decalee_echoue():
    rng = np.random.default_rng(3)
    r = rng.normal(1.0, 0.4, 15)
    t2 = r + rng.normal(0.5, 0.4, 15)
    assert not P.h_i2(t2, t2 - 0.7, r)[0]
