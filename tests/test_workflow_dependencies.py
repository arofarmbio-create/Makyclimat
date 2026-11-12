"""Les dépendances Python directes des workflows ont une version exacte."""
from pathlib import Path
import re
import shlex
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def unpinned(tokens):
    errors = []
    it = iter(tokens)
    for token in it:
        if token in ('-r', '--requirement'):
            path = ROOT / next(it)
            for line in path.read_text(encoding='utf-8').splitlines():
                line = line.split('#')[0].strip()
                if line:
                    errors.extend(unpinned(shlex.split(line)))
        elif not re.fullmatch(r'[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?==[A-Za-z0-9_.+!-]+', token):
            errors.append(token)
    return errors


class WorkflowDependencies(unittest.TestCase):
    def test_all_python_installs_pinned(self):
        installs = 0
        for path in (ROOT / '.github/workflows').glob('*.yml'):
            workflow = yaml.safe_load(path.read_text(encoding='utf-8'))
            for job in workflow.get('jobs', {}).values():
                for step in job.get('steps', []):
                    for line in step.get('run', '').replace('\\\n', ' ').splitlines():
                        match = re.search(r'\bpip(?:3)? install (.+)', line)
                        if match:
                            installs += 1
                            with self.subTest(workflow=path.name, command=line):
                                self.assertEqual(unpinned(shlex.split(match[1])), [])
        self.assertGreater(installs, 30)


if __name__ == '__main__':
    unittest.main()
