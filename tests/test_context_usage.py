from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "NEYROLOCK_5"
sys.path.insert(0, str(APP_ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from backends.base import (  # noqa: E402
    BackendConfig,
    ContextUsage,
    Message,
    estimate_message_tokens,
    estimate_text_tokens,
)
from backends.local_gguf import LocalGGUFBackend  # noqa: E402


class _FakeLlama:
    metadata = {
        "tokenizer.chat_template": (
            "{% for message in messages %}"
            "<|{{ message['role'] }}|>{{ message['content'] }}"
            "{% endfor %}<|assistant|>"
        )
    }

    @staticmethod
    def token_eos() -> int:
        return 2

    @staticmethod
    def token_bos() -> int:
        return 1

    @staticmethod
    def detokenize(tokens, special=False) -> bytes:
        return b"</s>" if tokens == [2] else b"<s>"

    @staticmethod
    def tokenize(text: bytes, add_bos=True, special=False) -> list[int]:
        # A deterministic stand-in is sufficient to prove that the model
        # tokenizer path, not the fallback estimate, produced the result.
        count = max(1, len(text.decode("utf-8")) // 3)
        return list(range(count))


class ContextUsageTests(unittest.TestCase):
    def test_estimator_counts_unicode_roles_and_full_history(self) -> None:
        self.assertEqual(estimate_text_tokens(""), 0)
        self.assertGreaterEqual(estimate_text_tokens("привет"), 3)
        short = estimate_message_tokens([Message("user", "привет")])
        full = estimate_message_tokens(
            [
                Message("system", "Отвечай кратко"),
                Message("user", "привет"),
                Message("assistant", "Здравствуйте!"),
            ]
        )
        self.assertGreater(full, short)

    def test_context_usage_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            ContextUsage(-1, 8192)
        with self.assertRaises(ValueError):
            ContextUsage(1, 0)

    def test_local_backend_uses_configured_limit_before_model_load(self) -> None:
        backend = LocalGGUFBackend(BackendConfig({"n_ctx": "16384"}))
        usage = backend.context_usage([Message("user", "Тест")])
        self.assertEqual(usage.max_tokens, 16384)
        self.assertFalse(usage.exact)
        self.assertGreater(usage.used_tokens, 0)

    def test_local_backend_uses_loaded_gguf_chat_template_tokenizer(self) -> None:
        backend = LocalGGUFBackend(BackendConfig({"n_ctx": "8192"}))
        backend._llm = _FakeLlama()
        backend._loaded_n_ctx = 4096
        usage = backend.context_usage(
            [Message("system", "Правила"), Message("user", "Привет")]
        )
        self.assertEqual(usage.max_tokens, 4096)
        self.assertTrue(usage.exact)
        self.assertGreater(usage.used_tokens, 0)

    def test_local_runtime_speed_comes_from_loaded_tokenizer(self) -> None:
        backend = LocalGGUFBackend(
            BackendConfig({"n_ctx": "8192", "n_gpu_layers": "10"})
        )
        backend._llm = _FakeLlama()
        backend._loaded_n_ctx = 8192
        backend._loaded_settings = ("/tmp/model.gguf", 8192, 10)

        backend.record_generation("Реальный ответ модели", 2.0)
        metrics = backend.runtime_metrics()

        self.assertEqual(metrics.context_window, 8192)
        self.assertEqual(metrics.gpu_layers, 10)
        self.assertTrue(metrics.speed_exact)
        self.assertIsNotNone(metrics.tokens_per_second)
        self.assertGreater(metrics.tokens_per_second, 0)


if __name__ == "__main__":
    unittest.main()
