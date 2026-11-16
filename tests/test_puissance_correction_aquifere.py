"""Tests de l'analyse de puissance T-H2.3 (scripts/puissance_correction_aquifere.py)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import puissance_correction_aquifere as P  # noqa: E402


def test_logo_comme_boucle_naive():
    rng = np.random.default_rng(0)
    for _ in range(100):
        n = int(rng.integers(4, 15))
        e = rng.normal(size=n)
        lab = rng.integers(0, 3, (5, n))
        err1, err2 = P.logo(e, lab)
        for p in range(5):
            for i in range(n):
                m = (lab[p] == lab[p, i]) & (np.arange(n) != i)
                f1 = np.median(np.delete(e, i))
                f2 = np.median(e[m]) if m.sum() >= 2 else f1
                assert abs(err1[i] - (f1 - e[i])) < 1e-12
                assert abs(err2[p, i] - (f2 - e[i])) < 1e-12


def test_permutation_invariante_au_niveau():
    """Un décalage commun de e (erreur uniforme de la référence) ne change ni G ni p."""
    cl = np.repeat(["socle", "sables", "calcaires"], 5)
    e = np.random.default_rng(3).normal(0, 0.5, 15) + np.where(cl == "calcaires", 1.0, 0.0)
    g1, p1 = P.test_permutation(e, cl, np.random.default_rng(1), 199)
    g2, p2 = P.test_permutation(e + 0.8, cl, np.random.default_rng(1), 199)
    assert abs(g1 - g2) < 1e-12 and p1 == p2


def test_classes_tres_differentes_detectees_et_nulles_non():
    cl = np.repeat(["socle", "sables", "calcaires"], 5)
    rng = np.random.default_rng(4)
    e = rng.normal(0, 0.1, 15) + np.select([cl == "socle", cl == "sables"], [-1.0, 0.0], 1.0)
    assert P.test_permutation(e, cl, rng, 199)[1] < 0.05
    assert P.test_permutation(np.zeros(15), cl, rng, 199)[1] == 1.0


def test_groupes_vus():
    g = P.groupes_vus()
    assert len(g) == 8
    assert (g["classe"] == "socle").sum() == 6
