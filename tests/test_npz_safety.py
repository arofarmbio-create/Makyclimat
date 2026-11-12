"""Tous les lecteurs NumPy refusent explicitement la désérialisation pickle."""
import ast
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import load_grid


class NpzSafety(unittest.TestCase):
    def test_readers_explicitly_disable_pickle(self):
        count = 0
        for path in (ROOT / 'scripts').rglob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8-sig'))
            aliases = {'np', 'numpy'}
            direct = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    aliases.update(a.asname or a.name for a in n.names if a.name == 'numpy')
                if isinstance(n, ast.ImportFrom) and n.module == 'numpy':
                    direct.update(a.asname or a.name for a in n.names if a.name == 'load')
            for n in ast.walk(tree):
                if not isinstance(n, ast.Call):
                    continue
                f = n.func
                is_load = (isinstance(f, ast.Name) and f.id in direct) or (
                    isinstance(f, ast.Attribute) and f.attr == 'load'
                    and isinstance(f.value, ast.Name) and f.value.id in aliases)
                if is_load:
                    count += 1
                    with self.subTest(path=path.name, line=n.lineno):
                        self.assertTrue(any(k.arg == 'allow_pickle' and
                            isinstance(k.value, ast.Constant) and k.value.value is False
                            for k in n.keywords))
        self.assertGreater(count, 20)

    def test_object_array_rejected_and_numeric_unicode_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input.npz'
            np.savez(path, value=np.array([{'unexpected': 1}], dtype=object))
            with self.assertRaises(ValueError):
                load_grid(path)
            np.savez(path, value=np.array([1.5]), dates=np.array(['2026-11-12']))
            data = load_grid(path)
            self.assertEqual(data['value'].tolist(), [1.5])
            self.assertEqual(data['dates'].tolist(), ['2026-11-12'])


if __name__ == '__main__':
    unittest.main()
