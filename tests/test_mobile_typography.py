from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MOBILE_HTML = PROJECT_ROOT / "NEYROLOCK_5" / "resources" / "mobile.html"
REMOTE_SERVER = PROJECT_ROOT / "NEYROLOCK_5" / "core" / "remote_server.py"
ANDROID_ACTIVITY = (
    PROJECT_ROOT
    / "packaging"
    / "android"
    / "src"
    / "ru"
    / "dorryn"
    / "neyroloc"
    / "MainActivity.java"
)
ANDROID_BUILD = PROJECT_ROOT / "packaging" / "android" / "build_apk.sh"
FONT_DIR = PROJECT_ROOT / "NEYROLOCK_5" / "resources" / "fonts"


class MobileTypographyTests(unittest.TestCase):
    def test_bundled_onest_regular_bold_and_license_are_present(self) -> None:
        for filename in ("Onest-Regular.ttf", "Onest-Bold.ttf"):
            font = FONT_DIR / filename
            self.assertGreater(font.stat().st_size, 50_000)
            self.assertEqual(font.read_bytes()[:4], b"\x00\x01\x00\x00")

        license_text = (FONT_DIR / "OFL.txt").read_text(encoding="utf-8")
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", license_text)

    def test_pwa_uses_onest_with_only_regular_and_bold_weights(self) -> None:
        html = MOBILE_HTML.read_text(encoding="utf-8")

        self.assertEqual(html.count("@font-face"), 2)
        self.assertIn("url('/fonts/Onest-Regular.ttf')", html)
        self.assertIn("url('/fonts/Onest-Bold.ttf')", html)
        self.assertIn("--font-ui:'Onest'", html)
        self.assertIn("font-family:var(--font-ui)", html)
        self.assertNotIn("ui-monospace", html)
        self.assertNotIn("'SF Mono'", html)

        declared_weights = {
            int(weight)
            for weight in re.findall(r"font-weight\s*:\s*(\d+)", html)
        }
        self.assertEqual(declared_weights, {400, 700})

    def test_remote_server_exposes_both_bundled_font_routes(self) -> None:
        source = REMOTE_SERVER.read_text(encoding="utf-8")

        for style in ("Regular", "Bold"):
            path = f"/fonts/Onest-{style}.ttf"
            self.assertIn(path, source)
        self.assertGreaterEqual(source.count('"font/ttf"'), 2)
        self.assertIn("font-src 'self'", source)

    def test_pwa_reports_empty_generation_instead_of_silent_success(self) -> None:
        html = MOBILE_HTML.read_text(encoding="utf-8")

        self.assertIn("Модель не вернула ответ. Повторите запрос", html)

    def test_android_native_setup_uses_same_regular_and_bold_assets(self) -> None:
        activity = ANDROID_ACTIVITY.read_text(encoding="utf-8")
        build = ANDROID_BUILD.read_text(encoding="utf-8")

        self.assertIn('FONT_FAMILY = "Onest"', activity)
        self.assertIn('FONT_REGULAR_ASSET = "fonts/Onest-Regular.ttf"', activity)
        self.assertIn('FONT_BOLD_ASSET = "fonts/Onest-Bold.ttf"', activity)
        self.assertNotIn("Typeface.DEFAULT", activity)
        self.assertNotIn("Typeface.create(FONT_FAMILY", activity)
        self.assertIn("private void applyTypography(TextView view, boolean bold)", activity)
        self.assertIn("NEYROLOCK_5/resources/fonts", build)
        self.assertIn('for font_file in Onest-Regular.ttf Onest-Bold.ttf OFL.txt', build)
        self.assertIn('-A "$OUT/assets"', build)


if __name__ == "__main__":
    unittest.main()
