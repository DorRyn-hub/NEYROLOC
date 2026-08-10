from __future__ import annotations

import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "NEYROLOCK_5"
sys.path.insert(0, str(APP_ROOT))

from core import config as config_module  # noqa: E402
from core import history as history_module  # noqa: E402


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.config_dir = Path(self.temporary.name) / "settings"
        self.config_file = self.config_dir / "config.json"
        self.patches = (
            mock.patch.object(config_module, "CONFIG_DIR", self.config_dir),
            mock.patch.object(config_module, "CONFIG_FILE", self.config_file),
        )
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_defaults_are_safe_and_setters_persist(self) -> None:
        config = config_module.Config()
        self.assertIsNone(config.active_backend)
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.system_prompt, "")

        config.active_backend = "local_gguf"
        config.temperature = 5
        config.system_prompt = "Отвечай кратко"
        config.set_backend_config("local_gguf", {"n_ctx": "4096"})
        config.set_last_model("local_gguf", "model.gguf")

        reloaded = config_module.Config()
        self.assertEqual(reloaded.active_backend, "local_gguf")
        self.assertEqual(reloaded.temperature, 2.0)
        self.assertEqual(reloaded.system_prompt, "Отвечай кратко")
        self.assertEqual(reloaded.backend_config("local_gguf"), {"n_ctx": "4096"})
        self.assertEqual(reloaded.last_model("local_gguf"), "model.gguf")
        self.assertTrue(reloaded.save())
        self.assertEqual(stat.S_IMODE(self.config_file.stat().st_mode) & 0o077, 0)

    def test_invalid_json_falls_back_without_crashing(self) -> None:
        self.config_dir.mkdir(parents=True)
        self.config_file.write_text("{broken", encoding="utf-8")

        config = config_module.Config()

        self.assertEqual(config.data, {})
        self.assertIsNotNone(config.last_error)

    def test_invalid_temperature_is_rejected_or_normalized(self) -> None:
        self.config_dir.mkdir(parents=True)
        self.config_file.write_text(
            json.dumps({"temperature": "not-a-number"}),
            encoding="utf-8",
        )
        config = config_module.Config()
        self.assertEqual(config.temperature, 0.7)
        with self.assertRaises(ValueError):
            config.temperature = float("nan")


class HistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.history_dir = Path(self.temporary.name) / "history"
        patcher = mock.patch.object(history_module, "HISTORY_DIR", self.history_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_session_round_trip_and_visible_messages(self) -> None:
        session = history_module.ChatSession("Системная инструкция")
        session.add_user("Привет")
        session.add_assistant("Здравствуйте")

        path = history_module.save_session(session, "диалог")
        restored = history_module.load_session(path)

        self.assertEqual(path.name, "диалог.json")
        self.assertEqual(
            [message.as_dict() for message in restored.messages],
            [message.as_dict() for message in session.messages],
        )
        self.assertEqual(
            [message.role for message in restored.visible_messages()],
            ["user", "assistant"],
        )
        self.assertEqual(history_module.list_sessions(), [path])
        self.assertEqual(stat.S_IMODE(path.stat().st_mode) & 0o077, 0)

    def test_unsafe_name_and_invalid_schema_are_rejected(self) -> None:
        session = history_module.ChatSession()
        with self.assertRaises(ValueError):
            history_module.save_session(session, "../outside")
        with self.assertRaises(ValueError):
            history_module.ChatSession.from_dict(
                {"messages": [{"role": "tool", "content": "unexpected"}]}
            )
        with self.assertRaises(ValueError):
            history_module.ChatSession.from_dict({"version": 999, "messages": []})


if __name__ == "__main__":
    unittest.main()
