"""HuggingFace GGUF model library shared by the GUI and backends."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


ProgressCallback = Callable[[str], None]
# (переданные_байты, всего_байт) — для живого прогресс-бара в UI.
ProgressBytesCallback = Callable[[int, int], None]

# huggingface_hub по умолчанию качает через Xet (дедуп по чанкам) и сообщает
# прогресс только на финальном шаге "reconstructing file" — почти мгновенно
# и без промежуточных процентов, шкала выглядит "зависшей", потом скачком 100%.
# Классическая HTTP-загрузка репортит прогресс плавно, чанк за чанком — именно
# это нужно для честного процентного индикатора в реальном времени.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")


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
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.models_dir / "models_metadata.json"

    def _load_metadata(self) -> dict:
        if not self.metadata_file.exists():
            return {}
        try:
            return json.loads(self.metadata_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_metadata(self, data: dict) -> None:
        try:
            self.metadata_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise RuntimeError(
                f"Не удалось сохранить метаданные моделей ({self.metadata_file}): {exc}"
            ) from exc

    def recommended(self) -> list[RecommendedModel]:
        return list(self.RECOMMENDED_MODELS)

    def list_downloaded(self) -> list[DownloadedModel]:
        metadata = self._load_metadata()
        by_path: dict[Path, DownloadedModel] = {}

        for key, info in metadata.items():
            path = Path(info.get("local_path", ""))
            if not path.exists():
                continue
            by_path[path.resolve()] = DownloadedModel(
                key=key,
                repo_id=str(info.get("repo_id", "")),
                filename=str(info.get("filename") or path.name),
                path=path,
                size_mb=path.stat().st_size / (1024 * 1024),
                description=str(info.get("description") or ""),
            )

        # v2 sometimes left raw GGUF files without metadata. Keep them usable.
        for path in self.models_dir.rglob("*.gguf"):
            resolved = path.resolve()
            if resolved in by_path:
                continue
            by_path[resolved] = DownloadedModel(
                key=str(path),
                repo_id="local",
                filename=path.name,
                path=path,
                size_mb=path.stat().st_size / (1024 * 1024),
                description="Найдена локально без metadata.",
            )

        return sorted(by_path.values(), key=lambda item: item.filename.lower())

    def find_downloaded(self, model: str) -> DownloadedModel | None:
        model_path = Path(model).expanduser()
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
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
            local_path = Path(metadata[key].get("local_path", ""))
            if local_path.exists():
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

        metadata[key] = {
            "repo_id": repo_id,
            "filename": filename,
            "local_path": str(local_path),
            "description": description,
            "size_bytes": local_path.stat().st_size if local_path.exists() else 0,
        }
        self._save_metadata(metadata)

        if progress:
            progress(f"Готово: {local_path}")

        return local_path
