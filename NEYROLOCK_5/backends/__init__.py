"""Реестр доступных backend'ов."""

from __future__ import annotations

from .base import Backend
from .local_gguf import LocalGGUFBackend
from .online import GroqBackend, OpenAIBackend

ALL_BACKENDS: list[type[Backend]] = [
    LocalGGUFBackend,
    OpenAIBackend,
    GroqBackend,
]

__all__ = [
    "Backend",
    "ALL_BACKENDS",
    "LocalGGUFBackend",
    "GroqBackend",
    "OpenAIBackend",
]
