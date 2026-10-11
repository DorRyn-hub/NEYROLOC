#!/usr/bin/env python3
"""
🤖 NEYROLOCK v3.0 - Современный дашборд-интерфейс
• Карточки с градиентами
• Боковая навигация
• Статистика и индикаторы
• Красивые цвета
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import threading
import json
import datetime
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional


# ========== Кроссплатформенные хелперы ==========

def is_macos() -> bool:
    """Определяет, работает ли приложение на macOS."""
    return sys.platform == "darwin"


def is_windows() -> bool:
    """Определяет, работает ли приложение на Windows."""
    return sys.platform == "win32"


def get_modifier_key() -> str:
    """Возвращает модификатор клавиши в зависимости от ОС.

    macOS: Command
    Windows/Linux: Control
    """
    return "Command" if is_macos() else "Control"


def get_accelerator_prefix() -> str:
    """Возвращает префикс для отображения в меню.

    macOS: Cmd
    Windows/Linux: Ctrl
    """
    return "Cmd" if is_macos() else "Ctrl"


class NeyrolockDashboard:
    """Современный дашборд для NEYROLOCK."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NEYROLOCK - AI Dashboard")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Папка для данных
        self.data_dir = Path.home() / ".neyrolock"
        self.data_dir.mkdir(exist_ok=True)
        self.config_file = self.data_dir / "config.json"
        self.history_file = self.data_dir / "chat_history.json"

        # Состояние
        self.model = None
        self.backend = None
        self.chat_history = []
        self.is_generating = False
        self.temperature = 0.7
        self.messages_count = 0
        self.tokens_used = 0
        self.last_model_path = ""

        # Современные цвета (как на примере)
        self.colors = {
            "bg_dark": "#0d0d1a",           # Очень темный фон
            "bg_card": "#1a1a2e",           # Фон карточек
            "bg_card_hover": "#252540",     # Карточка при наведении
            "sidebar": "#12121f",           # Боковая панель
            "accent_pink": "#ff6b9d",       # Розовый акцент
            "accent_purple": "#c084fc",     # Фиолетовый
            "accent_green": "#4ade80",      # Зеленый
            "accent_yellow": "#fbbf24",     # Желтый
            "accent_cyan": "#22d3ee",       # Голубой
            "text_primary": "#ffffff",      # Основной текст
            "text_secondary": "#9ca3af",    # Вторичный текст
            "text_muted": "#6b7280",        # Приглушенный
            "border": "#2d2d44",            # Границы
            "gradient_start": "#667eea",    # Начало градиента
            "gradient_end": "#764ba2",      # Конец градиента
            "success": "#10b981",           # Успех
            "warning": "#f59e0b",           # Предупреждение
            "error": "#ef4444",             # Ошибка
        }

        self.cyber_font = "Menlo"
        self.current_font_size = 13

        # Применяем тему
        self.root.configure(bg=self.colors["bg_dark"])
        self.setup_styles()

        # Создаем интерфейс
        self.create_sidebar()
        self.create_main_area()
        self.setup_hotkeys()

        # Загружаем сохраненные данные
        self.load_config()
        self.load_chat_history()

        # Синхронизация
        self.setup_sync()

        # Стартовое сообщение если история пуста
        if not self.chat_history:
            self.add_system_message("🚀 Добро пожаловать в NEYROLOCK!")
            self.add_system_message("📦 Для начала загрузите модель через боковую панель")
        else:
            self.add_system_message(f"🔄 Загружена история: {len(self.chat_history)} сообщений")

        # Сохраняем при закрытии
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        """Настройка стилей."""
        style = ttk.Style()
        style.theme_use('clam')

        # Кнопки
        style.configure(
            "Card.TFrame",
            background=self.colors["bg_card"]
        )

        style.configure(
            "Sidebar.TFrame",
            background=self.colors["sidebar"]
        )

    def create_sidebar(self):
        """Создание боковой панели."""
        sidebar = tk.Frame(
            self.root,
            bg=self.colors["sidebar"],
            width=280
        )
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Логотип
        logo_frame = tk.Frame(sidebar, bg=self.colors["sidebar"])
        logo_frame.pack(fill=tk.X, pady=20, padx=15)

        logo_label = tk.Label(
            logo_frame,
            text="🧠 NEYROLOCK",
            font=(self.cyber_font, 20, "bold"),
            bg=self.colors["sidebar"],
            fg=self.colors["accent_purple"]
        )
        logo_label.pack()

        version_label = tk.Label(
            logo_frame,
            text="v3.0 Dashboard",
            font=(self.cyber_font, 10),
            bg=self.colors["sidebar"],
            fg=self.colors["text_muted"]
        )
        version_label.pack()

        # Разделитель
        self.create_separator(sidebar)

        # Статус модели
        status_frame = tk.Frame(sidebar, bg=self.colors["sidebar"])
        status_frame.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(
            status_frame,
            text="СТАТУС МОДЕЛИ",
            font=(self.cyber_font, 9, "bold"),
            bg=self.colors["sidebar"],
            fg=self.colors["text_muted"]
        ).pack(anchor=tk.W)

        self.model_status = tk.Label(
            status_frame,
            text="⚫ Не загружена",
            font=(self.cyber_font, 11),
            bg=self.colors["sidebar"],
            fg=self.colors["error"]
        )
        self.model_status.pack(anchor=tk.W, pady=(5, 0))

        self.model_name_label = tk.Label(
            status_frame,
            text="",
            font=(self.cyber_font, 9),
            bg=self.colors["sidebar"],
            fg=self.colors["text_secondary"],
            wraplength=250
        )
        self.model_name_label.pack(anchor=tk.W)

        # Разделитель
        self.create_separator(sidebar)

        # Кнопки действий
        actions_label = tk.Label(
            sidebar,
            text="ДЕЙСТВИЯ",
            font=(self.cyber_font, 9, "bold"),
            bg=self.colors["sidebar"],
            fg=self.colors["text_muted"]
        )
        actions_label.pack(anchor=tk.W, padx=15, pady=(10, 5))

        # Кнопки
        self.create_sidebar_button(sidebar, "📥 Скачать модель", self.download_model, self.colors["accent_pink"])
        self.create_sidebar_button(sidebar, "📂 Загрузить модель", self.load_local_model, self.colors["accent_purple"])
        self.create_sidebar_button(sidebar, "📋 Мои модели", self.show_downloaded_models, self.colors["accent_cyan"])
        self.create_sidebar_button(sidebar, "🔍 Поиск HuggingFace", self.search_models, self.colors["accent_yellow"])

        # Разделитель
        self.create_separator(sidebar)

        # Telegram
        telegram_label = tk.Label(
            sidebar,
            text="TELEGRAM",
            font=(self.cyber_font, 9, "bold"),
            bg=self.colors["sidebar"],
            fg=self.colors["text_muted"]
        )
        telegram_label.pack(anchor=tk.W, padx=15, pady=(10, 5))

        self.create_sidebar_button(sidebar, "📱 Настроить бот", self.show_telegram_setup, self.colors["accent_green"])
        self.create_sidebar_button(sidebar, "🚀 Запустить бот", self.start_telegram_bot, self.colors["accent_cyan"])

        # Разделитель
        self.create_separator(sidebar)

        # Настройки
        settings_label = tk.Label(
            sidebar,
            text="НАСТРОЙКИ",
            font=(self.cyber_font, 9, "bold"),
            bg=self.colors["sidebar"],
            fg=self.colors["text_muted"]
        )
        settings_label.pack(anchor=tk.W, padx=15, pady=(10, 5))

        self.create_sidebar_button(sidebar, "🎨 Размер шрифта", self.change_font_size, self.colors["text_secondary"])
        self.create_sidebar_button(sidebar, "🌈 Цвет шрифта", self.change_font_color, self.colors["text_secondary"])
        self.create_sidebar_button(sidebar, "🌡️ Температура", self.set_temperature, self.colors["text_secondary"])
        self.create_sidebar_button(sidebar, "📝 Системный промпт", self.set_system_prompt, self.colors["text_secondary"])

        # Нижняя часть
        bottom_frame = tk.Frame(sidebar, bg=self.colors["sidebar"])
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15, padx=15)

        self.create_sidebar_button(bottom_frame, "🧪 Тест markdown", self.test_markdown, self.colors["accent_cyan"])
        self.create_sidebar_button(bottom_frame, "🗑️ Очистить чат", self.clear_history, self.colors["warning"])
        self.create_sidebar_button(bottom_frame, "💾 Сохранить", self.save_dialog, self.colors["success"])

    def create_sidebar_button(self, parent, text, command, color):
        """Создание кнопки боковой панели."""
        btn_frame = tk.Frame(parent, bg=self.colors["sidebar"])
        # Убираем padx если parent уже имеет отступы
        if parent == self.root.winfo_children()[0]:  # sidebar
            btn_frame.pack(fill=tk.X, padx=15, pady=3)
        else:
            btn_frame.pack(fill=tk.X, pady=3)

        btn = tk.Label(
            btn_frame,
            text=text,
            font=(self.cyber_font, 11),
            bg=self.colors["sidebar"],
            fg=color,
            cursor="hand2",
            anchor=tk.W
        )
        btn.pack(fill=tk.X, pady=5)

        # Сохраняем команду в атрибут виджета для правильного замыкания
        btn.command = command

        # Эффекты при наведении
        def on_enter(e):
            btn.configure(fg=self.colors["text_primary"])
            btn_frame.configure(bg=self.colors["bg_card"])
            btn.configure(bg=self.colors["bg_card"])

        def on_leave(e):
            btn.configure(fg=color)
            btn_frame.configure(bg=self.colors["sidebar"])
            btn.configure(bg=self.colors["sidebar"])

        def on_click(e):
            btn.command()

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)

    def create_separator(self, parent):
        """Создание разделителя."""
        sep = tk.Frame(parent, bg=self.colors["border"], height=1)
        sep.pack(fill=tk.X, padx=15, pady=10)

    def create_main_area(self):
        """Создание основной области."""
        main = tk.Frame(self.root, bg=self.colors["bg_dark"])
        main.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Верхняя панель со статистикой
        self.create_stats_panel(main)

        # Основной контент
        content = tk.Frame(main, bg=self.colors["bg_dark"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Левая колонка - чат
        chat_frame = self.create_card(content, "💬 Чат с AI")
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Область чата
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=(self.cyber_font, self.current_font_size),
            state=tk.DISABLED,
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["accent_pink"],
            selectbackground=self.colors["accent_purple"],
            bd=0,
            padx=15,
            pady=15,
            relief=tk.FLAT
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.setup_chat_tags()

        # Копирование кода по двойному клику
        self.chat_display.bind("<Double-Button-1>", self.copy_code_block)
        self.code_blocks = {}

        # Поле ввода
        input_frame = tk.Frame(chat_frame, bg=self.colors["bg_card"])
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.input_text = tk.Text(
            input_frame,
            height=3,
            font=(self.cyber_font, self.current_font_size),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["accent_pink"],
            bd=0,
            padx=10,
            pady=10,
            relief=tk.FLAT
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_text.bind("<Return>", self.on_enter_pressed)

        # Кнопка отправки
        send_btn = tk.Label(
            input_frame,
            text="➤",
            font=(self.cyber_font, 24),
            bg=self.colors["accent_pink"],
            fg=self.colors["text_primary"],
            cursor="hand2",
            padx=20,
            pady=10
        )
        send_btn.pack(side=tk.RIGHT)
        send_btn.bind("<Button-1>", lambda e: self.send_message())

        # Правая колонка - информация
        info_column = tk.Frame(content, bg=self.colors["bg_dark"], width=350)
        info_column.pack(side=tk.RIGHT, fill=tk.Y)
        info_column.pack_propagate(False)

        # Карточка активности
        activity_card = self.create_card(info_column, "📊 Активность")
        activity_card.pack(fill=tk.X, pady=(0, 10))

        self.activity_label = tk.Label(
            activity_card,
            text="Сообщений: 0\nТокенов: ~0",
            font=(self.cyber_font, 12),
            bg=self.colors["bg_card"],
            fg=self.colors["text_secondary"],
            justify=tk.LEFT
        )
        self.activity_label.pack(padx=15, pady=15, anchor=tk.W)

        # Карточка горячих клавиш
        hotkeys_card = self.create_card(info_column, "⌨️ Горячие клавиши")
        hotkeys_card.pack(fill=tk.X, pady=(0, 10))

        hotkeys_text = "⌘S/⌘Ы - Сохранить\n⌘N/⌘Т - Очистить\n⌘D/⌘В - Скачать\n⌘L/⌘Д - Загрузить\n⌘C/⌘С - Копировать\n⌘V/⌘М - Вставить"
        tk.Label(
            hotkeys_card,
            text=hotkeys_text,
            font=(self.cyber_font, 10),
            bg=self.colors["bg_card"],
            fg=self.colors["text_muted"],
            justify=tk.LEFT
        ).pack(padx=15, pady=15, anchor=tk.W)

        # Карточка синхронизации
        sync_card = self.create_card(info_column, "📱 Синхронизация")
        sync_card.pack(fill=tk.X)

        self.sync_status = tk.Label(
            sync_card,
            text="⚫ Не активна",
            font=(self.cyber_font, 11),
            bg=self.colors["bg_card"],
            fg=self.colors["text_muted"]
        )
        self.sync_status.pack(padx=15, pady=15, anchor=tk.W)

    def create_stats_panel(self, parent):
        """Создание панели статистики."""
        stats_frame = tk.Frame(parent, bg=self.colors["bg_dark"])
        stats_frame.pack(fill=tk.X, padx=20, pady=20)

        # Карточки статистики
        stats = [
            ("🤖", "Модель", "Не загружена", self.colors["accent_pink"]),
            ("💬", "Сообщений", "0", self.colors["accent_purple"]),
            ("⚡", "Температура", "0.7", self.colors["accent_yellow"]),
            ("🔄", "Статус", "Готов", self.colors["accent_green"]),
        ]

        self.stat_labels = {}

        for icon, title, value, color in stats:
            card = tk.Frame(stats_frame, bg=self.colors["bg_card"], padx=20, pady=15)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            # Иконка и заголовок
            header = tk.Frame(card, bg=self.colors["bg_card"])
            header.pack(fill=tk.X)

            tk.Label(
                header,
                text=icon,
                font=(self.cyber_font, 20),
                bg=self.colors["bg_card"],
                fg=color
            ).pack(side=tk.LEFT)

            tk.Label(
                header,
                text=title,
                font=(self.cyber_font, 10),
                bg=self.colors["bg_card"],
                fg=self.colors["text_muted"]
            ).pack(side=tk.LEFT, padx=10)

            # Значение
            value_label = tk.Label(
                card,
                text=value,
                font=(self.cyber_font, 14, "bold"),
                bg=self.colors["bg_card"],
                fg=self.colors["text_primary"]
            )
            value_label.pack(anchor=tk.W, pady=(10, 0))

            self.stat_labels[title] = value_label

    def create_card(self, parent, title):
        """Создание карточки."""
        card = tk.Frame(parent, bg=self.colors["bg_card"], padx=0, pady=0)

        # Заголовок карточки
        header = tk.Frame(card, bg=self.colors["bg_card"])
        header.pack(fill=tk.X, padx=15, pady=(15, 0))

        tk.Label(
            header,
            text=title,
            font=(self.cyber_font, 12, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        ).pack(anchor=tk.W)

        # Линия под заголовком
        line = tk.Frame(card, bg=self.colors["border"], height=1)
        line.pack(fill=tk.X, padx=15, pady=10)

        return card

    def setup_chat_tags(self):
        """Настройка тегов чата."""
        self.chat_display.tag_configure(
            "user",
            foreground=self.colors["accent_cyan"],
            font=(self.cyber_font, self.current_font_size, "bold")
        )
        self.chat_display.tag_configure(
            "assistant",
            foreground=self.colors["accent_green"],
            font=(self.cyber_font, self.current_font_size)
        )
        self.chat_display.tag_configure(
            "system",
            foreground=self.colors["text_muted"],
            font=(self.cyber_font, self.current_font_size - 1, "italic")
        )
        self.chat_display.tag_configure(
            "timestamp",
            foreground=self.colors["text_muted"],
            font=(self.cyber_font, self.current_font_size - 3)
        )
        # Теги для markdown форматирования
        self.chat_display.tag_configure(
            "code_inline",
            foreground=self.colors["accent_yellow"],
            background="#2d2d44",
            font=(self.cyber_font, self.current_font_size)
        )
        self.chat_display.tag_configure(
            "bold",
            foreground=self.colors["text_primary"],
            font=(self.cyber_font, self.current_font_size, "bold")
        )
        self.chat_display.tag_configure(
            "italic",
            foreground=self.colors["text_primary"],
            font=(self.cyber_font, self.current_font_size, "italic")
        )
        self.chat_display.tag_configure(
            "header",
            foreground=self.colors["accent_pink"],
            font=(self.cyber_font, self.current_font_size + 2, "bold")
        )
        self.chat_display.tag_configure(
            "link",
            foreground=self.colors["accent_cyan"],
            underline=True
        )
        # Теги для блоков кода (легкие, без виджетов)
        self.chat_display.tag_configure(
            "code_header",
            foreground="#888888",
            font=(self.cyber_font, self.current_font_size - 1)
        )
        self.chat_display.tag_configure(
            "code_block",
            foreground=self.colors["accent_yellow"],
            background="#1a1a1a",
            font=(self.cyber_font, self.current_font_size)
        )

    def add_message(self, role, text, update_stats=True):
        """Добавление сообщения в чат."""
        self.chat_display.config(state=tk.NORMAL)

        timestamp = datetime.datetime.now().strftime("%H:%M")

        if role == "user":
            prefix = f"\n[{timestamp}] 👤 Вы\n"
            tag = "user"
        elif role == "assistant":
            prefix = f"\n[{timestamp}] 🤖 AI\n"
            tag = "assistant"
        else:
            prefix = f"\n[{timestamp}] ℹ️ "
            tag = "system"

        self.chat_display.insert(tk.END, prefix, tag)

        # Парсим markdown для assistant сообщений
        if role == "assistant" and text:
            self.render_markdown(text)
        else:
            self.chat_display.insert(tk.END, text + "\n", tag)

        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

        # Обновляем статистику только если нужно
        if update_stats and role in ["user", "assistant"] and text:
            self.messages_count += 1
            self.stat_labels["Сообщений"].config(text=str(self.messages_count))
            self.activity_label.config(text=f"Сообщений: {self.messages_count}\nТокенов: ~{self.tokens_used}")

    def render_markdown(self, text):
        """Рендеринг markdown текста с блоками кода."""
        import re

        # Разбиваем на части: текст и блоки кода
        parts = re.split(r'(```[\s\S]*?```)', text)

        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                # Это блок кода
                code_content = part[3:-3]

                # Извлекаем язык если указан
                lines = code_content.split('\n', 1)
                if len(lines) > 1 and lines[0].strip() and not ' ' in lines[0].strip():
                    language = lines[0].strip()
                    code = lines[1] if len(lines) > 1 else ""
                else:
                    language = ""
                    code = code_content

                # Создаем блок кода с кнопкой копирования
                self.create_code_block(code.strip(), language)
            else:
                # Обычный текст - парсим inline markdown
                self.render_inline_markdown(part)

    def create_code_block(self, code, language=""):
        """Создание блока кода (оптимизированная версия - без тяжелых виджетов)."""
        # Сохраняем код для копирования
        code_id = f"code_{len(self.chat_display.get('1.0', tk.END))}"
        if not hasattr(self, 'code_blocks'):
            self.code_blocks = {}
        self.code_blocks[code_id] = code

        # Заголовок
        header = f"\n┌─ {language if language else 'code'} ─────────────────── [📋 Ctrl+Click для копирования]\n"
        self.chat_display.insert(tk.END, header, "code_header")

        # Код с отступом
        for line in code.split('\n'):
            self.chat_display.insert(tk.END, f"│ {line}\n", "code_block")

        # Закрытие блока
        self.chat_display.insert(tk.END, "└" + "─" * 60 + "\n", "code_header")

        # Добавляем обработчик для копирования при Ctrl+Click
        # Это легче чем создавать отдельные виджеты

    def copy_code_block(self, event):
        """Копирование блока кода при двойном клике."""
        try:
            # Получаем позицию клика
            index = self.chat_display.index(f"@{event.x},{event.y}")

            # Проверяем есть ли тег code_block
            tags = self.chat_display.tag_names(index)

            if "code_block" in tags or "code_header" in tags:
                # Находим начало и конец блока кода
                # Ищем строку с "┌─"
                line_start = self.chat_display.index(f"{index} linestart")
                current_line = int(line_start.split('.')[0])

                # Ищем начало блока (строка с ┌)
                start_line = current_line
                for i in range(current_line, max(0, current_line - 50), -1):
                    line_text = self.chat_display.get(f"{i}.0", f"{i}.end")
                    if line_text.startswith("┌"):
                        start_line = i
                        break

                # Ищем конец блока (строка с └)
                end_line = current_line
                total_lines = int(self.chat_display.index('end').split('.')[0])
                for i in range(current_line, min(total_lines, current_line + 100)):
                    line_text = self.chat_display.get(f"{i}.0", f"{i}.end")
                    if line_text.startswith("└"):
                        end_line = i
                        break

                # Собираем код (без рамки)
                code_lines = []
                for i in range(start_line + 1, end_line):
                    line = self.chat_display.get(f"{i}.0", f"{i}.end")
                    if line.startswith("│ "):
                        code_lines.append(line[2:])  # Убираем "│ "

                code = '\n'.join(code_lines)

                # Копируем в буфер
                self.root.clipboard_clear()
                self.root.clipboard_append(code)

                # Показываем уведомление
                self.add_system_message("✅ Код скопирован в буфер обмена!")

        except Exception as e:
            print(f"Copy error: {e}")

    def render_inline_markdown(self, text):
        """Рендеринг inline markdown (bold, italic, code, headers)."""
        import re

        lines = text.split('\n')

        for i, line in enumerate(lines):
            # Заголовки
            if line.startswith('### '):
                self.chat_display.insert(tk.END, line[4:] + "\n", "header")
            elif line.startswith('## '):
                self.chat_display.insert(tk.END, line[3:] + "\n", "header")
            elif line.startswith('# '):
                self.chat_display.insert(tk.END, line[2:] + "\n", "header")
            elif line.startswith('**') and line.endswith('**') and len(line) > 4:
                # Весь текст жирный
                self.chat_display.insert(tk.END, line[2:-2] + "\n", "bold")
            else:
                # Парсим inline элементы
                self.parse_inline_elements(line)
                if i < len(lines) - 1:
                    self.chat_display.insert(tk.END, "\n", "assistant")

    def parse_inline_elements(self, text):
        """Парсинг inline элементов: `code`, **bold**, *italic*"""
        import re

        # Паттерн для inline кода, bold и italic
        pattern = r'(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)'
        parts = re.split(pattern, text)

        for part in parts:
            if part.startswith('`') and part.endswith('`') and len(part) > 2:
                # Inline код
                self.chat_display.insert(tk.END, part[1:-1], "code_inline")
            elif part.startswith('**') and part.endswith('**') and len(part) > 4:
                # Bold
                self.chat_display.insert(tk.END, part[2:-2], "bold")
            elif part.startswith('*') and part.endswith('*') and len(part) > 2:
                # Italic
                self.chat_display.insert(tk.END, part[1:-1], "italic")
            else:
                # Обычный текст
                self.chat_display.insert(tk.END, part, "assistant")

    def add_system_message(self, text):
        """Добавление системного сообщения."""
        self.add_message("system", text)

    def setup_hotkeys(self):
        """Настройка горячих клавиш (кроссплатформенная).

        macOS: Command+клавиша
        Windows/Linux: Control+клавиша
        """
        mod = get_modifier_key()

        # Основные горячие клавиши с динамическим модификатором
        self.root.bind(f"<{mod}-s>", lambda e: self.save_dialog())
        self.root.bind(f"<{mod}-n>", lambda e: self.clear_history())
        self.root.bind(f"<{mod}-d>", lambda e: self.download_model())
        self.root.bind(f"<{mod}-l>", lambda e: self.load_local_model())

        # Control-варианты для совместимости (работают везде)
        self.root.bind("<Control-s>", lambda e: self.save_dialog())
        self.root.bind("<Control-n>", lambda e: self.clear_history())
        self.root.bind("<Control-d>", lambda e: self.download_model())
        self.root.bind("<Control-l>", lambda e: self.load_local_model())

        # Обработчик для русской раскладки
        self.root.bind("<KeyPress>", self.handle_any_key)

    def handle_any_key(self, event):
        """Обработка клавиш для русской раскладки (кроссплатформенная)."""
        # Проверяем модификаторы: Command только на macOS, Control везде
        is_command = bool(event.state & 0x8) if is_macos() else False
        is_control = bool(event.state & 0x4)

        if not (is_command or is_control):
            return

        ru_actions = {
            'ы': self.save_dialog, 'т': self.clear_history,
            'в': self.download_model, 'д': self.load_local_model,
        }
        ru_clipboard = {'с': 'copy', 'м': 'paste', 'ч': 'cut', 'я': 'undo'}

        char = event.char.lower() if event.char else ''

        if char in ru_actions:
            ru_actions[char]()
            return "break"
        elif char in ru_clipboard:
            try:
                focused = self.root.focus_get()
                if focused:
                    action = ru_clipboard[char]
                    if action == 'copy':
                        focused.event_generate("<<Copy>>")
                    elif action == 'paste':
                        focused.event_generate("<<Paste>>")
                    return "break"
            except:
                pass

    def on_enter_pressed(self, event):
        """Обработка Enter."""
        if not event.state & 0x1:
            self.send_message()
            return "break"

    def send_message(self):
        """Отправка сообщения."""
        if self.is_generating:
            return

        if not self.model:
            messagebox.showwarning("Модель не загружена", "Сначала загрузите модель через боковую панель!")
            return

        user_text = self.input_text.get("1.0", tk.END).strip()
        if not user_text:
            return

        self.input_text.delete("1.0", tk.END)
        self.add_message("user", user_text)
        self.chat_history.append({"role": "user", "content": user_text})

        # Отправляем в sync для Telegram
        if self.sync_manager:
            self.sync_manager.send_message("gui", "user", user_text)

        self.is_generating = True
        self.stat_labels["Статус"].config(text="Генерация...", fg=self.colors["warning"])

        thread = threading.Thread(target=self.generate_response, args=(user_text,))
        thread.daemon = True
        thread.start()

    def generate_response(self, user_message):
        """Генерация ответа."""
        try:
            if self.backend == "local":
                messages = self.chat_history.copy()
                response_text = ""

                # Добавляем временное сообщение "печатает..."
                self.root.after(0, lambda: self.add_streaming_placeholder())

                stream = self.model.create_chat_completion(
                    messages=messages,
                    stream=True,
                    max_tokens=512,
                    temperature=self.temperature
                )

                for chunk in stream:
                    if not self.is_generating:
                        break
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            content = delta['content']
                            response_text += content
                            self.tokens_used += len(content.split())
                            self.root.after(0, lambda c=content: self.update_streaming_text(c))

                # После завершения стриминга - рендерим с markdown
                self.root.after(0, lambda: self.finalize_streamed_message(response_text))
                self.chat_history.append({"role": "assistant", "content": response_text})

                # Отправляем в sync для Telegram
                if self.sync_manager:
                    self.sync_manager.send_message("gui", "assistant", response_text)

        except Exception as e:
            self.root.after(0, lambda: self.add_system_message(f"❌ Ошибка: {e}"))
        finally:
            self.root.after(0, self.finish_generation)

    def add_streaming_placeholder(self):
        """Добавление placeholder для стриминга."""
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"\n[{timestamp}] 🤖 AI\n", "assistant")
        # Сохраняем позицию начала текста
        self.stream_start_pos = self.chat_display.index(tk.END)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def update_streaming_text(self, text):
        """Обновление текста при стриминге (без markdown)."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text, "assistant")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def finalize_streamed_message(self, full_text):
        """Финализация сообщения с рендерингом markdown."""
        if not full_text.strip():
            return

        # Проверяем есть ли код блоки в тексте
        if '```' in full_text:
            # Удаляем простой текст и заменяем на отформатированный
            self.chat_display.config(state=tk.NORMAL)

            # Находим и удаляем старый текст
            if hasattr(self, 'stream_start_pos'):
                self.chat_display.delete(self.stream_start_pos, tk.END)

            # Рендерим с markdown
            self.render_markdown(full_text)
            self.chat_display.insert(tk.END, "\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)

        # Обновляем статистику
        self.messages_count += 1
        self.stat_labels["Сообщений"].config(text=str(self.messages_count))
        self.activity_label.config(text=f"Сообщений: {self.messages_count}\nТокенов: ~{self.tokens_used}")

    def update_last_message(self, text):
        """Обновление последнего сообщения (deprecated, kept for compatibility)."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text, "assistant")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def finish_generation(self):
        """Завершение генерации."""
        self.is_generating = False
        self.stat_labels["Статус"].config(text="Готов", fg=self.colors["success"])
        self.activity_label.config(text=f"Сообщений: {self.messages_count}\nТокенов: ~{self.tokens_used}")

    def setup_sync(self):
        """Настройка синхронизации."""
        self.sync_manager = None
        try:
            from sync_manager import SyncManager
            self.sync_manager = SyncManager()
            self.sync_manager.update_status("gui_active", True)

            # Запускаем мониторинг сообщений из Telegram
            self.sync_manager.start_monitoring(
                on_message=self.on_telegram_message,
                on_stream=self.on_telegram_stream
            )

            self.sync_status.config(text="🟢 Активна", fg=self.colors["success"])
            self.add_system_message("📱 Синхронизация с Telegram включена")
        except Exception as e:
            print(f"Sync error: {e}")
            self.sync_status.config(text="⚫ Не активна", fg=self.colors["text_muted"])

    def on_telegram_message(self, msg):
        """Обработка сообщения из Telegram."""
        if msg.get("source") == "telegram":
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Показываем в GUI
            if role == "user":
                self.root.after(0, lambda: self.add_message("user", f"[TG] {content}"))
                self.root.after(0, lambda: self.chat_history.append({"role": "user", "content": content}))
            elif role == "assistant":
                self.root.after(0, lambda: self.add_message("assistant", content))
                self.root.after(0, lambda: self.chat_history.append({"role": "assistant", "content": content}))

    def on_telegram_stream(self, stream_data):
        """Обработка стриминга из Telegram."""
        # Можно добавить визуализацию стриминга
        pass

    # ==================== Методы загрузки моделей ====================

    def download_model(self):
        """Скачивание модели."""
        try:
            from model_manager import ModelManager
            self.model_manager = ModelManager()
        except ImportError:
            messagebox.showerror("Ошибка", "Установите: pip3 install huggingface-hub")
            return

        # Диалог выбора
        win = tk.Toplevel(self.root)
        win.title("📥 Скачать модель")
        win.geometry("600x500")
        win.configure(bg=self.colors["bg_dark"])
        win.transient(self.root)

        tk.Label(win, text="📥 Выберите модель", font=(self.cyber_font, 16, "bold"),
                bg=self.colors["bg_dark"], fg=self.colors["accent_pink"]).pack(pady=15)

        # Категории
        cat_var = tk.StringVar(value="small")
        for cat, name in [("tiny", "🐣 Tiny (300-700MB)"), ("small", "⭐ Small (2GB)"),
                          ("medium", "💪 Medium (4-5GB)")]:
            tk.Radiobutton(win, text=name, variable=cat_var, value=cat,
                          font=(self.cyber_font, 11), bg=self.colors["bg_dark"],
                          fg=self.colors["text_primary"], selectcolor=self.colors["bg_card"]
                          ).pack(anchor=tk.W, padx=20)

        # Список
        listbox = tk.Listbox(win, font=(self.cyber_font, 11), bg=self.colors["bg_card"],
                            fg=self.colors["text_primary"], selectbackground=self.colors["accent_purple"],
                            height=8)
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        def update_list(*args):
            listbox.delete(0, tk.END)
            for m in self.model_manager.RECOMMENDED_MODELS.get(cat_var.get(), []):
                size = f"{m['size_mb']/1000:.1f}GB" if m['size_mb'] >= 1000 else f"{m['size_mb']}MB"
                listbox.insert(tk.END, f"{m['filename'][:40]} ({size})")

        cat_var.trace_add('write', update_list)
        update_list()

        def download():
            sel = listbox.curselection()
            if not sel:
                return
            info = self.model_manager.RECOMMENDED_MODELS[cat_var.get()][sel[0]]
            win.destroy()
            self.add_system_message(f"⏳ Скачивание {info['filename']}...")

            def dl():
                try:
                    path = self.model_manager.download_model(info['repo_id'], info['filename'], info['description'])
                    if path:
                        self.root.after(0, lambda: self.add_system_message(f"✅ Модель скачана: {info['filename']}"))
                        if messagebox.askyesno("Загрузить?", "Загрузить модель сейчас?"):
                            self.root.after(0, lambda: self.load_gguf_model(path))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

            threading.Thread(target=dl, daemon=True).start()

        tk.Button(win, text="📥 Скачать", command=download, font=(self.cyber_font, 12, "bold"),
                 bg=self.colors["accent_pink"], fg=self.colors["text_primary"], bd=0, padx=30, pady=10
                 ).pack(pady=10)

    def load_local_model(self):
        """Загрузка локальной модели."""
        path = filedialog.askopenfilename(
            title="Выберите .gguf файл",
            filetypes=[("GGUF", "*.gguf"), ("All", "*.*")],
            initialdir=str(Path.home() / ".neyrolock_models")
        )
        if path:
            self.load_gguf_model(path)

    def load_gguf_model(self, path):
        """Загрузка GGUF модели."""
        try:
            from llama_cpp import Llama
        except ImportError as e:
            messagebox.showerror("Ошибка", "Установите: pip3 install llama-cpp-python")
            return
        except RuntimeError as e:
            if "incompatible architecture" in str(e):
                messagebox.showerror(
                    "Ошибка архитектуры",
                    "llama-cpp-python установлен для другой архитектуры.\n\n"
                    "Переустановите:\n"
                    "pip3 uninstall llama-cpp-python\n"
                    "pip3 install llama-cpp-python --force-reinstall --no-cache-dir"
                )
            else:
                messagebox.showerror("Ошибка", f"Не удалось загрузить llama_cpp:\n{e}")
            return
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки llama_cpp:\n{e}")
            return

        self.add_system_message(f"⏳ Загрузка модели...")
        self.stat_labels["Статус"].config(text="Загрузка...", fg=self.colors["warning"])

        def load():
            try:
                model = Llama(model_path=path, n_ctx=2048, n_gpu_layers=-1, verbose=False)
                self.model = model
                self.backend = "local"
                self.model_path = path
                name = Path(path).name
                self.root.after(0, lambda: self.on_model_loaded(name))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
                self.root.after(0, lambda: self.stat_labels["Статус"].config(text="Ошибка", fg=self.colors["error"]))

        threading.Thread(target=load, daemon=True).start()

    def on_model_loaded(self, name):
        """После загрузки модели."""
        self.model_status.config(text="🟢 Загружена", fg=self.colors["success"])
        self.model_name_label.config(text=name[:30])
        self.stat_labels["Модель"].config(text=name[:20])
        self.stat_labels["Статус"].config(text="Готов", fg=self.colors["success"])
        self.add_system_message(f"✅ Модель загружена: {name}")

        # Сохраняем путь к модели
        if hasattr(self, 'model_path'):
            self.last_model_path = self.model_path
            self.save_config()

        # Обновляем синхронизацию
        if self.sync_manager:
            self.sync_manager.update_status("model_loaded", True)
            self.sync_manager.update_status("model_name", name)

    def show_downloaded_models(self):
        """Показ скачанных моделей."""
        try:
            from model_manager import ModelManager
            mm = ModelManager()
            files = list(mm.models_dir.glob("**/*.gguf"))
            if not files:
                messagebox.showinfo("Пусто", f"Нет моделей в {mm.models_dir}")
                return

            win = tk.Toplevel(self.root)
            win.title("📋 Мои модели")
            win.geometry("600x400")
            win.configure(bg=self.colors["bg_dark"])

            listbox = tk.Listbox(win, font=(self.cyber_font, 11), bg=self.colors["bg_card"],
                                fg=self.colors["text_primary"], height=15)
            listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            paths = []
            for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
                size = f.stat().st_size / (1024*1024)
                s = f"{size/1000:.1f}GB" if size >= 1000 else f"{size:.0f}MB"
                listbox.insert(tk.END, f"{f.name} ({s})")
                paths.append(str(f))

            def load():
                sel = listbox.curselection()
                if sel:
                    win.destroy()
                    self.load_gguf_model(paths[sel[0]])

            tk.Button(win, text="📂 Загрузить", command=load, font=(self.cyber_font, 12, "bold"),
                     bg=self.colors["accent_purple"], fg=self.colors["text_primary"], bd=0, padx=30, pady=10
                     ).pack(pady=10)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def search_models(self):
        """Поиск на HuggingFace с полным окном результатов."""
        query = simpledialog.askstring("Поиск", "Введите запрос для поиска GGUF моделей:")
        if not query:
            return

        self.add_system_message(f"🔍 Поиск '{query}' на HuggingFace...")

        try:
            from huggingface_hub import HfApi
            api = HfApi()
        except ImportError:
            messagebox.showerror("Ошибка", "Установите: pip3 install huggingface-hub")
            return

        # Создаем окно поиска
        search_win = tk.Toplevel(self.root)
        search_win.title(f"🔍 HuggingFace - Поиск: {query}")
        search_win.geometry("1000x700")
        search_win.configure(bg=self.colors["bg_dark"])
        search_win.transient(self.root)

        # Заголовок
        header_frame = tk.Frame(search_win, bg=self.colors["bg_dark"])
        header_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(
            header_frame,
            text=f"🔍 Результаты поиска: {query}",
            font=(self.cyber_font, 18, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_pink"]
        ).pack(side=tk.LEFT)

        # Статус загрузки
        status_label = tk.Label(
            header_frame,
            text="⏳ Загрузка...",
            font=(self.cyber_font, 12),
            bg=self.colors["bg_dark"],
            fg=self.colors["warning"]
        )
        status_label.pack(side=tk.RIGHT)

        # Основная область
        main_frame = tk.Frame(search_win, bg=self.colors["bg_dark"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Левая панель - список результатов
        list_frame = tk.Frame(main_frame, bg=self.colors["bg_card"])
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(
            list_frame,
            text="📦 Найденные модели",
            font=(self.cyber_font, 12, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        ).pack(anchor=tk.W, padx=15, pady=(15, 10))

        results_listbox = tk.Listbox(
            list_frame,
            font=(self.cyber_font, 11),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_primary"],
            selectbackground=self.colors["accent_purple"],
            selectforeground=self.colors["text_primary"],
            height=20,
            bd=0
        )
        results_listbox.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Правая панель - детали
        details_frame = tk.Frame(main_frame, bg=self.colors["bg_card"], width=400)
        details_frame.pack(side=tk.RIGHT, fill=tk.Y)
        details_frame.pack_propagate(False)

        tk.Label(
            details_frame,
            text="ℹ️ Информация о модели",
            font=(self.cyber_font, 12, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        ).pack(anchor=tk.W, padx=15, pady=(15, 10))

        details_text = scrolledtext.ScrolledText(
            details_frame,
            font=(self.cyber_font, 10),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_secondary"],
            wrap=tk.WORD,
            bd=0,
            height=15
        )
        details_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # Кнопки действий
        actions_frame = tk.Frame(details_frame, bg=self.colors["bg_card"])
        actions_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Список файлов для скачивания
        files_label = tk.Label(
            actions_frame,
            text="📁 GGUF файлы:",
            font=(self.cyber_font, 10, "bold"),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"]
        )
        files_label.pack(anchor=tk.W, pady=(0, 5))

        files_listbox = tk.Listbox(
            actions_frame,
            font=(self.cyber_font, 9),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_cyan"],
            height=6,
            bd=0
        )
        files_listbox.pack(fill=tk.X, pady=(0, 10))

        download_btn = tk.Label(
            actions_frame,
            text="📥 Скачать выбранный файл",
            font=(self.cyber_font, 11, "bold"),
            bg=self.colors["accent_pink"],
            fg=self.colors["text_primary"],
            cursor="hand2",
            pady=10
        )
        download_btn.pack(fill=tk.X)

        # Хранение результатов - используем словарь для обхода проблем с областью видимости
        data_store = {
            'results': [],
            'files': [],
            'current_model_idx': -1
        }

        def update_details(event=None):
            """Обновление деталей выбранной модели."""
            try:
                sel = results_listbox.curselection()
                if not sel:
                    return

                if not data_store['results']:
                    return

                idx = sel[0]
                if idx >= len(data_store['results']):
                    return

                # Сохраняем индекс текущей модели
                data_store['current_model_idx'] = idx

                model = data_store['results'][idx]
                details_text.config(state=tk.NORMAL)
                details_text.delete("1.0", tk.END)

                # Безопасное получение атрибутов
                downloads = getattr(model, 'downloads', 0)
                likes = getattr(model, 'likes', 0)
                last_modified = getattr(model, 'lastModified', 'N/A')
                if isinstance(last_modified, str) and len(last_modified) >= 10:
                    last_modified = last_modified[:10]
                tags = getattr(model, 'tags', []) or []

                # Получаем описание
                description = 'Нет описания'
                if hasattr(model, 'card_data') and model.card_data:
                    if isinstance(model.card_data, dict):
                        description = model.card_data.get('model_summary', 'Нет описания')

                info = f"""🏷️ ID: {model.id}

📥 Скачиваний: {downloads:,}
⭐ Лайков: {likes}
📅 Обновлено: {last_modified}

🏷️ Теги:
{', '.join(tags[:10]) if tags else 'Нет тегов'}

📝 Описание:
{description}

🔗 Ссылка:
https://huggingface.co/{model.id}
"""
                details_text.insert(tk.END, info)
                details_text.config(state=tk.DISABLED)

                # Загружаем список файлов
                files_listbox.delete(0, tk.END)
                files_listbox.insert(tk.END, "⏳ Загрузка файлов...")
                data_store['files'].clear()

                def load_files():
                    try:
                        from huggingface_hub import list_repo_files
                        all_files = list_repo_files(model.id)
                        gguf_files = [f for f in all_files if f.endswith('.gguf')]

                        def update_files():
                            files_listbox.delete(0, tk.END)
                            for f in gguf_files[:20]:  # Максимум 20 файлов
                                files_listbox.insert(tk.END, f)
                                data_store['files'].append(f)
                            if not gguf_files:
                                files_listbox.insert(tk.END, "❌ Нет .gguf файлов")

                        search_win.after(0, update_files)
                    except Exception as e:
                        search_win.after(0, lambda: files_listbox.delete(0, tk.END))
                        search_win.after(0, lambda: files_listbox.insert(tk.END, f"❌ Ошибка: {e}"))

                threading.Thread(target=load_files, daemon=True).start()

            except Exception as e:
                details_text.config(state=tk.NORMAL)
                details_text.delete("1.0", tk.END)
                details_text.insert(tk.END, f"❌ Ошибка загрузки: {e}")
                details_text.config(state=tk.DISABLED)

        results_listbox.bind('<<ListboxSelect>>', update_details)

        def download_selected():
            """Скачивание выбранного файла."""
            file_sel = files_listbox.curselection()

            # Проверяем что модель была выбрана
            if data_store['current_model_idx'] < 0 or not data_store['results']:
                messagebox.showwarning("Выберите", "Сначала выберите модель из списка слева!")
                return

            if not file_sel or not data_store['files']:
                messagebox.showwarning("Выберите", "Выберите файл для скачивания!")
                return

            file_text = files_listbox.get(file_sel[0])
            if file_text.startswith("❌") or file_text.startswith("⏳"):
                messagebox.showwarning("Ошибка", "Выберите валидный .gguf файл!")
                return

            model = data_store['results'][data_store['current_model_idx']]
            filename = data_store['files'][file_sel[0]]

            if messagebox.askyesno("Скачать?", f"Скачать {filename}?\n\nЭто может занять несколько минут."):
                search_win.destroy()
                self.add_system_message(f"⏳ Скачивание {filename}...")

                def dl():
                    try:
                        from model_manager import ModelManager
                        mm = ModelManager()
                        path = mm.download_model(model.id, filename, f"Модель из поиска HuggingFace")
                        if path:
                            self.root.after(0, lambda: self.add_system_message(f"✅ Скачано: {filename}"))
                            if messagebox.askyesno("Загрузить?", f"Загрузить {filename} сейчас?"):
                                self.root.after(0, lambda: self.load_gguf_model(path))
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

                threading.Thread(target=dl, daemon=True).start()

        download_btn.bind("<Button-1>", lambda e: download_selected())

        # Нижняя панель
        bottom_frame = tk.Frame(search_win, bg=self.colors["bg_dark"])
        bottom_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        result_count = tk.Label(
            bottom_frame,
            text="",
            font=(self.cyber_font, 10),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_muted"]
        )
        result_count.pack(side=tk.LEFT)

        tk.Label(
            bottom_frame,
            text="❌ Закрыть",
            font=(self.cyber_font, 11),
            bg=self.colors["error"],
            fg=self.colors["text_primary"],
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
        bottom_frame.winfo_children()[-1].bind("<Button-1>", lambda e: search_win.destroy())

        # Поиск в фоне
        def do_search():
            try:
                results = list(api.list_models(
                    search=query + " gguf",
                    sort="downloads",
                    direction=-1,
                    limit=50
                ))

                def update_results():
                    # Сохраняем результаты в словарь
                    data_store['results'] = results

                    for model in results:
                        downloads = getattr(model, 'downloads', 0)
                        downloads_str = f"{downloads:,}" if downloads else "0"
                        results_listbox.insert(tk.END, f"{model.id} ({downloads_str} скач.)")

                    status_label.config(text=f"✅ Найдено: {len(results)}", fg=self.colors["success"])
                    result_count.config(text=f"Найдено {len(results)} моделей с GGUF файлами")

                    if results:
                        results_listbox.selection_set(0)
                        # Вызываем обновление деталей с небольшой задержкой для гарантии выделения
                        search_win.after(100, update_details)

                search_win.after(0, update_results)

            except Exception as e:
                search_win.after(0, lambda: status_label.config(text=f"❌ Ошибка: {e}", fg=self.colors["error"]))

        threading.Thread(target=do_search, daemon=True).start()

    # ==================== Telegram ====================

    def show_telegram_setup(self):
        """Настройка Telegram."""
        token = simpledialog.askstring("Telegram", "Введите токен от @BotFather:", show="*")
        if token:
            config_dir = Path.home() / ".neyrolock"
            config_dir.mkdir(exist_ok=True)
            with open(config_dir / "telegram_config.json", 'w') as f:
                json.dump({"token": token}, f)
            self.add_system_message("✅ Токен Telegram сохранен!")

    def start_telegram_bot(self):
        """Запуск бота."""
        config_file = Path.home() / ".neyrolock" / "telegram_config.json"
        if not config_file.exists():
            messagebox.showwarning("Токен", "Сначала настройте токен!")
            return

        with open(config_file) as f:
            token = json.load(f).get("token", "")

        if token:
            env = os.environ.copy()
            env["TELEGRAM_BOT_TOKEN"] = token
            subprocess.Popen([sys.executable, str(Path(__file__).parent / "telegram_bot.py"), "--token", token],
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.add_system_message("🚀 Telegram бот запущен!")
            self.sync_status.config(text="🟢 Бот работает", fg=self.colors["success"])

    # ==================== Настройки ====================

    def change_font_size(self):
        """Изменение шрифта."""
        size = simpledialog.askinteger("Шрифт", "Размер (10-20):", initialvalue=self.current_font_size)
        if size:
            self.current_font_size = size
            self.chat_display.config(font=(self.cyber_font, size))
            self.input_text.config(font=(self.cyber_font, size))
            self.setup_chat_tags()

    def change_font_color(self):
        """Изменение цвета шрифта."""
        # Создаем окно выбора цвета
        color_win = tk.Toplevel(self.root)
        color_win.title("🌈 Выберите цвет шрифта")
        color_win.geometry("400x500")
        color_win.configure(bg=self.colors["bg_dark"])
        color_win.transient(self.root)

        tk.Label(
            color_win,
            text="🌈 Цвет шрифта чата",
            font=(self.cyber_font, 16, "bold"),
            bg=self.colors["bg_dark"],
            fg=self.colors["accent_pink"]
        ).pack(pady=15)

        # Предустановленные цвета
        colors_list = [
            ("#4ade80", "Зеленый (по умолчанию)"),
            ("#ffffff", "Белый"),
            ("#22d3ee", "Голубой"),
            ("#c084fc", "Фиолетовый"),
            ("#ff6b9d", "Розовый"),
            ("#fbbf24", "Желтый"),
            ("#f97316", "Оранжевый"),
            ("#ef4444", "Красный"),
            ("#a3e635", "Лайм"),
            ("#2dd4bf", "Бирюзовый"),
        ]

        selected_color = tk.StringVar(value=self.colors["accent_green"])

        for color_hex, color_name in colors_list:
            frame = tk.Frame(color_win, bg=self.colors["bg_dark"])
            frame.pack(fill=tk.X, padx=20, pady=3)

            rb = tk.Radiobutton(
                frame,
                variable=selected_color,
                value=color_hex,
                bg=self.colors["bg_dark"],
                activebackground=self.colors["bg_dark"],
                selectcolor=self.colors["bg_card"]
            )
            rb.pack(side=tk.LEFT)

            # Цветовой квадрат
            color_box = tk.Frame(frame, bg=color_hex, width=25, height=25)
            color_box.pack(side=tk.LEFT, padx=10)
            color_box.pack_propagate(False)

            tk.Label(
                frame,
                text=color_name,
                font=(self.cyber_font, 12),
                bg=self.colors["bg_dark"],
                fg=self.colors["text_primary"]
            ).pack(side=tk.LEFT)

        # Кастомный цвет
        custom_frame = tk.Frame(color_win, bg=self.colors["bg_dark"])
        custom_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(
            custom_frame,
            text="Или введите HEX цвет:",
            font=(self.cyber_font, 11),
            bg=self.colors["bg_dark"],
            fg=self.colors["text_muted"]
        ).pack(anchor=tk.W)

        custom_entry = tk.Entry(
            custom_frame,
            font=(self.cyber_font, 12),
            bg=self.colors["bg_card"],
            fg=self.colors["text_primary"],
            insertbackground=self.colors["accent_pink"]
        )
        custom_entry.pack(fill=tk.X, pady=5)
        custom_entry.insert(0, "#")

        # Превью
        preview_frame = tk.Frame(color_win, bg=self.colors["bg_card"], padx=10, pady=10)
        preview_frame.pack(fill=tk.X, padx=20, pady=10)

        preview_label = tk.Label(
            preview_frame,
            text="Превью: Так будет выглядеть текст AI",
            font=(self.cyber_font, 12),
            bg=self.colors["bg_card"],
            fg=self.colors["accent_green"]
        )
        preview_label.pack()

        def update_preview(*args):
            color = selected_color.get()
            preview_label.config(fg=color)

        selected_color.trace_add('write', update_preview)

        def apply_color():
            color = custom_entry.get().strip() if custom_entry.get().strip() != "#" else selected_color.get()
            if not color.startswith("#"):
                color = "#" + color

            # Обновляем цвет
            self.colors["accent_green"] = color
            self.chat_display.tag_configure(
                "assistant",
                foreground=color,
                font=(self.cyber_font, self.current_font_size)
            )
            self.add_system_message(f"🌈 Цвет шрифта изменен на {color}")
            color_win.destroy()

        tk.Button(
            color_win,
            text="✅ Применить",
            command=apply_color,
            font=(self.cyber_font, 12, "bold"),
            bg=self.colors["accent_green"],
            fg=self.colors["text_primary"],
            bd=0,
            padx=30,
            pady=10
        ).pack(pady=15)

    def set_temperature(self):
        """Установка температуры."""
        temp = simpledialog.askfloat("Температура", "Значение (0.0-2.0):", initialvalue=self.temperature)
        if temp is not None:
            self.temperature = temp
            self.stat_labels["Температура"].config(text=str(temp))

    def set_system_prompt(self):
        """Системный промпт."""
        prompt = simpledialog.askstring("Промпт", "Системный промпт:")
        if prompt:
            if self.chat_history and self.chat_history[0].get('role') == 'system':
                self.chat_history[0]['content'] = prompt
            else:
                self.chat_history.insert(0, {"role": "system", "content": prompt})
            self.add_system_message(f"📝 Системный промпт установлен")

    def clear_history(self):
        """Очистка истории."""
        if messagebox.askyesno("Очистить?", "Очистить историю чата?"):
            self.chat_history = []
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.messages_count = 0
            self.tokens_used = 0
            self.stat_labels["Сообщений"].config(text="0")
            self.add_system_message("🗑️ История очищена")

    def save_dialog(self):
        """Сохранение диалога."""
        if not self.chat_history:
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({"messages": self.chat_history}, f, ensure_ascii=False, indent=2)
            self.add_system_message(f"💾 Сохранено: {Path(path).name}")

    def test_markdown(self):
        """Тестовое сообщение с markdown форматированием."""
        test_message = """## 1. Установи библиотеку

```bash
pip install python-telegram-bot
```

## 2. Пример кода простого бота

```python
from telegram.ext import Updater, CommandHandler

TOKEN = 'YOUR_BOT_TOKEN'

def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет, я бот!'
    )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
```

**Примечание**: Используйте `HTTPS` для безопасности. Также проверьте *документацию* библиотеки."""

        self.add_message("assistant", test_message)

    # ==================== Память и сохранение ====================

    def save_config(self):
        """Сохранение конфигурации."""
        config = {
            "temperature": self.temperature,
            "font_size": self.current_font_size,
            "font_color": self.colors["accent_green"],
            "last_model_path": self.last_model_path,
            "messages_count": self.messages_count,
            "tokens_used": self.tokens_used,
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфига: {e}")

    def load_config(self):
        """Загрузка конфигурации."""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.temperature = config.get("temperature", 0.7)
            self.current_font_size = config.get("font_size", 13)
            self.colors["accent_green"] = config.get("font_color", "#4ade80")
            self.last_model_path = config.get("last_model_path", "")
            self.messages_count = config.get("messages_count", 0)
            self.tokens_used = config.get("tokens_used", 0)

            # Применяем настройки
            self.chat_display.config(font=(self.cyber_font, self.current_font_size))
            self.input_text.config(font=(self.cyber_font, self.current_font_size))
            self.setup_chat_tags()
            self.stat_labels["Температура"].config(text=str(self.temperature))
            self.stat_labels["Сообщений"].config(text=str(self.messages_count))
            self.activity_label.config(text=f"Сообщений: {self.messages_count}\nТокенов: ~{self.tokens_used}")

            # Предлагаем загрузить последнюю модель (с задержкой чтобы не блокировать инициализацию)
            if self.last_model_path and Path(self.last_model_path).exists():
                self.root.after(1000, self.ask_load_last_model)

        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")

    def ask_load_last_model(self):
        """Предложение загрузить последнюю модель."""
        if self.last_model_path and Path(self.last_model_path).exists():
            if messagebox.askyesno("Загрузить модель?", f"Загрузить последнюю модель?\n{Path(self.last_model_path).name}"):
                self.load_gguf_model(self.last_model_path)

    def save_chat_history(self):
        """Сохранение истории чата."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "history": self.chat_history,
                    "timestamp": datetime.datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории: {e}")

    def load_chat_history(self):
        """Загрузка истории чата (оптимизированная)."""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.chat_history = data.get("history", [])

            # Отображаем только последние 20 сообщений для скорости
            recent_messages = self.chat_history[-20:] if len(self.chat_history) > 20 else self.chat_history

            # Быстрое отображение без полного markdown рендеринга
            self.chat_display.config(state=tk.NORMAL)
            for msg in recent_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ["user", "assistant"]:
                    timestamp = "..."
                    if role == "user":
                        prefix = f"\n[{timestamp}] 👤 Вы\n"
                        self.chat_display.insert(tk.END, prefix, "user")
                        self.chat_display.insert(tk.END, content + "\n", "user")
                    else:
                        prefix = f"\n[{timestamp}] 🤖 AI\n"
                        self.chat_display.insert(tk.END, prefix, "assistant")
                        # Упрощенный рендеринг - без создания виджетов
                        self.chat_display.insert(tk.END, content + "\n", "assistant")

            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)

            if len(self.chat_history) > 20:
                self.add_system_message(f"📜 Показаны последние 20 из {len(self.chat_history)} сообщений")

        except Exception as e:
            print(f"Ошибка загрузки истории: {e}")

    def on_closing(self):
        """Обработка закрытия приложения."""
        # Сохраняем все данные
        self.save_config()
        self.save_chat_history()

        # Останавливаем синхронизацию
        if self.sync_manager:
            self.sync_manager.update_status("gui_active", False)
            self.sync_manager.stop_monitoring()

        self.root.destroy()

    def run(self):
        """Запуск."""
        self.root.mainloop()


def main():
    app = NeyrolockDashboard()
    app.run()


if __name__ == "__main__":
    main()
