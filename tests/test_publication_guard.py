"""Garde de publication : fixtures locales, sans données ni réseau réels."""
import copy
import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate import consequential_errors
import validate


class PublicationGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        (self.base / 'metrics/d').mkdir(parents=True)
        self.today = dt.date(2026, 11, 12)
        self.cfg = {'forecast': {'max_age_days': 3}}
        self.meta = {'forecast': {
            'fetched_at': '2026-11-12T00:00:00+00:00', 'first': '2026-11-12',
            'last': '2026-11-18', 'hazards': ['rain', 'wind', 'heat', 'dry', 'flood'],
            'flood': {'available': True, 'fetched_at': '2026-11-12',
                      'ensemble': {'available': True, 'fetched_at': '2026-11-12', 'members': 51}}}}
        self.row = {'p': 100, 'ew': [0, 1, 2, 3, 1], 'ewp': [0, 20, 40, 60, 20],
                    'ewt': [0, 10, 20, 30, 10], 'ewe5': [0, 2, 4, 6, 2],
                    'ev': [20, 50, 30, 40, 2, 1.2, 100, 30, 20, 10],
                    'x': {'susc_inond_pct': 65, 'potentiel_eau_pct': 42}}
        self.top = {'adm1': {'R': copy.deepcopy(self.row)}, 'adm2': {'D': copy.deepcopy(self.row)}}
        self.detail = {'adm3': {}, 'adm4': {'F': copy.deepcopy(self.row)}}

    def errors(self, skip_age=False):
        (self.base / 'metrics/d/D.json').write_text(json.dumps(self.detail), encoding='utf-8')
        return consequential_errors(self.base, self.meta, self.top, self.cfg, self.today, skip_age)

    def test_valid_all_levels(self):
        self.assertEqual(self.errors(), [])

    def test_optional_unavailable_without_active_values(self):
        self.meta['forecast'] = None
        self.top = {'adm1': {'R': {'p': 100}}, 'adm2': {'D': {'p': 100}}}
        self.detail = {'adm4': {'F': {'p': 10}}}
        (self.base / 'pluvial_forecast.json').write_text('{"available": false}', encoding='utf-8')
        self.assertEqual(self.errors(), [])

    def test_stale_weather_flood_ensemble_and_future(self):
        for source in (self.meta['forecast'], self.meta['forecast']['flood'], self.meta['forecast']['flood']['ensemble']):
            for bad in ('2026-11-01', '2026-11-13', 'incorrect'):
                with self.subTest(date=bad):
                    source['fetched_at'] = bad
                    self.assertTrue(self.errors())
            source['fetched_at'] = '2026-11-12'

    def test_skip_age_does_not_skip_bounds(self):
        self.meta['forecast']['fetched_at'] = '2026-10-01'
        self.assertEqual(self.errors(skip_age=True), [])
        self.detail['adm4']['F']['x']['susc_inond_pct'] = 101
        self.assertTrue(self.errors(skip_age=True))

    def test_detail_invalid_levels_probabilities_population_and_numbers(self):
        for key, bad in [('ew', [0, 0, 0, 0, 4]), ('ew', [0]),
                         ('ewp', [102, 0, 0, 0, 0]), ('ewt', [0, 22, 0, 0, 0]),
                         ('fp2', [0, 101, 0]), ('ev', [float('nan')] * 10)]:
            with self.subTest(field=key, value=bad):
                self.detail['adm4']['F'] = copy.deepcopy(self.row)
                self.detail['adm4']['F'][key] = bad
                self.assertTrue(self.errors())

    def test_no_weather_metadata_with_active_alerts(self):
        self.meta['forecast'] = None
        self.assertTrue(self.errors())

    def test_no_flood_source_with_active_values(self):
        self.meta['forecast']['flood'] = {'available': False}
        self.assertTrue(self.errors())

    def test_sensitive_external_bounds(self):
        for key, bad in [('potentiel_eau_pct', 101), ('water_table_depth_m', -1),
                         ('recharge12_mm', float('inf')), ('ruiss_prevu_niveau', 3)]:
            with self.subTest(field=key):
                self.detail['adm4']['F']['x'] = {key: bad}
                self.assertTrue(self.errors())

    def test_pluvial_available_and_stale(self):
        self.detail['adm4']['F']['x'] = {'ruiss_prevu_mm': 10}
        self.assertTrue(self.errors())
        pluvial = {'available': True, 'experimental': True, 'warning': 'Expérimental',
                   'generated': '2026-11-12', 'forecast_fetched_at': '2026-11-12',
                   'days': ['2026-11-12', '2026-11-13'],
                   'regions': [{'niveau_max': 1, 'part_fokontany_vigilance_pct': 20}]}
        path = self.base / 'pluvial_forecast.json'
        path.write_text(json.dumps(pluvial), encoding='utf-8')
        self.assertEqual(self.errors(), [])
        pluvial['forecast_fetched_at'] = '2026-10-01'
        path.write_text(json.dumps(pluvial), encoding='utf-8')
        self.assertTrue(self.errors())
        path.write_text('{', encoding='utf-8')
        self.assertTrue(self.errors())

    def test_missing_detail(self):
        self.assertTrue(consequential_errors(self.base, self.meta, self.top, self.cfg, self.today))

    def test_cli_fails_before_publication(self):
        self.meta.update(national={'pop': 100}, data_through='2026-11-12')
        self.cfg.update(name='Fixture', rainfall={'season_start_month': 11, 'season_end_month': 4})
        for row in self.top['adm2'].values():
            row.update(l=1, e=20, t=10)
        self.detail['adm4']['F']['ew'] = [4]*5
        self.errors()  # écrit le fichier de détail invalide
        for name, content in [('meta.json', self.meta), ('metrics/top.json', self.top),
                              ('index.json', {}), ('catalogue.json', {}),
                              ('geo/adm1.geojson', {}), ('geo/adm2.geojson', {})]:
            path = self.base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(content), encoding='utf-8')
        with patch.object(validate, 'country_docs_dir', return_value=self.base), \
             patch.object(validate, 'load_config', return_value=self.cfg), \
             patch.object(sys, 'argv', ['validate.py', '--skip-age']), \
             contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as failure:
            validate.main()
        self.assertEqual(failure.exception.code, 1)

    def test_workflow_gate_precedes_upload_and_is_mandatory(self):
        path = Path(__file__).resolve().parents[1] / '.github/workflows/update-data.yml'
        jobs = yaml.safe_load(path.read_text(encoding='utf-8'))['jobs']
        steps = jobs['build']['steps']
        gate = next(i for i, s in enumerate(steps) if 'scripts/validate.py' in s.get('run', ''))
        upload = next(i for i, s in enumerate(steps) if s.get('uses', '').startswith('actions/upload-pages-artifact@'))
        self.assertLess(gate, upload)
        self.assertNotIn('continue-on-error', steps[gate])
        self.assertNotIn('||', steps[gate]['run'])
        self.assertEqual(jobs['deploy']['needs'], 'build')


if __name__ == '__main__':
    unittest.main()
