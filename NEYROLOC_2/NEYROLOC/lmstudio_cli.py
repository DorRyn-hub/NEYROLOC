#!/usr/bin/env python
"""
LM Studio CLI - Консольный интерфейс для работы с LM Studio
Красивый, функциональный CLI в стиле Warp GPT
"""

import os
import sys
import json
import readline
import datetime
from pathlib import Path
from typing import Optional, List, Dict

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.prompt import Prompt
    from rich import print as rprint
except ImportError:
    print("Ошибка: Необходимо установить библиотеку 'rich'")
    print("Выполните: pip install rich")
    sys.exit(1)

try:
    import lmstudio as lms
except ImportError:
    print("Ошибка: Необходимо установить библиотеку 'lmstudio'")
    print("Выполните: pip install lmstudio")
    sys.exit(1)


class LMStudioCLI:
    """Главный класс CLI приложения."""

    def __init__(self):
        """Инициализация CLI."""
        self.console = Console()
        self.client: Optional[lms.Client] = None
        self.model = None
        self.chat = None
        self.current_model_id: Optional[str] = None
        self.history_dir = Path.home() / ".lmstudio_cli" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Настройка readline для истории команд
        histfile = self.history_dir / ".cli_history"
        try:
            readline.read_history_file(histfile)
            readline.set_history_length(1000)
        except (FileNotFoundError, PermissionError, OSError):
            # Игнорируем ошибки чтения истории - не критично
            pass

        import atexit
        # Регистрируем сохранение истории при выходе (с обработкой ошибок)
        def save_history():
            try:
                readline.write_history_file(histfile)
            except (PermissionError, OSError):
                pass  # Не критично, если не удалось сохранить историю
        atexit.register(save_history)

    def show_banner(self):
        """Отображает приветственный баннер."""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                  LM STUDIO CLI INTERFACE                  ║
║                   Powered by lmstudio-python              ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")
        self.console.print(
            "Введите [bold yellow]/help[/] для справки или начните диалог\n",
            style="dim"
        )

    def connect_to_server(self) -> bool:
        """
        Подключается к LM Studio серверу.

        Returns:
            True если подключение успешно, False иначе
        """
        try:
            with self.console.status("[bold green]Подключение к LM Studio..."):
                self.client = lms.Client()
                # Проверяем доступность моделей
                loaded_models = self.client.llm.list_loaded()

                if not loaded_models:
                    self.console.print(
                        "[bold red]⚠ Нет загруженных моделей![/]",
                        style="bold red"
                    )
                    self.console.print(
                        "Загрузите модель в LM Studio перед использованием\n"
                    )
                    return False

                # Получаем первую доступную модель
                self.model = self.client.llm.get()
                self.current_model_id = loaded_models[0].identifier

                self.console.print(
                    f"[bold green]✓ Подключено к модели:[/] {self.current_model_id}\n"
                )

                # Создаем новый чат
                self.reset_chat()

                return True

        except ConnectionError as e:
            self._show_connection_error(str(e))
            return False

        except Exception as e:
            # Обрабатываем все остальные ошибки, включая "port is not yet resolved"
            error_msg = str(e).lower()
            if "port" in error_msg or "not reachable" in error_msg or "connection" in error_msg:
                self._show_connection_error(str(e))
            else:
                self.console.print(
                    Panel(
                        f"[bold red]Неожиданная ошибка:[/]\n\n{e}\n\n"
                        f"[yellow]Попробуйте:[/]\n"
                        f"  • Перезапустить LM Studio\n"
                        f"  • Проверить логи LM Studio на наличие ошибок\n"
                        f"  • Создать issue на GitHub если проблема повторяется",
                        title="Ошибка",
                        border_style="red"
                    )
                )
            return False

    def _show_connection_error(self, error_message: str):
        """
        Показывает красивое сообщение об ошибке подключения.

        Args:
            error_message: Текст ошибки
        """
        self.console.print(
            Panel(
                f"[bold red]❌ LM Studio не доступен[/]\n\n"
                f"[dim]Ошибка: {error_message}[/]\n\n"
                f"[yellow]📋 Что нужно сделать:[/]\n\n"
                f"[bold cyan]1. Запустите LM Studio[/]\n"
                f"   • Скачайте с https://lmstudio.ai (если еще не установлен)\n"
                f"   • Откройте приложение LM Studio\n\n"
                f"[bold cyan]2. Загрузите модель[/]\n"
                f"   • Перейдите в раздел 'Search' или 'My Models'\n"
                f"   • Выберите модель (рекомендуем Llama 3.2 3B или Qwen 2.5 7B)\n"
                f"   • Нажмите кнопку 'Load' (не просто 'Download'!)\n"
                f"   • Дождитесь полной загрузки модели в память\n\n"
                f"[bold cyan]3. Убедитесь, что сервер активен[/]\n"
                f"   • В LM Studio должна быть кнопка 'Server Running' или зеленый индикатор\n"
                f"   • Обычно сервер запускается автоматически при загрузке модели\n"
                f"   • Порт по умолчанию: 1234\n\n"
                f"[bold green]4. Запустите CLI снова[/]\n"
                f"   • python lmstudio_cli.py\n\n"
                f"[dim]💡 Подсказка: Запустите 'python test_connection.py' для проверки[/]",
                title="⚠️  Требуется LM Studio",
                border_style="red",
                padding=(1, 2)
            )
        )

    def reset_chat(self, system_prompt: str = None):
        """
        Сбрасывает историю чата.

        Args:
            system_prompt: Системный промпт (опционально)
        """
        if system_prompt is None:
            system_prompt = (
                "Ты полезный AI ассистент. Отвечай на русском языке, "
                "будь информативным, точным и дружелюбным."
            )
        self.chat = lms.Chat(system_prompt)

    def list_models(self):
        """Отображает список доступных моделей."""
        try:
            loaded = self.client.llm.list_loaded()

            if not loaded:
                self.console.print("[yellow]Нет загруженных моделей[/]")
                return

            table = Table(title="Загруженные модели", show_header=True)
            table.add_column("#", style="cyan", width=4)
            table.add_column("Идентификатор", style="green")
            table.add_column("Статус", style="yellow")

            for i, model in enumerate(loaded, 1):
                status = "✓ Активна" if model.identifier == self.current_model_id else ""
                table.add_row(str(i), model.identifier, status)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Ошибка получения списка моделей:[/] {e}")

    def switch_model(self, model_id: str = None):
        """
        Переключает на другую модель.

        Args:
            model_id: ID модели для переключения
        """
        try:
            loaded = self.client.llm.list_loaded()

            if not loaded:
                self.console.print("[yellow]Нет доступных моделей[/]")
                return

            if model_id is None:
                # Интерактивный выбор
                self.list_models()
                model_id = Prompt.ask(
                    "\n[cyan]Введите номер или ID модели[/]"
                )

            # Пробуем интерпретировать как номер
            try:
                idx = int(model_id) - 1
                if 0 <= idx < len(loaded):
                    model_id = loaded[idx].identifier
            except ValueError:
                pass

            # Переключаемся на модель
            self.model = self.client.llm.get(model_id)
            self.current_model_id = model_id
            self.console.print(
                f"[green]✓ Переключено на модель:[/] {model_id}"
            )

            # Сбрасываем чат
            self.reset_chat()

        except Exception as e:
            self.console.print(f"[red]Ошибка переключения модели:[/] {e}")

    def show_history(self):
        """Отображает историю текущего диалога."""
        if not self.chat:
            self.console.print("[yellow]История пуста[/]")
            return

        self.console.print(
            Panel(
                str(self.chat),
                title="История диалога",
                border_style="blue"
            )
        )

    def save_history_to_file(self):
        """Сохраняет историю диалога в файл."""
        if not self.chat:
            self.console.print("[yellow]Нет истории для сохранения[/]")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.history_dir / f"chat_{timestamp}.json"

        try:
            # Извлекаем сообщения из чата
            history_data = {
                "timestamp": timestamp,
                "model": self.current_model_id,
                "messages": str(self.chat)  # Сохраняем как строку
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)

            self.console.print(
                f"[green]✓ История сохранена в:[/] {filename}"
            )

        except Exception as e:
            self.console.print(f"[red]Ошибка сохранения:[/] {e}")

    def show_help(self):
        """Отображает справку по командам."""
        help_text = """
[bold cyan]Доступные команды:[/]

[yellow]/help[/]              - Показать эту справку
[yellow]/exit[/] или [yellow]/quit[/]  - Выйти из программы
[yellow]/models[/]            - Показать список загруженных моделей
[yellow]/switch[/]            - Переключить модель
[yellow]/history[/]           - Показать историю текущего диалога
[yellow]/save[/]              - Сохранить историю в файл
[yellow]/clear[/]             - Очистить историю диалога
[yellow]/reset[/]             - Создать новый чат (с опциональным системным промптом)

[bold cyan]Горячие клавиши:[/]

[yellow]Ctrl+C[/]             - Прервать генерацию
[yellow]Ctrl+D[/]             - Выход
[yellow]↑/↓[/]                - Навигация по истории команд

[bold cyan]Примеры использования:[/]

  Просто пишите сообщения для общения с моделью
  Используйте команды, начинающиеся с [yellow]/[/] для управления
        """
        self.console.print(Panel(help_text, title="Справка", border_style="cyan"))

    def handle_command(self, command: str) -> bool:
        """
        Обрабатывает системные команды.

        Args:
            command: Команда для обработки

        Returns:
            True если нужно продолжить работу, False для выхода
        """
        command = command.lower().strip()

        if command in ['/exit', '/quit']:
            return False

        elif command == '/help':
            self.show_help()

        elif command == '/models':
            self.list_models()

        elif command == '/switch':
            self.switch_model()

        elif command == '/history':
            self.show_history()

        elif command == '/save':
            self.save_history_to_file()

        elif command == '/clear':
            self.reset_chat()
            self.console.print("[green]✓ История диалога очищена[/]")

        elif command.startswith('/reset'):
            # Можно указать новый системный промпт
            parts = command.split(' ', 1)
            system_prompt = parts[1] if len(parts) > 1 else None
            self.reset_chat(system_prompt)
            self.console.print("[green]✓ Создан новый чат[/]")

        else:
            self.console.print(
                f"[red]Неизвестная команда:[/] {command}\n"
                f"Введите [yellow]/help[/] для справки"
            )

        return True

    def chat_with_model(self, user_input: str):
        """
        Отправляет сообщение модели и получает ответ.

        Args:
            user_input: Сообщение пользователя
        """
        # Добавляем сообщение в историю
        self.chat.add_user_message(user_input)

        try:
            # Выводим начало ответа
            self.console.print("\n[bold green]🤖 Ассистент:[/]", end=" ")

            # Получаем потоковый ответ
            for fragment in self.model.respond_stream(self.chat, on_message=self.chat.append):
                # Выводим фрагменты в реальном времени
                self.console.print(fragment.content, end="", style="green")

            self.console.print("\n")  # Новая строка после ответа

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠ Генерация прервана[/]\n")
            # Удаляем последнее сообщение пользователя, так как ответ не получен
            # (в реальности chat API может не поддерживать это, но для примера)

        except Exception as e:
            self.console.print(f"\n[red]✗ Ошибка:[/] {e}\n")

    def run(self):
        """Основной цикл приложения."""
        self.show_banner()

        # Подключаемся к серверу
        if not self.connect_to_server():
            sys.exit(1)

        # Основной цикл
        while True:
            try:
                # Получаем ввод пользователя
                user_input = Prompt.ask("\n[bold blue]👤 Вы[/]").strip()

                # Пустой ввод - пропускаем
                if not user_input:
                    continue

                # Обрабатываем команды
                if user_input.startswith('/'):
                    if not self.handle_command(user_input):
                        break
                    continue

                # Обычное сообщение - отправляем модели
                self.chat_with_model(user_input)

            except EOFError:
                self.console.print("\n\n[cyan]До свидания![/]")
                break

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Прервано пользователем[/]")
                if Prompt.ask("\nВыйти?", choices=["y", "n"], default="n") == "y":
                    break

        # Завершение
        if self.client:
            self.client.disconnect()
            self.console.print("[dim]Отключено от сервера[/]")


def main():
    """Точка входа в приложение."""
    try:
        cli = LMStudioCLI()
        cli.run()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
