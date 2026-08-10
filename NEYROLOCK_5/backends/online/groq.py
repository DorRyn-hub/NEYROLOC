"""Groq backend — облако, OpenAI-совместимый API."""

from __future__ import annotations

from collections.abc import Iterator
from importlib.util import find_spec

from ..base import Backend, Message


REQUEST_TIMEOUT_SECONDS = 120.0


class GroqBackend(Backend):
    id = "groq"
    display_name = "Groq"
    description = "Облако, бесплатно, очень быстро"
    category = "online"
    config_fields = [
        ("api_key", "API-ключ Groq", "password"),
    ]

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, config=None) -> None:
        super().__init__(config)
        self._client = None

    @classmethod
    def is_available(cls) -> bool:
        try:
            return find_spec("openai") is not None
        except (ImportError, ValueError):
            return False

    def _client_obj(self):
        from openai import OpenAI

        with self._state_lock:
            self._ensure_open()
            api_key = self.config.get("api_key")
            if not api_key:
                raise RuntimeError("Не указан API-ключ Groq.")
            if self._client is None:
                self._client = OpenAI(
                    api_key=api_key,
                    base_url=self.BASE_URL,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    max_retries=2,
                )
            return self._client

    def list_models(self) -> list[str]:
        try:
            models = self._client_obj().models.list()
            return sorted(
                {
                    str(model.id)
                    for model in models.data
                    if getattr(model, "id", None)
                }
            )
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Не удалось получить список моделей Groq ({type(exc).__name__})."
            ) from exc

    def generate(self, messages: list[Message], temperature: float = 0.7) -> Iterator[str]:
        self._begin_generation()
        temperature = self._validate_generation_request(messages, temperature)
        if not self.current_model:
            raise RuntimeError("Модель не выбрана.")

        stream = self._client_obj().chat.completions.create(
            model=self.current_model,
            messages=[m.as_dict() for m in messages],
            temperature=temperature,
            stream=True,
        )
        try:
            self._register_stream(stream)
            for chunk in stream:
                if self._generation_cancelled():
                    break
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content
        finally:
            self._finish_generation(stream)
            self._close_stream(stream)

    def close(self) -> None:
        super().close()
        with self._state_lock:
            client = self._client
            self._client = None
        if client is not None:
            self._close_stream(client)
