"""Базовый интерфейс backend'а."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
import math
import threading
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

    def __post_init__(self) -> None:
        if self.role not in {"system", "user", "assistant"}:
            raise ValueError(f"Недопустимая роль сообщения: {self.role!r}.")
        if not isinstance(self.content, str):
            raise TypeError("Текст сообщения должен быть строкой.")

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
        self._state_lock = threading.RLock()
        self._cancel_event = threading.Event()
        self._active_stream: Any = None
        self._closed = False

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """True, если установлены необходимые библиотеки."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Список доступных моделей. Может бросать исключение, если backend не сконфигурирован."""

    def set_model(self, model: str) -> None:
        model = str(model).strip()
        if not model:
            raise ValueError("Название модели не может быть пустым.")
        with self._state_lock:
            self._ensure_open()
            self.current_model = model

    def clear_model(self) -> None:
        """Clear a failed selection without reaching into backend internals."""
        with self._state_lock:
            self._ensure_open()
            self.current_model = None

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

    @property
    def closed(self) -> bool:
        with self._state_lock:
            return self._closed

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Backend уже закрыт.")

    def _begin_generation(self) -> None:
        with self._state_lock:
            self._ensure_open()
            self._cancel_event.clear()

    def _validate_generation_request(
        self,
        messages: list[Message],
        temperature: float,
    ) -> float:
        if not isinstance(messages, list) or not messages:
            raise ValueError("История сообщений пуста.")
        if any(not isinstance(message, Message) for message in messages):
            raise TypeError("messages должен содержать только объекты Message.")
        try:
            parsed_temperature = float(temperature)
        except (TypeError, ValueError) as exc:
            raise ValueError("Температура должна быть числом.") from exc
        if not math.isfinite(parsed_temperature):
            raise ValueError("Температура должна быть конечным числом.")
        return min(max(parsed_temperature, 0.0), 2.0)

    def _register_stream(self, stream: Any) -> None:
        with self._state_lock:
            self._ensure_open()
            self._active_stream = stream

    def _finish_generation(self, stream: Any) -> None:
        with self._state_lock:
            if self._active_stream is stream:
                self._active_stream = None

    def _generation_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    @staticmethod
    def _close_stream(stream: Any) -> None:
        close = getattr(stream, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                # Some generator implementations reject cross-thread close;
                # the cancellation event still stops at the next yielded chunk.
                pass

    def cancel(self) -> None:
        """Request cancellation and close the active provider stream if possible."""
        self._cancel_event.set()
        with self._state_lock:
            stream = self._active_stream
        if stream is not None:
            self._close_stream(stream)

    def close(self) -> None:
        """Освободить ресурсы (соединения, модели в памяти). По умолчанию ничего не делает."""
        with self._state_lock:
            self._closed = True
        self.cancel()
