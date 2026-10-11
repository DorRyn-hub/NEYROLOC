#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NEYROLOCK - AI Chat CLI
Универсальный чат с AI моделями

Поддерживает:
  - LM Studio (локально, бесплатно)
  - Ollama (локально, бесплатно)
  - Groq (облако, бесплатно)
"""

import os
import sys
import json
import datetime
from pathlib import Path
from typing import Optional, List, Dict
from enum import Enum

# Проверка зависимостей
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import print as rprint
except ImportError:
    print("=" * 50)
    print("NEYROLOCK - Установка зависимостей")
    print("=" * 50)
    print("\nНеобходимо установить библиотеку 'rich'")
    print("\nВыполните команду:")
    print("  pip install rich")
    print("\nИли для полной установки:")
    print("  pip install rich openai")
    print("=" * 50)
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("=" * 50)
    print("NEYROLOCK - Установка зависимостей")
    print("=" * 50)
    print("\nНеобходимо установить библиотеку 'openai'")
    print("\nВыполните команду:")
    print("  pip install openai")
    print("=" * 50)
    sys.exit(1)


class Backend(Enum):
    LMSTUDIO = "LM Studio"
    OLLAMA = "Ollama"
    GROQ = "Groq (облако)"


class NeyrolockCLI:
    """Главный класс приложения."""

    VERSION = "3.1.0"

    def __init__(self):
        self.console = Console()
        self.client: Optional[OpenAI] = None
        self.backend: Optional[Backend] = None
        self.model_name: str = ""
        self.chat_history: List[Dict] = []
        self.system_prompt = "Ты полезный AI ассистент. Отвечай на русском языке."

        # Папка для конфигурации
        self.config_dir = Path.home() / ".neyrolock"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

        # Загрузка конфигурации
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Загружает конфигурацию."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_config(self):
        """Сохраняет конфигурацию."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def show_banner(self):
        """Показывает баннер."""
        banner = f"""
[bold cyan]╔════════════════════════════════════════════════════════╗
║                                                        ║
║     ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗        ║
║     ████╗  ██║██╔════╝╚██╗ ██╔╝██╔══██╗██╔═══██╗       ║
║     ██╔██╗ ██║█████╗   ╚████╔╝ ██████╔╝██║   ██║       ║
║     ██║╚██╗██║██╔══╝    ╚██╔╝  ██╔══██╗██║   ██║       ║
║     ██║ ╚████║███████╗   ██║   ██║  ██║╚██████╔╝       ║
║     ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝        ║
║                                                        ║
║              [white]AI Chat Interface v{self.VERSION}[/white]                  ║
║                                                        ║
╚════════════════════════════════════════════════════════╝[/bold cyan]
"""
        self.console.print(banner)

    def show_backend_menu(self):
        """Показывает меню выбора backend."""
        self.console.print()

        table = Table(
            title="[bold]Выберите AI провайдера[/bold]",
            show_header=True,
            header_style="bold cyan"
        )
        table.add_column("#", style="cyan", width=4, justify="center")
        table.add_column("Провайдер", style="green", width=15)
        table.add_column("Описание", style="white", width=30)
        table.add_column("Требования", style="yellow", width=25)

        backends = [
            ("1", "LM Studio", "Локальный, любые модели", "LM Studio + модель"),
            ("2", "Ollama", "Локальный, простой", "Ollama + модель"),
            ("3", "Groq", "Облако, бесплатно, быстро", "API ключ (бесплатный)"),
        ]

        for num, name, desc, req in backends:
            table.add_row(num, name, desc, req)

        self.console.print(table)
        self.console.print()

    def setup_lmstudio(self) -> bool:
        """Настройка LM Studio."""
        self.console.print("\n[bold cyan]Настройка LM Studio[/bold cyan]\n")

        self.console.print(
            Panel(
                "[bold]Перед использованием убедитесь:[/bold]\n\n"
                "1. LM Studio запущен\n"
                "2. Модель загружена (кнопка 'Load' в LM Studio)\n"
                "3. Сервер активен (зелёный индикатор)\n\n"
                "[dim]Скачать LM Studio: https://lmstudio.ai[/dim]",
                title="Требования",
                border_style="yellow"
            )
        )

        base_url = Prompt.ask(
            "\n[cyan]URL сервера LM Studio[/cyan]",
            default="http://localhost:1234/v1"
        )

        try:
            with self.console.status("[bold green]Подключение к LM Studio..."):
                self.client = OpenAI(
                    base_url=base_url,
                    api_key="lm-studio"
                )

                # Получаем список моделей
                models = self.client.models.list()
                model_list = [m.id for m in models.data]

                if not model_list:
                    self.console.print(
                        "\n[bold red]Нет загруженных моделей![/bold red]\n"
                        "Загрузите модель в LM Studio и попробуйте снова.\n"
                    )
                    return False

            # Выбор модели
            self.console.print("\n[bold green]Доступные модели:[/bold green]")
            for i, model in enumerate(model_list, 1):
                self.console.print(f"  {i}. {model}")

            if len(model_list) == 1:
                self.model_name = model_list[0]
            else:
                choice = Prompt.ask(
                    "\n[cyan]Выберите модель (номер)[/cyan]",
                    default="1"
                )
                try:
                    idx = int(choice) - 1
                    self.model_name = model_list[idx]
                except (ValueError, IndexError):
                    self.model_name = model_list[0]

            self.backend = Backend.LMSTUDIO
            self.config['last_backend'] = 'lmstudio'
            self.config['lmstudio_url'] = base_url
            self._save_config()

            self.console.print(f"\n[bold green]Подключено к LM Studio[/bold green]")
            self.console.print(f"[dim]Модель: {self.model_name}[/dim]\n")
            return True

        except Exception as e:
            self.console.print(
                Panel(
                    f"[bold red]Ошибка подключения:[/bold red]\n\n{e}\n\n"
                    "[yellow]Проверьте:[/yellow]\n"
                    "  1. LM Studio запущен\n"
                    "  2. Модель загружена\n"
                    "  3. Сервер работает на порту 1234",
                    title="Ошибка",
                    border_style="red"
                )
            )
            return False

    def setup_ollama(self) -> bool:
        """Настройка Ollama."""
        self.console.print("\n[bold cyan]Настройка Ollama[/bold cyan]\n")

        self.console.print(
            Panel(
                "[bold]Перед использованием:[/bold]\n\n"
                "1. Установите Ollama: https://ollama.com\n"
                "2. Запустите: [cyan]ollama serve[/cyan]\n"
                "3. Скачайте модель: [cyan]ollama pull llama3.2[/cyan]\n\n"
                "[dim]Популярные модели: llama3.2, mistral, gemma2[/dim]",
                title="Требования",
                border_style="yellow"
            )
        )

        base_url = Prompt.ask(
            "\n[cyan]URL сервера Ollama[/cyan]",
            default="http://localhost:11434/v1"
        )

        model_name = Prompt.ask(
            "[cyan]Имя модели[/cyan]",
            default="llama3.2"
        )

        try:
            with self.console.status("[bold green]Проверка подключения..."):
                self.client = OpenAI(
                    base_url=base_url,
                    api_key="ollama"
                )

                # Тестовый запрос
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )

            self.model_name = model_name
            self.backend = Backend.OLLAMA
            self.config['last_backend'] = 'ollama'
            self.config['ollama_url'] = base_url
            self.config['ollama_model'] = model_name
            self._save_config()

            self.console.print(f"\n[bold green]Подключено к Ollama[/bold green]")
            self.console.print(f"[dim]Модель: {model_name}[/dim]\n")
            return True

        except Exception as e:
            self.console.print(
                Panel(
                    f"[bold red]Ошибка подключения:[/bold red]\n\n{e}\n\n"
                    "[yellow]Проверьте:[/yellow]\n"
                    f"  1. Ollama запущен: [cyan]ollama serve[/cyan]\n"
                    f"  2. Модель скачана: [cyan]ollama pull {model_name}[/cyan]",
                    title="Ошибка",
                    border_style="red"
                )
            )
            return False

    def setup_groq(self) -> bool:
        """Настройка Groq."""
        self.console.print("\n[bold cyan]Настройка Groq (облако)[/bold cyan]\n")

        self.console.print(
            Panel(
                "[bold]Groq - бесплатный облачный AI[/bold]\n\n"
                "1. Получите API ключ: https://console.groq.com/keys\n"
                "2. Регистрация бесплатная\n"
                "3. Быстрые ответы (до 500 токенов/сек)\n\n"
                "[dim]Доступные модели: llama-3.3-70b, mixtral-8x7b[/dim]",
                title="Информация",
                border_style="cyan"
            )
        )

        # Проверяем сохранённый ключ
        saved_key = self.config.get('groq_api_key', '')
        if saved_key:
            use_saved = Confirm.ask(
                "\n[cyan]Использовать сохранённый API ключ?[/cyan]",
                default=True
            )
            if use_saved:
                api_key = saved_key
            else:
                api_key = Prompt.ask("[cyan]Введите Groq API ключ[/cyan]", password=True)
        else:
            api_key = Prompt.ask("[cyan]Введите Groq API ключ[/cyan]", password=True)

        models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]

        self.console.print("\n[bold]Доступные модели:[/bold]")
        for i, m in enumerate(models, 1):
            self.console.print(f"  {i}. {m}")

        choice = Prompt.ask(
            "\n[cyan]Выберите модель (номер)[/cyan]",
            default="1"
        )

        try:
            idx = int(choice) - 1
            model_name = models[idx]
        except (ValueError, IndexError):
            model_name = models[0]

        try:
            with self.console.status("[bold green]Проверка API ключа..."):
                self.client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=api_key
                )

                # Тестовый запрос
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )

            self.model_name = model_name
            self.backend = Backend.GROQ
            self.config['last_backend'] = 'groq'
            self.config['groq_api_key'] = api_key
            self.config['groq_model'] = model_name
            self._save_config()

            self.console.print(f"\n[bold green]Подключено к Groq[/bold green]")
            self.console.print(f"[dim]Модель: {model_name}[/dim]\n")
            return True

        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                self.console.print(
                    Panel(
                        "[bold red]Неверный API ключ![/bold red]\n\n"
                        "Получите ключ на https://console.groq.com/keys",
                        title="Ошибка",
                        border_style="red"
                    )
                )
            else:
                self.console.print(
                    Panel(
                        f"[bold red]Ошибка:[/bold red]\n\n{e}",
                        title="Ошибка",
                        border_style="red"
                    )
                )
            return False

    def setup_backend(self) -> bool:
        """Настройка провайдера."""
        self.show_backend_menu()

        choice = Prompt.ask(
            "[cyan]Выберите провайдера[/cyan]",
            choices=["1", "2", "3"],
            default="1"
        )

        if choice == "1":
            return self.setup_lmstudio()
        elif choice == "2":
            return self.setup_ollama()
        elif choice == "3":
            return self.setup_groq()

        return False

    def chat(self, user_message: str):
        """Отправляет сообщение и получает ответ."""
        if not self.client:
            self.console.print("[red]Провайдер не настроен![/red]")
            return

        # Формируем сообщения
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.chat_history)
        messages.append({"role": "user", "content": user_message})

        try:
            self.console.print("\n[bold green]AI:[/bold green] ", end="")

            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                max_tokens=2048,
                temperature=0.7
            )

            response_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    self.console.print(content, end="", style="green")
                    response_text += content

            self.console.print("\n")

            # Сохраняем в историю
            self.chat_history.append({"role": "user", "content": user_message})
            self.chat_history.append({"role": "assistant", "content": response_text})

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Прервано[/yellow]\n")
        except Exception as e:
            self.console.print(f"\n[red]Ошибка: {e}[/red]\n")

    def show_help(self):
        """Показывает справку."""
        help_text = """
[bold cyan]Команды:[/bold cyan]

[yellow]/help[/yellow]      - Эта справка
[yellow]/clear[/yellow]     - Очистить историю диалога
[yellow]/history[/yellow]   - Показать историю
[yellow]/save[/yellow]      - Сохранить диалог в файл
[yellow]/switch[/yellow]    - Сменить AI провайдера
[yellow]/system[/yellow]    - Изменить системный промпт
[yellow]/exit[/yellow]      - Выход

[bold cyan]Горячие клавиши:[/bold cyan]

[yellow]Ctrl+C[/yellow]     - Прервать генерацию
[yellow]Ctrl+D[/yellow]     - Выход
        """
        self.console.print(Panel(help_text, title="Справка", border_style="cyan"))

    def show_history(self):
        """Показывает историю."""
        if not self.chat_history:
            self.console.print("[yellow]История пуста[/yellow]")
            return

        text = ""
        for msg in self.chat_history:
            if msg['role'] == 'user':
                text += f"[bold blue]Вы:[/bold blue] {msg['content']}\n\n"
            else:
                text += f"[bold green]AI:[/bold green] {msg['content']}\n\n"

        self.console.print(Panel(text.strip(), title="История диалога", border_style="blue"))

    def save_history(self):
        """Сохраняет историю."""
        if not self.chat_history:
            self.console.print("[yellow]История пуста[/yellow]")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config_dir / f"chat_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "backend": self.backend.value if self.backend else None,
            "model": self.model_name,
            "messages": self.chat_history
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.console.print(f"[green]Сохранено в:[/green] {filename}")

    def set_system_prompt(self):
        """Изменяет системный промпт."""
        self.console.print(f"\n[dim]Текущий промпт: {self.system_prompt}[/dim]\n")
        new_prompt = Prompt.ask("[cyan]Новый системный промпт[/cyan]")
        if new_prompt:
            self.system_prompt = new_prompt
            self.console.print("[green]Системный промпт обновлён[/green]")

    def run(self):
        """Главный цикл."""
        self.show_banner()

        # Настройка провайдера
        while not self.setup_backend():
            if not Confirm.ask("\n[yellow]Попробовать снова?[/yellow]", default=True):
                self.console.print("\n[cyan]До свидания![/cyan]")
                return

        self.console.print(
            "[dim]Введите сообщение или /help для справки[/dim]\n"
        )

        # Основной цикл
        while True:
            try:
                user_input = Prompt.ask("[bold blue]Вы[/bold blue]").strip()

                if not user_input:
                    continue

                # Обработка команд
                if user_input.startswith('/'):
                    cmd = user_input.lower().split()[0]

                    if cmd in ['/exit', '/quit', '/q']:
                        self.console.print("\n[cyan]До свидания![/cyan]")
                        break
                    elif cmd == '/help':
                        self.show_help()
                    elif cmd == '/clear':
                        self.chat_history = []
                        self.console.print("[green]История очищена[/green]")
                    elif cmd == '/history':
                        self.show_history()
                    elif cmd == '/save':
                        self.save_history()
                    elif cmd == '/switch':
                        self.setup_backend()
                    elif cmd == '/system':
                        self.set_system_prompt()
                    else:
                        self.console.print(
                            f"[red]Неизвестная команда: {cmd}[/red]\n"
                            "Введите /help для справки"
                        )
                    continue

                # Отправляем сообщение
                self.chat(user_input)

            except KeyboardInterrupt:
                self.console.print("\n")
                if Confirm.ask("[yellow]Выйти?[/yellow]", default=False):
                    self.console.print("\n[cyan]До свидания![/cyan]")
                    break
            except EOFError:
                self.console.print("\n[cyan]До свидания![/cyan]")
                break


def main():
    """Точка входа."""
    try:
        cli = NeyrolockCLI()
        cli.run()
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()
