#!/usr/bin/env python
"""
🤖 AI CLI - Универсальный интерфейс для работы с AI моделями

Поддерживает:
  • LM Studio (локально)
  • Ollama (локально)
  • Локальные GGUF модели (HuggingFace)
  • Groq (облако, бесплатно)
  • OpenAI (облако, платно)
  • Скачивание моделей с HuggingFace прямо из программы!
"""

import os
import sys
import json
import readline
import datetime
from pathlib import Path
from typing import Optional, List, Dict
from enum import Enum

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
except ImportError:
    print("❌ Установите: pip install rich")
    sys.exit(1)


class Backend(Enum):
    """Типы backend'ов."""
    LMSTUDIO = "lmstudio"
    OLLAMA = "ollama"
    LOCAL = "local"
    GROQ = "groq"
    OPENAI = "openai"


class AICLI:
    """Универсальный CLI для работы с различными AI backend'ами."""

    def __init__(self):
        """Инициализация."""
        self.console = Console()
        self.backend = None
        self.client = None
        self.model = None
        self.chat_history = []

        # Настройка папок
        self.config_dir = Path.home() / ".ai_cli"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

        # История команд
        histfile = self.config_dir / ".cli_history"
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
║                    🤖 AI CLI v2.0                         ║
║         Универсальный интерфейс для работы с AI           ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")

    def show_backend_menu(self):
        """Показывает меню выбора backend."""
        table = Table(title="Выберите backend", show_header=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Backend", style="green")
        table.add_column("Описание", style="white")
        table.add_column("Требования", style="yellow")

        backends = [
            ("1", "LM Studio", "Локальный, полнофункциональный", "LM Studio + модель"),
            ("2", "Ollama", "Локальный, простой", "Ollama + модель"),
            ("3", "Local GGUF", "Локальный, любые модели", "Файл .gguf"),
            ("4", "Groq", "Облако, бесплатно, быстро", "API ключ (бесплатный)"),
            ("5", "OpenAI", "Облако, платно, качественно", "API ключ (платный)"),
            ("6", "Скачать модель", "HuggingFace → GGUF", "Интернет")
        ]

        for num, name, desc, req in backends:
            table.add_row(num, name, desc, req)

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def setup_lmstudio(self):
        """Настройка LM Studio."""
        try:
            import lmstudio as lms

            with self.console.status("[bold green]Подключение к LM Studio..."):
                self.client = lms.Client()
                loaded = self.client.llm.list_loaded()

                if not loaded:
                    self.console.print("[red]⚠ Нет загруженных моделей в LM Studio[/]")
                    return False

                self.model = self.client.llm.get()
                self.backend = Backend.LMSTUDIO

                self.console.print(f"[green]✓ Подключено к LM Studio[/]")
                self.console.print(f"[dim]Модель: {loaded[0].identifier}[/]\n")
                return True

        except ImportError:
            self.console.print("[red]Установите: pip install lmstudio[/]")
            return False
        except Exception as e:
            self.console.print(f"[red]Ошибка подключения к LM Studio: {e}[/]")
            return False

    def setup_ollama(self):
        """Настройка Ollama."""
        try:
            from openai import OpenAI

            base_url = Prompt.ask(
                "Base URL Ollama",
                default="http://localhost:11434/v1"
            )

            model_name = Prompt.ask(
                "Имя модели",
                default="llama3.2:3b"
            )

            self.client = OpenAI(
                base_url=base_url,
                api_key="ollama"  # Ollama не требует API ключ
            )

            # Проверка подключения
            with self.console.status("[bold green]Проверка подключения..."):
                try:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=5
                    )
                except Exception as e:
                    self.console.print(f"[red]Ошибка: {e}[/]")
                    self.console.print("[yellow]Убедитесь что Ollama запущен: ollama serve[/]")
                    return False

            self.backend = Backend.OLLAMA
            self.model = model_name

            self.console.print(f"[green]✓ Подключено к Ollama[/]")
            self.console.print(f"[dim]Модель: {model_name}[/]\n")
            return True

        except ImportError:
            self.console.print("[red]Установите: pip install openai[/]")
            return False

    def setup_local_gguf(self):
        """Настройка локальной GGUF модели."""
        try:
            from llama_cpp import Llama
            from model_manager import ModelManager

            manager = ModelManager()

            # Показываем скачанные модели
            downloaded = manager.list_downloaded_models()

            if downloaded:
                self.console.print("\n[bold cyan]Скачанные модели:[/]\n")
                manager.show_downloaded_models()

                if Confirm.ask("\nИспользовать одну из этих моделей?", default=True):
                    model_idx = int(Prompt.ask(
                        "Номер модели",
                        choices=[str(i+1) for i in range(len(downloaded))],
                        default="1"
                    )) - 1

                    model_path = str(downloaded[model_idx]['path'])
                else:
                    if Confirm.ask("Скачать новую модель?", default=True):
                        model_path = manager.interactive_download()
                        if not model_path:
                            return False
                        model_path = str(model_path)
                    else:
                        # Ручной ввод пути
                        model_path = Prompt.ask("Введите путь к файлу .gguf")
            else:
                self.console.print("\n[yellow]Скачанных моделей нет[/]")
                if Confirm.ask("Скачать модель с HuggingFace?", default=True):
                    model_path = manager.interactive_download()
                    if not model_path:
                        return False
                    model_path = str(model_path)
                else:
                    model_path = Prompt.ask("Введите путь к файлу .gguf")

            # Загружаем модель
            n_ctx = int(Prompt.ask("Размер контекста (токенов)", default="2048"))
            n_gpu = int(Prompt.ask("Слои на GPU (-1 = все)", default="-1"))

            with self.console.status("[bold green]Загрузка модели..."):
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu,
                    verbose=False
                )

            self.backend = Backend.LOCAL
            self.console.print(f"[green]✓ Модель загружена[/]")
            self.console.print(f"[dim]Файл: {Path(model_path).name}[/]\n")
            return True

        except ImportError as e:
            if "llama_cpp" in str(e):
                self.console.print("[red]Установите: pip install llama-cpp-python[/]")
            else:
                self.console.print("[red]Установите: pip install huggingface-hub[/]")
            return False
        except Exception as e:
            self.console.print(f"[red]Ошибка: {e}[/]")
            return False

    def setup_groq(self):
        """Настройка Groq."""
        try:
            from openai import OpenAI

            api_key = Prompt.ask(
                "Groq API ключ",
                password=True
            )

            model_name = Prompt.ask(
                "Модель",
                default="llama-3.3-70b-versatile",
                choices=["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]
            )

            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=api_key
            )

            # Тестовый запрос
            with self.console.status("[bold green]Проверка ключа..."):
                try:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=5
                    )
                except Exception as e:
                    self.console.print(f"[red]Ошибка: {e}[/]")
                    return False

            self.backend = Backend.GROQ
            self.model = model_name

            self.console.print(f"[green]✓ Подключено к Groq[/]")
            self.console.print(f"[dim]Модель: {model_name}[/]\n")
            return True

        except ImportError:
            self.console.print("[red]Установите: pip install openai[/]")
            return False

    def setup_openai(self):
        """Настройка OpenAI."""
        try:
            from openai import OpenAI

            api_key = Prompt.ask(
                "OpenAI API ключ",
                password=True
            )

            model_name = Prompt.ask(
                "Модель",
                default="gpt-4o-mini",
                choices=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
            )

            self.client = OpenAI(api_key=api_key)

            # Тестовый запрос
            with self.console.status("[bold green]Проверка ключа..."):
                try:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=5
                    )
                except Exception as e:
                    self.console.print(f"[red]Ошибка: {e}[/]")
                    return False

            self.backend = Backend.OPENAI
            self.model = model_name

            self.console.print(f"[green]✓ Подключено к OpenAI[/]")
            self.console.print(f"[dim]Модель: {model_name}[/]\n")
            return True

        except ImportError:
            self.console.print("[red]Установите: pip install openai[/]")
            return False

    def download_models_menu(self):
        """Меню скачивания моделей."""
        try:
            from model_manager import ModelManager

            manager = ModelManager()
            model_path = manager.interactive_download()

            if model_path and Confirm.ask("\nИспользовать эту модель сейчас?", default=True):
                return self.setup_local_gguf()

            return False

        except ImportError:
            self.console.print("[red]Установите: pip install huggingface-hub[/]")
            return False

    def setup_backend(self):
        """Настройка backend."""
        self.show_backend_menu()

        choice = Prompt.ask(
            "Выберите backend",
            choices=["1", "2", "3", "4", "5", "6"],
            default="3"
        )

        if choice == "1":
            return self.setup_lmstudio()
        elif choice == "2":
            return self.setup_ollama()
        elif choice == "3":
            return self.setup_local_gguf()
        elif choice == "4":
            return self.setup_groq()
        elif choice == "5":
            return self.setup_openai()
        elif choice == "6":
            return self.download_models_menu()

        return False

    def chat(self, user_message: str):
        """Отправляет сообщение модели."""
        if not self.model:
            self.console.print("[red]Модель не настроена![/]")
            return

        try:
            self.console.print("\n[bold green]🤖 AI:[/] ", end="")

            if self.backend == Backend.LMSTUDIO:
                # LM Studio
                import lmstudio as lms
                chat = lms.Chat()
                for msg in self.chat_history:
                    if msg['role'] == 'user':
                        chat.add_user_message(msg['content'])
                    elif msg['role'] == 'assistant':
                        chat.add_assistant_message(msg['content'])

                chat.add_user_message(user_message)

                response_text = ""
                for fragment in self.model.respond_stream(chat):
                    self.console.print(fragment.content, end="", style="green")
                    response_text += fragment.content

                self.chat_history.append({"role": "user", "content": user_message})
                self.chat_history.append({"role": "assistant", "content": response_text})

            elif self.backend == Backend.LOCAL:
                # Локальная GGUF модель
                messages = self.chat_history + [{"role": "user", "content": user_message}]

                response_text = ""
                stream = self.model.create_chat_completion(
                    messages=messages,
                    stream=True,
                    max_tokens=512,
                    temperature=0.7
                )

                for chunk in stream:
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            content = delta['content']
                            self.console.print(content, end="", style="green")
                            response_text += content

                self.chat_history.append({"role": "user", "content": user_message})
                self.chat_history.append({"role": "assistant", "content": response_text})

            else:
                # OpenAI-совместимые API (Ollama, Groq, OpenAI)
                messages = self.chat_history + [{"role": "user", "content": user_message}]

                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True
                )

                response_text = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        self.console.print(content, end="", style="green")
                        response_text += content

                self.chat_history.append({"role": "user", "content": user_message})
                self.chat_history.append({"role": "assistant", "content": response_text})

            self.console.print("\n")

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠ Прервано[/]\n")
        except Exception as e:
            self.console.print(f"\n[red]✗ Ошибка: {e}[/]\n")

    def show_help(self):
        """Показывает справку."""
        help_text = """
[bold cyan]Команды:[/]

/help      - Эта справка
/history   - Показать историю
/clear     - Очистить историю
/save      - Сохранить диалог
/download  - Скачать модель с HuggingFace
/switch    - Сменить backend
/exit      - Выход
        """
        self.console.print(Panel(help_text, title="Справка", border_style="cyan"))

    def show_history(self):
        """Показывает историю."""
        if not self.chat_history:
            self.console.print("[yellow]История пуста[/]")
            return

        text = "\n\n".join([
            f"[bold blue]👤 User:[/] {msg['content']}" if msg['role'] == 'user'
            else f"[bold green]🤖 AI:[/] {msg['content']}"
            for msg in self.chat_history
        ])

        self.console.print(Panel(text, title="История", border_style="blue"))

    def save_history(self):
        """Сохраняет историю."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config_dir / f"chat_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "backend": self.backend.value if self.backend else None,
                "model": str(self.model) if self.model else None,
                "messages": self.chat_history
            }, f, ensure_ascii=False, indent=2)

        self.console.print(f"[green]✓ Сохранено в:[/] {filename}")

    def run(self):
        """Главный цикл."""
        self.show_banner()

        # Настройка backend
        if not self.setup_backend():
            self.console.print("\n[yellow]Выход без настройки backend[/]")
            return

        self.console.print("[dim]Введите сообщение или команду (/help для справки)[/]\n")

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
                    elif cmd == '/history':
                        self.show_history()
                    elif cmd == '/clear':
                        self.chat_history = []
                        self.console.print("[green]✓ История очищена[/]")
                    elif cmd == '/save':
                        self.save_history()
                    elif cmd == '/download':
                        self.download_models_menu()
                    elif cmd == '/switch':
                        self.setup_backend()
                    else:
                        self.console.print(f"[red]Неизвестная команда: {cmd}[/]")
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
    cli = AICLI()
    cli.run()


if __name__ == "__main__":
    main()
