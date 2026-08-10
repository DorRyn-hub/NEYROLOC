"""HuggingFace GGUF model library shared by the GUI and backends."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from core.json_store import (
    JsonStoreError,
    advisory_file_lock,
    atomic_write_json,
    ensure_private_directory,
    read_json_object,
)


ProgressCallback = Callable[[str], None]
# (переданные_байты, всего_байт) — для живого прогресс-бара в UI.
ProgressBytesCallback = Callable[[int, int], None]

# huggingface_hub по умолчанию качает через Xet (дедуп по чанкам) и сообщает
# прогресс только на финальном шаге "reconstructing file" — почти мгновенно
# и без промежуточных процентов, шкала выглядит "зависшей", потом скачком 100%.
# Классическая HTTP-загрузка репортит прогресс плавно, чанк за чанком — именно
# это нужно для честного процентного индикатора в реальном времени.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

# MainWindow and LocalGGUFBackend own separate ModelLibrary instances.  Their
# metadata updates still target the same file, so coordinate them process-wide.
_METADATA_LOCK = threading.RLock()
MAX_METADATA_BYTES = 4 * 1024 * 1024


def _progress_tqdm_class(callback: ProgressBytesCallback | None):
    """Класс tqdm, форвардящий (n, total) в callback — для hf_hub_download(tqdm_class=...)."""
    from tqdm import tqdm as tqdm_base

    class _ProgressTqdm(tqdm_base):
        def update(self, n=1):
            result = super().update(n)
            if callback is not None and self.total:
                try:
                    callback(self.n, self.total)
                except Exception:
                    pass
            return result

    return _ProgressTqdm


@dataclass(frozen=True)
class RecommendedModel:
    category: str
    repo_id: str
    filename: str
    description: str
    size_mb: int

    @property
    def size_label(self) -> str:
        if self.size_mb >= 1000:
            return f"{self.size_mb / 1000:.1f} GB"
        return f"{self.size_mb} MB"


@dataclass(frozen=True)
class DownloadedModel:
    key: str
    repo_id: str
    filename: str
    path: Path
    size_mb: float
    description: str = ""

    @property
    def size_label(self) -> str:
        if self.size_mb >= 1000:
            return f"{self.size_mb / 1000:.1f} GB"
        return f"{self.size_mb:.0f} MB"


class ModelLibrary:
    """Non-interactive version of the v2 HuggingFace model manager."""

    RECOMMENDED_MODELS: tuple[RecommendedModel, ...] = (
        RecommendedModel(
            "Тестовые",
            "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
            "qwen2.5-0.5b-instruct-q4_k_m.gguf",
            "Очень маленькая модель для быстрой проверки.",
            300,
        ),
        RecommendedModel(
            "Тестовые",
            "unsloth/Llama-3.2-1B-Instruct-GGUF",
            "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
            "Маленькая Llama для слабых машин.",
            700,
        ),
        RecommendedModel(
            "Оптимальные",
            "unsloth/Llama-3.2-3B-Instruct-GGUF",
            "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            "Хороший баланс скорости и качества.",
            2000,
        ),
        RecommendedModel(
            "Оптимальные",
            "Qwen/Qwen2.5-3B-Instruct-GGUF",
            "qwen2.5-3b-instruct-q4_k_m.gguf",
            "Умная компактная модель Qwen.",
            2000,
        ),
        RecommendedModel(
            "Мощные",
            "bartowski/Qwen2.5-7B-Instruct-GGUF",
            "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
            "Качественная 7B модель, требует больше RAM.",
            4400,
        ),
        RecommendedModel(
            "Мощные",
            "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
            "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "Сильная Llama 3.1 8B для локального чата.",
            4900,
        ),
        RecommendedModel(
            "Мультимодальные",
            "lmstudio-community/llava-1.5-7b-hf-GGUF",
            "llava-1.5-7b-hf-Q4_K_M.gguf",
            "LLaVA 1.5 7B для сценариев с изображениями.",
            4200,
        ),
    )

    def __init__(self, models_dir: Path | None = None) -> None:
        self.models_dir = models_dir or Path.home() / ".neyrolock_models"
        ensure_private_directory(self.models_dir)
        self.metadata_file = self.models_dir / "models_metadata.json"
        self.metadata_lock_file = self.models_dir / ".models_metadata.lock"
        self.last_metadata_error: str | None = None

    def _read_metadata_unlocked(self) -> dict[str, dict]:
        if not self.metadata_file.exists():
            self.last_metadata_error = None
            return {}
        try:
            raw = read_json_object(
                self.metadata_file,
                max_bytes=MAX_METADATA_BYTES,
            )
        except (OSError, JsonStoreError) as exc:
            self.last_metadata_error = f"Не удалось прочитать метаданные: {exc}"
            return {}

        # Ignore only malformed entries; one damaged record must not hide
        # every valid downloaded model.
        metadata = {
            str(key): value
            for key, value in raw.items()
            if isinstance(key, str) and isinstance(value, dict)
        }
        self.last_metadata_error = None
        return metadata

    def _load_metadata(self) -> dict[str, dict]:
        with _METADATA_LOCK, advisory_file_lock(self.metadata_lock_file):
            return self._read_metadata_unlocked()

    def _write_metadata_unlocked(self, data: dict) -> None:
        atomic_write_json(
            self.metadata_file,
            data,
            mode=0o600,
            max_bytes=MAX_METADATA_BYTES,
        )
        self.last_metadata_error = None

    def _save_metadata(self, data: dict) -> None:
        with _METADATA_LOCK, advisory_file_lock(self.metadata_lock_file):
            try:
                self._write_metadata_unlocked(data)
            except (OSError, TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"Не удалось сохранить метаданные моделей ({self.metadata_file}): {exc}"
                ) from exc

    def recommended(self) -> list[RecommendedModel]:
        return list(self.RECOMMENDED_MODELS)

    def list_downloaded(self) -> list[DownloadedModel]:
        metadata = self._load_metadata()
        by_path: dict[Path, DownloadedModel] = {}

        for key, info in metadata.items():
            raw_path = info.get("local_path")
            if not isinstance(raw_path, str) or not raw_path:
                continue
            path = Path(raw_path).expanduser()
            try:
                if not path.is_file():
                    continue
                resolved = path.resolve()
                size_mb = path.stat().st_size / (1024 * 1024)
            except OSError:
                continue
            by_path[resolved] = DownloadedModel(
                key=key,
                repo_id=str(info.get("repo_id") or ""),
                filename=str(info.get("filename") or path.name),
                path=path,
                size_mb=size_mb,
                description=str(info.get("description") or ""),
            )

        # v2 sometimes left raw GGUF files without metadata. Keep them usable.
        try:
            candidates = self.models_dir.rglob("*.gguf")
            for path in candidates:
                try:
                    if not path.is_file():
                        continue
                    resolved = path.resolve()
                    if resolved in by_path:
                        continue
                    size_mb = path.stat().st_size / (1024 * 1024)
                except OSError:
                    continue
                by_path[resolved] = DownloadedModel(
                    key=str(path),
                    repo_id="local",
                    filename=path.name,
                    path=path,
                    size_mb=size_mb,
                    description="Найдена локально без metadata.",
                )
        except OSError:
            pass

        return sorted(by_path.values(), key=lambda item: item.filename.lower())

    def find_downloaded(self, model: str) -> DownloadedModel | None:
        model_path = Path(model).expanduser()
        try:
            is_file = model_path.is_file()
        except OSError:
            is_file = False
        if is_file:
            try:
                size_mb = model_path.stat().st_size / (1024 * 1024)
            except OSError:
                return None
            return DownloadedModel(
                key=str(model_path),
                repo_id="local",
                filename=model_path.name,
                path=model_path,
                size_mb=size_mb,
            )

        for item in self.list_downloaded():
            if model in {item.filename, str(item.path), item.key}:
                return item
        return None

    def download_model(
        self,
        repo_id: str,
        filename: str,
        description: str = "",
        force: bool = False,
        token: str | None = None,
        progress: ProgressCallback | None = None,
        progress_bytes: ProgressBytesCallback | None = None,
    ) -> Path:
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise RuntimeError(
                "Не установлен huggingface-hub. Выполните: pip install huggingface-hub"
            ) from exc

        repo_id = repo_id.strip()
        filename = filename.strip()
        if not repo_id or not filename:
            raise RuntimeError("Нужно указать repo_id и filename.")

        key = f"{repo_id}/{filename}"
        metadata = self._load_metadata()
        if not force and key in metadata:
            raw_path = metadata[key].get("local_path")
            local_path = Path(raw_path).expanduser() if isinstance(raw_path, str) else None
            if local_path is not None and local_path.is_file():
                if progress:
                    progress(f"Модель уже скачана: {local_path.name}")
                return local_path

        if progress:
            progress(f"Скачивание {filename} из {repo_id}...")

        local_dir = self.models_dir / repo_id.replace("/", "_")
        local_path = Path(
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=self.models_dir,
                local_dir=local_dir,
                local_dir_use_symlinks=False,
                token=token,
                tqdm_class=_progress_tqdm_class(progress_bytes),
            )
        )

        try:
            if not local_path.is_file() or local_path.stat().st_size <= 0:
                raise RuntimeError("Скачанный файл модели отсутствует или пуст.")
        except OSError as exc:
            raise RuntimeError(f"Не удалось проверить скачанную модель: {exc}") from exc

        # The download may take hours. Reload under the process-wide lock so a
        # second completed download is not lost by writing our stale snapshot.
        with _METADATA_LOCK, advisory_file_lock(self.metadata_lock_file):
            try:
                metadata = self._read_metadata_unlocked()
                metadata[key] = {
                    "repo_id": repo_id,
                    "filename": filename,
                    "local_path": str(local_path),
                    "description": description,
                    "size_bytes": local_path.stat().st_size,
                }
                self._write_metadata_unlocked(metadata)
            except (OSError, TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"Не удалось сохранить метаданные моделей ({self.metadata_file}): {exc}"
                ) from exc

        if progress:
            progress(f"Готово: {local_path}")

        return local_path
