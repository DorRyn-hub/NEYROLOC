"""История чатов — JSON-файлы в ~/.neyrolock_5/history/."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

from backends.base import Message


HISTORY_DIR = Path.home() / ".neyrolock_5" / "history"


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
            "messages": [m.as_dict() for m in self.messages],
            "saved_at": datetime.datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChatSession":
        session = cls()
        session.messages = [
            Message(m["role"], m["content"]) for m in data.get("messages", [])
        ]
        return session


def save_session(session: ChatSession, name: str | None = None) -> Path:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    if name is None:
        name = datetime.datetime.now().strftime("chat_%Y%m%d_%H%M%S")
    if not name.endswith(".json"):
        name += ".json"
    path = HISTORY_DIR / name
    path.write_text(
        json.dumps(session.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def load_session(path: Path) -> ChatSession:
    data = json.loads(path.read_text(encoding="utf-8"))
    return ChatSession.from_dict(data)


def list_sessions() -> list[Path]:
    if not HISTORY_DIR.exists():
        return []
    return sorted(HISTORY_DIR.glob("*.json"), reverse=True)
