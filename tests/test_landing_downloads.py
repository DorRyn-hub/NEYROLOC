from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LANDING_PAGE = PROJECT_ROOT / "deploy" / "landing.html"
DEPLOY_SCRIPT = PROJECT_ROOT / "deploy" / "deploy_phase2.sh"


class DownloadMarkupParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.platforms: dict[str, dict[str, str | bool | None]] = {}
        self._current_platform: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        platform = attributes.get("data-platform")
        if platform is None:
            return
        self._current_platform = platform
        self._text = []
        self.platforms[platform] = {
            "tag": tag,
            "href": attributes.get("href"),
            "has_download": "download" in attributes,
            "aria-disabled": attributes.get("aria-disabled"),
            "text": "",
        }

    def handle_data(self, data: str) -> None:
        if self._current_platform is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._current_platform is None:
            return
        expected_tag = self.platforms[self._current_platform]["tag"]
        if tag != expected_tag:
            return
        text = " ".join(" ".join(self._text).split())
        self.platforms[self._current_platform]["text"] = text
        self._current_platform = None
        self._text = []


class LandingDownloadsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = LANDING_PAGE.read_text(encoding="utf-8")
        self.parser = DownloadMarkupParser()
        self.parser.feed(self.html)

    def test_four_platform_downloads_have_canonical_routes(self) -> None:
        expected = {
            "linux": "/download/NEYROLOC-Linux.AppImage",
            "macos": "/download/NEYROLOC-macOS.dmg",
            "windows": "/download/NEYROLOC-Windows.zip",
            "android": "/download/NEYROLOC-Android.apk",
        }

        for platform, route in expected.items():
            with self.subTest(platform=platform):
                card = self.parser.platforms[platform]
                self.assertEqual(card["tag"], "a")
                self.assertEqual(card["href"], route)
                self.assertTrue(card["has_download"])
                self.assertIsNone(card["aria-disabled"])

    def test_iphone_is_not_a_link_and_has_publication_status(self) -> None:
        card = self.parser.platforms["iphone"]
        self.assertEqual(card["tag"], "div")
        self.assertIsNone(card["href"])
        self.assertEqual(card["aria-disabled"], "true")
        self.assertIn("Скоро будет опубликовано в общий доступ.", card["text"])

    def test_deploy_script_installs_every_download_and_keeps_old_android_route(self) -> None:
        script = DEPLOY_SCRIPT.read_text(encoding="utf-8")
        destinations = {
            "NEYROLOC-Linux.AppImage",
            "NEYROLOC-macOS.dmg",
            "NEYROLOC-Windows.zip",
            "NEYROLOC-Android.apk",
            "android",
        }
        installed = set(
            re.findall(r"/var/www/neyroloc/download/([A-Za-z0-9._-]+)", script)
        )
        self.assertTrue(destinations.issubset(installed))
        self.assertIn('if [[ ! -s "$required_file" ]]', script)

    def test_landing_and_deploy_use_bundled_onest_400_and_700(self) -> None:
        script = DEPLOY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("font-family:'Onest'", self.html)
        self.assertIn("/fonts/Onest-Regular.ttf", self.html)
        self.assertIn("/fonts/Onest-Bold.ttf", self.html)
        weights = {
            int(value)
            for value in re.findall(r"font-weight\s*:\s*(\d+)", self.html)
        }
        self.assertEqual(weights, {400, 700})
        self.assertIn("/tmp/Onest-Regular.ttf", script)
        self.assertIn("/tmp/Onest-Bold.ttf", script)
        self.assertIn(
            "/var/www/neyroloc/fonts/Onest-Regular.ttf",
            script,
        )
        self.assertIn(
            "/var/www/neyroloc/fonts/Onest-Bold.ttf",
            script,
        )


if __name__ == "__main__":
    unittest.main()
