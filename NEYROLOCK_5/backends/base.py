"""Базовый интерфейс backend'а."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any


ProgressCallback = Callable[[str], None]

# Локальные модели (Ollama/LM Studio/GGUF) иногда не выдают EOS и уходят
# в бесконечное повторение (см. историю чата). Полностью безлимитная генерация
# в таком случае жрёт весь контекст мусором. SAFE_MAX_TOKENS — щедрый, но конечный
# потолок; SAFE_REPEAT_PENALTY снижает саму вероятность зацикливания.
SAFE_MAX_TOKENS = 4096
SAFE_REPEAT_PENALTY = 1.15


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class BackendConfig:
    """Произвольная конфигурация backend'а (API-ключ, base_url, путь к модели и т.д.).

    Хранится сериализуемой в config.json. Ключи — на усмотрение конкретного backend'а.
    """

    values: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.values[key] = value


class Backend(ABC):
    """Абстрактный backend для генерации ответов."""

    #: Уникальный идентификатор (используется в config.json).
    id: str = ""
    #: Человекочитаемое имя для UI.
    display_name: str = ""
    #: Краткое описание для боковой панели.
    description: str = ""
    #: "local" | "online" — используется UI для группировки списка backend'ов.
    category: str = "local"
    #: Список полей конфигурации, которые UI должен показать пользователю.
    #: Каждое поле — (key, label, kind), где kind ∈ {"text", "password", "file"}.
    config_fields: list[tuple[str, str, str]] = []

    def __init__(self, config: BackendConfig | None = None) -> None:
        self.config = config or BackendConfig()
        self.current_model: str | None = None

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """True, если установлены необходимые библиотеки."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Список доступных моделей. Может бросать исключение, если backend не сконфигурирован."""

    def set_model(self, model: str) -> None:
        self.current_model = model

    def prepare(self, progress: ProgressCallback | None = None) -> None:
        """Подготовка ресурсов: скачать модель, загрузить веса в память и т.п.

        Вызывается из UI после выбора модели — крутится в QThread, поэтому
        блокирующие операции допустимы. Отчёт о прогрессе передаётся через
        ``progress("сообщение")``. По умолчанию ничего не делает.
        """
        return None

    @abstractmethod
    def generate(
        self,
        messages: list[Message],
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """Сгенерировать ответ, выдавая фрагменты текста по мере поступления.

        Должен быть синхронным итератором — UI крутит его в QThread.
        """

    def close(self) -> None:
        """Освободить ресурсы (соединения, модели в памяти). По умолчанию ничего не делает."""
