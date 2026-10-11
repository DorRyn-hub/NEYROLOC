"""Настройки приложения — JSON в ~/.neyrolock_5/config.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".neyrolock_5"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if CONFIG_FILE.exists():
            try:
                self.data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.data = {}
        else:
            self.data = {}

    def save(self) -> None:
        try:
            CONFIG_FILE.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    # --- глобальные параметры ---

    @property
    def active_backend(self) -> str | None:
        return self.data.get("active_backend")

    @active_backend.setter
    def active_backend(self, value: str | None) -> None:
        self.data["active_backend"] = value
        self.save()

    @property
    def temperature(self) -> float:
        return float(self.data.get("temperature", 0.7))

    @temperature.setter
    def temperature(self, value: float) -> None:
        self.data["temperature"] = float(value)
        self.save()

    @property
    def system_prompt(self) -> str:
        return self.data.get("system_prompt", "")

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        self.data["system_prompt"] = value
        self.save()

    # --- настройки конкретного backend'а ---

    def backend_config(self, backend_id: str) -> dict[str, Any]:
        return self.data.setdefault("backends", {}).setdefault(backend_id, {})

    def set_backend_config(self, backend_id: str, values: dict[str, Any]) -> None:
        self.data.setdefault("backends", {})[backend_id] = values
        self.save()

    def last_model(self, backend_id: str) -> str | None:
        return self.data.setdefault("last_model", {}).get(backend_id)

    def set_last_model(self, backend_id: str, model: str) -> None:
        self.data.setdefault("last_model", {})[backend_id] = model
        self.save()
