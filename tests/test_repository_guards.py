import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RepositoryGuardsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Test User')
        self.git('config', 'user.email', 'test@example.invalid')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode().strip()

    def staged(self, name, content):
        (self.repo / name).write_text(content)
        self.git('add', '--', name)

    def check(self):
        return subprocess.run(['python3', str(ROOT / 'scripts/check_repository.py'), '--index'],
                              cwd=self.repo, capture_output=True, text=True)

    def test_safe_source_passes(self):
        self.staged('main.py', 'print("hello")\n')
        self.assertEqual(self.check().returncode, 0)

    def test_private_file_cannot_be_force_staged(self):
        self.staged('.env', 'EXAMPLE=value\n')
        self.assertNotEqual(self.check().returncode, 0)

    def test_secret_is_blocked_without_value_in_output(self):
        value = 'ghp_' + 'Ab3dE5fGh7IjK9LmN1OpQ3rSt5UvW7xYz9Ab'
        self.staged('main.py', 'credential = "' + value + '"\n')
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(value, result.stdout + result.stderr)

    def test_disallowed_attribution_is_blocked(self):
        self.staged('README.md', ''.join(map(chr, [67, 111, 100, 101, 120])))
        self.assertNotEqual(self.check().returncode, 0)

    def test_push_rejects_rewritten_branch_and_tag(self):
        self.staged('main.py', 'print(1)\n')
        self.git('commit', '-m', 'First')
        first = self.git('rev-parse', 'HEAD')
        self.staged('main.py', 'print(2)\n')
        self.git('commit', '-m', 'Second')
        second = self.git('rev-parse', 'HEAD')
        for ref in ['refs/heads/main', 'refs/tags/v1']:
            result = subprocess.run(['python3', str(ROOT / 'scripts/pre_push.py')], cwd=self.repo,
                                    input=f'{ref} {first} {ref} {second}\n', capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
