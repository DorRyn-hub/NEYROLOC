#!/usr/bin/env python
"""
Универсальный CLI для работы с LLM БЕЗ LM Studio
Поддерживает: Ollama, OpenAI, Groq, LocalAI и другие
"""

import os
import sys
import json
import readline
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
except ImportError:
    print("❌ Установите библиотеку 'rich': pip install rich")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("❌ Установите библиотеку 'openai': pip install openai")
    sys.exit(1)


class UniversalCLI:
    """CLI для работы с различными LLM backend'ами."""

    def __init__(self):
        """Инициализация."""
        self.console = Console()
        self.client: Optional[OpenAI] = None
        self.chat_history = []
        self.backend = None
        self.model = None

        # Настройка истории
        self.history_dir = Path.home() / ".universal_llm_cli"
        self.history_dir.mkdir(exist_ok=True)

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
║            UNIVERSAL LLM CLI (БЕЗ LM STUDIO)              ║
║          Работает с Ollama, OpenAI, Groq и др.            ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")

    def setup_backend(self):
        """Настройка backend'а."""
        self.console.print("\n[bold yellow]Выберите backend:[/]\n")

        backends = {
            "1": ("Ollama (локально)", "ollama"),
            "2": ("OpenAI (облако, платно)", "openai"),
            "3": ("Groq (облако, бесплатно)", "groq"),
            "4": ("Пользовательский URL", "custom"),
        }

        for key, (name, _) in backends.items():
            self.console.print(f"  {key}. {name}")

        choice = Prompt.ask("\nВаш выбор", choices=list(backends.keys()), default="1")
        backend_name, backend_type = backends[choice]

        self.console.print(f"\n[green]✓ Выбран backend:[/] {backend_name}\n")

        if backend_type == "ollama":
            self._setup_ollama()
        elif backend_type == "openai":
            self._setup_openai()
        elif backend_type == "groq":
            self._setup_groq()
        elif backend_type == "custom":
            self._setup_custom()

    def _setup_ollama(self):
        """Настройка Ollama."""
        self.backend = "ollama"
        base_url = "http://localhost:11434/v1"

        try:
            self.client = OpenAI(
                base_url=base_url,
                api_key="ollama"  # Ollama не требует ключ, но поле обязательное
            )

            # Пробуем получить список моделей
            self.console.print("[dim]Проверка подключения к Ollama...[/]")

            # Список популярных моделей для Ollama
            suggested_models = [
                "llama3.2:3b",
                "qwen2.5:7b",
                "llama3.2:1b",
                "phi3:mini"
            ]

            self.console.print("\n[yellow]Рекомендуемые модели:[/]")
            for i, model in enumerate(suggested_models, 1):
                self.console.print(f"  {i}. {model}")

            self.console.print("\n[dim]Если модель не установлена, запустите:[/]")
            self.console.print("[dim]  ollama pull llama3.2:3b[/]\n")

            choice = Prompt.ask(
                "Выберите модель (1-4 или введите имя)",
                default="1"
            )

            # Если ввели номер - выбираем модель по индексу
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(suggested_models):
                    self.model = suggested_models[idx]
                else:
                    self.model = choice  # Если номер вне диапазона - используем как имя
            except ValueError:
                self.model = choice  # Если не номер - используем как имя модели

            self.console.print(f"[green]✓ Используется модель:[/] {self.model}\n")

        except Exception as e:
            self.console.print(
                Panel(
                    f"[red]Ошибка подключения к Ollama![/]\n\n"
                    f"{e}\n\n"
                    f"[yellow]Установите Ollama:[/]\n"
                    f"  macOS: brew install ollama\n"
                    f"  Linux: curl -fsSL https://ollama.com/install.sh | sh\n\n"
                    f"[yellow]Запустите сервер:[/]\n"
                    f"  ollama serve\n\n"
                    f"[yellow]Загрузите модель:[/]\n"
                    f"  ollama pull llama3.2:3b",
                    title="❌ Ollama не доступен",
                    border_style="red"
                )
            )
            sys.exit(1)

    def _setup_openai(self):
        """Настройка OpenAI."""
        self.backend = "openai"

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.console.print("[yellow]Введите OpenAI API ключ:[/]")
            self.console.print("[dim](или установите переменную OPENAI_API_KEY)[/]")
            api_key = Prompt.ask("API Key", password=True)

        self.client = OpenAI(api_key=api_key)
        self.model = Prompt.ask(
            "Модель",
            default="gpt-3.5-turbo"
        )

        self.console.print(f"[green]✓ Настроен OpenAI с моделью:[/] {self.model}\n")

    def _setup_groq(self):
        """Настройка Groq."""
        self.backend = "groq"

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            self.console.print("[yellow]Получите бесплатный ключ на https://console.groq.com[/]")
            api_key = Prompt.ask("Groq API Key", password=True)

        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )

        models = ["llama-3.2-3b-preview", "mixtral-8x7b-32768", "gemma2-9b-it"]
        self.console.print("\n[yellow]Доступные модели:[/]")
        for i, m in enumerate(models, 1):
            self.console.print(f"  {i}. {m}")

        choice = Prompt.ask(
            "Выберите модель (1-3 или введите имя)",
            default="1"
        )

        # Если ввели номер - выбираем модель по индексу
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                self.model = models[idx]
            else:
                self.model = choice  # Если номер вне диапазона - используем как имя
        except ValueError:
            self.model = choice  # Если не номер - используем как имя модели

        self.console.print(f"[green]✓ Настроен Groq с моделью:[/] {self.model}\n")

    def _setup_custom(self):
        """Настройка пользовательского сервера."""
        self.backend = "custom"

        base_url = Prompt.ask(
            "Base URL",
            default="http://localhost:8000/v1"
        )

        api_key = Prompt.ask(
            "API Key (или оставьте пустым)",
            default="none"
        )

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

        self.model = Prompt.ask("Имя модели")
        self.console.print(f"[green]✓ Настроен кастомный backend[/]\n")

    def chat(self, user_message: str):
        """Отправляет сообщение и получает ответ."""
        # Добавляем сообщение в историю
        self.chat_history.append({
            "role": "user",
            "content": user_message
        })

        try:
            self.console.print("\n[bold green]🤖 Ассистент:[/] ", end="")

            # Потоковый ответ
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.chat_history,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    self.console.print(content, end="", style="green")
                    full_response += content

            self.console.print("\n")

            # Добавляем ответ в историю
            self.chat_history.append({
                "role": "assistant",
                "content": full_response
            })

        except Exception as e:
            self.console.print(f"\n[red]Ошибка:[/] {e}\n")

    def show_help(self):
        """Показывает справку."""
        help_text = """
[bold cyan]Команды:[/]

/help     - Эта справка
/history  - Показать историю
/clear    - Очистить историю
/save     - Сохранить диалог
/exit     - Выход
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

    def save_history(self):
        """Сохраняет историю."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.history_dir / f"chat_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "backend": self.backend,
                "model": self.model,
                "messages": self.chat_history
            }, f, ensure_ascii=False, indent=2)

        self.console.print(f"[green]✓ Сохранено в:[/] {filename}")

    def run(self):
        """Главный цикл."""
        self.show_banner()
        self.setup_backend()

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
                    elif cmd == '/history':
                        self.show_history()
                    elif cmd == '/clear':
                        self.chat_history = []
                        self.console.print("[green]✓ История очищена[/]")
                    elif cmd == '/save':
                        self.save_history()
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
    cli = UniversalCLI()
    cli.run()


if __name__ == "__main__":
    main()
