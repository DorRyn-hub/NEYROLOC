"""Локальные GGUF модели через llama-cpp-python."""

from __future__ import annotations

from collections.abc import Iterator
from importlib.util import find_spec
from pathlib import Path
import threading

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
        self._loaded_settings: tuple[str, int, int] | None = None
        self._library = ModelLibrary()
        self._prepare_lock = threading.Lock()
        self._model_lock = threading.RLock()

    @classmethod
    def is_available(cls) -> bool:
        try:
            return find_spec("llama_cpp") is not None
        except (ImportError, ValueError):
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
                path = downloaded.path
                return self._validate_model_path(path)

        if configured:
            path = Path(str(configured)).expanduser()
            if path.is_file():
                return self._validate_model_path(path)

        if selected:
            path = Path(selected).expanduser()
            if path.is_file():
                return self._validate_model_path(path)

        raise RuntimeError(
            "Модель GGUF не найдена. Выберите скачанную модель или укажите путь к .gguf."
        )

    @staticmethod
    def _validate_model_path(path: Path) -> Path:
        try:
            if not path.is_file():
                raise RuntimeError(f"Файл модели не найден: {path}")
            if path.suffix.lower() != ".gguf":
                raise RuntimeError("Локальная модель должна быть файлом .gguf.")
            if path.stat().st_size <= 0:
                raise RuntimeError("Файл модели пуст.")
            return path.resolve()
        except OSError as exc:
            raise RuntimeError(f"Не удалось открыть файл модели: {exc}") from exc

    def _settings(self, path: Path) -> tuple[str, int, int]:
        try:
            n_ctx = int(self.config.get("n_ctx") or 8192)
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                "Некорректное значение «Размер контекста» — ожидается целое число "
                "(например, 8192)."
            ) from exc
        if not 512 <= n_ctx <= 262_144:
            raise RuntimeError("Размер контекста должен быть от 512 до 262144.")

        try:
            n_gpu_layers = int(self.config.get("n_gpu_layers") or -1)
        except (ValueError, TypeError) as exc:
            raise RuntimeError(
                "Некорректное значение «Слоёв на GPU» — ожидается целое число "
                "(-1 = все слои)."
            ) from exc
        if not -1 <= n_gpu_layers <= 10_000:
            raise RuntimeError("Количество слоёв на GPU должно быть -1 или от 0 до 10000.")
        return str(path), n_ctx, n_gpu_layers

    @staticmethod
    def _dispose_llm(llm) -> None:
        close = getattr(llm, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass

    def _load_llm(self, settings: tuple[str, int, int]):
        from llama_cpp import Llama

        path_str, n_ctx, n_gpu_layers = settings

        def _load(**extra) -> Llama:
            return Llama(
                model_path=path_str,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                # KV-кеш на GPU + flash attention — заметно быстрее генерация
                # на Metal/CUDA. Не все сборки поддерживают flash_attn.
                offload_kqv=True,
                verbose=False,
                **extra,
            )

        try:
            llm = _load(flash_attn=True)
        except Exception:
            llm = _load(flash_attn=False)

        # Если в GGUF нет шаблона, перезагружаем модель с явным ChatML.
        # Одновременно держать две большие GGUF-модели нельзя: это легко
        # исчерпывает RAM/VRAM, поэтому сначала освобождаем исходный экземпляр.
        metadata = getattr(llm, "metadata", None)
        if not isinstance(metadata, dict) or not metadata.get("tokenizer.chat_template"):
            self._dispose_llm(llm)
            try:
                llm = _load(flash_attn=False, chat_format="chatml")
            except Exception:
                # Preserve a usable model even if this llama-cpp build does not
                # accept an explicit chat format.
                llm = _load(flash_attn=False)
        return llm

    def prepare(self, progress: ProgressCallback | None = None) -> None:
        with self._prepare_lock:
            # If the user changes selection while a large model is loading,
            # finish that isolated load, discard it and load the latest choice.
            while True:
                self._ensure_open()
                requested_model = self.current_model
                path = self._resolve_model_path()
                settings = self._settings(path)
                with self._model_lock:
                    if self._llm is not None and self._loaded_settings == settings:
                        return
                    previous = self._llm
                    self._llm = None
                    self._loaded_path = None
                    self._loaded_settings = None
                if previous is not None:
                    # Loading two GGUF instances together commonly exhausts
                    # RAM/VRAM. Release old weights before allocating new ones.
                    self._dispose_llm(previous)

                if progress:
                    progress(
                        f"Загружаю в память: {path.name} "
                        f"({path.stat().st_size / (1024**3):.2f} ГБ)…"
                    )
                candidate = self._load_llm(settings)

                if self.closed:
                    self._dispose_llm(candidate)
                    raise RuntimeError("Загрузка модели отменена: backend закрыт.")
                if self.current_model != requested_model:
                    self._dispose_llm(candidate)
                    continue

                with self._model_lock:
                    if self.closed:
                        self._dispose_llm(candidate)
                        raise RuntimeError("Загрузка модели отменена: backend закрыт.")
                    previous = self._llm
                    self._llm = candidate
                    self._loaded_path = settings[0]
                    self._loaded_n_ctx = settings[1]
                    self._loaded_settings = settings
                if progress:
                    progress("Готово.")
                return

    def generate(self, messages: list[Message], temperature: float = 0.7) -> Iterator[str]:
        self._begin_generation()
        temperature = self._validate_generation_request(messages, temperature)
        # Fast no-op when the loaded settings still match; also guarantees that
        # a direct set_model() call can never silently generate with old weights.
        self.prepare()

        stream = None
        with self._model_lock:
            self._ensure_open()
            if self._llm is None:
                raise RuntimeError("Модель не загружена.")

            # Модели без надёжного EOS могут повторяться до заполнения контекста.
            max_tokens = min(SAFE_MAX_TOKENS, max(self._loaded_n_ctx // 2, 512))
            stream = self._llm.create_chat_completion(
                messages=[m.as_dict() for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                repeat_penalty=SAFE_REPEAT_PENALTY,
                stream=True,
            )
            try:
                # Регистрация тоже может увидеть параллельный close(). В этом
                # случае finally всё равно закроет уже созданный native stream.
                self._register_stream(stream)
                for chunk in stream:
                    if self._generation_cancelled():
                        break
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield content
            finally:
                self._finish_generation(stream)
                self._close_stream(stream)

    def close(self) -> None:
        super().close()
        with self._model_lock:
            llm = self._llm
            self._llm = None
            self._loaded_path = None
            self._loaded_settings = None
        if llm is not None:
            self._dispose_llm(llm)
