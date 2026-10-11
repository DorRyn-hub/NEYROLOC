"""Groq backend — облако, OpenAI-совместимый API."""

from __future__ import annotations

from collections.abc import Iterator

from ..base import Backend, Message


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
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def _client_obj(self):
        from openai import OpenAI

        api_key = self.config.get("api_key")
        if not api_key:
            raise RuntimeError("Не указан API-ключ Groq.")
        if self._client is None:
            self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        return self._client

    def list_models(self) -> list[str]:
        try:
            models = self._client_obj().models.list()
            return [m.id for m in models.data]
        except Exception:
            # Фолбэк — несколько ходовых моделей Groq.
            return [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
            ]

    def generate(self, messages: list[Message], temperature: float = 0.7) -> Iterator[str]:
        if not self.current_model:
            raise RuntimeError("Модель не выбрана.")

        stream = self._client_obj().chat.completions.create(
            model=self.current_model,
            messages=[m.as_dict() for m in messages],
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content
