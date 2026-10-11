"""Local guards must survive a snapshot that predates versioning tools."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PersistentHooksTests(unittest.TestCase):
    def test_guards_survive_removal_of_versioned_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            def git(*args, check=True):
                return subprocess.run(['git', '-C', str(repo), *args],
                                      check=check, capture_output=True, text=True)
            git('init', '-b', 'main')
            git('config', 'user.name', 'Test User')
            git('config', 'user.email', 'test@example.invalid')
            shutil.copytree(ROOT / 'scripts', repo / 'scripts')
            shutil.copy2(ROOT / '.gitleaks.toml', repo / '.gitleaks.toml')
            subprocess.run(['python3', str(repo / 'scripts/install_hooks.py')],
                           cwd=repo, check=True, capture_output=True)
            hook_path = Path(git('config', '--get', 'core.hooksPath').stdout.strip())
            self.assertEqual(hook_path, repo / '.git/project-hooks')
            shutil.rmtree(repo / 'scripts')
            shutil.rmtree(repo / '.githooks')
            (repo / '.gitleaks.toml').unlink()
            self.assertTrue((hook_path / 'pre-commit').is_file())
            self.assertTrue((repo / '.git/project-guards/gitleaks.toml').is_file())
            (repo / '.env').write_text('EXAMPLE=value\n')
            git('add', '.env')
            blocked = git('commit', '-m', 'Unsafe snapshot', check=False)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn('private/artifact path', blocked.stdout + blocked.stderr)
            git('rm', '--cached', '.env')
            (repo / 'main.py').write_text('print("safe")\n')
            git('add', 'main.py')
            git('commit', '-m', 'Safe snapshot')
            self.assertEqual(git('log', '-1', '--format=%s').stdout.strip(), 'Safe snapshot')


if __name__ == '__main__':
    unittest.main()
