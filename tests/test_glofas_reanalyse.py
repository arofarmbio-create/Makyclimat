"""Tests hors réseau : API simulée, reprise, mailles et garde du workflow."""
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import xarray as xr
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_glofas_reanalyse as R


class Rep:
    def __init__(self, data, code=200):
        self.data, self.status_code = data, code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class API:
    def __init__(self):
        self.posts, self.deletes, self.jobs = [], [], []
        self.etats = {"j1": ["accepted"]}

    def post(self, url, json, **kwargs):
        self.posts.append((url, json))
        return Rep({"jobID": "j1"})

    def get(self, url, **kwargs):
        if url.endswith('/jobs'):
            return Rep({"jobs": self.jobs})
        if url.endswith('/results'):
            return Rep({"asset": {"value": {"href": "https://stockage/debit.nc"}}})
        etats = self.etats.get(url.rsplit('/', 1)[-1])
        if etats is None:
            return Rep({}, 404)
        return Rep({"status": etats.pop(0) if len(etats) > 1 else etats[0]})

    def delete(self, url, **kwargs):
        self.deletes.append(url)
        return Rep({})


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        self.note = self.d / 'glofas_reanalyse_2003.demande.json'
        self.api = API()

    def collecte(self, publier=None):
        return R.demande_reprenable(self.api, {}, R.requete(2003), self.note, 0, publier)

    def test_requete_officielle_et_saison(self):
        r = R.requete(2003)
        self.assertEqual(r['year'], ['2003', '2004'])
        self.assertEqual(r['system_version'], ['version_4_0'])
        self.assertEqual(r['product_type'], ['consolidated'])
        self.assertEqual(r['variable'], ['average_river_discharge_in_the_last_24_hours'])
        self.assertEqual(r['timespan'], 'time_mean')
        self.assertEqual(r['area'], [-11.5, 43, -26, 51])
        self.assertNotIn('hyear', r)
        dates = R.dates_saison(2003).astype(str)
        self.assertEqual((dates[0], dates[-1]), ('2003-11-25', '2004-04-05'))
        self.assertIn('2004-02-29', dates)

    def test_entrees(self):
        self.assertEqual(R.saisons('2016 2003 2003'), [2003, 2016])
        for value in ('', '2002', '2017', '2003; echo secret', '$(id)', '02003'):
            with self.assertRaises(ValueError):
                R.saisons(value)

    def test_attente_reprise_sans_doublon(self):
        publies = []
        self.assertIsNone(self.collecte(publies.append))
        self.assertEqual(publies, [self.note])
        self.assertEqual(self.api.posts[0], (f'{R.BASE}/processes/{R.JEU}/execution',
                                           {'inputs': R.requete(2003)}))
        self.api.etats['j1'] = ['running', 'successful']
        self.assertEqual(self.collecte(), 'https://stockage/debit.nc')
        self.assertEqual(len(self.api.posts), 1)

    def test_echec_publication_ne_resoumet_pas(self):
        def panne(_):
            raise RuntimeError('publication refusée')
        with self.assertRaises(RuntimeError):
            self.collecte(panne)
        self.assertTrue(self.note.exists())
        self.collecte()
        self.assertEqual(len(self.api.posts), 1)

    def test_note_incompatible_ou_corrompue(self):
        self.collecte()
        n = json.loads(self.note.read_text())
        n['requete']['year'] = ['2006']
        self.note.write_text(json.dumps(n))
        with self.assertRaises(ValueError):
            self.collecte()
        self.note.write_text('{')
        with self.assertRaises(ValueError):
            self.collecte()
        self.assertEqual(len(self.api.posts), 1)

    def test_demande_disparue_et_echec_explicite(self):
        self.collecte()
        self.api.etats.clear()
        with self.assertRaises(RuntimeError):
            self.collecte()
        self.assertEqual(len(self.api.posts), 2)
        self.api.etats['j1'] = ['running', 'failed']
        with self.assertRaises(RuntimeError):
            self.collecte()

    def test_menage_epargne_autres_notes_et_running(self):
        self.collecte()
        autre = self.d / 'glofas_reanalyse_2004.demande.json'
        autre.write_text(json.dumps({'jobID': 'j2'}))
        now = dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc)
        self.api.jobs = [dict(jobID=j, status=s, processID=p, created='2026-11-11T00:00:00Z')
                         for j, s, p in [('j1', 'accepted', R.JEU), ('j2', 'accepted', R.JEU),
                                         ('j3', 'accepted', R.JEU), ('j4', 'running', R.JEU),
                                         ('j5', 'accepted', 'autre-jeu')]]
        self.assertFalse(R.menage(self.api, {}, self.d, self.note, now))
        self.assertEqual(self.api.deletes, [f'{R.BASE}/jobs/j3'])
        autre.write_text('{')
        with self.assertRaises(ValueError):
            R.menage(self.api, {}, self.d, self.note, now)
        self.assertEqual(len(self.api.deletes), 1)

    def test_menage_inventaire_incomplet_ou_notes_absentes(self):
        self.api.jobs = [{}] * 100
        with self.assertRaisesRegex(RuntimeError, 'Inventaire'):
            R.menage(self.api, {}, self.d, self.note)
        with self.assertRaisesRegex(ValueError, 'Dossier'):
            R.menage(self.api, {}, self.d/'absent', self.note)
        self.assertEqual(self.api.deletes, [])

    def test_suivi_attend_puis_rend_la_main(self):
        temps = [0]
        def dormir(s):
            temps[0] += s
        out = R.demande_reprenable(self.api, {}, R.requete(2003), self.note, 125,
                                    horloge=lambda: temps[0], dormir=dormir)
        self.assertIsNone(out)
        self.assertEqual(temps[0], 125)
        self.assertEqual(len(self.api.posts), 1)

    def jeu(self):
        dates = np.arange(np.datetime64('2003-11-24'), np.datetime64('2004-04-07'))
        q = np.arange(len(dates)*6).reshape(len(dates), 2, 3).astype(float)
        return xr.Dataset({'dis24': (('time', 'latitude', 'longitude'), q)},
                          coords={'time': dates, 'latitude': [-15.025, -15.075],
                                  'longitude': [45.025, 45.075, 45.125]})

    def test_union_et_extraction_paire_sans_interpolation(self):
        np.savez(self.d/'glofas_v4_2003_12.npz', lat=[-15.025], lon=[45.125])
        np.savez(self.d/'glofas_v4_2004_01.npz', lat=[-15.075, -15.025], lon=[45.025, 45.125])
        lat, lon = R.mailles(self.d)
        self.assertEqual(len(lat), 2)
        ds = self.jeu()
        out = R.extraire(ds, 2003, lat, lon)
        np.testing.assert_equal(out['q'], ds.dis24.values[1:-1, [1, 0], [0, 2]])
        self.assertEqual(out['q'].dtype, np.float32)
        np.savez_compressed(self.d/'sortie.npz', **out)
        with np.load(self.d/'sortie.npz', allow_pickle=False) as z:
            self.assertEqual(set(z.files), {'q', 'dates', 'lat', 'lon'})

    def test_valid_time_et_axes_inverses(self):
        ds = self.jeu().rename({'time': 'valid_time'}).isel(latitude=slice(None, None, -1))
        out = R.extraire(ds, 2003, np.array([-15.025]), np.array([45.125]))
        np.testing.assert_equal(out['q'][:, 0], self.jeu().dis24.values[1:-1, 0, 2])

    def test_nom_inconnu_et_dimension_unitaire(self):
        """Run 43230289148 (12/11) : nom de variable hors liste ; on prend la seule variable spatiale."""
        ds = self.jeu().rename({'dis24': 'nom_nouveau'}).expand_dims(surface=[0.0], axis=1)
        ds['heure'] = ('time', np.zeros(ds.sizes['time']))       # variable non spatiale ignorée
        out = R.extraire(ds, 2003, np.array([-15.025]), np.array([45.125]))
        np.testing.assert_equal(out['q'][:, 0], self.jeu().dis24.values[1:-1, 0, 2])
        ds['autre'] = ds['nom_nouveau']
        with self.assertRaisesRegex(ValueError, 'ambiguë'):
            R.extraire(ds, 2003, np.array([-15.025]), np.array([45.125]))

    def test_refus_jours_et_mailles_manquants(self):
        for ds in (self.jeu().isel(time=slice(3, None)),
                   xr.concat([self.jeu(), self.jeu().isel(time=[3])], dim='time')):
            with self.assertRaisesRegex(ValueError, 'Jours'):
                R.extraire(ds, 2003, np.array([-15.025]), np.array([45.125]))
        with self.assertRaisesRegex(ValueError, 'Maille'):
            R.extraire(self.jeu(), 2003, np.array([-15.035]), np.array([45.125]))

    def test_code_75_avant_telechargement(self):
        args = ['script', '--saison', '2003', '--references', str(self.d), '--notes', str(self.d),
                '--sortie', str(self.d/'out')]
        np.savez(self.d/'glofas_v4_2003_12.npz', lat=[-15.025], lon=[45.125])
        with patch.object(sys, 'argv', args), patch.dict('os.environ', {'CDS_API_KEY': 'faux'}), \
                patch.object(R, 'menage', return_value=True), \
                patch.object(R, 'demande_reprenable', return_value=None):
            self.assertEqual(R.main(), 75)
        self.assertFalse(list((self.d/'out').glob('*.npz')))

    def test_collecte_complete_fausse_api_et_netcdf(self):
        # Même parcours que le CLI : note, résultat HTTP simulé, NetCDF puis NPZ.
        brut = self.d/'faux.nc'
        self.jeu().to_netcdf(brut, engine='scipy')
        contenu = brut.read_bytes()
        api = self.api
        api.etats['j1'] = ['successful']
        original_get = api.get

        class Flux(Rep):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def iter_content(self, taille):
                yield contenu

        def get(url, **kwargs):
            if url == 'https://stockage/debit.nc':
                self.assertEqual(kwargs['headers'], {})
                self.assertFalse(kwargs['allow_redirects'])
                return Flux({})
            return original_get(url, **kwargs)

        api.get = get
        np.savez(self.d/'glofas_v4_2003_12.npz', lat=[-15.025], lon=[45.125])
        args = ['script', '--saison', '2003', '--references', str(self.d), '--notes', str(self.d),
                '--sortie', str(self.d/'out')]
        with patch.object(sys, 'argv', args), patch.dict('os.environ', {'CDS_API_KEY': 'faux'}), \
                patch('requests.Session') as session:
            session.return_value.__enter__.return_value = api
            # engine scipy explicite : dépendance déjà présente dans la CI générale.
            ouvrir = xr.open_dataset
            with patch.object(xr, 'open_dataset', side_effect=lambda p: ouvrir(p, engine='scipy')):
                self.assertEqual(R.main(), 0)
        with np.load(self.d/'out/glofas_reanalyse_2003.npz', allow_pickle=False) as z:
            np.testing.assert_equal(z['q'][:, 0], self.jeu().dis24.values[1:-1, 0, 2])
        self.assertTrue(self.note.exists())

    def test_workflow_manuel_et_permissions(self):
        wf = yaml.safe_load((ROOT/'.github/workflows/build-glofas-reanalyse.yml').read_text(encoding='utf-8'))
        self.assertEqual(set(wf.get('on', wf.get(True))), {'workflow_dispatch'})
        self.assertEqual(wf['permissions'], {})
        self.assertEqual(wf['jobs']['plan']['permissions'], {'contents': 'read'})
        self.assertEqual(wf['jobs']['collecte']['strategy']['max-parallel'], 1)
        self.assertFalse(wf['concurrency']['cancel-in-progress'])


if __name__ == '__main__':
    unittest.main()
