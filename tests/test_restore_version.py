"""Exercise restoration against disposable bare remotes, without GitHub access."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/restore_version.py"
SPEC = importlib.util.spec_from_file_location("restore_version", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RestoreVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.repo = self.root / "work"
        self.remote.mkdir()
        self.repo.mkdir()
        self.run_git(self.remote, "init", "--bare")
        self.run_git(self.repo, "init", "-b", "main")
        self.run_git(self.repo, "config", "user.name", "Test User")
        self.run_git(self.repo, "config", "user.email", "test@example.invalid")
        self.run_git(self.repo, "remote", "add", "origin", str(self.remote))
        (self.repo / "snapshot.txt").write_text("first\n")
        self.run_git(self.repo, "add", ".")
        self.run_git(self.repo, "commit", "-m", "First")
        self.first = self.run_git(self.repo, "rev-parse", "HEAD")
        self.run_git(self.repo, "tag", "v1")
        (self.repo / "snapshot.txt").write_text("second\n")
        (self.repo / "new.txt").write_text("only in second\n")
        self.run_git(self.repo, "add", ".")
        self.run_git(self.repo, "commit", "-m", "Second")
        self.second = self.run_git(self.repo, "rev-parse", "HEAD")
        self.run_git(self.repo, "tag", "v2")
        self.run_git(self.repo, "push", "origin", "main", "--tags")
        self.scanner = self.root / "check_repository.py"
        self.scanner.write_text("import sys\nassert sys.argv[1] == '--tree'\nassert len(sys.argv[2]) == 40\n")

    def run_git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              text=True, capture_output=True).stdout.strip()

    def restore(self, version):
        return MODULE.restore_version(self.repo, version, self.scanner)

    def remote_main(self):
        return self.run_git(self.remote, "rev-parse", "refs/heads/main")

    def test_round_trip_has_exact_trees_and_preserves_history(self):
        first_restore = self.restore("v1")
        self.assertEqual(first_restore["commit"], self.remote_main())
        self.assertEqual(self.run_git(self.repo, "rev-parse", first_restore["commit"] + "^{tree}"),
                         self.run_git(self.repo, "rev-parse", self.first + "^{tree}"))
        self.assertEqual(self.run_git(self.repo, "rev-parse", first_restore["commit"] + "^"), self.second)
        self.assertEqual(self.run_git(self.remote, "rev-parse", "refs/tags/" + first_restore["backup_tag"]), self.second)
        second_restore = self.restore(self.second)
        self.assertEqual(second_restore["commit"], self.remote_main())
        self.assertEqual(second_restore["tree"], self.run_git(self.repo, "rev-parse", self.second + "^{tree}"))
        self.assertEqual(self.run_git(self.repo, "rev-parse", second_restore["commit"] + "^"), first_restore["commit"])
        self.assertNotEqual(first_restore["backup_tag"], second_restore["backup_tag"])
        self.assertEqual(self.run_git(self.repo, "rev-parse", "HEAD"), self.second)
        self.assertEqual((self.repo / "snapshot.txt").read_text(), "second\n")
        self.assertEqual(self.run_git(self.repo, "status", "--porcelain"), "")

    def test_invalid_versions_do_not_publish(self):
        for value in ["", "-x", "HEAD~1", "missing", "v1\nother", "v1^{tree}"]:
            with self.subTest(value=value), self.assertRaises((ValueError, RuntimeError)):
                self.restore(value)
        self.assertEqual(self.remote_main(), self.second)
        self.assertEqual(self.run_git(self.remote, "tag", "-l", "before-restore/*"), "")

    def test_nonancestor_is_rejected(self):
        unrelated = self.run_git(self.repo, "commit-tree", self.first + "^{tree}", "-m", "Unrelated")
        with self.assertRaises(RuntimeError):
            self.restore(unrelated)
        self.assertEqual(self.remote_main(), self.second)

    def test_unsafe_snapshot_is_rejected(self):
        self.scanner.write_text("import sys\nsys.exit(1)\n")
        with self.assertRaisesRegex(RuntimeError, "security check failed"):
            self.restore("v1")
        self.assertEqual(self.remote_main(), self.second)
        self.assertEqual(self.run_git(self.remote, "tag", "-l", "before-restore/*"), "")

    def test_remote_race_rejects_whole_atomic_push(self):
        racer = self.root / "racer"
        subprocess.run(["git", "clone", "--branch", "main", str(self.remote), str(racer)],
                       check=True, capture_output=True)
        self.run_git(racer, "config", "user.name", "Test User")
        self.run_git(racer, "config", "user.email", "test@example.invalid")
        (racer / "raced.txt").write_text("concurrent update\n")
        self.run_git(racer, "add", ".")
        self.run_git(racer, "commit", "-m", "Concurrent update")
        racer_sha = self.run_git(racer, "rev-parse", "HEAD")
        self.scanner.write_text(
            "import subprocess\n"
            f"subprocess.run(['git', '-C', {str(racer)!r}, 'push', 'origin', 'main'], check=True)\n"
        )
        with self.assertRaises(RuntimeError):
            self.restore("v1")
        self.assertEqual(self.remote_main(), racer_sha)
        self.assertEqual(self.run_git(self.remote, "tag", "-l", "before-restore/*"), "")


if __name__ == "__main__":
    unittest.main()
