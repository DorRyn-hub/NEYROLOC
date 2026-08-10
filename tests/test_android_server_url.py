from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANDROID_ROOT = PROJECT_ROOT / "packaging" / "android"
SERVER_URL_SOURCE = ANDROID_ROOT / "src" / "ru" / "dorryn" / "neyroloc" / "ServerUrl.java"
MAIN_ACTIVITY_SOURCE = ANDROID_ROOT / "src" / "ru" / "dorryn" / "neyroloc" / "MainActivity.java"
SERVER_URL_TEST = ANDROID_ROOT / "tests" / "ru" / "dorryn" / "neyroloc" / "ServerUrlTest.java"


class AndroidServerUrlTests(unittest.TestCase):
    def test_pure_java_url_logic(self) -> None:
        javac = shutil.which("javac")
        java = shutil.which("java")
        if not javac or not java:
            self.skipTest("JDK is not installed")

        with tempfile.TemporaryDirectory() as temporary:
            compile_result = subprocess.run(
                [javac, "-d", temporary, str(SERVER_URL_SOURCE), str(SERVER_URL_TEST)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            test_result = subprocess.run(
                [java, "-cp", temporary, "ru.dorryn.neyroloc.ServerUrlTest"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(test_result.returncode, 0, test_result.stderr)
            self.assertIn("ServerUrlTest OK", test_result.stdout)

    def test_main_activity_compiles_against_android_api_when_available(self) -> None:
        javac = shutil.which("javac")
        sdk_root = Path(
            os.environ.get("ANDROID_SDK_ROOT")
            or os.environ.get("ANDROID_HOME")
            or Path.home() / "android-sdk"
        )
        android_jar = sdk_root / "platforms" / "android-36" / "android.jar"
        if not javac or not android_jar.is_file():
            self.skipTest("JDK or Android API 36 is not installed")

        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    javac,
                    "--release",
                    "8",
                    "-classpath",
                    str(android_jar),
                    "-d",
                    temporary,
                    str(SERVER_URL_SOURCE),
                    str(MAIN_ACTIVITY_SOURCE),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
