"""Локальные GGUF модели через llama-cpp-python."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from .base import SAFE_MAX_TOKENS, SAFE_REPEAT_PENALTY, Backend, Message, ProgressCallback
from core.model_library import ModelLibrary


class LocalGGUFBackend(Backend):
    id = "local_gguf"
    display_name = "Local GGUF"
    description = "Полностью offline, файл .gguf"
    config_fields = [
        ("model_path", "Путь к файлу .gguf", "file"),
        ("n_ctx", "Размер контекста (n_ctx)", "text"),
        ("n_gpu_layers", "Слоёв на GPU (-1 = все)", "text"),
    ]

    def __init__(self, config=None) -> None:
        super().__init__(config)
        self._llm = None
        self._loaded_path: str | None = None
        self._loaded_n_ctx: int = 8192
        self._library = ModelLibrary()

    @classmethod
    def is_available(cls) -> bool:
        try:
            import llama_cpp  # noqa: F401
            return True
        except ImportError:
            return False

    def list_models(self) -> list[str]:
        names = [item.filename for item in self._library.list_downloaded()]
        path = self.config.get("model_path")
        if path:
            name = Path(path).name
            if name not in names:
                names.insert(0, name)
        return names

    def _resolve_model_path(self) -> Path:
        selected = self.current_model or ""
        configured = self.config.get("model_path")

        if selected:
            downloaded = self._library.find_downloaded(selected)
            if downloaded is not None:
                return downloaded.path

        if configured:
            path = Path(str(configured)).expanduser()
            if path.exists():
                return path

        if selected:
            path = Path(selected).expanduser()
            if path.exists():
                return path

        raise RuntimeError(
            "Модель GGUF не найдена. Выберите скачанную модель или укажите путь к .gguf."
        )

    def prepare(self, progress: ProgressCallback | None = None) -> None:
        from llama_cpp import Llama

        path = self._resolve_model_path()
        path_str = str(path)
        if self._llm is not None and self._loaded_path == path_str:
            return

        # Освободить предыдущую модель.
        self._llm = None

        if progress:
            progress(
                f"Загружаю в память: {Path(path).name} "
                f"({Path(path).stat().st_size / (1024**3):.2f} ГБ)…"
            )

        try:
            n_ctx = int(self.config.get("n_ctx") or 8192)
        except (ValueError, TypeError):
            raise RuntimeError(
                "Некорректное значение «Размер контекста» — ожидается целое число (например, 8192)."
            )
        try:
            n_gpu_layers = int(self.config.get("n_gpu_layers") or -1)
        except (ValueError, TypeError):
            raise RuntimeError(
                "Некорректное значение «Слоёв на GPU» — ожидается целое число (-1 = все слои)."
            )

        def _load(**extra) -> Llama:
            return Llama(
                model_path=path_str,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                # KV-кеш на GPU + flash attention — заметно быстрее генерация
                # на Metal/CUDA. flash_attn поддерживают не все квантования,
                # поэтому при ошибке загрузки откатываемся без него.
                offload_kqv=True,
                verbose=False,
                **extra,
            )

        try:
            llm = _load(flash_attn=True)
        except Exception:
            llm = _load(flash_attn=False)

        # Если в самом GGUF нет chat-шаблона, llama-cpp тихо подставляет
        # устаревший формат "llama-2", который ломает форматирование у
        # современных инструктивных моделей ("странные" ответы). ChatML —
        # надёжный фолбэк, которому следует большинство актуальных моделей.
        if not llm.metadata.get("tokenizer.chat_template"):
            prev = llm
            try:
                llm = _load(flash_attn=False, chat_format="chatml")
            except Exception:
                llm = prev  # оставляем рабочий экземпляр без chat_format
            else:
                del prev  # освобождаем VRAM от предыдущей копии

        self._llm = llm
        self._loaded_path = path_str
        self._loaded_n_ctx = n_ctx

        if progress:
            progress("Готово.")

    def generate(self, messages: list[Message], temperature: float = 0.7) -> Iterator[str]:
        if self._llm is None:
            self.prepare()
        assert self._llm is not None

        # Раньше было -1 (до заполнения контекста) — модели без надёжного EOS
        # уходили в бесконечный повтор на весь контекст. Ограничиваем щедрым,
        # но конечным потолком, не превышающим половину n_ctx.
        max_tokens = min(SAFE_MAX_TOKENS, max(self._loaded_n_ctx // 2, 512))
        stream = self._llm.create_chat_completion(
            messages=[m.as_dict() for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            repeat_penalty=SAFE_REPEAT_PENALTY,
            stream=True,
        )
        for chunk in stream:
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                yield content

    def close(self) -> None:
        self._llm = None
        self._loaded_path = None
