"""Tests R-21 bis exclusivement synthétiques, aucun accès aux données du dépôt."""
import datetime as dt
from pathlib import Path
import sys
import unittest
import warnings
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import r21_diagnostic as d


T = dt.date(2004, 1, 10)


def mois(q, t=T):
    q = np.asarray(q, float)
    return [(t.year, t.month, [t], np.arange(q.shape[1]), q[None])]


class DiagnosticTests(unittest.TestCase):
    def test_classes_priorite_et_couverture(self):
        jours = d.etendre([T], 3)
        for valeur, classe in [(0, "b"), (.499, "b"), (.5, "c"), (.999, "c"), (1, "e")]:
            self.assertEqual(d.classer([T], jours, np.full(7, valeur))["classe"], classe)
        v = [1, 0, 0, np.nan, 0, 0, 0]
        self.assertEqual(d.classer([T], jours, v)["classe"], "n")
        self.assertEqual(d.classer([T], jours, v, False)["classe"], "a")
        v[3] = 0
        self.assertEqual(d.classer([T], jours, v)["classe"], "d")
        v[3] = 1
        self.assertEqual(d.classer([T], jours, v)["classe"], "e")
        result = d.classer([T, T + dt.timedelta(1), T + dt.timedelta(2)], [T], [.4])
        self.assertAlmostEqual(result["couverture"], 1 / 3)
        self.assertTrue(result["couverture_faible"])

    def test_rapport_equivalence_alertes_r21(self):
        rng = np.random.default_rng(18)
        q = rng.uniform(0, 25, (11, 4))
        q[2, 0] = np.nan
        M = mois(q)
        A = sparse.csr_matrix([[1, 0], [1, 0], [0, 1], [0, 1]])
        jours = d.etendre([T], 4)
        thr = np.array([10, 12, 15, np.nan])
        ctrl, pmax = d.alertes(M, thr, A, jours)
        np.testing.assert_array_equal(d.rapports(M, thr, A, jours) >= 1, ctrl)
        for pi in d.PIS:
            np.testing.assert_array_equal(d.rapports(M, thr, A, jours, pi) >= 1, pmax >= pi - 1e-6)

    def test_rang_membres_absents(self):
        q = np.full((11, 1), 20.)
        q[0] = np.nan
        A = sparse.eye(1, format="csr")
        jours = [T + dt.timedelta(1)]
        self.assertEqual(d.rapports(mois(q), np.array([10.]), A, jours, 1)[0, 0], 0)
        self.assertTrue(np.isnan(d.rapports(mois(q), np.array([10.]), A, jours)[0, 0]))
        self.assertEqual(d.rapports(mois(q), np.array([10.]), A, jours, .9)[0, 0], 2)
        with self.assertRaises(ValueError):
            d.rapports(mois(q[:10]), np.array([10.]), A, jours, .5)

    def test_maximum_initialisations_apres_rang(self):
        q = np.zeros((2, 11, 1))
        q[0, :5, 0] = 20
        q[1, 5:, 0] = 20
        M = [(2004, 1, [T, T + dt.timedelta(1)], np.array([0]), q)]
        r = d.rapports(M, np.array([10.]), sparse.eye(1, format="csr"), [T + dt.timedelta(2)], .8)
        self.assertEqual(r[0, 0], 0)  # ne pas fusionner les membres de deux initialisations

    def test_reanalyse_exige_trois_jours(self):
        M = mois(np.ones((11, 2)))
        dates = [T + dt.timedelta(k) for k in (1, 2, 3)]
        q = np.array([[1, 1], [4, np.nan], [2, 9]])
        v = d.fenetres_reanalyse(M, dates, q)[0][-1]
        self.assertEqual(v[0, 0, 0], 4)
        self.assertTrue(np.isnan(v[0, 0, 1]))
        self.assertTrue(np.isnan(d.fenetres_reanalyse(M, dates[:2], q[:2])[0][-1]).all())
        with self.assertRaises(ValueError):
            d.fenetres_reanalyse(M, [T, T], q[:2])

    def test_seuils_reanalyse_blocs_et_exclusion_saison(self):
        M = []
        for y in range(1990, 2000):
            for m in (1, 2, 3, 12):
                M.append((y, m, [dt.date(y, m, 1), dt.date(y, m, 2)], np.array([0, 1]),
                          np.array([[[10., np.nan]], [[np.nan, np.nan]]])))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            S, _ = d.seuils_reanalyse(M, 2, [1995])
            self.assertEqual(S[1995][0], 10)
            self.assertTrue(np.isnan(S[1995][1]))
            S, _ = d.seuils_reanalyse(M[:29], 2, [2010])
            self.assertTrue(np.isnan(S[2010]).all())
        # Seuil de prévision : comportement NaN R-21 inchangé.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            S, _ = d.seuils(M, 2, [1995])
        self.assertTrue(np.isnan(S[1995]).all())

    def test_k_plateau_et_cible_nulle(self):
        jours = [T + dt.timedelta(k) for k in range(5)]
        ctrl = np.ones((5, 1))
        tem = np.ones((5, 1), bool)
        cal = d.calibrer_k(ctrl, ctrl * 3, tem, jours)
        self.assertEqual(cal["k"], 1)
        self.assertFalse(cal["hors_tolerance"])
        for masque, valeurs in [(tem, ctrl * 0), (tem * False, ctrl)]:
            cal = d.calibrer_k(valeurs, ctrl, masque, jours)
            self.assertEqual(cal["k"], 1)
            self.assertTrue(cal["hors_tolerance"])

    def test_k_departage_symetrique(self):
        # Charges non monotones possibles : on compte les épisodes, pas les jours.
        charges = [9.] * len(d.KS)
        charges[list(d.KS).index(.9)] = 1
        charges[list(d.KS).index(1.1)] = 1
        with patch.object(d, "charge", side_effect=[1.] + charges):
            cal = d.calibrer_k(np.ones((1, 1)), np.ones((1, 1)), np.ones((1, 1), bool), [T])
        self.assertEqual(cal["k"], .9)

    def test_k_support_commun(self):
        ctrl = np.array([[1.], [np.nan], [0.]])
        rr = np.array([[np.nan], [2.], [0.]])
        cal = d.calibrer_k(ctrl, rr, np.ones((3, 1), bool), d.etendre([T], 1))
        self.assertEqual(cal["jours_communs"], 1)
        self.assertTrue(cal["hors_tolerance"])

    def test_regles_lecture(self):
        self.assertTrue(d.lecture(.25, .2, [-.1, .2], 0).startswith("référence basse"))
        self.assertEqual(d.lecture(.3, .2, [0, .2], 0), "hypothèses mêlées")
        self.assertTrue(d.lecture(.4, .25, [.001, .3], 3).startswith("C privilégiée"))
        for pc, ic, hors in [(.26, [.01, .3], 0), (.25, [0, .3], 0), (.25, [.01, .3], 4)]:
            self.assertTrue(d.lecture(.4, pc, ic, hors).startswith("descriptif"))

    def test_comparaison_a_n_bootstrap_apparie(self):
        U = pd.DataFrame({"saison": [1, 1, 2, 2], "classe_controle": list("aene"),
                          "classe_ensemble": list("aene"), "classe_reanalyse": list("aeee")})
        r = d.comparer(U, n_boot=50)
        self.assertEqual(r["n"], 3)
        self.assertAlmostEqual(r["taux"]["reanalyse"], 2 / 3)
        self.assertEqual(r["ic"]["ecart"], [0., 0.])
        self.assertEqual(d.comparer(U, sans_riviere=True)["n"], 2)
        table = d.croisement(U, "controle")
        self.assertEqual(table.shape, (6, 6))
        self.assertEqual(table.loc["e", "n"], 1)
        self.assertEqual(table.to_numpy().sum(), 4)
        self.assertEqual(d.comparer(U.iloc[[2]])["n"], 0)

    def test_bassins_seuil_population_dates_temoins(self):
        F = pd.DataFrame({"adm2": ["a", "a", "b"], "bassin": ["x", "y", "x"],
                          "population": [20, 80, 100], "commune": ["c1", "c2", "c3"],
                          "sous_bassin": ["s1", "s2", "s3"]})
        liens = d.rattachements(F)
        self.assertTrue(liens.principal.all())
        F.loc[0, "population"] = 19
        liens = d.rattachements(F)
        U = [dict(saison=2003, episode=1, territoire=a, dates=[T + dt.timedelta(k)])
             for a, k in [("a", 0), ("b", 3)]]
        principal = d.unites_bassins(U, liens)
        x = next(u for u in principal if u["territoire"] == "x")
        self.assertEqual(x["dates"], [T + dt.timedelta(3)])
        x = next(u for u in d.unites_bassins(U, liens, True) if u["territoire"] == "x")
        self.assertEqual(x["dates"], [T, T + dt.timedelta(3)])
        self.assertFalse(d.temoins_bassins([T], ["x"], {(2004, 1): ["a"]}, liens)[0, 0])

    def test_cyclones_positions_publiees_et_centroide(self):
        F = pd.DataFrame({"adm2": ["a", "a"], "lat": [0, 4], "lon": [0, 4], "population": [3, 1]})
        self.assertEqual(d.centroides(F)["a"], (1, 1))
        self.assertEqual(d.contexte_cyclonique([T], (0, 0), []) ["contexte"], "aucun cyclone")
        for lon, classe in [(.5, "<100 km"), (2, "100–300 km"), (4, ">300 km")]:
            r = d.contexte_cyclonique([T], (0, 0), [(T, 0, lon), (T + dt.timedelta(2), 0, 0)])
            self.assertEqual(r["contexte"], classe)
        r = d.contexte_cyclonique([T], (0, 0), [(T, 0, -4), (T, 0, 4)])
        self.assertEqual(r["contexte"], ">300 km")  # pas d'interpolation entre les positions

    def test_integration_synthetique_et_pi_bassins(self):
        M, R = [], []
        for y in range(1990, 2001):
            for m in (1, 2, 3, 12):
                t = dt.date(y, m, 10)
                M += mois(np.full((11, 1), 10.), t)
                R += mois(np.full((1, 1), 10.), t)
        jours = sorted({t + dt.timedelta(k) for _, _, ts, _, _ in M for t in ts for k in range(-3, 6)})
        U = [dict(episode=1, saison=1999, territoire="a", dates=[dt.date(2000, 1, 11)]),
             dict(episode=2, saison=1999, territoire="absent", dates=[dt.date(2000, 1, 11)])]
        A = sparse.eye(1, format="csr")
        result = d.diagnostic(M, R, A, ["a"], jours, np.ones((len(jours), 1), bool), U)
        self.assertEqual(result["unites"].classe_reanalyse.tolist(), ["e", "a"])
        self.assertEqual(result["comparaisons"]["commun"]["n"], 2)
        self.assertEqual(result["plis"].k.iloc[0], 1)
        bassin = d.diagnostic(M, R, A, ["a"], jours, np.ones((len(jours), 1), bool), U, pis={1999: .38})
        self.assertEqual(bassin["plis"].pi.iloc[0], .38)
        self.assertEqual(result["comparaisons"]["pm1"]["n"], 2)
        self.assertEqual(result["comparaisons"]["k1"]["n"], 2)
        self.assertEqual(list(d.comparer_echelles(result["unites"], bassin["unites"])), [1, 2])
        with self.assertRaises(ValueError):
            d.diagnostic(M, R[:-1], A, ["a"], jours, np.ones((len(jours), 1), bool), U)

    def test_sensibilites_ne_recuperent_pas_non_evaluable(self):
        U = pd.DataFrame({"saison": [1, 1, 2], "classe_controle": list("aan"),
                          "classe_ensemble": list("aan"), "classe_reanalyse": list("aan"),
                          "detecte_k1": [True] * 3,
                          **{"detecte_pm1_" + m: [True] * 3 for m in d.METHODES}})
        for r in d.sensibilites(U).values():
            self.assertEqual(r["n"], 2)
            self.assertEqual(r["taux"]["reanalyse"], 0)

    def test_saison_test_exclue_des_seuils(self):
        M = []
        for y in range(1990, 2001):
            for m in (1, 2, 3, 12):
                t = dt.date(y, m, 10)
                value = 10000 if d.season_of(t) == 1999 else 10
                M += mois(np.full((1, 1), value), t)
        S, _ = d.seuils_reanalyse(M, 1, [1999, 1998])
        self.assertEqual(S[1999][0], 10)
        self.assertGreater(S[1998][0], 10)

    def test_aucune_maille_hors_selection_r21(self):
        A = sparse.csr_matrix([[1], [1]])
        M = mois(np.array([[10., 100.]] * 11))
        R = mois(np.array([[1., 100.]]))
        jours = d.etendre([T + dt.timedelta(1)], 3)
        U = [dict(episode=1, saison=2003, territoire="a", dates=[T + dt.timedelta(1)])]
        with patch.object(d, "seuils", return_value=({2003: np.array([10., np.nan])}, 30)), \
             patch.object(d, "seuils_reanalyse", return_value=({2003: np.array([10., 10.])}, 30)):
            r = d.diagnostic(M, R, A, ["a"], jours, np.ones((len(jours), 1), bool), U, pis={2003: .38})
        self.assertEqual(r["unites"].classe_reanalyse.iloc[0], "b")


if __name__ == "__main__":
    unittest.main()
