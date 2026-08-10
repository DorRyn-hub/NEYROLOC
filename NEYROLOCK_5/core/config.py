"""Настройки приложения — JSON в ~/.neyrolock_5/config.json."""

from __future__ import annotations

import math
import threading
from pathlib import Path
from typing import Any

from core.json_store import (
    JsonStoreError,
    atomic_write_json,
    ensure_private_directory,
    read_json_object,
)


CONFIG_DIR = Path.home() / ".neyrolock_5"
CONFIG_FILE = CONFIG_DIR / "config.json"
MAX_CONFIG_BYTES = 2 * 1024 * 1024


class Config:
    def __init__(self) -> None:
        ensure_private_directory(CONFIG_DIR)
        self._lock = threading.RLock()
        self.data: dict[str, Any] = {}
        self.last_error: str | None = None
        self.load()

    def load(self) -> None:
        with self._lock:
            self.last_error = None
            if not CONFIG_FILE.exists():
                self.data = {}
                return
            try:
                self.data = read_json_object(CONFIG_FILE, max_bytes=MAX_CONFIG_BYTES)
                try:
                    CONFIG_FILE.chmod(0o600)
                except OSError:
                    pass
            except (OSError, JsonStoreError) as exc:
                self.data = {}
                self.last_error = f"Не удалось загрузить настройки: {exc}"

    def save(self) -> bool:
        """Persist current settings atomically.

        Callers historically did not handle write errors, so the method keeps
        that API safe and reports failure through its return value and
        ``last_error`` instead of crashing the GUI.
        """
        with self._lock:
            try:
                atomic_write_json(CONFIG_FILE, self.data, mode=0o600)
            except (OSError, TypeError, ValueError) as exc:
                self.last_error = f"Не удалось сохранить настройки: {exc}"
                return False
            self.last_error = None
            return True

    # --- глобальные параметры ---

    @property
    def active_backend(self) -> str | None:
        value = self.data.get("active_backend")
        return value if isinstance(value, str) and value else None

    @active_backend.setter
    def active_backend(self, value: str | None) -> None:
        with self._lock:
            self.data["active_backend"] = value if value else None
            self.save()

    @property
    def temperature(self) -> float:
        try:
            value = float(self.data.get("temperature", 0.7))
        except (TypeError, ValueError):
            return 0.7
        if not math.isfinite(value):
            return 0.7
        return min(max(value, 0.0), 2.0)

    @temperature.setter
    def temperature(self, value: float) -> None:
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Температура должна быть числом.") from exc
        if not math.isfinite(parsed):
            raise ValueError("Температура должна быть конечным числом.")
        with self._lock:
            self.data["temperature"] = min(max(parsed, 0.0), 2.0)
            self.save()

    @property
    def system_prompt(self) -> str:
        value = self.data.get("system_prompt", "")
        return value if isinstance(value, str) else ""

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        with self._lock:
            self.data["system_prompt"] = str(value)
            self.save()

    # --- настройки конкретного backend'а ---

    def backend_config(self, backend_id: str) -> dict[str, Any]:
        with self._lock:
            backends = self.data.get("backends")
            if not isinstance(backends, dict):
                backends = {}
                self.data["backends"] = backends
            values = backends.get(backend_id)
            if not isinstance(values, dict):
                values = {}
                backends[backend_id] = values
            return values

    def set_backend_config(self, backend_id: str, values: dict[str, Any]) -> None:
        if not backend_id:
            raise ValueError("backend_id не может быть пустым.")
        if not isinstance(values, dict):
            raise TypeError("values должен быть словарём.")
        with self._lock:
            backends = self.data.get("backends")
            if not isinstance(backends, dict):
                backends = {}
                self.data["backends"] = backends
            backends[backend_id] = dict(values)
            self.save()

    def last_model(self, backend_id: str) -> str | None:
        with self._lock:
            models = self.data.get("last_model")
            if not isinstance(models, dict):
                models = {}
                self.data["last_model"] = models
            value = models.get(backend_id)
            return value if isinstance(value, str) and value else None

    def set_last_model(self, backend_id: str, model: str) -> None:
        if not backend_id:
            raise ValueError("backend_id не может быть пустым.")
        with self._lock:
            models = self.data.get("last_model")
            if not isinstance(models, dict):
                models = {}
                self.data["last_model"] = models
            models[backend_id] = str(model)
            self.save()
