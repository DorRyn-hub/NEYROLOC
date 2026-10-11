"""OpenAI backend (или любой OpenAI-совместимый сервер через base_url)."""

from __future__ import annotations

from collections.abc import Iterator

from ..base import Backend, Message


class OpenAIBackend(Backend):
    id = "openai"
    display_name = "OpenAI"
    description = "Облако, платно (или OpenAI-совместимый сервер)"
    category = "online"
    config_fields = [
        ("api_key", "API-ключ", "password"),
        ("base_url", "Base URL (необязательно)", "text"),
    ]

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
            raise RuntimeError("Не указан API-ключ OpenAI.")
        if self._client is None:
            kwargs: dict = {"api_key": api_key}
            base_url = self.config.get("base_url")
            if base_url:
                kwargs["base_url"] = base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def list_models(self) -> list[str]:
        try:
            models = self._client_obj().models.list()
            return sorted({m.id for m in models.data})
        except Exception:
            return [
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4.1",
                "gpt-4.1-mini",
                "o4-mini",
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
