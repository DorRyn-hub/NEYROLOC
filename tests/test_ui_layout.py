from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "NEYROLOCK_5"
sys.path.insert(0, str(APP_ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication, QFrame, QLabel
except (ImportError, ModuleNotFoundError):
    PYSIDE_AVAILABLE = False
else:
    from core import config as config_module
    from core import history as history_module
    from core import model_library as model_library_module
    from ui import main_window as main_window_module
    from ui.main_window import MainWindow
    from ui.styles import APP_QSS

    PYSIDE_AVAILABLE = True


@unittest.skipUnless(PYSIDE_AVAILABLE, "PySide6 is required for UI layout tests")
class UiLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(APP_QSS)

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        temporary_root = Path(self.temporary.name)
        config_dir = temporary_root / "settings"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)
        config_file.write_text(
            json.dumps(
                {
                    "active_backend": "local_gguf",
                    "backends": {
                        "local_gguf": {
                            "model_path": str(
                                temporary_root
                                / "models"
                                / "a-very-long-model-name-Instruct-Q4_K_M.gguf"
                            ),
                            "n_ctx": "8192",
                            "n_gpu_layers": "10",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        self.patches = (
            mock.patch.object(config_module, "CONFIG_DIR", config_dir),
            mock.patch.object(config_module, "CONFIG_FILE", config_file),
            mock.patch.object(
                history_module,
                "HISTORY_DIR",
                temporary_root / "history",
            ),
            mock.patch.object(
                main_window_module,
                "HISTORY_DIR",
                temporary_root / "history",
            ),
            mock.patch.object(
                model_library_module.Path,
                "home",
                return_value=temporary_root,
            ),
        )
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.window = MainWindow()
        self.addCleanup(self._close_window)

    def _close_window(self) -> None:
        self.window.close()
        self.app.processEvents()

    def _show_at(self, width: int, height: int) -> None:
        self.window.resize(width, height)
        self.window.show()
        self.app.processEvents()

    def test_empty_state_and_composer_do_not_clip(self) -> None:
        for width, height in ((1280, 720), (640, 480), (1440, 900)):
            with self.subTest(size=(width, height)):
                self._show_at(width, height)
                card = self.window.chat.findChild(QFrame, "emptyState")
                self.assertIsNotNone(card)
                self.assertGreaterEqual(card.height(), card.sizeHint().height())
                for label in card.findChildren(QLabel):
                    self.assertGreaterEqual(
                        label.height(),
                        label.sizeHint().height(),
                        label.objectName(),
                    )

                composer = self.window.chat.findChild(QFrame, "composer")
                self.assertLessEqual(composer.height(), 96)
                self.assertTrue(self.window.chat._send_btn.isVisible())
                self.assertFalse(self.window.chat._stop_btn.isVisible())
                self.assertFalse(self.window.chat._stop_btn.isEnabled())

        compact_height = self.window.chat._input.height()
        self.window.chat._input.setPlainText("1\n2\n3\n4\n5\n6")
        self.app.processEvents()
        self.assertGreater(self.window.chat._input.height(), compact_height)
        self.assertLessEqual(self.window.chat._input.height(), 120)
        self.window.chat._input.clear()
        self.app.processEvents()
        self.assertEqual(self.window.chat._input.height(), compact_height)

        self.window.chat._input.setPlainText("длинная строка " * 80)
        self.app.processEvents()
        self.assertGreater(self.window.chat._input.height(), compact_height)
        self.assertLessEqual(self.window.chat._input.height(), 120)
        self.window.chat._input.clear()
        self.app.processEvents()
        self.assertEqual(self.window.chat._input.height(), compact_height)

        self.window.chat.set_busy(True)
        self.app.processEvents()
        self.assertFalse(self.window.chat._send_btn.isVisible())
        self.assertTrue(self.window.chat._stop_btn.isVisible())
        self.assertTrue(self.window.chat._stop_btn.isEnabled())

    def test_sidebar_is_scrollable_adaptive_and_reports_restored_backend(self) -> None:
        self._show_at(640, 480)
        compact_sidebar_width = self.window._sidebar_scroll.width()
        self.assertLessEqual(
            self.window.sidebar.width(),
            self.window._sidebar_scroll.viewport().width(),
        )

        self._show_at(1764, 1148)
        self.assertGreater(self.window._sidebar_scroll.width(), compact_sidebar_width)
        self.assertLessEqual(self.window._sidebar_scroll.width(), 420)

        self._show_at(900, 600)
        scrollbar = self.window._sidebar_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.app.processEvents()
        last_hint = next(
            label
            for label in self.window.sidebar.findChildren(QLabel)
            if label.text().startswith("Зависимости устанавливаются")
        )
        hint_top = last_hint.mapTo(
            self.window._sidebar_scroll.viewport(), QPoint(0, 0)
        ).y()
        self.assertGreaterEqual(hint_top, 0)
        self.assertLessEqual(
            hint_top + last_hint.height(),
            self.window._sidebar_scroll.viewport().height(),
        )

        model_path = self.window.sidebar._config_inputs["model_path"]
        self.assertEqual(model_path.toolTip(), model_path.text())
        self.assertEqual(
            self.window.sidebar._apply_btn.toolTip(),
            "Запросить список моделей",
        )
        self.assertNotIn("Выберите backend", self.window.statusBar().currentMessage())
        self.assertIn("Local GGUF", self.window.statusBar().currentMessage())


if __name__ == "__main__":
    unittest.main()
