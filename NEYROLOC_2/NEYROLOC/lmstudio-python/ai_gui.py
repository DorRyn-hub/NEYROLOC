#!/usr/bin/env python
"""
🤖 AI GUI - Графический интерфейс для работы с AI моделями
С меню управления и удобным интерфейсом
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import threading
import json
import datetime
import sys
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


class AIGUI:
    """Графический интерфейс для AI CLI."""

    def __init__(self):
        """Инициализация GUI."""
        self.root = tk.Tk()
        self.root.title("🤖 AI Assistant - Локальные модели с HuggingFace")
        self.root.geometry("900x700")

        # Состояние
        self.model = None
        self.backend = None
        self.chat_history = []
        self.is_generating = False

        # Конфигурация
        self.config_dir = Path.home() / ".ai_gui"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Создание интерфейса
        self.create_menu()
        self.create_widgets()
        self.create_status_bar()

        # Приветственное сообщение
        self.append_to_chat("system", "👋 Добро пожаловать в AI Assistant!\n\n"
                           "Для начала работы:\n"
                           "1. Меню 'Модели' → 'Скачать модель с HuggingFace'\n"
                           "2. Или 'Модели' → 'Загрузить локальную модель'\n\n"
                           "После загрузки модели можно начинать диалог!")

    def create_menu(self):
        """Создание меню (кроссплатформенное)."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Получаем префикс для акселераторов (Cmd на macOS, Ctrl на Windows)
        prefix = get_accelerator_prefix()

        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 Файл", menu=file_menu)
        file_menu.add_command(label="💾 Сохранить диалог", command=self.save_dialog, accelerator=f"{prefix}+S")
        file_menu.add_command(label="📂 Загрузить диалог", command=self.load_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="🗑️ Очистить историю", command=self.clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Выход", command=self.quit_app, accelerator=f"{prefix}+Q")

        # Меню "Модели"
        models_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🤖 Модели", menu=models_menu)
        models_menu.add_command(label="📥 Скачать модель с HuggingFace...", command=self.download_model)
        models_menu.add_command(label="📂 Загрузить локальную модель...", command=self.load_local_model)
        models_menu.add_separator()
        models_menu.add_command(label="📋 Показать скачанные модели", command=self.show_downloaded_models)
        models_menu.add_command(label="🔍 Найти модель на HuggingFace", command=self.search_models)
        models_menu.add_separator()
        models_menu.add_command(label="ℹ️ Информация о текущей модели", command=self.show_model_info)
        models_menu.add_command(label="🔄 Выгрузить модель", command=self.unload_model)

        # Меню "Backend"
        backend_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="⚙️ Backend", menu=backend_menu)
        backend_menu.add_command(label="🖥️ Local GGUF (рекомендуется)", command=lambda: self.switch_backend("local"))
        backend_menu.add_command(label="🏠 LM Studio", command=lambda: self.switch_backend("lmstudio"))
        backend_menu.add_command(label="🦙 Ollama", command=lambda: self.switch_backend("ollama"))
        backend_menu.add_separator()
        backend_menu.add_command(label="⚡ Groq (облако, бесплатно)", command=lambda: self.switch_backend("groq"))
        backend_menu.add_command(label="🌐 OpenAI (облако, платно)", command=lambda: self.switch_backend("openai"))

        # Меню "Настройки"
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔧 Настройки", menu=settings_menu)
        settings_menu.add_command(label="🎨 Размер шрифта", command=self.change_font_size)
        settings_menu.add_command(label="📝 Системный промпт", command=self.set_system_prompt)
        settings_menu.add_command(label="🌡️ Температура генерации", command=self.set_temperature)

        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
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

        # Информационная панель сверху
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.model_label = ttk.Label(info_frame, text="Модель: Не загружена", font=("Helvetica", 12, "bold"))
        self.model_label.pack(side=tk.LEFT)

        self.backend_label = ttk.Label(info_frame, text="Backend: -", font=("Helvetica", 10))
        self.backend_label.pack(side=tk.RIGHT)

        # Область чата
        chat_frame = ttk.LabelFrame(main_frame, text="💬 Диалог", padding="5")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Helvetica", 13),
            state=tk.DISABLED,
            bg="#f5f5f5"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Настройка тегов для форматирования
        self.chat_display.tag_configure("user", foreground="#0066cc", font=("Helvetica", 13, "bold"))
        self.chat_display.tag_configure("assistant", foreground="#009933", font=("Helvetica", 13))
        self.chat_display.tag_configure("system", foreground="#666666", font=("Helvetica", 12, "italic"))

        # Область ввода
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)

        self.input_text = tk.Text(input_frame, height=3, font=("Helvetica", 13), wrap=tk.WORD)
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_text.bind("<Return>", self.on_enter_pressed)
        self.input_text.bind("<Shift-Return>", lambda e: None)  # Shift+Enter для новой строки

        # Кнопки справа
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(side=tk.RIGHT)

        self.send_button = ttk.Button(buttons_frame, text="📤 Отправить", command=self.send_message)
        self.send_button.pack(pady=(0, 5))

        self.stop_button = ttk.Button(buttons_frame, text="⏹️ Стоп", command=self.stop_generation, state=tk.DISABLED)
        self.stop_button.pack()

    def create_status_bar(self):
        """Создание статусной строки."""
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def append_to_chat(self, role: str, message: str):
        """Добавляет сообщение в чат."""
        self.chat_display.config(state=tk.NORMAL)

        if role == "user":
            prefix = "\n👤 Вы:\n"
            tag = "user"
        elif role == "assistant":
            prefix = "\n🤖 AI:\n"
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
        if not event.state & 0x1:  # Если не Shift
            self.send_message()
            return "break"  # Предотвращаем добавление новой строки

    def send_message(self):
        """Отправка сообщения."""
        if self.is_generating:
            return

        if not self.model:
            messagebox.showwarning("Модель не загружена",
                                   "Сначала загрузите модель!\n\n"
                                   "Меню 'Модели' → 'Скачать модель с HuggingFace'\n"
                                   "или 'Загрузить локальную модель'")
            return

        user_message = self.input_text.get("1.0", tk.END).strip()
        if not user_message:
            return

        # Очищаем поле ввода
        self.input_text.delete("1.0", tk.END)

        # Отображаем сообщение пользователя
        self.append_to_chat("user", user_message)

        # Добавляем в историю
        self.chat_history.append({"role": "user", "content": user_message})

        # Генерируем ответ в отдельном потоке
        self.is_generating = True
        self.send_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("🔄 Генерация ответа...")

        thread = threading.Thread(target=self.generate_response, args=(user_message,))
        thread.daemon = True
        thread.start()

    def generate_response(self, user_message: str):
        """Генерация ответа (в отдельном потоке)."""
        try:
            if self.backend == "local":
                # Локальная GGUF модель
                messages = self.chat_history.copy()

                response_text = ""

                # Начинаем отображение ответа
                self.root.after(0, lambda: self.append_to_chat("assistant", ""))

                stream = self.model.create_chat_completion(
                    messages=messages,
                    stream=True,
                    max_tokens=512,
                    temperature=0.7
                )

                for chunk in stream:
                    if not self.is_generating:
                        break

                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            content = delta['content']
                            response_text += content
                            # Обновляем последнее сообщение
                            self.root.after(0, lambda c=content: self.update_last_message(c))

                # Добавляем ответ в историю
                self.chat_history.append({"role": "assistant", "content": response_text})

            elif self.backend in ["ollama", "groq", "openai"]:
                # OpenAI-совместимые API
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

                self.chat_history.append({"role": "assistant", "content": response_text})

        except Exception as e:
            self.root.after(0, lambda: self.append_to_chat("system", f"❌ Ошибка: {e}"))

        finally:
            self.root.after(0, self.finish_generation)

    def update_last_message(self, text: str):
        """Обновляет последнее сообщение в чате (для потокового вывода)."""
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

    # ==================== Меню: Модели ====================

    def download_model(self):
        """Скачивание модели с HuggingFace."""
        try:
            from model_manager import ModelManager
        except ImportError:
            messagebox.showerror("Ошибка", "Не найден model_manager.py\n"
                                 "Убедитесь, что файл находится в той же папке.")
            return

        # Создаем окно выбора
        download_window = tk.Toplevel(self.root)
        download_window.title("📥 Скачать модель с HuggingFace")
        download_window.geometry("600x500")
        download_window.transient(self.root)
        download_window.grab_set()

        manager = ModelManager()

        # Заголовок
        ttk.Label(download_window, text="Выберите модель для скачивания:",
                  font=("Helvetica", 14, "bold")).pack(pady=10)

        # Категории
        categories_frame = ttk.LabelFrame(download_window, text="Категории моделей", padding="10")
        categories_frame.pack(fill=tk.X, padx=10, pady=5)

        category_var = tk.StringVar(value="small")

        categories = [
            ("tiny", "🐣 Крошечные (300-700MB) - для тестов"),
            ("small", "📦 Маленькие (2GB) - рекомендуется ⭐"),
            ("medium", "💪 Средние (4-5GB) - больше качества"),
            ("multimodal", "🎨 Мультимодальные (4GB) - текст + изображения")
        ]

        for value, text in categories:
            ttk.Radiobutton(categories_frame, text=text, variable=category_var, value=value).pack(anchor=tk.W)

        # Список моделей
        models_frame = ttk.LabelFrame(download_window, text="Доступные модели", padding="10")
        models_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        models_listbox = tk.Listbox(models_frame, font=("Helvetica", 11))
        models_listbox.pack(fill=tk.BOTH, expand=True)

        def update_models_list(*args):
            models_listbox.delete(0, tk.END)
            category = category_var.get()
            models = manager.RECOMMENDED_MODELS.get(category, [])
            for i, model in enumerate(models, 1):
                size = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']}MB"
                models_listbox.insert(tk.END, f"{i}. {model['filename']} ({size})")
            if models:
                models_listbox.select_set(0)

        category_var.trace('w', update_models_list)
        update_models_list()

        # Кнопки
        buttons_frame = ttk.Frame(download_window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)

        def start_download():
            selection = models_listbox.curselection()
            if not selection:
                messagebox.showwarning("Выберите модель", "Пожалуйста, выберите модель из списка")
                return

            category = category_var.get()
            model_idx = selection[0]
            model_info = manager.RECOMMENDED_MODELS[category][model_idx]

            size_gb = model_info['size_mb'] / 1000
            if not messagebox.askyesno("Подтверждение",
                                       f"Скачать модель:\n{model_info['filename']}\n\n"
                                       f"Размер: {size_gb:.1f} GB\n\n"
                                       f"Продолжить?"):
                return

            download_window.destroy()

            # Скачиваем в отдельном потоке
            self.update_status(f"📥 Скачивание {model_info['filename']}...")

            def download_thread():
                try:
                    path = manager.download_model(
                        repo_id=model_info['repo_id'],
                        filename=model_info['filename'],
                        description=model_info['description']
                    )

                    if path:
                        self.root.after(0, lambda: self.on_model_downloaded(str(path)))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось скачать модель"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка скачивания: {e}"))
                finally:
                    self.root.after(0, lambda: self.update_status("Готов"))

            thread = threading.Thread(target=download_thread)
            thread.daemon = True
            thread.start()

        ttk.Button(buttons_frame, text="📥 Скачать выбранную модель", command=start_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="❌ Отмена", command=download_window.destroy).pack(side=tk.RIGHT, padx=5)

    def on_model_downloaded(self, model_path: str):
        """Обработка после скачивания модели."""
        if messagebox.askyesno("Модель скачана",
                               f"Модель успешно скачана!\n\n"
                               f"Путь: {model_path}\n\n"
                               f"Загрузить модель сейчас?"):
            self.load_gguf_model(model_path)

    def load_local_model(self):
        """Загрузка локальной GGUF модели."""
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
            messagebox.showerror("Ошибка", "Не установлен llama-cpp-python!\n\n"
                                 "Выполните:\npip3 install llama-cpp-python")
            return

        # Спрашиваем параметры
        n_ctx = simpledialog.askinteger("Размер контекста",
                                        "Введите размер контекста (токенов):",
                                        initialvalue=2048, minvalue=512, maxvalue=8192)
        if not n_ctx:
            return

        n_gpu = simpledialog.askinteger("Слои на GPU",
                                        "Введите количество слоев на GPU\n(-1 = все на GPU, 0 = только CPU):",
                                        initialvalue=-1, minvalue=-1, maxvalue=100)
        if n_gpu is None:
            return

        self.update_status("⏳ Загрузка модели...")

        def load_thread():
            try:
                model = Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu,
                    verbose=False
                )

                self.model = model
                self.backend = "local"
                self.model_path = model_path
                model_name = Path(model_path).name

                self.root.after(0, lambda: self.on_model_loaded(model_name))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка загрузки",
                                                                f"Не удалось загрузить модель:\n{e}"))
            finally:
                self.root.after(0, lambda: self.update_status("Готов"))

        thread = threading.Thread(target=load_thread)
        thread.daemon = True
        thread.start()

    def on_model_loaded(self, model_name: str):
        """Обработка после загрузки модели."""
        self.model_label.config(text=f"Модель: {model_name}")
        self.backend_label.config(text=f"Backend: Local GGUF")
        self.append_to_chat("system", f"✅ Модель загружена: {model_name}\n\nМожете начинать диалог!")
        self.chat_history = []  # Сбрасываем историю
        messagebox.showinfo("Успех", f"Модель загружена!\n{model_name}")

    def show_downloaded_models(self):
        """Показывает скачанные модели."""
        try:
            from model_manager import ModelManager
            manager = ModelManager()
            models = manager.list_downloaded_models()

            if not models:
                messagebox.showinfo("Скачанные модели", "Нет скачанных моделей.\n\n"
                                    "Используйте меню 'Модели' → 'Скачать модель с HuggingFace'")
                return

            # Создаем окно
            window = tk.Toplevel(self.root)
            window.title("📋 Скачанные модели")
            window.geometry("700x400")
            window.transient(self.root)

            ttk.Label(window, text="Скачанные модели:", font=("Helvetica", 14, "bold")).pack(pady=10)

            # Список моделей
            listbox = tk.Listbox(window, font=("Helvetica", 11))
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            for i, model in enumerate(models, 1):
                size = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']:.0f}MB"
                listbox.insert(tk.END, f"{i}. {model['filename']} - {size}")

            # Кнопки
            buttons_frame = ttk.Frame(window)
            buttons_frame.pack(fill=tk.X, padx=10, pady=10)

            def load_selected():
                selection = listbox.curselection()
                if selection:
                    model_path = str(models[selection[0]]['path'])
                    window.destroy()
                    self.load_gguf_model(model_path)

            ttk.Button(buttons_frame, text="📂 Загрузить выбранную", command=load_selected).pack(side=tk.LEFT)
            ttk.Button(buttons_frame, text="❌ Закрыть", command=window.destroy).pack(side=tk.RIGHT)

        except ImportError:
            messagebox.showerror("Ошибка", "Не найден model_manager.py")

    def search_models(self):
        """Поиск моделей на HuggingFace."""
        query = simpledialog.askstring("Поиск моделей", "Введите запрос для поиска на HuggingFace:")
        if not query:
            return

        try:
            from model_manager import ModelManager
            manager = ModelManager()

            self.update_status(f"🔍 Поиск: {query}...")

            def search_thread():
                try:
                    # Получаем результаты
                    models = list(manager.api.list_models(
                        search=f"{query} GGUF",
                        limit=10,
                        sort="downloads",
                        direction=-1
                    ))

                    self.root.after(0, lambda: self.show_search_results(models))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Ошибка поиска", str(e)))
                finally:
                    self.root.after(0, lambda: self.update_status("Готов"))

            thread = threading.Thread(target=search_thread)
            thread.daemon = True
            thread.start()

        except ImportError:
            messagebox.showerror("Ошибка", "Не найден model_manager.py")

    def show_search_results(self, models):
        """Показывает результаты поиска."""
        if not models:
            messagebox.showinfo("Результаты поиска", "Модели не найдены")
            return

        window = tk.Toplevel(self.root)
        window.title("🔍 Результаты поиска")
        window.geometry("600x400")
        window.transient(self.root)

        ttk.Label(window, text="Найденные модели:", font=("Helvetica", 14, "bold")).pack(pady=10)

        listbox = tk.Listbox(window, font=("Helvetica", 11))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for model in models:
            downloads = f"{model.downloads:,}" if model.downloads else "N/A"
            listbox.insert(tk.END, f"{model.id} (Downloads: {downloads})")

        ttk.Label(window, text="Для скачивания используйте меню 'Модели' → 'Скачать с HuggingFace'",
                  font=("Helvetica", 10, "italic")).pack(pady=5)
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=10)

    def show_model_info(self):
        """Информация о модели."""
        if not self.model:
            messagebox.showinfo("Информация", "Модель не загружена")
            return

        info = f"Backend: {self.backend}\n"
        if hasattr(self, 'model_path'):
            path = Path(self.model_path)
            size_mb = path.stat().st_size / (1024 * 1024)
            info += f"Файл: {path.name}\n"
            info += f"Размер: {size_mb:.1f} MB\n"
            info += f"Путь: {path}\n"

        info += f"\nСообщений в истории: {len(self.chat_history)}"

        messagebox.showinfo("Информация о модели", info)

    def unload_model(self):
        """Выгрузка модели."""
        if self.model:
            self.model = None
            self.backend = None
            self.model_label.config(text="Модель: Не загружена")
            self.backend_label.config(text="Backend: -")
            self.append_to_chat("system", "🔄 Модель выгружена")
            messagebox.showinfo("Готово", "Модель выгружена из памяти")

    # ==================== Меню: Backend ====================

    def switch_backend(self, backend_type: str):
        """Переключение backend."""
        if backend_type == "local":
            self.show_downloaded_models()
        elif backend_type == "lmstudio":
            self.setup_lmstudio()
        elif backend_type == "ollama":
            self.setup_ollama()
        elif backend_type == "groq":
            self.setup_groq()
        elif backend_type == "openai":
            self.setup_openai()

    def setup_lmstudio(self):
        """Настройка LM Studio."""
        try:
            import lmstudio as lms

            self.update_status("Подключение к LM Studio...")
            client = lms.Client()
            loaded = client.llm.list_loaded()

            if not loaded:
                messagebox.showwarning("LM Studio", "Нет загруженных моделей в LM Studio.\n\n"
                                       "Откройте LM Studio и загрузите модель.")
                return

            self.client = client
            self.model = client.llm.get()
            self.backend = "lmstudio"
            self.model_name = loaded[0].identifier

            self.model_label.config(text=f"Модель: {self.model_name}")
            self.backend_label.config(text="Backend: LM Studio")
            self.append_to_chat("system", f"✅ Подключено к LM Studio: {self.model_name}")
            self.update_status("Готов")

        except ImportError:
            messagebox.showerror("Ошибка", "Не установлен lmstudio SDK!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к LM Studio:\n{e}")
            self.update_status("Готов")

    def setup_ollama(self):
        """Настройка Ollama."""
        try:
            from openai import OpenAI

            base_url = simpledialog.askstring("Ollama URL",
                                              "Введите Base URL Ollama:",
                                              initialvalue="http://localhost:11434/v1")
            if not base_url:
                return

            model_name = simpledialog.askstring("Модель",
                                                "Введите имя модели:",
                                                initialvalue="llama3.2:3b")
            if not model_name:
                return

            self.client = OpenAI(base_url=base_url, api_key="ollama")
            self.model = True
            self.model_name = model_name
            self.backend = "ollama"

            self.model_label.config(text=f"Модель: {model_name}")
            self.backend_label.config(text="Backend: Ollama")
            self.append_to_chat("system", f"✅ Подключено к Ollama: {model_name}")

        except ImportError:
            messagebox.showerror("Ошибка", "Установите openai: pip3 install openai")

    def setup_groq(self):
        """Настройка Groq."""
        try:
            from openai import OpenAI

            api_key = simpledialog.askstring("Groq API ключ",
                                             "Введите Groq API ключ:\n"
                                             "(получить на https://console.groq.com)",
                                             show="*")
            if not api_key:
                return

            model_name = simpledialog.askstring("Модель",
                                                "Выберите модель:",
                                                initialvalue="llama-3.3-70b-versatile")
            if not model_name:
                return

            self.client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
            self.model = True
            self.model_name = model_name
            self.backend = "groq"

            self.model_label.config(text=f"Модель: {model_name}")
            self.backend_label.config(text="Backend: Groq (облако)")
            self.append_to_chat("system", f"✅ Подключено к Groq: {model_name}")

        except ImportError:
            messagebox.showerror("Ошибка", "Установите openai: pip3 install openai")

    def setup_openai(self):
        """Настройка OpenAI."""
        try:
            from openai import OpenAI

            api_key = simpledialog.askstring("OpenAI API ключ",
                                             "Введите OpenAI API ключ:",
                                             show="*")
            if not api_key:
                return

            model_name = simpledialog.askstring("Модель",
                                                "Выберите модель:",
                                                initialvalue="gpt-4o-mini")
            if not model_name:
                return

            self.client = OpenAI(api_key=api_key)
            self.model = True
            self.model_name = model_name
            self.backend = "openai"

            self.model_label.config(text=f"Модель: {model_name}")
            self.backend_label.config(text="Backend: OpenAI (облако)")
            self.append_to_chat("system", f"✅ Подключено к OpenAI: {model_name}")

        except ImportError:
            messagebox.showerror("Ошибка", "Установите openai: pip3 install openai")

    # ==================== Меню: Файл ====================

    def save_dialog(self):
        """Сохранение диалога."""
        if not self.chat_history:
            messagebox.showinfo("Пусто", "Нет истории для сохранения")
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"chat_{timestamp}.json"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile=default_name,
            initialdir=str(self.config_dir)
        )

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": timestamp,
                    "backend": self.backend,
                    "messages": self.chat_history
                }, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("Сохранено", f"Диалог сохранен:\n{file_path}")

    def load_dialog(self):
        """Загрузка диалога."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            initialdir=str(self.config_dir)
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.chat_history = data.get('messages', [])

                # Отображаем загруженную историю
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.delete("1.0", tk.END)
                self.chat_display.config(state=tk.DISABLED)

                for msg in self.chat_history:
                    self.append_to_chat(msg['role'], msg['content'])

                messagebox.showinfo("Загружено", f"Диалог загружен:\n{file_path}")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить диалог:\n{e}")

    def clear_history(self):
        """Очистка истории."""
        if messagebox.askyesno("Подтверждение", "Очистить историю диалога?"):
            self.chat_history = []
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.append_to_chat("system", "🗑️ История очищена")

    def quit_app(self):
        """Выход из приложения."""
        if messagebox.askyesno("Выход", "Выйти из программы?"):
            self.root.quit()

    # ==================== Меню: Настройки ====================

    def change_font_size(self):
        """Изменение размера шрифта."""
        size = simpledialog.askinteger("Размер шрифта",
                                       "Введите размер шрифта:",
                                       initialvalue=13, minvalue=10, maxvalue=24)
        if size:
            self.chat_display.config(font=("Helvetica", size))
            self.input_text.config(font=("Helvetica", size))

    def set_system_prompt(self):
        """Установка системного промпта."""
        prompt = simpledialog.askstring("Системный промпт",
                                        "Введите системный промпт:",
                                        initialvalue="Ты полезный AI ассистент. Отвечай на русском языке.")
        if prompt:
            # Добавляем в начало истории
            if self.chat_history and self.chat_history[0].get('role') == 'system':
                self.chat_history[0]['content'] = prompt
            else:
                self.chat_history.insert(0, {"role": "system", "content": prompt})

            messagebox.showinfo("Готово", "Системный промпт установлен")

    def set_temperature(self):
        """Установка температуры."""
        temp = simpledialog.askfloat("Температура",
                                     "Введите температуру (0.0 - 2.0):\n"
                                     "0.0 = детерминированный\n"
                                     "0.7 = творческий (по умолчанию)\n"
                                     "2.0 = очень творческий",
                                     initialvalue=0.7, minvalue=0.0, maxvalue=2.0)
        if temp is not None:
            self.temperature = temp
            messagebox.showinfo("Готово", f"Температура: {temp}")

    # ==================== Меню: Помощь ====================

    def show_quick_start(self):
        """Быстрый старт."""
        prefix = get_accelerator_prefix()
        text = f"""🚀 БЫСТРЫЙ СТАРТ

1. Скачайте модель:
   Меню 'Модели' → 'Скачать модель с HuggingFace'
   Выберите категорию 'small' и модель 'Llama 3.2 3B'

2. Загрузите модель:
   После скачивания модель загрузится автоматически
   Или: Меню 'Модели' → 'Загрузить локальную модель'

3. Начните диалог:
   Напишите сообщение в поле ввода внизу
   Нажмите Enter или кнопку 'Отправить'

4. Управление:
   - Меню сверху для всех действий
   - Сохранение: {prefix}+S или Меню 'Файл' → 'Сохранить'
   - Очистка: Меню 'Файл' → 'Очистить историю'

💡 Рекомендация: начните с Llama 3.2 3B (2GB) - отличный баланс!"""

        messagebox.showinfo("Быстрый старт", text)

    def show_shortcuts(self):
        """Горячие клавиши."""
        prefix = get_accelerator_prefix()
        text = f"""⌨️ ГОРЯЧИЕ КЛАВИШИ

Enter - Отправить сообщение
Shift+Enter - Новая строка в поле ввода
{prefix}+S - Сохранить диалог
{prefix}+Q - Выход

📝 Меню доступно сверху окна"""

        messagebox.showinfo("Горячие клавиши", text)

    def show_about(self):
        """О программе."""
        text = """🤖 AI Assistant GUI v2.0

Графический интерфейс для работы с AI моделями

✨ Возможности:
• Скачивание моделей с HuggingFace
• Локальные GGUF модели
• LM Studio, Ollama, Groq, OpenAI
• Сохранение диалогов
• Настройка параметров

🔧 Технологии:
• Python + Tkinter
• llama-cpp-python
• huggingface-hub
• Rich

📁 Папка конфигурации: ~/.ai_gui/

👨‍💻 2025"""

        messagebox.showinfo("О программе", text)

    def run(self):
        """Запуск приложения."""
        # Горячие клавиши (кроссплатформенные)
        mod = get_modifier_key()
        self.root.bind(f"<{mod}-s>", lambda e: self.save_dialog())
        self.root.bind(f"<{mod}-q>", lambda e: self.quit_app())

        # Control-варианты для совместимости
        self.root.bind("<Control-s>", lambda e: self.save_dialog())
        self.root.bind("<Control-q>", lambda e: self.quit_app())

        self.root.mainloop()


def main():
    """Точка входа."""
    app = AIGUI()
    app.run()


if __name__ == "__main__":
    main()
