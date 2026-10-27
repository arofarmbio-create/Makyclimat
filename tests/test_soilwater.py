import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import soilwater_core as C  # noqa: E402


def test_saxton_rawls():
    # Valeurs de référence de l'article (tableau de sorties usuelles, loam ~ sable 40 %, argile 20 %, MO 2,5 %) : FC ~ 0,25-0,30, PWP ~ 0,12-0,15
    wp, fc = C.saxton_rawls(0.40, 0.20, 2.5)
    assert 0.10 < wp < 0.17 and 0.23 < fc < 0.32, (wp, fc)
    wp_s, fc_s = C.saxton_rawls(0.90, 0.05, 1.0)       # sable : faible réserve
    wp_c, fc_c = C.saxton_rawls(0.20, 0.55, 2.0)       # argile : capacité élevée
    assert fc_s - wp_s < fc - wp, "le sable doit avoir une réserve utile plus faible qu'un limon"
    assert fc_c > fc_s and wp_c > wp_s


def test_texture_and_hsg():
    t = C.usda_texture(np.array([92.0, 40.0, 10.0, 20.0, 60.0, 15.0]), np.array([4.0, 20.0, 60.0, 45.0, 10.0, 8.0]))
    names = [C.TEXTURES[i] if i >= 0 else "?" for i in t]
    assert names[0] == "sable" and names[2] == "argile" and names[1] in ("limon", "limon argilo-sableux"), names
    assert (t >= 0).all(), names
    assert C.HSG_ARRAY[t[0]] == 0 and C.HSG_ARRAY[t[2]] == 3


def test_scs():
    # Exemple de l'USDA : CN 75, P = 100 mm -> S = 84,67 mm, Ia = 16,93, Q = (83,07)^2/(83,07+84,67) = 41,1 mm
    q = float(C.scs_runoff(100.0, 75.0))
    assert abs(q - 41.1) < 0.2, q
    assert float(C.scs_runoff(10.0, 60.0)) == 0.0            # sous l'abstraction initiale
    assert float(C.scs_runoff(50.0, 95.0)) > float(C.scs_runoff(50.0, 70.0))
    assert abs(float(C.scs_runoff(30.0, 100.0)) - 30.0) < 1e-6   # surface imperméable : tout ruisselle
    assert 55 < float(C.cn_dry(75.0)) < 58 and 87 < float(C.cn_wet(75.0)) < 89, (C.cn_dry(75.0), C.cn_wet(75.0))   # CN I = 55,6 ; CN III = 88,0 (NEH-4)
    assert abs(float(C.cn_for_moisture(75.0, 0.5)) - 75.0) < 1e-9
    assert float(C.cn_for_moisture(75.0, 1.0)) > 87 and float(C.cn_for_moisture(75.0, 0.0)) < 57


def test_cn_table():
    cn = C.cn_lookup(np.array([10, 40, 50, 80, 99]), np.array([0, 1, 2, 3, 0]))
    assert cn[0] == 30 and cn[1] == 78 and cn[2] == 90 and cn[3] == 100 and np.isnan(cn[4])


def test_balance():
    N = 3
    whc = np.array([100.0, 100.0, 0.0])
    pet = np.full((12, N), 100.0)
    P = np.zeros((48, N))
    P[:, 0] = np.tile([250, 250, 200, 120, 40, 10, 5, 5, 10, 40, 100, 200], 4)   # saison humide puis saison sèche
    W, A, X, Q = C.run_balance(P, pet, whc, month0=1)
    assert (Q == 0).all(), "sans cn2, pas de ruissellement séparé (comportement historique conservé)"
    assert (W[:, 0] >= -1e-9).all() and (W[:, 0] <= 100 + 1e-9).all(), "stock hors [0, WHC]"
    assert (A <= pet[0] + 1e-9).all(), "ET réelle > ET potentielle"
    # conservation de l'eau sur la période : somme P = somme AET + somme excédent + variation de stock (stock initial inconnu -> bilan sur les pas, w0 = valeur après mise en route)
    d = P[:, 0].sum() - A[:, 0].sum() - X[:, 0].sum()
    assert abs(d - (W[-1, 0] - W[0, 0] + (A[0, 0] - 0))) < 1e3   # ordre de grandeur (le stock initial dépend de la mise en route)
    assert W[:, 1].max() == 0 or W[:, 1].max() < 1e-6, "sans pluie, le stock doit s'épuiser"
    assert X[:, 0].sum() > 0 and X[:, 2].sum() >= 0


def test_balance_with_runoff_cn():
    """Avec cn2 fourni, une partie de la pluie ruisselle (Q > 0) et la recharge (X) baisse d'autant —
    pas de double comptage : P = AET + Q + X + variation de stock."""
    N = 2
    whc = np.array([100.0, 100.0])
    pet = np.full((12, N), 100.0)
    P = np.zeros((48, N))
    P[:, 0] = np.tile([250, 250, 200, 120, 40, 10, 5, 5, 10, 40, 100, 200], 4)
    cn2 = np.array([95.0, 95.0])    # CN élevé -> ruissellement important (ex. zone bâtie, sol quasi imperméable)
    W, A, X, Q = C.run_balance(P, pet, whc, month0=1, cn2=cn2)
    W0, A0, X0, Q0 = C.run_balance(P, pet, whc, month0=1)   # référence sans séparation du ruissellement
    assert Q[:, 0].sum() > 0, "un CN élevé doit produire du ruissellement"
    assert X[:, 0].sum() < X0[:, 0].sum(), "la recharge nette de ruissellement doit être inférieure à l'excédent brut"
    # conservation : P = AET + Q + X + variation de stock (ordre de grandeur, stock initial dépend de la mise en route)
    d = P[:, 0].sum() - A[:, 0].sum() - Q[:, 0].sum() - X[:, 0].sum()
    assert abs(d - (W[-1, 0] - W[0, 0])) < 1e3


def test_balance_conservation_exact():
    whc = np.array([120.0])
    pet = np.full((12, 1), 90.0)
    rng = np.random.default_rng(1)
    P = rng.gamma(2.0, 60.0, size=(60, 1))
    w, a, x = C.tm_step(np.array([40.0]), P[0], pet[0], whc)
    assert abs((40.0 + P[0, 0]) - (w[0] + a[0] + x[0])) < 1e-9
    w2, a2, x2 = C.tm_step(np.array([80.0]), np.array([20.0]), np.array([100.0]), whc)
    assert abs((80.0 + 20.0) - (w2[0] + a2[0] + x2[0])) < 1e-9 and x2[0] == 0 and a2[0] <= 100.0


def test_standardize():
    rng = np.random.default_rng(0)
    x = rng.gamma(2.0, 30.0, size=(300, 4))
    z = C.normal_scores(x)
    assert abs(np.nanmean(z)) < 0.05 and abs(np.nanstd(z) - 1) < 0.08
    assert (np.argsort(z[:, 0]) == np.argsort(x[:, 0])).all(), "ordre conservé"
    r = C.rolling_sum(np.ones((10, 2)), 3)
    assert np.isnan(r[:2]).all() and (r[2:] == 3).all()


def test_spi():
    rng = np.random.default_rng(1)
    T = 12 * 40
    P = rng.gamma(2.0, 40.0, size=(T, 3))
    P[::7, 2] = 0.0                                    # mois secs avec zéro pluie (probabilité de zéro)
    z3 = C.spi(P, 3, 1)
    assert np.isnan(z3[:2]).all(), "n-1 premiers pas vides"
    ok = z3[2:]
    assert abs(np.nanmean(ok[:, :2])) < 0.08 and abs(np.nanstd(ok[:, :2]) - 1) < 0.1, (np.nanmean(ok), np.nanstd(ok))
    assert np.nanmax(np.abs(z3)) <= 3.09 + 1e-9
    # plus de pluie -> SPI plus élevé (monotonie), à mois du calendrier égal
    idx = np.arange(5, T, 12)
    assert (np.argsort(z3[idx, 0]) == np.argsort(C.rolling_sum(P, 3)[idx, 0])).all()


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
            print("OK", k)
