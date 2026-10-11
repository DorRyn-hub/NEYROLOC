#!/usr/bin/env python
"""
Менеджер моделей для скачивания и управления моделями с HuggingFace
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("❌ Установите: pip install rich")
    exit(1)

try:
    from huggingface_hub import hf_hub_download, list_repo_files, HfApi
    from huggingface_hub.utils import HfHubHTTPError
except ImportError:
    print("❌ Установите: pip install huggingface-hub")
    exit(1)


@dataclass
class ModelInfo:
    """Информация о модели."""
    repo_id: str
    filename: str
    local_path: Optional[Path] = None
    size_mb: Optional[float] = None
    description: Optional[str] = None


class ModelManager:
    """Менеджер для скачивания и управления моделями."""

    # Рекомендуемые модели для разных задач
    RECOMMENDED_MODELS = {
        "tiny": [
            {
                "repo_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
                "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
                "description": "Очень маленькая модель (300MB) - для быстрых тестов",
                "size_mb": 300
            },
            {
                "repo_id": "unsloth/Llama-3.2-1B-Instruct-GGUF",
                "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
                "description": "Маленькая модель от Meta (700MB) - хороший баланс",
                "size_mb": 700
            }
        ],
        "small": [
            {
                "repo_id": "unsloth/Llama-3.2-3B-Instruct-GGUF",
                "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
                "description": "Llama 3.2 3B от Meta (2GB) - рекомендуется для начала",
                "size_mb": 2000
            },
            {
                "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
                "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
                "description": "Qwen 2.5 3B (2GB) - очень умная модель",
                "size_mb": 2000
            }
        ],
        "medium": [
            {
                "repo_id": "bartowski/Qwen2.5-7B-Instruct-GGUF",
                "filename": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
                "description": "Qwen 2.5 7B (4.4GB) - мощная модель",
                "size_mb": 4400
            },
            {
                "repo_id": "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
                "filename": "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf",
                "description": "Llama 3.1 8B (4.9GB) - отличное качество",
                "size_mb": 4900
            }
        ],
        "multimodal": [
            {
                "repo_id": "lmstudio-community/llava-1.5-7b-hf-GGUF",
                "filename": "llava-1.5-7b-hf-Q4_K_M.gguf",
                "description": "LLaVA 1.5 7B - работа с изображениями",
                "size_mb": 4200
            }
        ]
    }

    def __init__(self, models_dir: Optional[Path] = None):
        """
        Инициализация менеджера моделей.

        Args:
            models_dir: Директория для хранения моделей
        """
        self.console = Console()
        self.models_dir = models_dir or Path.home() / ".neyrolock_models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Файл с метаданными моделей
        self.metadata_file = self.models_dir / "models_metadata.json"
        self.metadata = self._load_metadata()

        self.api = HfApi()

    def _load_metadata(self) -> Dict:
        """Загружает метаданные моделей."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_metadata(self):
        """Сохраняет метаданные моделей."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.console.print(f"[yellow]Предупреждение: не удалось сохранить метаданные: {e}[/]")

    def show_recommended_models(self):
        """Показывает список рекомендуемых моделей."""
        self.console.print("\n[bold cyan]📦 Рекомендуемые модели с HuggingFace[/]\n")

        categories = {
            "tiny": "Крошечные модели (для тестов)",
            "small": "Маленькие модели (рекомендуется)",
            "medium": "Средние модели (требуется больше RAM)",
            "multimodal": "Мультимодальные модели (текст + изображения)"
        }

        for category, title in categories.items():
            models = self.RECOMMENDED_MODELS[category]

            table = Table(title=title, show_header=True)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Модель", style="green")
            table.add_column("Размер", style="yellow", justify="right")
            table.add_column("Описание", style="white")

            for i, model in enumerate(models, 1):
                size = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']}MB"
                table.add_row(
                    str(i),
                    model['filename'],
                    size,
                    model['description']
                )

            self.console.print(table)
            self.console.print()

    def download_model(
        self,
        repo_id: str,
        filename: str,
        description: Optional[str] = None,
        force: bool = False
    ) -> Optional[Path]:
        """
        Скачивает модель с HuggingFace.

        Args:
            repo_id: ID репозитория на HuggingFace (напр. "Qwen/Qwen2.5-3B-Instruct-GGUF")
            filename: Имя файла для скачивания
            description: Описание модели
            force: Принудительно скачать даже если файл существует

        Returns:
            Путь к скачанной модели или None в случае ошибки
        """
        # Проверяем, есть ли уже модель
        model_key = f"{repo_id}/{filename}"
        if not force and model_key in self.metadata:
            local_path = Path(self.metadata[model_key]['local_path'])
            if local_path.exists():
                self.console.print(f"[yellow]✓ Модель уже скачана:[/] {local_path}")
                return local_path

        try:
            self.console.print(f"\n[bold cyan]📥 Скачивание модели...[/]")
            self.console.print(f"[dim]Репозиторий:[/] {repo_id}")
            self.console.print(f"[dim]Файл:[/] {filename}\n")

            # Скачиваем с прогресс-баром
            with Progress(
                "[progress.description]{task.description}",
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=self.console
            ) as progress:

                task = progress.add_task(f"Скачивание {filename}", total=None)

                local_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    cache_dir=self.models_dir,
                    local_dir=self.models_dir / repo_id.replace("/", "_"),
                    local_dir_use_symlinks=False
                )

                progress.update(task, completed=True)

            # Сохраняем метаданные
            local_path = Path(local_path)
            self.metadata[model_key] = {
                "repo_id": repo_id,
                "filename": filename,
                "local_path": str(local_path),
                "description": description,
                "size_bytes": local_path.stat().st_size if local_path.exists() else 0
            }
            self._save_metadata()

            self.console.print(f"\n[bold green]✓ Модель успешно скачана![/]")
            self.console.print(f"[dim]Путь:[/] {local_path}\n")

            return local_path

        except HfHubHTTPError as e:
            self.console.print(f"\n[bold red]✗ Ошибка HuggingFace:[/] {e}")
            self.console.print("[yellow]Проверьте правильность repo_id и filename[/]\n")
            return None

        except Exception as e:
            self.console.print(f"\n[bold red]✗ Ошибка скачивания:[/] {e}\n")
            return None

    def download_recommended(self, category: str = "small", index: int = 0) -> Optional[Path]:
        """
        Скачивает рекомендуемую модель.

        Args:
            category: Категория модели (tiny/small/medium/multimodal)
            index: Индекс модели в категории (0-based)

        Returns:
            Путь к скачанной модели
        """
        if category not in self.RECOMMENDED_MODELS:
            self.console.print(f"[red]Неизвестная категория:[/] {category}")
            return None

        models = self.RECOMMENDED_MODELS[category]
        if index >= len(models):
            self.console.print(f"[red]Неверный индекс:[/] {index}")
            return None

        model = models[index]
        return self.download_model(
            repo_id=model['repo_id'],
            filename=model['filename'],
            description=model['description']
        )

    def list_downloaded_models(self) -> List[Dict]:
        """
        Возвращает список скачанных моделей.

        Returns:
            Список моделей с информацией
        """
        downloaded = []

        for model_key, info in self.metadata.items():
            local_path = Path(info['local_path'])
            if local_path.exists():
                size_mb = local_path.stat().st_size / (1024 * 1024)
                downloaded.append({
                    'key': model_key,
                    'repo_id': info['repo_id'],
                    'filename': info['filename'],
                    'path': local_path,
                    'size_mb': size_mb,
                    'description': info.get('description', '')
                })

        return downloaded

    def show_downloaded_models(self):
        """Показывает таблицу скачанных моделей."""
        models = self.list_downloaded_models()

        if not models:
            self.console.print("[yellow]Нет скачанных моделей[/]")
            return

        table = Table(title="Скачанные модели", show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Имя файла", style="green")
        table.add_column("Размер", style="yellow", justify="right")
        table.add_column("Путь", style="dim")

        for i, model in enumerate(models, 1):
            size = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']:.0f}MB"
            table.add_row(
                str(i),
                model['filename'],
                size,
                str(model['path'])
            )

        self.console.print(table)

    def delete_model(self, model_key: str) -> bool:
        """
        Удаляет модель.

        Args:
            model_key: Ключ модели (repo_id/filename)

        Returns:
            True если удалено успешно
        """
        if model_key not in self.metadata:
            self.console.print(f"[red]Модель не найдена:[/] {model_key}")
            return False

        try:
            local_path = Path(self.metadata[model_key]['local_path'])
            if local_path.exists():
                local_path.unlink()
                self.console.print(f"[green]✓ Файл удален:[/] {local_path}")

            del self.metadata[model_key]
            self._save_metadata()

            self.console.print(f"[green]✓ Модель удалена из списка[/]")
            return True

        except Exception as e:
            self.console.print(f"[red]✗ Ошибка удаления:[/] {e}")
            return False

    def search_models(self, query: str, limit: int = 10):
        """
        Ищет модели на HuggingFace.

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
        """
        try:
            self.console.print(f"\n[bold cyan]🔍 Поиск моделей:[/] {query}\n")

            # Поиск моделей GGUF формата
            models = list(self.api.list_models(
                search=f"{query} GGUF",
                limit=limit,
                sort="downloads",
                direction=-1
            ))

            if not models:
                self.console.print("[yellow]Модели не найдены[/]")
                return

            table = Table(show_header=True)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Репозиторий", style="green")
            table.add_column("Загрузок", style="yellow", justify="right")

            for i, model in enumerate(models, 1):
                downloads = f"{model.downloads:,}" if model.downloads else "N/A"
                table.add_row(str(i), model.id, downloads)

            self.console.print(table)
            self.console.print(f"\n[dim]Используйте repo_id для скачивания конкретной модели[/]\n")

        except Exception as e:
            self.console.print(f"[red]✗ Ошибка поиска:[/] {e}")

    def interactive_download(self):
        """Интерактивный режим скачивания модели."""
        self.console.print(Panel(
            "[bold cyan]Скачивание модели с HuggingFace[/]\n\n"
            "[yellow]1.[/] Выберите из рекомендуемых\n"
            "[yellow]2.[/] Укажите свою модель (repo_id + filename)\n"
            "[yellow]3.[/] Найти модель по названию",
            title="Выберите способ",
            border_style="cyan"
        ))

        choice = Prompt.ask("Ваш выбор", choices=["1", "2", "3"], default="1")

        if choice == "1":
            # Рекомендуемые модели
            self.show_recommended_models()

            category = Prompt.ask(
                "\nВыберите категорию",
                choices=["tiny", "small", "medium", "multimodal"],
                default="small"
            )

            models = self.RECOMMENDED_MODELS[category]
            if len(models) > 1:
                model_idx = int(Prompt.ask(
                    "Номер модели",
                    choices=[str(i+1) for i in range(len(models))],
                    default="1"
                )) - 1
            else:
                model_idx = 0

            model = models[model_idx]

            # Подтверждение
            size_gb = model['size_mb'] / 1000
            if not Confirm.ask(f"\n[yellow]Скачать {model['filename']} ({size_gb:.1f}GB)?[/]"):
                return None

            return self.download_model(
                repo_id=model['repo_id'],
                filename=model['filename'],
                description=model['description']
            )

        elif choice == "2":
            # Ручной ввод
            repo_id = Prompt.ask("\nВведите repo_id (напр. Qwen/Qwen2.5-3B-Instruct-GGUF)")
            filename = Prompt.ask("Введите filename (напр. qwen2.5-3b-instruct-q4_k_m.gguf)")

            return self.download_model(repo_id=repo_id, filename=filename)

        elif choice == "3":
            # Поиск
            query = Prompt.ask("\nВведите запрос для поиска")
            self.search_models(query)

            if Confirm.ask("\nХотите скачать одну из найденных моделей?"):
                repo_id = Prompt.ask("Введите repo_id")
                filename = Prompt.ask("Введите filename")
                return self.download_model(repo_id=repo_id, filename=filename)

        return None


def main():
    """Пример использования."""
    console = Console()
    manager = ModelManager()

    console.print(Panel(
        "[bold cyan]Менеджер моделей HuggingFace[/]\n\n"
        "[yellow]1.[/] Показать рекомендуемые модели\n"
        "[yellow]2.[/] Скачать модель\n"
        "[yellow]3.[/] Показать скачанные модели\n"
        "[yellow]4.[/] Найти модель\n"
        "[yellow]5.[/] Выход",
        title="Меню",
        border_style="cyan"
    ))

    choice = Prompt.ask("Ваш выбор", choices=["1", "2", "3", "4", "5"], default="1")

    if choice == "1":
        manager.show_recommended_models()
    elif choice == "2":
        manager.interactive_download()
    elif choice == "3":
        manager.show_downloaded_models()
    elif choice == "4":
        query = Prompt.ask("Введите запрос для поиска")
        manager.search_models(query)


if __name__ == "__main__":
    main()
