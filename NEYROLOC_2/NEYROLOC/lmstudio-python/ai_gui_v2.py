#!/usr/bin/env python
"""
🤖 AI GUI v2.0 - Улучшенный графический интерфейс
• Красочный интерфейс
• Горячие клавиши на русской раскладке
• Интеграция с Telegram-ботом
• Улучшенная настройка шрифтов
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


class AIGUIv2:
    """Улучшенный графический интерфейс для AI."""

    def __init__(self):
        """Инициализация GUI."""
        self.root = tk.Tk()
        self.root.title("🤖 NEYROLOCK - Локальные модели с HuggingFace")
        self.root.geometry("1000x750")
        self.root.minsize(800, 600)

        # Состояние
        self.model = None
        self.backend = None
        self.chat_history = []
        self.is_generating = False
        self.temperature = 0.7
        self.current_font_size = 14
        self.telegram_sync = None  # Для синхронизации с Telegram

        # Кибер-шрифт (моноширинный, технологичный)
        self.cyber_font = "Menlo"  # Встроенный моноширинный шрифт Mac
        # Альтернативы: "SF Mono", "Monaco", "Courier New"

        # Цвета для красочного интерфейса
        self.colors = {
            "bg_main": "#1e1e2e",           # Темный фон
            "bg_chat": "#2d2d3f",           # Фон чата
            "bg_input": "#3d3d5c",          # Фон ввода
            "text_user": "#89b4fa",          # Синий для пользователя
            "text_ai": "#a6e3a1",            # Зеленый для AI
            "text_system": "#cdd6f4",        # Светлый для системы
            "accent": "#f5c2e7",             # Розовый акцент
            "accent2": "#fab387",            # Оранжевый акцент
            "button_bg": "#45475a",          # Фон кнопок
            "button_fg": "#cdd6f4",          # Текст кнопок
            "status_bg": "#313244",          # Фон статуса
        }

        # Применяем темную тему
        self.setup_theme()

        # Конфигурация
        self.config_dir = Path.home() / ".neyrolock"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Создание интерфейса
        self.create_menu()
        self.create_widgets()
        self.create_status_bar()
        self.setup_hotkeys()

        # Синхронизация с Telegram
        self.setup_sync()

        # Приветственное сообщение
        self.append_to_chat("system", "🌟 Добро пожаловать в NEYROLOCK! 🌟\n\n"
                           "✨ Новые возможности:\n"
                           "• 🎨 Красочный интерфейс\n"
                           "• 🌍 Горячие клавиши на русской раскладке\n"
                           "• 📱 Интеграция с Telegram-ботом\n"
                           "• 🔧 Улучшенные настройки\n\n"
                           "🚀 Для начала:\n"
                           "1. Меню 'Модели' → 'Скачать модель'\n"
                           "2. Выберите модель и дождитесь скачивания\n"
                           "3. Начинайте общаться!\n\n"
                           "💡 Горячие клавиши работают на русской раскладке!")

    def setup_sync(self):
        """Настройка синхронизации с Telegram."""
        self.sync_manager = None
        try:
            from sync_manager import SyncManager
            self.sync_manager = SyncManager()
            self.sync_manager.update_status("gui_active", True)
            if self.model:
                self.sync_manager.update_status("model_loaded", True)
                if hasattr(self, 'model_path'):
                    self.sync_manager.update_status("model_name", Path(self.model_path).name)

            # Запускаем мониторинг сообщений из Telegram
            self.sync_manager.start_monitoring(
                on_message=self.on_sync_message,
                on_stream=self.on_sync_stream
            )
            self.append_to_chat("system", "📱 Синхронизация с Telegram включена")
        except ImportError as e:
            self.append_to_chat("system", f"⚠️ Синхронизация недоступна: {e}")
        except Exception as e:
            self.append_to_chat("system", f"⚠️ Ошибка синхронизации: {e}")

    def on_sync_message(self, message: dict):
        """Обработка сообщения из Telegram."""
        # Показываем только сообщения из Telegram
        if message.get("source") == "telegram":
            role = message.get("role", "user")
            content = message.get("content", "")
            chat_id = message.get("chat_id", 0)

            # Добавляем метку Telegram
            prefix = f"[TG:{chat_id}] " if chat_id else "[TG] "

            # Обновляем UI из основного потока
            def update_ui():
                self.append_to_chat(role, f"{prefix}{content}")
                # Добавляем в историю
                self.chat_history.append({"role": role, "content": content})

            self.root.after(0, update_ui)

    def on_sync_stream(self, stream_data: dict):
        """Обработка стриминга из Telegram."""
        if stream_data.get("source") == "telegram" and stream_data.get("is_streaming"):
            # Обновляем статус
            chars = stream_data.get("chars_count", 0)
            self.root.after(0, lambda: self.update_status(f"📱 TG стриминг: {chars} символов..."))

    def setup_theme(self):
        """Настройка темной темы."""
        self.root.configure(bg=self.colors["bg_main"])

        # Стиль для ttk виджетов
        style = ttk.Style()
        style.theme_use('clam')

        # Настройка стилей с кибер-шрифтом
        style.configure("TFrame", background=self.colors["bg_main"])
        style.configure("TLabel", background=self.colors["bg_main"], foreground=self.colors["text_system"])
        style.configure("TButton",
                       background=self.colors["button_bg"],
                       foreground=self.colors["button_fg"],
                       font=(self.cyber_font, 12, "bold"))
        style.map("TButton",
                 background=[("active", self.colors["accent"])])

        style.configure("Accent.TButton",
                       background=self.colors["accent2"],
                       foreground="#1e1e2e",
                       font=(self.cyber_font, 12, "bold"))

        style.configure("TLabelframe",
                       background=self.colors["bg_main"],
                       foreground=self.colors["accent"])
        style.configure("TLabelframe.Label",
                       background=self.colors["bg_main"],
                       foreground=self.colors["accent"],
                       font=(self.cyber_font, 12, "bold"))

    def setup_hotkeys(self):
        """Настройка горячих клавиш (кроссплатформенная, включая русскую раскладку).

        macOS: Command+клавиша
        Windows/Linux: Control+клавиша
        """
        mod = get_modifier_key()

        # Основные горячие клавиши с динамическим модификатором
        self.root.bind(f"<{mod}-s>", lambda e: self.save_dialog())
        self.root.bind(f"<{mod}-q>", lambda e: self.quit_app())
        self.root.bind(f"<{mod}-n>", lambda e: self.clear_history())
        self.root.bind(f"<{mod}-d>", lambda e: self.download_model())
        self.root.bind(f"<{mod}-l>", lambda e: self.load_local_model())
        self.root.bind(f"<{mod}-t>", lambda e: self.show_telegram_setup())

        # Control-варианты для совместимости (работают везде)
        self.root.bind("<Control-s>", lambda e: self.save_dialog())
        self.root.bind("<Control-q>", lambda e: self.quit_app())
        self.root.bind("<Control-n>", lambda e: self.clear_history())
        self.root.bind("<Control-d>", lambda e: self.download_model())
        self.root.bind("<Control-l>", lambda e: self.load_local_model())
        self.root.bind("<Control-t>", lambda e: self.show_telegram_setup())

        # Универсальный обработчик для всех клавиш (работает на русской раскладке)
        self.root.bind("<KeyPress>", self.handle_any_key)

    def handle_any_key(self, event):
        """Обработка всех клавиш для поддержки русской раскладки (кроссплатформенная)."""
        # Проверяем модификаторы: Command только на macOS, Control везде
        is_command = bool(event.state & 0x8) if is_macos() else False
        is_control = bool(event.state & 0x4)

        if not (is_command or is_control):
            return

        # Маппинг русских символов на действия
        ru_to_action = {
            'ы': self.save_dialog,      # S -> Ы
            'й': self.quit_app,         # Q -> Й
            'т': self.clear_history,    # N -> Т
            'в': self.download_model,   # D -> В
            'д': self.load_local_model, # L -> Д
            'е': self.show_telegram_setup,  # T -> Е
            # Большие буквы тоже
            'Ы': self.save_dialog,
            'Й': self.quit_app,
            'Т': self.clear_history,
            'В': self.download_model,
            'Д': self.load_local_model,
            'Е': self.show_telegram_setup,
        }

        # Маппинг для копирования/вставки на русской раскладке
        ru_clipboard = {
            'с': 'copy',   # C -> С
            'м': 'paste',  # V -> М
            'ч': 'cut',    # X -> Ч
            'я': 'undo',   # Z -> Я
            'С': 'copy',
            'М': 'paste',
            'Ч': 'cut',
            'Я': 'undo',
        }

        # Получаем символ
        char = event.char if event.char else ''
        keysym = event.keysym if event.keysym else ''

        # Проверяем русские символы для команд
        if char in ru_to_action:
            ru_to_action[char]()
            return "break"
        elif keysym in ru_to_action:
            ru_to_action[keysym]()
            return "break"

        # Проверяем копирование/вставку на русской раскладке
        if char in ru_clipboard:
            action = ru_clipboard[char]
            try:
                focused = self.root.focus_get()
                if focused:
                    if action == 'copy':
                        focused.event_generate("<<Copy>>")
                    elif action == 'paste':
                        focused.event_generate("<<Paste>>")
                    elif action == 'cut':
                        focused.event_generate("<<Cut>>")
                    elif action == 'undo':
                        focused.event_generate("<<Undo>>")
                    return "break"
            except Exception:
                pass
        elif keysym in ru_clipboard:
            action = ru_clipboard[keysym]
            try:
                focused = self.root.focus_get()
                if focused:
                    if action == 'copy':
                        focused.event_generate("<<Copy>>")
                    elif action == 'paste':
                        focused.event_generate("<<Paste>>")
                    elif action == 'cut':
                        focused.event_generate("<<Cut>>")
                    elif action == 'undo':
                        focused.event_generate("<<Undo>>")
                    return "break"
            except Exception:
                pass

    def create_menu(self):
        """Создание меню."""
        menubar = tk.Menu(self.root, bg=self.colors["bg_main"], fg=self.colors["text_system"],
                         font=(self.cyber_font, 11))
        self.root.config(menu=menubar)

        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg_chat"], fg=self.colors["text_system"],
                           font=(self.cyber_font, 11))
        menubar.add_cascade(label="📁 Файл", menu=file_menu)
        file_menu.add_command(label="💾 Сохранить диалог", command=self.save_dialog, accelerator="⌘S / ⌘Ы")
        file_menu.add_command(label="📂 Загрузить диалог", command=self.load_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="🗑️ Очистить историю", command=self.clear_history, accelerator="⌘N / ⌘Т")
        file_menu.add_separator()
        file_menu.add_command(label="❌ Выход", command=self.quit_app, accelerator="⌘Q / ⌘Й")

        # Меню "Модели"
        models_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg_chat"], fg=self.colors["text_system"])
        menubar.add_cascade(label="🤖 Модели", menu=models_menu)
        models_menu.add_command(label="📥 Скачать модель с HuggingFace", command=self.download_model, accelerator="⌘D / ⌘В")
        models_menu.add_command(label="📂 Загрузить локальную модель", command=self.load_local_model, accelerator="⌘L / ⌘Д")
        models_menu.add_separator()
        models_menu.add_command(label="📋 Показать скачанные модели", command=self.show_downloaded_models)
        models_menu.add_command(label="🔍 Найти модель на HuggingFace", command=self.search_models)
        models_menu.add_separator()
        models_menu.add_command(label="ℹ️ Информация о текущей модели", command=self.show_model_info)
        models_menu.add_command(label="🔄 Выгрузить модель", command=self.unload_model)

        # Меню "Backend"
        backend_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg_chat"], fg=self.colors["text_system"])
        menubar.add_cascade(label="⚙️ Backend", menu=backend_menu)
        backend_menu.add_command(label="🖥️ Local GGUF (рекомендуется)", command=lambda: self.switch_backend("local"))
        backend_menu.add_command(label="🏠 NEYROLOCK Server", command=lambda: self.switch_backend("lmstudio"))
        backend_menu.add_command(label="🦙 Ollama", command=lambda: self.switch_backend("ollama"))
        backend_menu.add_separator()
        backend_menu.add_command(label="⚡ Groq (облако, бесплатно)", command=lambda: self.switch_backend("groq"))
        backend_menu.add_command(label="🌐 OpenAI (облако, платно)", command=lambda: self.switch_backend("openai"))

        # Меню "Telegram" (НОВОЕ!)
        telegram_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg_chat"], fg=self.colors["text_system"])
        menubar.add_cascade(label="📱 Telegram", menu=telegram_menu)
        telegram_menu.add_command(label="🤖 Настроить Telegram-бот", command=self.show_telegram_setup, accelerator="⌘T / ⌘Е")
        telegram_menu.add_command(label="📖 Как получить токен", command=self.show_telegram_guide)
        telegram_menu.add_separator()
        telegram_menu.add_command(label="🚀 Запустить бот", command=self.start_telegram_bot)

        # Меню "Настройки"
        settings_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg_chat"], fg=self.colors["text_system"])
        menubar.add_cascade(label="🔧 Настройки", menu=settings_menu)
        settings_menu.add_command(label="🎨 Размер шрифта", command=self.change_font_size)
        settings_menu.add_command(label="📝 Системный промпт", command=self.set_system_prompt)
        settings_menu.add_command(label="🌡️ Температура генерации", command=self.set_temperature)
        settings_menu.add_separator()
        settings_menu.add_command(label="🌙 Тема: Темная", state=tk.DISABLED)

        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg_chat"], fg=self.colors["text_system"])
        menubar.add_cascade(label="❓ Помощь", menu=help_menu)
        help_menu.add_command(label="📖 Быстрый старт", command=self.show_quick_start)
        help_menu.add_command(label="⌨️ Горячие клавиши", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ О программе", command=self.show_about)

    def create_widgets(self):
        """Создание виджетов."""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Верхняя панель с градиентом
        header_frame = tk.Frame(main_frame, bg=self.colors["bg_main"], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        # Заголовок
        title_label = tk.Label(
            header_frame,
            text="🤖 NEYROLOCK",
            font=(self.cyber_font, 24, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent"]
        )
        title_label.pack(side=tk.LEFT, padx=10)

        # Информация о модели справа
        info_frame = tk.Frame(header_frame, bg=self.colors["bg_main"])
        info_frame.pack(side=tk.RIGHT, padx=10)

        self.model_label = tk.Label(
            info_frame,
            text="📦 Модель: Не загружена",
            font=(self.cyber_font, 12, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent2"]
        )
        self.model_label.pack(anchor=tk.E)

        self.backend_label = tk.Label(
            info_frame,
            text="⚙️ Backend: -",
            font=(self.cyber_font, 10),
            bg=self.colors["bg_main"],
            fg=self.colors["text_system"]
        )
        self.backend_label.pack(anchor=tk.E)

        # Область чата с красивой рамкой
        chat_frame = tk.LabelFrame(
            main_frame,
            text="💬 Диалог",
            font=(self.cyber_font, 14, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent"],
            bd=2,
            relief=tk.GROOVE
        )
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Чат с темным фоном и кибер-шрифтом
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=(self.cyber_font, self.current_font_size),
            state=tk.DISABLED,
            bg=self.colors["bg_chat"],
            fg=self.colors["text_system"],
            insertbackground=self.colors["accent"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_main"],
            bd=0,
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Настройка тегов для цветного форматирования
        self.update_chat_tags()

        # Область ввода
        input_frame = tk.Frame(main_frame, bg=self.colors["bg_main"])
        input_frame.pack(fill=tk.X)

        # Метка над полем ввода
        input_label = tk.Label(
            input_frame,
            text="✍️ Ваше сообщение:",
            font=(self.cyber_font, 11, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent2"]
        )
        input_label.pack(anchor=tk.W, pady=(0, 5))

        # Поле ввода
        input_container = tk.Frame(input_frame, bg=self.colors["bg_main"])
        input_container.pack(fill=tk.X)

        self.input_text = tk.Text(
            input_container,
            height=3,
            font=(self.cyber_font, self.current_font_size),
            wrap=tk.WORD,
            bg=self.colors["bg_input"],
            fg=self.colors["text_system"],
            insertbackground=self.colors["accent"],
            selectbackground=self.colors["accent"],
            bd=2,
            relief=tk.GROOVE,
            padx=10,
            pady=10
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_text.bind("<Return>", self.on_enter_pressed)
        self.input_text.bind("<Shift-Return>", lambda e: None)

        # Кнопки справа с градиентом
        buttons_frame = tk.Frame(input_container, bg=self.colors["bg_main"])
        buttons_frame.pack(side=tk.RIGHT)

        self.send_button = tk.Button(
            buttons_frame,
            text="📤 Отправить",
            command=self.send_message,
            font=(self.cyber_font, 12, "bold"),
            bg=self.colors["accent2"],
            fg=self.colors["bg_main"],
            activebackground=self.colors["accent"],
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.send_button.pack(pady=(0, 5))

        self.stop_button = tk.Button(
            buttons_frame,
            text="⏹️ Стоп",
            command=self.stop_generation,
            state=tk.DISABLED,
            font=(self.cyber_font, 11),
            bg=self.colors["button_bg"],
            fg=self.colors["button_fg"],
            disabledforeground="#666666",
            bd=0,
            padx=20,
            pady=8
        )
        self.stop_button.pack()

    def update_chat_tags(self):
        """Обновляет теги форматирования с текущим размером шрифта."""
        self.chat_display.tag_configure(
            "user",
            foreground=self.colors["text_user"],
            font=(self.cyber_font, self.current_font_size, "bold")
        )
        self.chat_display.tag_configure(
            "assistant",
            foreground=self.colors["text_ai"],
            font=(self.cyber_font, self.current_font_size)
        )
        self.chat_display.tag_configure(
            "system",
            foreground=self.colors["text_system"],
            font=(self.cyber_font, self.current_font_size - 1, "italic")
        )
        self.chat_display.tag_configure(
            "timestamp",
            foreground="#666666",
            font=(self.cyber_font, self.current_font_size - 3)
        )

    def create_status_bar(self):
        """Создание статусной строки."""
        status_frame = tk.Frame(self.root, bg=self.colors["status_bg"], height=30)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        status_frame.pack_propagate(False)

        self.status_var = tk.StringVar(value="✅ Готов к работе")
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=self.colors["status_bg"],
            fg=self.colors["text_system"],
            font=(self.cyber_font, 11),
            anchor=tk.W,
            padx=10
        )
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Индикатор горячих клавиш
        hotkey_label = tk.Label(
            status_frame,
            text="⌨️ RU/EN",
            bg=self.colors["status_bg"],
            fg=self.colors["accent"],
            font=(self.cyber_font, 10)
        )
        hotkey_label.pack(side=tk.RIGHT, padx=10)

    def change_font_size(self):
        """Изменение размера шрифта во всем интерфейсе."""
        size = simpledialog.askinteger(
            "Размер шрифта",
            "Введите размер шрифта (10-24):",
            initialvalue=self.current_font_size,
            minvalue=10,
            maxvalue=24
        )

        if size:
            self.current_font_size = size

            # Обновляем шрифт в чате (кибер-шрифт)
            self.chat_display.config(font=(self.cyber_font, size))
            self.update_chat_tags()

            # Обновляем шрифт в поле ввода
            self.input_text.config(font=(self.cyber_font, size))

            # Пересоздаем теги для всего текста
            self.chat_display.config(state=tk.NORMAL)
            content = self.chat_display.get("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)

            messagebox.showinfo("Готово", f"Размер шрифта изменен на {size}")

    # ==================== Telegram интеграция ====================

    def show_telegram_setup(self):
        """Настройка Telegram-бота."""
        setup_window = tk.Toplevel(self.root)
        setup_window.title("📱 Настройка Telegram-бота")
        setup_window.geometry("600x500")
        setup_window.configure(bg=self.colors["bg_main"])
        setup_window.transient(self.root)
        setup_window.grab_set()

        # Заголовок
        tk.Label(
            setup_window,
            text="🤖 Настройка Telegram-бота",
            font=("Helvetica", 18, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent"]
        ).pack(pady=20)

        # Инструкция
        instruction_text = """
📝 Как создать Telegram-бота:

1. Откройте Telegram и найдите @BotFather
2. Отправьте команду /newbot
3. Введите имя бота (например: NEYROLOCK Bot)
4. Введите username бота (например: my_ai_bot)
5. BotFather выдаст вам токен

⚠️ Токен выглядит так:
123456789:ABCdefGHIjklMNOpqrsTUVwxyz

Скопируйте токен и вставьте ниже 👇
        """

        instruction_label = tk.Label(
            setup_window,
            text=instruction_text,
            font=("Helvetica", 12),
            bg=self.colors["bg_main"],
            fg=self.colors["text_system"],
            justify=tk.LEFT
        )
        instruction_label.pack(padx=20, pady=10)

        # Поле для токена
        token_frame = tk.Frame(setup_window, bg=self.colors["bg_main"])
        token_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(
            token_frame,
            text="🔑 Токен бота:",
            font=("Helvetica", 12, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent2"]
        ).pack(anchor=tk.W)

        self.token_entry = tk.Entry(
            token_frame,
            font=("Helvetica", 12),
            bg=self.colors["bg_input"],
            fg=self.colors["text_system"],
            insertbackground=self.colors["accent"],
            show="*",
            width=50
        )
        self.token_entry.pack(fill=tk.X, pady=5)

        # Кнопка показать/скрыть токен
        show_var = tk.BooleanVar(value=False)

        def toggle_show():
            if show_var.get():
                self.token_entry.config(show="")
            else:
                self.token_entry.config(show="*")

        show_check = tk.Checkbutton(
            token_frame,
            text="Показать токен",
            variable=show_var,
            command=toggle_show,
            bg=self.colors["bg_main"],
            fg=self.colors["text_system"],
            selectcolor=self.colors["bg_chat"]
        )
        show_check.pack(anchor=tk.W)

        # Кнопки
        buttons_frame = tk.Frame(setup_window, bg=self.colors["bg_main"])
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)

        def save_and_start():
            token = self.token_entry.get().strip()
            if not token:
                messagebox.showwarning("Ошибка", "Введите токен бота!")
                return

            # Сохраняем токен
            config_file = self.config_dir / "telegram_config.json"
            with open(config_file, 'w') as f:
                json.dump({"token": token}, f)

            setup_window.destroy()

            if messagebox.askyesno("Запуск", "Токен сохранен!\n\nЗапустить Telegram-бот сейчас?"):
                self.start_telegram_bot()

        tk.Button(
            buttons_frame,
            text="✅ Сохранить и запустить",
            command=save_and_start,
            font=("Helvetica", 12, "bold"),
            bg=self.colors["accent2"],
            fg=self.colors["bg_main"],
            bd=0,
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            buttons_frame,
            text="❌ Отмена",
            command=setup_window.destroy,
            font=("Helvetica", 12),
            bg=self.colors["button_bg"],
            fg=self.colors["button_fg"],
            bd=0,
            padx=20,
            pady=10
        ).pack(side=tk.RIGHT, padx=5)

    def show_telegram_guide(self):
        """Подробная инструкция по Telegram."""
        guide = """
📱 ПОДРОБНАЯ ИНСТРУКЦИЯ ПО СОЗДАНИЮ TELEGRAM-БОТА

🔹 ШАГ 1: Откройте BotFather
   • Откройте Telegram
   • В поиске найдите @BotFather
   • Это официальный бот для создания ботов

🔹 ШАГ 2: Создайте нового бота
   • Отправьте команду: /newbot
   • BotFather спросит имя бота
   • Введите любое имя (например: "NEYROLOCK Bot")

🔹 ШАГ 3: Выберите username
   • BotFather попросит username
   • Должен заканчиваться на "bot"
   • Например: "my_ai_assistant_bot"

🔹 ШАГ 4: Получите токен
   • BotFather выдаст токен
   • Выглядит так: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   • Скопируйте его!

🔹 ШАГ 5: Настройте бот
   • Вставьте токен в программу
   • Нажмите "Сохранить и запустить"
   • Готово!

⚠️ ВАЖНО:
• Никому не показывайте токен!
• Если токен скомпрометирован - создайте нового бота
• Бот работает пока запущена программа

💡 После запуска:
• Найдите своего бота в Telegram
• Отправьте /start
• Используйте кнопки для управления
• Весь функционал как в GUI версии!
        """

        messagebox.showinfo("Инструкция по Telegram", guide)

    def start_telegram_bot(self):
        """Запуск Telegram-бота."""
        config_file = self.config_dir / "telegram_config.json"

        if not config_file.exists():
            messagebox.showwarning(
                "Токен не найден",
                "Сначала настройте Telegram-бот!\n\n"
                "Меню 'Telegram' → 'Настроить Telegram-бот'"
            )
            return

        with open(config_file, 'r') as f:
            config = json.load(f)

        token = config.get("token", "")
        if not token:
            messagebox.showwarning("Ошибка", "Токен пустой!")
            return

        # Проверяем наличие библиотеки
        try:
            import telegram
        except ImportError:
            if messagebox.askyesno(
                "Установка библиотеки",
                "Необходима библиотека python-telegram-bot\n\n"
                "Установить сейчас?"
            ):
                self.update_status("📦 Установка python-telegram-bot...")
                subprocess.run([sys.executable, "-m", "pip", "install", "python-telegram-bot", "--quiet"])
                messagebox.showinfo("Готово", "Библиотека установлена!\n\nПопробуйте запустить бот снова.")
            return

        # Запускаем бот в отдельном процессе с токеном через environment variable
        self.update_status("🤖 Запуск Telegram-бота...")

        def run_bot():
            try:
                env = os.environ.copy()
                env["TELEGRAM_BOT_TOKEN"] = token

                # Запускаем бот
                process = subprocess.Popen(
                    [sys.executable, str(Path(__file__).parent / "telegram_bot.py"), "--token", token],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.telegram_bot_process = process
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка запуска бота", str(e)))

        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()

        messagebox.showinfo(
            "Telegram-бот запущен",
            "✅ Бот запущен в фоне!\n\n"
            "Теперь:\n"
            "1. Откройте Telegram\n"
            "2. Найдите своего бота\n"
            "3. Отправьте /start\n\n"
            "Бот будет работать пока открыта программа.\n"
            "Сообщения синхронизируются автоматически!"
        )

        self.update_status("✅ Telegram-бот работает")

    # ==================== Остальные методы (как в ai_gui.py) ====================

    def append_to_chat(self, role: str, message: str):
        """Добавляет сообщение в чат."""
        self.chat_display.config(state=tk.NORMAL)

        # Добавляем timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M")

        if role == "user":
            prefix = f"\n[{timestamp}] 👤 Вы:\n"
            tag = "user"
        elif role == "assistant":
            prefix = f"\n[{timestamp}] 🤖 AI:\n"
            tag = "assistant"
        else:
            prefix = "\n"
            tag = "system"

        self.chat_display.insert(tk.END, prefix, tag)
        self.chat_display.insert(tk.END, message + "\n", tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def update_status(self, message: str):
        """Обновляет статусную строку."""
        self.status_var.set(message)
        self.root.update_idletasks()

    def on_enter_pressed(self, event):
        """Обработка нажатия Enter."""
        if not event.state & 0x1:
            self.send_message()
            return "break"

    def send_message(self):
        """Отправка сообщения."""
        if self.is_generating:
            return

        if not self.model:
            messagebox.showwarning(
                "Модель не загружена",
                "Сначала загрузите модель!\n\n"
                "Меню 'Модели' → 'Скачать модель с HuggingFace'\n"
                "или 'Загрузить локальную модель'"
            )
            return

        user_message = self.input_text.get("1.0", tk.END).strip()
        if not user_message:
            return

        self.input_text.delete("1.0", tk.END)
        self.append_to_chat("user", user_message)
        self.chat_history.append({"role": "user", "content": user_message})

        # Синхронизируем с Telegram
        if hasattr(self, 'sync_manager') and self.sync_manager:
            self.sync_manager.send_message("gui", "user", user_message, 0)
            self.sync_manager.start_stream("gui", 0)

        self.is_generating = True
        self.send_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("🔄 Генерация ответа...")

        thread = threading.Thread(target=self.generate_response, args=(user_message,))
        thread.daemon = True
        thread.start()

    def generate_response(self, user_message: str):
        """Генерация ответа."""
        try:
            if self.backend == "local":
                messages = self.chat_history.copy()
                response_text = ""

                self.root.after(0, lambda: self.append_to_chat("assistant", ""))

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
                            self.root.after(0, lambda c=content: self.update_last_message(c))

                            # Синхронизируем стрим с Telegram
                            if hasattr(self, 'sync_manager') and self.sync_manager:
                                self.sync_manager.update_stream(content)

                self.chat_history.append({"role": "assistant", "content": response_text})

                # Завершаем стрим и отправляем сообщение
                if hasattr(self, 'sync_manager') and self.sync_manager:
                    self.sync_manager.end_stream()
                    self.sync_manager.send_message("gui", "assistant", response_text, 0)

            elif self.backend in ["ollama", "groq", "openai"]:
                messages = self.chat_history.copy()

                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=True
                )

                response_text = ""
                self.root.after(0, lambda: self.append_to_chat("assistant", ""))

                for chunk in stream:
                    if not self.is_generating:
                        break

                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        response_text += content
                        self.root.after(0, lambda c=content: self.update_last_message(c))

                        # Синхронизируем стрим с Telegram
                        if hasattr(self, 'sync_manager') and self.sync_manager:
                            self.sync_manager.update_stream(content)

                self.chat_history.append({"role": "assistant", "content": response_text})

                # Завершаем стрим и отправляем сообщение
                if hasattr(self, 'sync_manager') and self.sync_manager:
                    self.sync_manager.end_stream()
                    self.sync_manager.send_message("gui", "assistant", response_text, 0)

        except Exception as e:
            self.root.after(0, lambda: self.append_to_chat("system", f"❌ Ошибка: {e}"))
            if hasattr(self, 'sync_manager') and self.sync_manager:
                self.sync_manager.end_stream()

        finally:
            self.root.after(0, self.finish_generation)

    def update_last_message(self, text: str):
        """Обновляет последнее сообщение."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text, "assistant")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def finish_generation(self):
        """Завершение генерации."""
        self.is_generating = False
        self.send_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("✅ Готов")

    def stop_generation(self):
        """Остановка генерации."""
        self.is_generating = False
        self.update_status("⏹️ Генерация остановлена")

    # Методы работы с моделями
    def download_model(self):
        """Скачивание модели с HuggingFace."""
        try:
            from model_manager import ModelManager
            self.model_manager = ModelManager()
        except ImportError:
            messagebox.showerror("Ошибка", "Не найден model_manager.py\n\nУстановите: pip3 install huggingface-hub")
            return

        # Создаем окно скачивания
        download_window = tk.Toplevel(self.root)
        download_window.title("📥 Скачать модель с HuggingFace")
        download_window.geometry("700x600")
        download_window.configure(bg=self.colors["bg_main"])
        download_window.transient(self.root)
        download_window.grab_set()

        # Заголовок
        tk.Label(
            download_window,
            text="📥 Скачать модель с HuggingFace",
            font=("Helvetica", 18, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent"]
        ).pack(pady=15)

        # Категории
        categories_frame = tk.LabelFrame(
            download_window,
            text="🏷️ Выберите категорию",
            font=("Helvetica", 12, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent2"]
        )
        categories_frame.pack(fill=tk.X, padx=20, pady=10)

        category_var = tk.StringVar(value="small")

        categories = [
            ("tiny", "🐣 Tiny (300-700MB) - Быстрые, малые"),
            ("small", "🌟 Small (2GB) - Рекомендуется"),
            ("medium", "💪 Medium (4-5GB) - Мощные"),
            ("multimodal", "🖼️ Multimodal (4GB) - Картинки")
        ]

        for cat_id, cat_name in categories:
            rb = tk.Radiobutton(
                categories_frame,
                text=cat_name,
                variable=category_var,
                value=cat_id,
                font=("Helvetica", 11),
                bg=self.colors["bg_main"],
                fg=self.colors["text_system"],
                selectcolor=self.colors["bg_chat"],
                activebackground=self.colors["bg_main"],
                activeforeground=self.colors["accent"]
            )
            rb.pack(anchor=tk.W, padx=10, pady=3)

        # Список моделей
        models_frame = tk.LabelFrame(
            download_window,
            text="🤖 Доступные модели",
            font=("Helvetica", 12, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent2"]
        )
        models_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        models_listbox = tk.Listbox(
            models_frame,
            font=("Helvetica", 11),
            bg=self.colors["bg_chat"],
            fg=self.colors["text_system"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_main"],
            height=10
        )
        models_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def update_models_list(*args):
            models_listbox.delete(0, tk.END)
            category = category_var.get()
            models = self.model_manager.RECOMMENDED_MODELS.get(category, [])
            for model in models:
                size_str = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']}MB"
                models_listbox.insert(tk.END, f"{model['filename'].split('.')[0][:35]} ({size_str})")

        category_var.trace_add('write', update_models_list)
        update_models_list()

        # Прогресс
        progress_var = tk.StringVar(value="Выберите модель и нажмите 'Скачать'")
        progress_label = tk.Label(
            download_window,
            textvariable=progress_var,
            font=(self.cyber_font, 10),
            bg=self.colors["bg_main"],
            fg=self.colors["text_system"]
        )
        progress_label.pack(pady=5)

        # Кнопки
        buttons_frame = tk.Frame(download_window, bg=self.colors["bg_main"])
        buttons_frame.pack(fill=tk.X, padx=20, pady=15)

        def start_download():
            selection = models_listbox.curselection()
            if not selection:
                messagebox.showwarning("Выберите модель", "Сначала выберите модель из списка!")
                return

            category = category_var.get()
            model_index = selection[0]
            model_info = self.model_manager.RECOMMENDED_MODELS[category][model_index]

            progress_var.set(f"⏳ Скачивание {model_info['filename']}...")
            download_window.update()

            def download_thread():
                try:
                    model_path = self.model_manager.download_model(
                        model_info['repo_id'],
                        model_info['filename'],
                        model_info['description']
                    )

                    if model_path:
                        self.root.after(0, lambda: progress_var.set("✅ Скачивание завершено!"))
                        self.root.after(0, lambda: self.on_download_complete(model_path, download_window))
                    else:
                        self.root.after(0, lambda: progress_var.set("❌ Ошибка скачивания"))
                except Exception as e:
                    self.root.after(0, lambda: progress_var.set(f"❌ Ошибка: {str(e)[:50]}"))
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))

            thread = threading.Thread(target=download_thread)
            thread.daemon = True
            thread.start()

        tk.Button(
            buttons_frame,
            text="📥 Скачать",
            command=start_download,
            font=("Helvetica", 12, "bold"),
            bg=self.colors["accent2"],
            fg=self.colors["bg_main"],
            bd=0,
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="❌ Отмена",
            command=download_window.destroy,
            font=("Helvetica", 12),
            bg=self.colors["button_bg"],
            fg=self.colors["button_fg"],
            bd=0,
            padx=30,
            pady=10
        ).pack(side=tk.RIGHT, padx=10)

    def on_download_complete(self, model_path: str, window):
        """После завершения скачивания."""
        window.destroy()
        if messagebox.askyesno("Загрузить модель", f"Модель скачана:\n{Path(model_path).name}\n\nЗагрузить сейчас?"):
            self.load_gguf_model(model_path)

    def load_local_model(self):
        """Загрузка локальной модели."""
        file_path = filedialog.askopenfilename(
            title="Выберите файл модели GGUF",
            filetypes=[("GGUF Models", "*.gguf"), ("All Files", "*.*")],
            initialdir=str(Path.home() / "Downloads")
        )

        if file_path:
            self.load_gguf_model(file_path)

    def load_gguf_model(self, model_path: str):
        """Загружает GGUF модель."""
        try:
            from llama_cpp import Llama
        except ImportError:
            messagebox.showerror("Ошибка", "Не установлен llama-cpp-python!")
            return

        n_ctx = simpledialog.askinteger("Контекст", "Размер контекста:", initialvalue=2048)
        if not n_ctx:
            return

        n_gpu = simpledialog.askinteger("GPU", "Слои на GPU (-1 = все):", initialvalue=-1)
        if n_gpu is None:
            return

        self.update_status("⏳ Загрузка модели...")

        def load_thread():
            try:
                model = Llama(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu, verbose=False)
                self.model = model
                self.backend = "local"
                self.model_path = model_path
                model_name = Path(model_path).name
                self.root.after(0, lambda: self.on_model_loaded(model_name))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"{e}"))
            finally:
                self.root.after(0, lambda: self.update_status("✅ Готов"))

        thread = threading.Thread(target=load_thread)
        thread.daemon = True
        thread.start()

    def on_model_loaded(self, model_name: str):
        """После загрузки модели."""
        self.model_label.config(text=f"📦 Модель: {model_name}")
        self.backend_label.config(text="⚙️ Backend: Local GGUF")
        self.append_to_chat("system", f"✅ Модель загружена: {model_name}\n\nМожете начинать диалог!")
        self.chat_history = []

        # Синхронизируем статус с Telegram
        if hasattr(self, 'sync_manager') and self.sync_manager:
            self.sync_manager.update_status("model_loaded", True)
            self.sync_manager.update_status("model_name", model_name)

    def show_downloaded_models(self):
        """Показать скачанные модели и выбрать для загрузки."""
        try:
            from model_manager import ModelManager
            mm = ModelManager()
        except ImportError:
            messagebox.showerror("Ошибка", "Не найден model_manager.py")
            return

        # Ищем .gguf файлы
        models_dir = mm.models_dir
        gguf_files = list(models_dir.glob("**/*.gguf"))

        if not gguf_files:
            messagebox.showinfo(
                "Модели не найдены",
                f"В папке {models_dir} не найдено .gguf файлов.\n\n"
                "Скачайте модель через меню 'Модели' → 'Скачать модель с HuggingFace'"
            )
            return

        # Создаем окно выбора
        select_window = tk.Toplevel(self.root)
        select_window.title("📋 Скачанные модели")
        select_window.geometry("700x500")
        select_window.configure(bg=self.colors["bg_main"])
        select_window.transient(self.root)
        select_window.grab_set()

        tk.Label(
            select_window,
            text="📋 Выберите модель для загрузки",
            font=(self.cyber_font, 16, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent"]
        ).pack(pady=15)

        # Список моделей
        models_frame = tk.Frame(select_window, bg=self.colors["bg_main"])
        models_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        models_listbox = tk.Listbox(
            models_frame,
            font=(self.cyber_font, 11),
            bg=self.colors["bg_chat"],
            fg=self.colors["text_system"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_main"],
            height=15
        )
        models_listbox.pack(fill=tk.BOTH, expand=True)

        # Заполняем список
        model_paths = []
        for f in sorted(gguf_files, key=lambda x: x.stat().st_mtime, reverse=True):
            size_mb = f.stat().st_size / (1024 * 1024)
            size_str = f"{size_mb/1000:.1f}GB" if size_mb >= 1000 else f"{size_mb:.0f}MB"
            models_listbox.insert(tk.END, f"{f.name} ({size_str})")
            model_paths.append(str(f))

        # Кнопки
        buttons_frame = tk.Frame(select_window, bg=self.colors["bg_main"])
        buttons_frame.pack(fill=tk.X, padx=20, pady=15)

        def load_selected():
            selection = models_listbox.curselection()
            if not selection:
                messagebox.showwarning("Выберите модель", "Выберите модель из списка!")
                return
            model_path = model_paths[selection[0]]
            select_window.destroy()
            self.load_gguf_model(model_path)

        tk.Button(
            buttons_frame,
            text="📂 Загрузить",
            command=load_selected,
            font=(self.cyber_font, 12, "bold"),
            bg=self.colors["accent2"],
            fg=self.colors["bg_main"],
            bd=0,
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="❌ Отмена",
            command=select_window.destroy,
            font=(self.cyber_font, 12),
            bg=self.colors["button_bg"],
            fg=self.colors["button_fg"],
            bd=0,
            padx=30,
            pady=10
        ).pack(side=tk.RIGHT, padx=10)

    def search_models(self):
        """Поиск моделей на HuggingFace."""
        query = simpledialog.askstring(
            "Поиск моделей",
            "Введите запрос для поиска на HuggingFace:\n(например: llama gguf, qwen instruct)",
            parent=self.root
        )

        if not query:
            return

        try:
            from huggingface_hub import HfApi
            api = HfApi()
        except ImportError:
            messagebox.showerror("Ошибка", "Установите: pip3 install huggingface-hub")
            return

        self.update_status(f"🔍 Поиск '{query}' на HuggingFace...")

        def search_thread():
            try:
                # Ищем репозитории с GGUF моделями
                results = list(api.list_models(
                    search=query + " gguf",
                    sort="downloads",
                    direction=-1,
                    limit=20
                ))

                self.root.after(0, lambda: self.show_search_results(results, query))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка поиска", str(e)))
            finally:
                self.root.after(0, lambda: self.update_status("✅ Готов"))

        thread = threading.Thread(target=search_thread)
        thread.daemon = True
        thread.start()

    def show_search_results(self, results, query):
        """Показать результаты поиска."""
        if not results:
            messagebox.showinfo("Результаты", f"По запросу '{query}' ничего не найдено")
            return

        # Окно результатов
        results_window = tk.Toplevel(self.root)
        results_window.title(f"🔍 Результаты поиска: {query}")
        results_window.geometry("800x600")
        results_window.configure(bg=self.colors["bg_main"])
        results_window.transient(self.root)

        tk.Label(
            results_window,
            text=f"🔍 Найдено моделей: {len(results)}",
            font=(self.cyber_font, 16, "bold"),
            bg=self.colors["bg_main"],
            fg=self.colors["accent"]
        ).pack(pady=15)

        # Текстовое поле с результатами
        results_text = scrolledtext.ScrolledText(
            results_window,
            wrap=tk.WORD,
            font=(self.cyber_font, 11),
            bg=self.colors["bg_chat"],
            fg=self.colors["text_system"],
            height=25
        )
        results_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Заполняем результаты
        for i, model in enumerate(results, 1):
            results_text.insert(tk.END, f"#{i} {model.id}\n", "title")
            results_text.insert(tk.END, f"   📥 Скачиваний: {model.downloads:,}\n")
            results_text.insert(tk.END, f"   ⭐ Лайков: {model.likes}\n")
            if model.tags:
                tags = ", ".join(model.tags[:5])
                results_text.insert(tk.END, f"   🏷️ Теги: {tags}\n")
            results_text.insert(tk.END, f"   🔗 https://huggingface.co/{model.id}\n")
            results_text.insert(tk.END, "\n")

        results_text.tag_configure("title", foreground=self.colors["accent"], font=(self.cyber_font, 12, "bold"))
        results_text.config(state=tk.DISABLED)

        tk.Button(
            results_window,
            text="❌ Закрыть",
            command=results_window.destroy,
            font=(self.cyber_font, 12),
            bg=self.colors["button_bg"],
            fg=self.colors["button_fg"],
            bd=0,
            padx=30,
            pady=10
        ).pack(pady=10)

    def show_model_info(self):
        """Информация о модели."""
        if not self.model:
            messagebox.showinfo("Информация", "Модель не загружена")
            return
        info = f"Backend: {self.backend}\nТемпература: {self.temperature}"
        if hasattr(self, 'model_path'):
            info += f"\nПуть: {self.model_path}"
        messagebox.showinfo("Информация", info)

    def unload_model(self):
        """Выгрузка модели."""
        if self.model:
            self.model = None
            self.backend = None
            self.model_label.config(text="📦 Модель: Не загружена")
            self.backend_label.config(text="⚙️ Backend: -")
            messagebox.showinfo("Готово", "Модель выгружена")

    def switch_backend(self, backend_type: str):
        """Переключение backend."""
        messagebox.showinfo("Backend", f"Переключение на {backend_type}")

    def save_dialog(self):
        """Сохранение диалога."""
        if not self.chat_history:
            messagebox.showinfo("Пусто", "Нет истории")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"chat_{timestamp}.json"
        )

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({"messages": self.chat_history}, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Сохранено", f"Диалог сохранен:\n{file_path}")

    def load_dialog(self):
        """Загрузка диалога."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.chat_history = data.get('messages', [])
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete("1.0", tk.END)
                self.chat_display.config(state=tk.DISABLED)
                for msg in self.chat_history:
                    self.append_to_chat(msg['role'], msg['content'])
                messagebox.showinfo("Загружено", "Диалог загружен")
            except Exception as e:
                messagebox.showerror("Ошибка", f"{e}")

    def clear_history(self):
        """Очистка истории."""
        if messagebox.askyesno("Подтверждение", "Очистить историю?"):
            self.chat_history = []
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.append_to_chat("system", "🗑️ История очищена")

    def quit_app(self):
        """Выход."""
        if messagebox.askyesno("Выход", "Выйти?"):
            self.root.quit()

    def set_system_prompt(self):
        """Системный промпт."""
        prompt = simpledialog.askstring("Системный промпт", "Введите промпт:")
        if prompt:
            if self.chat_history and self.chat_history[0].get('role') == 'system':
                self.chat_history[0]['content'] = prompt
            else:
                self.chat_history.insert(0, {"role": "system", "content": prompt})
            messagebox.showinfo("Готово", "Системный промпт установлен")

    def set_temperature(self):
        """Температура."""
        temp = simpledialog.askfloat("Температура", "Введите температуру (0.0-2.0):", initialvalue=self.temperature)
        if temp is not None:
            self.temperature = temp
            messagebox.showinfo("Готово", f"Температура: {temp}")

    def show_quick_start(self):
        """Быстрый старт."""
        text = """🚀 БЫСТРЫЙ СТАРТ

1. Скачайте модель: Меню 'Модели' → 'Скачать'
2. Или загрузите: 'Модели' → 'Загрузить локальную'
3. Напишите сообщение и нажмите Enter

💡 Горячие клавиши работают на русской раскладке!
   ⌘S/⌘Ы - Сохранить
   ⌘Q/⌘Й - Выход
   ⌘N/⌘Т - Новый диалог"""
        messagebox.showinfo("Быстрый старт", text)

    def show_shortcuts(self):
        """Горячие клавиши."""
        text = """⌨️ ГОРЯЧИЕ КЛАВИШИ (работают на RU и EN раскладках!)

📁 Файл:
   ⌘S / ⌘Ы - Сохранить диалог
   ⌘Q / ⌘Й - Выход
   ⌘N / ⌘Т - Очистить историю

🤖 Модели:
   ⌘D / ⌘В - Скачать модель
   ⌘L / ⌘Д - Загрузить модель

📱 Telegram:
   ⌘T / ⌘Е - Настроить бот

✍️ Ввод:
   Enter - Отправить сообщение
   Shift+Enter - Новая строка"""
        messagebox.showinfo("Горячие клавиши", text)

    def show_about(self):
        """О программе."""
        text = """🤖 NEYROLOCK v2.0

✨ Новое в версии 2.0:
• 🎨 Красочный темный интерфейс
• 🌍 Горячие клавиши на RU/EN раскладках
• 📱 Интеграция с Telegram-ботом
• 🔧 Улучшенные настройки шрифтов
• ⏱️ Таймстампы сообщений

👨‍💻 2025"""
        messagebox.showinfo("О программе", text)

    def run(self):
        """Запуск приложения."""
        self.root.mainloop()


def main():
    """Точка входа."""
    app = AIGUIv2()
    app.run()


if __name__ == "__main__":
    main()
