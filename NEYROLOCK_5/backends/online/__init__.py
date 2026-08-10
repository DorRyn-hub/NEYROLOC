"""Backend'ы облачных (онлайн) LLM-провайдеров."""

from __future__ import annotations

from .groq import GroqBackend
from .openai_backend import OpenAIBackend

__all__ = ["GroqBackend", "OpenAIBackend"]
