"""История чатов — JSON-файлы в ~/.neyrolock_5/history/."""

from __future__ import annotations

import datetime
from pathlib import Path

from backends.base import Message
from core.json_store import atomic_write_json, ensure_private_directory, read_json_object


HISTORY_DIR = Path.home() / ".neyrolock_5" / "history"
HISTORY_FORMAT_VERSION = 1
MAX_HISTORY_FILE_BYTES = 16 * 1024 * 1024
MAX_HISTORY_MESSAGES = 10_000
MAX_HISTORY_MESSAGE_CHARS = 1_000_000
MAX_HISTORY_TOTAL_CHARS = 8_000_000
_ALLOWED_ROLES = frozenset({"system", "user", "assistant"})


class ChatSession:
    """Одна сессия диалога."""

    def __init__(self, system_prompt: str = "") -> None:
        self.messages: list[Message] = []
        if system_prompt:
            self.messages.append(Message("system", system_prompt))

    def add_user(self, text: str) -> None:
        self.messages.append(Message("user", text))

    def add_assistant(self, text: str) -> None:
        self.messages.append(Message("assistant", text))

    def reset(self, system_prompt: str = "") -> None:
        self.messages = []
        if system_prompt:
            self.messages.append(Message("system", system_prompt))

    def visible_messages(self) -> list[Message]:
        """Сообщения, которые надо показывать пользователю (без system)."""
        return [m for m in self.messages if m.role != "system"]

    def to_dict(self) -> dict:
        return {
            "version": HISTORY_FORMAT_VERSION,
            "messages": [m.as_dict() for m in self.messages],
            "saved_at": datetime.datetime.now().astimezone().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatSession":
        if not isinstance(data, dict):
            raise ValueError("Корнем истории чата должен быть JSON-объект.")
        version = data.get("version", HISTORY_FORMAT_VERSION)
        if version != HISTORY_FORMAT_VERSION:
            raise ValueError(f"Неподдерживаемая версия истории чата: {version!r}.")

        raw_messages = data.get("messages", [])
        if not isinstance(raw_messages, list):
            raise ValueError("Поле messages должно быть списком.")
        if len(raw_messages) > MAX_HISTORY_MESSAGES:
            raise ValueError(
                f"В истории слишком много сообщений (максимум {MAX_HISTORY_MESSAGES})."
            )

        session = cls()
        total_chars = 0
        messages: list[Message] = []
        for index, item in enumerate(raw_messages):
            if not isinstance(item, dict):
                raise ValueError(f"Сообщение #{index + 1} должно быть объектом.")
            role = item.get("role")
            content = item.get("content")
            if role not in _ALLOWED_ROLES:
                raise ValueError(f"Недопустимая роль в сообщении #{index + 1}.")
            if not isinstance(content, str):
                raise ValueError(f"Текст сообщения #{index + 1} должен быть строкой.")
            if len(content) > MAX_HISTORY_MESSAGE_CHARS:
                raise ValueError(f"Сообщение #{index + 1} слишком большое.")
            total_chars += len(content)
            if total_chars > MAX_HISTORY_TOTAL_CHARS:
                raise ValueError("Суммарный размер истории чата слишком большой.")
            messages.append(Message(role, content))
        session.messages = messages
        return session


def save_session(session: ChatSession, name: str | None = None) -> Path:
    if not isinstance(session, ChatSession):
        raise TypeError("session должен быть объектом ChatSession.")
    ensure_private_directory(HISTORY_DIR)
    if name is None:
        name = datetime.datetime.now().strftime("chat_%Y%m%d_%H%M%S_%f")
    name = str(name).strip()
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError("Имя истории должно быть простым именем файла.")
    if not name.lower().endswith(".json"):
        name += ".json"
    path = HISTORY_DIR / name
    payload = session.to_dict()
    # Validate before writing so every successfully saved file is guaranteed to
    # satisfy the same schema and logical limits as load_session().
    ChatSession.from_dict(payload)
    atomic_write_json(
        path,
        payload,
        mode=0o600,
        max_bytes=MAX_HISTORY_FILE_BYTES,
    )
    return path


def load_session(path: Path) -> ChatSession:
    data = read_json_object(Path(path), max_bytes=MAX_HISTORY_FILE_BYTES)
    return ChatSession.from_dict(data)


def list_sessions() -> list[Path]:
    if not HISTORY_DIR.exists():
        return []
    try:
        sessions = [path for path in HISTORY_DIR.glob("*.json") if path.is_file()]
    except OSError:
        return []
    return sorted(sessions, key=lambda path: path.name, reverse=True)
