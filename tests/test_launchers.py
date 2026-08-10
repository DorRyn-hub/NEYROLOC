from __future__ import annotations

import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def run_python(self, source: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-c", source],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_root_launcher_import_has_no_qt_or_ui_side_effects(self) -> None:
        source = """
import importlib.util
import sys
from pathlib import Path
path = Path('main.py').resolve()
spec = importlib.util.spec_from_file_location('neyroloc_root_launcher', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.APP_DIR.name == 'NEYROLOCK_5'
assert module.APP_DIR.is_dir()
assert 'PySide6' not in sys.modules
assert 'ui.main_window' not in sys.modules
print('OK')
"""
        result = self.run_python(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK", result.stdout)

    def test_active_backend_registry_imports_without_model_or_network(self) -> None:
        source = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path('NEYROLOCK_5').resolve()))
from backends import ALL_BACKENDS
assert [backend.id for backend in ALL_BACKENDS] == ['local_gguf', 'openai', 'groq']
assert 'llama_cpp' not in sys.modules
assert 'openai' not in sys.modules
for backend in ALL_BACKENDS:
    backend.is_available()
assert 'llama_cpp' not in sys.modules
assert 'openai' not in sys.modules
print('OK')
"""
        result = self.run_python(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK", result.stdout)

    def test_command_launcher_uses_override_and_not_archive(self) -> None:
        zsh = shutil.which("zsh")
        echo = shutil.which("echo")
        if not zsh or not echo:
            self.skipTest("zsh/echo is unavailable")
        launcher = PROJECT_ROOT / "START_NEYROLOC_NEW.command"
        env = os.environ.copy()
        env["NEYROLOC_PYTHON"] = echo
        result = subprocess.run(
            [zsh, str(launcher), "launch-check"],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(PROJECT_ROOT / "main.py"), result.stdout)
        self.assertIn("launch-check", result.stdout)
        self.assertNotIn("NEYROLOC_2", launcher.read_text(encoding="utf-8"))

    def test_macos_packaging_is_app_relative_and_safe_by_default(self) -> None:
        launcher = (PROJECT_ROOT / "packaging" / "launcher.c").read_text(encoding="utf-8")
        build_script = (PROJECT_ROOT / "packaging" / "build_app.sh").read_text(encoding="utf-8")
        standalone_script = (
            PROJECT_ROOT / "packaging" / "build_standalone_macos.sh"
        ).read_text(encoding="utf-8")
        self.assertNotIn("/Users/", launcher)
        self.assertNotIn("/Users/", standalone_script)
        self.assertIn("../Resources/app/main.py", launcher)
        self.assertIn("$PROJECT_DIR/dist", build_script)
        self.assertIn("--install", build_script)
        self.assertIn('MACOS_DEPLOYMENT_TARGET="15.0"', standalone_script)
        self.assertIn("3.10|3.11|3.12|3.13", standalone_script)
        self.assertIn("requirements-macos-build.txt", standalone_script)
        self.assertIn("codesign --force --deep --sign -", standalone_script)
        self.assertIn("verify_macos_target", standalone_script)

        result = subprocess.run(
            [str(PROJECT_ROOT / "packaging" / "build_app.sh"), "--help"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("local", build_script.lower())


if __name__ == "__main__":
    unittest.main()
