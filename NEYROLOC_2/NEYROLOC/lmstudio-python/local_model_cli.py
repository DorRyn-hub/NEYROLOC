#!/usr/bin/env python
"""
CLI для работы с ЛОКАЛЬНЫМИ моделями с HuggingFace
Выбирайте модель через Finder - работает полностью OFFLINE!
"""

import os
import sys
import json
import readline
from pathlib import Path
from typing import Optional
from tkinter import Tk, filedialog

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
except ImportError:
    print("❌ Установите: pip install rich")
    sys.exit(1)

try:
    from llama_cpp import Llama
except ImportError:
    print("❌ Установите: pip install llama-cpp-python")
    print("Для Mac с Apple Silicon (M1/M2/M3):")
    print("  CMAKE_ARGS=\"-DLLAMA_METAL=on\" pip install llama-cpp-python")
    sys.exit(1)

try:
    from model_manager import ModelManager
except ImportError:
    print("⚠ model_manager.py не найден - функция скачивания моделей недоступна")
    ModelManager = None


class LocalModelCLI:
    """CLI для работы с локальными моделями."""

    def __init__(self):
        """Инициализация."""
        self.console = Console()
        self.model: Optional[Llama] = None
        self.chat_history = []
        self.model_path = None

        # Настройка истории
        self.history_dir = Path.home() / ".local_llm_cli"
        self.history_dir.mkdir(exist_ok=True)

        # Инициализация менеджера моделей
        self.model_manager = ModelManager() if ModelManager else None

        histfile = self.history_dir / ".cli_history"
        try:
            readline.read_history_file(histfile)
            readline.set_history_length(1000)
        except (FileNotFoundError, PermissionError, OSError):
            pass

        import atexit
        def save_history():
            try:
                readline.write_history_file(histfile)
            except (PermissionError, OSError):
                pass
        atexit.register(save_history)

    def show_banner(self):
        """Показывает баннер."""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║        ЛОКАЛЬНЫЕ МОДЕЛИ ИЗ HUGGINGFACE (OFFLINE)          ║
║           Выберите файл модели через Finder               ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")

    def show_instructions(self):
        """Показывает инструкции по скачиванию моделей."""
        instructions = """
[bold yellow]📥 Как скачать модель с HuggingFace:[/]

[bold cyan]1. Найдите модель:[/]
   • Откройте https://huggingface.co/models
   • Фильтр: GGUF format (важно!)
   • Рекомендуемые модели:
     - Qwen/Qwen2.5-3B-Instruct-GGUF
     - bartowski/Llama-3.2-3B-Instruct-GGUF
     - TheBloke/Mistral-7B-Instruct-v0.2-GGUF

[bold cyan]2. Скачайте файл:[/]
   • Перейдите в "Files and versions"
   • Скачайте файл .gguf (обычно Q4_K_M.gguf - хороший баланс)
   • Сохраните в удобную папку

[bold cyan]3. Размеры файлов:[/]
   • Q2 - самый маленький, хуже качество (~1-2GB)
   • Q4 - оптимальный баланс (~2-4GB) ⭐ РЕКОМЕНДУЕТСЯ
   • Q8 - лучшее качество, больше размер (~4-8GB)

[bold green]Готово![/] Теперь выберите файл через Finder
        """
        self.console.print(Panel(instructions, border_style="cyan"))

    def select_model_file(self) -> Optional[str]:
        """Открывает Finder для выбора файла модели."""
        self.console.print("\n[yellow]Открываю Finder для выбора модели...[/]")
        self.console.print("[dim]Выберите файл .gguf[/]\n")

        # Создаем скрытое окно Tkinter
        root = Tk()
        root.withdraw()  # Скрываем главное окно
        root.attributes('-topmost', True)  # Поверх всех окон

        # Открываем диалог выбора файла
        file_path = filedialog.askopenfilename(
            title="Выберите файл модели GGUF",
            filetypes=[
                ("GGUF Models", "*.gguf"),
                ("All Files", "*.*")
            ],
            initialdir=str(Path.home() / "Downloads")
        )

        root.destroy()

        if not file_path:
            self.console.print("[red]Файл не выбран[/]")
            return None

        file_path = Path(file_path)

        if not file_path.exists():
            self.console.print(f"[red]Файл не найден:[/] {file_path}")
            return None

        if not file_path.suffix == '.gguf':
            self.console.print("[yellow]⚠ Предупреждение: Файл не .gguf[/]")
            if not Confirm.ask("Все равно продолжить?"):
                return None

        self.console.print(f"[green]✓ Выбран файл:[/] {file_path.name}")
        self.console.print(f"[dim]Путь: {file_path}[/]")

        return str(file_path)

    def load_model(self, model_path: str):
        """Загружает модель из файла."""
        self.model_path = model_path
        file_size_mb = Path(model_path).stat().st_size / (1024 * 1024)

        self.console.print(f"\n[yellow]Загрузка модели...[/]")
        self.console.print(f"[dim]Размер файла: {file_size_mb:.1f} MB[/]")

        try:
            # Параметры загрузки
            n_ctx = Prompt.ask(
                "\nРазмер контекста (токенов)",
                default="2048",
                show_default=True
            )

            n_gpu_layers = Prompt.ask(
                "Слои на GPU (0 = только CPU, -1 = все на GPU)",
                default="-1",
                show_default=True
            )

            with self.console.status("[bold green]Загрузка модели в память..."):
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=int(n_ctx),
                    n_gpu_layers=int(n_gpu_layers),
                    verbose=False
                )

            self.console.print("\n[bold green]✓ Модель загружена успешно![/]\n")

            # Показываем информацию
            info = Panel(
                f"[bold]Модель:[/] {Path(model_path).name}\n"
                f"[bold]Размер:[/] {file_size_mb:.1f} MB\n"
                f"[bold]Контекст:[/] {n_ctx} токенов\n"
                f"[bold]GPU слои:[/] {n_gpu_layers}",
                title="✓ Готово к работе",
                border_style="green"
            )
            self.console.print(info)

            return True

        except Exception as e:
            self.console.print(
                Panel(
                    f"[red]Ошибка загрузки модели:[/]\n\n{e}\n\n"
                    f"[yellow]Возможные причины:[/]\n"
                    f"  • Недостаточно RAM\n"
                    f"  • Поврежденный файл модели\n"
                    f"  • Несовместимый формат\n\n"
                    f"[yellow]Попробуйте:[/]\n"
                    f"  • Выбрать модель меньшего размера (Q4 вместо Q8)\n"
                    f"  • Уменьшить n_ctx (например, 1024)\n"
                    f"  • Установить n_gpu_layers=0 (только CPU)",
                    title="❌ Ошибка",
                    border_style="red"
                )
            )
            return False

    def chat(self, user_message: str):
        """Отправляет сообщение модели."""
        if not self.model:
            self.console.print("[red]Модель не загружена![/]")
            return

        # Добавляем в историю
        self.chat_history.append({
            "role": "user",
            "content": user_message
        })

        try:
            self.console.print("\n[bold green]🤖 Модель:[/] ", end="")

            # Генерация с потоковым выводом
            response_text = ""

            stream = self.model.create_chat_completion(
                messages=self.chat_history,
                stream=True,
                max_tokens=512,
                temperature=0.7,
            )

            for chunk in stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content = delta['content']
                        self.console.print(content, end="", style="green")
                        response_text += content

            self.console.print("\n")

            # Добавляем ответ в историю
            self.chat_history.append({
                "role": "assistant",
                "content": response_text
            })

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠ Генерация прервана[/]\n")
        except Exception as e:
            self.console.print(f"\n[red]Ошибка генерации:[/] {e}\n")

    def show_help(self):
        """Показывает справку."""
        help_text = """
[bold cyan]Команды:[/]

/help      - Эта справка
/download  - Скачать модель с HuggingFace 🆕
/models    - Показать скачанные модели 🆕
/search    - Найти модель на HuggingFace 🆕
/history   - Показать историю
/clear     - Очистить историю
/save      - Сохранить диалог
/info      - Информация о модели
/reload    - Загрузить другую модель
/exit      - Выход
        """
        self.console.print(Panel(help_text, title="Справка", border_style="cyan"))

    def show_history(self):
        """Показывает историю."""
        if not self.chat_history:
            self.console.print("[yellow]История пуста[/]")
            return

        text = "\n\n".join([
            f"[bold blue]User:[/] {msg['content']}" if msg['role'] == 'user'
            else f"[bold green]Assistant:[/] {msg['content']}"
            for msg in self.chat_history
        ])

        self.console.print(Panel(text, title="История", border_style="blue"))

    def show_info(self):
        """Показывает информацию о модели."""
        if not self.model_path:
            self.console.print("[yellow]Модель не загружена[/]")
            return

        path = Path(self.model_path)
        size_mb = path.stat().st_size / (1024 * 1024)

        info = Panel(
            f"[bold]Файл:[/] {path.name}\n"
            f"[bold]Путь:[/] {path}\n"
            f"[bold]Размер:[/] {size_mb:.1f} MB\n"
            f"[bold]Сообщений в истории:[/] {len(self.chat_history)}",
            title="Информация о модели",
            border_style="cyan"
        )
        self.console.print(info)

    def save_history(self):
        """Сохраняет историю."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.history_dir / f"chat_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "model_path": self.model_path,
                "model_name": Path(self.model_path).name if self.model_path else None,
                "messages": self.chat_history
            }, f, ensure_ascii=False, indent=2)

        self.console.print(f"[green]✓ Сохранено в:[/] {filename}")

    def download_model(self):
        """Скачивает модель с HuggingFace."""
        if not self.model_manager:
            self.console.print("[red]Менеджер моделей недоступен. Установите: pip install huggingface-hub[/]")
            return

        model_path = self.model_manager.interactive_download()

        if model_path and Confirm.ask("\nЗагрузить эту модель сейчас?", default=True):
            self.load_model(str(model_path))
            self.chat_history = []

    def show_downloaded_models(self):
        """Показывает список скачанных моделей."""
        if not self.model_manager:
            self.console.print("[red]Менеджер моделей недоступен[/]")
            return

        self.model_manager.show_downloaded_models()

        models = self.model_manager.list_downloaded_models()
        if models and Confirm.ask("\nЗагрузить одну из этих моделей?", default=False):
            model_idx = int(Prompt.ask(
                "Номер модели",
                choices=[str(i+1) for i in range(len(models))],
                default="1"
            )) - 1

            model_path = models[model_idx]['path']
            self.load_model(str(model_path))
            self.chat_history = []

    def search_models(self, cmd: str):
        """Ищет модели на HuggingFace."""
        if not self.model_manager:
            self.console.print("[red]Менеджер моделей недоступен[/]")
            return

        # Извлекаем запрос из команды
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            query = Prompt.ask("Введите запрос для поиска")
        else:
            query = parts[1]

        self.model_manager.search_models(query)

    def run(self):
        """Главный цикл."""
        self.show_banner()

        # Спрашиваем, показывать ли инструкции
        if Confirm.ask("\nПоказать инструкции по скачиванию моделей?", default=True):
            self.show_instructions()

        # Выбор файла модели
        model_path = self.select_model_file()

        if not model_path:
            self.console.print("\n[yellow]Выход без выбора модели[/]")
            return

        # Загрузка модели
        if not self.load_model(model_path):
            return

        self.console.print("[dim]Введите сообщение или команду (начинается с /)[/]")
        self.console.print("[dim]Введите /help для справки[/]\n")

        while True:
            try:
                user_input = Prompt.ask("\n[bold blue]👤 Вы[/]").strip()

                if not user_input:
                    continue

                if user_input.startswith('/'):
                    cmd = user_input.lower()

                    if cmd in ['/exit', '/quit']:
                        self.console.print("\n[cyan]До свидания![/]")
                        break
                    elif cmd == '/help':
                        self.show_help()
                    elif cmd == '/download':
                        self.download_model()
                    elif cmd == '/models':
                        self.show_downloaded_models()
                    elif cmd.startswith('/search'):
                        self.search_models(user_input)
                    elif cmd == '/history':
                        self.show_history()
                    elif cmd == '/clear':
                        self.chat_history = []
                        self.console.print("[green]✓ История очищена[/]")
                    elif cmd == '/save':
                        self.save_history()
                    elif cmd == '/info':
                        self.show_info()
                    elif cmd == '/reload':
                        model_path = self.select_model_file()
                        if model_path:
                            self.load_model(model_path)
                            self.chat_history = []
                    else:
                        self.console.print(f"[red]Неизвестная команда:[/] {cmd}")
                    continue

                self.chat(user_input)

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Прервано[/]")
                if Confirm.ask("Выйти?", default=False):
                    break
            except EOFError:
                self.console.print("\n[cyan]До свидания![/]")
                break


def main():
    """Точка входа."""
    cli = LocalModelCLI()
    cli.run()


if __name__ == "__main__":
    main()
