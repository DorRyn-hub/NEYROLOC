"""Workspace integration checks with isolated settings and an in-memory backend."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "NEYROLOCK_5"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton
except ImportError:
    QT_AVAILABLE = False
else:
    QT_AVAILABLE = True
    import core.config as config_module
    import ui.main_window as main_module
    import ui.sidebar as sidebar_module
    from backends.base import Backend, Message
    from core.model_library import DownloadedModel, ModelLibrary
    from ui.styles import APP_QSS
    from ui.typography import apply_application_typography

    class LocalFixture(Backend):
        id = "local_gguf"
        display_name = "Локальная модель"
        config_fields = [("model_path", "Модель", "file")]

        @classmethod
        def is_available(cls):
            return True

        def list_models(self):
            return ["fixture-model"]

        def prepare(self, progress=None):
            pass

        def generate(self, messages, temperature=0.7):
            yield "Тестовый "
            yield "ответ"

        def close(self):
            pass

    class CloudFixture(LocalFixture):
        id = "openai"
        category = "online"
        display_name = "Облачный источник"
        config_fields = [("api_key", "API-ключ", "password")]


@unittest.skipUnless(QT_AVAILABLE, "PySide6 is required")
class GraphiteWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        apply_application_typography(cls.app)
        cls.app.setStyleSheet(APP_QSS)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.library = ModelLibrary(root / "models")
        patches = [
            patch.object(config_module, "CONFIG_DIR", root),
            patch.object(config_module, "CONFIG_FILE", root / "config.json"),
            patch.object(main_module, "ModelLibrary", return_value=self.library),
            patch.object(main_module, "list_sessions", return_value=[]),
            patch.object(main_module, "ALL_BACKENDS", [LocalFixture, CloudFixture]),
            patch.object(sidebar_module, "ALL_BACKENDS", [LocalFixture, CloudFixture]),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.window = main_module.MainWindow()
        self.window.show()
        self.app.processEvents()
        self.addCleanup(self._close_window)

    def _close_window(self):
        self.window.close()
        self.app.processEvents()

    def _wait(self, predicate):
        for _ in range(100):
            self.app.processEvents()
            if predicate():
                return
            QTest.qWait(10)
        self.fail("Операция не завершилась")

    def _ready_backend(self):
        self.window.backend = LocalFixture()
        self.window.backend.set_model("fixture-model")
        self.window._model_ready = True
        self.window.chat.set_input_enabled(True)

    def test_navigation_preserves_settings_draft_and_conversation(self):
        self.window.sidebar.set_config_values({"model_path": "draft.gguf"})
        self.window.chat.set_messages([Message("user", "Вопрос")])
        for page in ("settings", "models", "chat"):
            self.window._navigate(page)
        self.assertEqual(self.window.sidebar.get_config_values()["model_path"], "draft.gguf")
        self.assertEqual(self.window.chat._bubbles[0].text(), "Вопрос")

    def test_loading_messages_removes_welcome_immediately(self):
        self.window.chat.set_messages([Message("assistant", "Ответ")])
        placeholders = [widget for widget in self.window.chat.findChildren(QLabel)
                        if widget.objectName() == "emptyTitle"]
        self.assertTrue(all(not label.isVisible() for label in placeholders))
        self.window.chat.clear_messages()
        self.window.chat.clear_messages()
        self.app.processEvents()
        placeholders = [self.window.chat._messages_layout.itemAt(i).widget()
                        for i in range(self.window.chat._messages_layout.count())]
        self.assertEqual(sum(bool(w and w.property("isPlaceholder")) for w in placeholders), 1)

    def test_disabled_composer_cannot_submit_by_enter(self):
        sent = []
        self.window.chat.sendRequested.connect(sent.append)
        self.window.chat._input.setPlainText("Вопрос")
        self.window.chat._on_submit()
        self.assertEqual(sent, [])
        self.assertEqual(self.window.chat._input.toPlainText(), "Вопрос")

    def test_prepare_stream_and_regenerate_complete_without_network(self):
        self.window.config.set_last_model("local_gguf", "fixture-model")
        self.window._on_apply_clicked()
        self._wait(lambda: self.window._model_ready)
        self.window._on_send("Вопрос")
        self.assertFalse(self.window.sidebar._model_combo.isEnabled())
        self.assertFalse(self.window.sidebar.connection_page.isEnabled())
        self.assertTrue(self.window.chat._busy)
        self._wait(lambda: self.window._worker is None)
        self.assertEqual(self.window.session.messages[-1].content, "Тестовый ответ")
        self.assertTrue(self.window.sidebar._model_combo.isEnabled())
        self.window._on_regenerate()
        self._wait(lambda: self.window._worker is None)
        self.assertEqual([m.role for m in self.window.session.messages], ["user", "assistant"])

    def test_provider_switch_blocks_sending_with_old_backend(self):
        self._ready_backend()
        self.window._choose_backend("openai")
        self.assertFalse(self.window._model_ready)
        self.assertFalse(self.window.chat._input_enabled)
        self.window._on_send("Вопрос")
        self.assertEqual(self.window.session.visible_messages(), [])
        self.assertIn("облачному", self.window.sidebar._privacy.text())
        self.assertEqual(self.window.chat._model_caption.text(), "Модель не подключена")

    def test_model_selection_waits_until_prepare_finishes(self):
        self._ready_backend()
        self.window._prepare_worker = object()
        self.window._on_model_changed("next-model")
        self.assertEqual(self.window.backend.current_model, "fixture-model")
        self.assertEqual(self.window._pending_model, "next-model")
        self.window._prepare_worker = None
        self.window._pending_model = None

    def test_same_model_can_be_prepared_again_after_failure(self):
        self._ready_backend()
        self.window._model_ready = False
        self.window._on_model_changed("fixture-model")
        self.assertIsNotNone(self.window._prepare_worker)
        self._wait(lambda: self.window._prepare_worker is None)
        self.assertTrue(self.window._model_ready)

    def test_phone_modal_restores_current_page_selection(self):
        self.window._navigate("models")
        with patch.object(self.window, "_on_remote_access"):
            self.window.workspace_nav._pages["phone"].click()
        self.assertEqual(self.window._pages.currentIndex(), 1)
        self.assertTrue(self.window.workspace_nav._pages["models"].isChecked())

    def test_download_progress_survives_navigation_and_error_stays_visible(self):
        page = self.window._library_page
        self.window._navigate("models")
        page.set_downloading(True)
        page.set_download_progress(42, 420, 1000)
        self.window._download_worker = object()
        self.window._navigate("chat")
        self.window._navigate("models")
        self.assertIs(self.window._library_page, page)
        self.assertEqual(page._download_progress.value(), 42)
        self.assertFalse(page._card_actions[0].isEnabled())
        self.window._download_worker = None
        page.set_downloading(False)
        page.set_download_status("Ошибка скачивания: тест")
        self.assertTrue(page._download_panel.isVisible())
        self.assertFalse(page._spinner_timer.isActive())
        self.assertTrue(page._card_actions[0].isEnabled())

    def test_model_card_filters_and_activates_without_closing_page(self):
        page = self.window._library_page
        model = DownloadedModel("fixture", "fixture/repo", "fixture.gguf", Path(self.directory.name)/"fixture.gguf", 300)
        with patch.object(self.library, "list_downloaded", return_value=[model]):
            self.window._navigate("models")
        page._filter_edit.setText("absent")
        self.assertTrue(page._empty_library.isVisible())
        page._filter_edit.setText("fixture")
        card = page._downloaded_card_rows[0][0]
        self.assertTrue(card.isVisible())
        self.assertFalse(page._empty_library.isVisible())
        selected = []
        page.useModelRequested.disconnect()
        page.useModelRequested.connect(selected.append)
        card.findChild(QPushButton).click()
        self.assertEqual(selected, [str(model.path)])
        self.assertTrue(page.isVisible())
        self.assertFalse(page.isWindow())

    def test_short_window_keeps_settings_and_composer_accessible(self):
        self.window.resize(1000, 680)
        self.app.processEvents()
        settings = self.window.workspace_nav._pages["settings"]
        bottom = settings.mapTo(self.window, settings.rect().bottomRight())
        self.assertLess(bottom.y(), self.window.height())
        detail_bottom = self.window.workspace_nav.model.mapTo(
            self.window, self.window.workspace_nav.model.rect().bottomRight())
        self.assertLess(detail_bottom.y(), self.window.height())
        self.assertLessEqual(self.window.chat._input.width(), self.window.chat.width())


if __name__ == "__main__":
    unittest.main()
