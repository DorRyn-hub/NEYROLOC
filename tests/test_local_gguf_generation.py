from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "NEYROLOCK_5"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from backends.base import BackendConfig, Message  # noqa: E402
from backends.local_gguf import LocalGGUFBackend  # noqa: E402


class _FakeLlama:
    def __init__(self, streams: list[list[dict]]) -> None:
        self._streams = iter(streams)
        self.temperatures: list[float] = []

    def create_chat_completion(self, **kwargs):
        self.temperatures.append(kwargs["temperature"])
        return iter(next(self._streams))


class LocalGGUFGenerationTests(unittest.TestCase):
    @staticmethod
    def _backend(fake_llm: _FakeLlama) -> LocalGGUFBackend:
        backend = LocalGGUFBackend(BackendConfig())
        backend._llm = fake_llm
        backend.prepare = lambda progress=None: None
        return backend

    def test_empty_stream_retries_once_with_safe_temperature(self) -> None:
        backend = self._backend(
            _FakeLlama(
                [
                    [{"choices": [{"delta": {}}]}],
                    [{"choices": [{"delta": {"content": "Ответ"}}]}],
                ]
            )
        )

        result = list(backend.generate([Message("user", "Привет")], 2.0))

        self.assertEqual(result, ["Ответ"])
        self.assertEqual(backend._llm.temperatures, [2.0, 0.7])

    def test_two_empty_streams_raise_instead_of_silent_success(self) -> None:
        backend = self._backend(
            _FakeLlama(
                [
                    [{"choices": [{"delta": {"content": "   "}}]}],
                    [{"choices": [{"delta": {"content": ""}}]}],
                ]
            )
        )

        with self.assertRaisesRegex(RuntimeError, "без ответа"):
            list(backend.generate([Message("user", "Привет")], 0.4))

        self.assertEqual(backend._llm.temperatures, [0.4, 0.4])


if __name__ == "__main__":
    unittest.main()
