# 🧠 NEYROLOCK - Полная Документация Проекта

## 📋 Содержание
1. [Обзор проекта](#обзор-проекта)
2. [Архитектура](#архитектура)
3. [Зависимости и библиотеки](#зависимости-и-библиотеки)
4. [Структура файлов](#структура-файлов)
5. [Основные компоненты](#основные-компоненты)
6. [API и интерфейсы](#api-и-интерфейсы)
7. [Установка и настройка](#установка-и-настройка)
8. [Использование](#использование)

---

## 🎯 Обзор проекта

**NEYROLOCK** - это мультиплатформенное приложение для работы с локальными AI моделями через современный графический интерфейс и Telegram бота.

### Ключевые возможности:
- 🖥️ **Desktop GUI** - современный темный интерфейс с дашбордом
- 📱 **Telegram Bot** - полноценный бот с синхронизацией
- 🔄 **Синхронизация** - обмен сообщениями между GUI и Telegram
- 📥 **HuggingFace интеграция** - поиск и скачивание моделей
- 💾 **Персистентность** - сохранение истории, настроек, токенов
- 🎨 **Markdown рендеринг** - красивое отображение кода
- 🌐 **Русская раскладка** - горячие клавиши на русском

### Технологии:
- **Python 3.12+**
- **Tkinter** - GUI фреймворк
- **llama-cpp-python** - локальные GGUF модели
- **python-telegram-bot** - Telegram бот
- **HuggingFace Hub** - скачивание моделей

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    NEYROLOCK v3.0                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────┐         ┌──────────────┐           │
│  │  GUI Desktop  │ ◄────► │ SyncManager  │ ◄────►    │
│  │  (ai_gui_v3)  │         │  (JSON files)│           │
│  └───────────────┘         └──────────────┘           │
│         │                         │                     │
│         │                         ▼                     │
│         │                  ┌──────────────┐            │
│         │                  │ Telegram Bot │            │
│         │                  │(telegram_bot)│            │
│         │                  └──────────────┘            │
│         ▼                                               │
│  ┌───────────────────────────────────────────┐        │
│  │         ModelManager                       │        │
│  │  - HuggingFace Hub API                    │        │
│  │  - Local GGUF models                      │        │
│  │  - llama-cpp-python integration           │        │
│  └───────────────────────────────────────────┘        │
│         │                                               │
│         ▼                                               │
│  ┌───────────────────────────────────────────┐        │
│  │      Persistent Storage (~/.neyrolock)    │        │
│  │  - config.json                            │        │
│  │  - chat_history.json                      │        │
│  │  - telegram_config.json                   │        │
│  │  - sync/ (messages, status, stream)       │        │
│  └───────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### Потоки данных:

1. **Пользователь → GUI**
   - Ввод текста → `send_message()`
   - Добавление в `chat_history`
   - Отправка в `SyncManager`
   - Генерация через `llama-cpp-python`
   - Рендеринг markdown

2. **Пользователь → Telegram**
   - Сообщение в бот → `handle_message()`
   - Генерация с стримингом (обновление каждые 3 символа)
   - Отправка в `SyncManager`
   - Обновление GUI через мониторинг

3. **GUI ↔ Telegram Sync**
   - GUI пишет в `sync/messages.json`
   - Telegram мониторит файл каждые 500мс
   - Обратная связь через те же файлы

---

## 📦 Зависимости и библиотеки

### Core Dependencies (`requirements_universal.txt`)

```python
# GUI Framework
tkinter                    # Встроен в Python - кроссплатформенный GUI

# AI Models
llama-cpp-python>=0.2.0   # Локальные GGUF модели, Metal/CUDA поддержка
                          # Используется для: load моделей, генерации текста

# HuggingFace Integration
huggingface-hub>=0.20.0   # Скачивание моделей с HuggingFace
                          # API: HfApi(), hf_hub_download()

# Telegram Bot
python-telegram-bot>=20.0 # Асинхронный Telegram бот
                          # Components: Application, Update, Handlers

# Image Processing (для иконки)
Pillow>=10.0.0           # Создание PNG иконок для .app bundle
```

### Development Dependencies

```python
# Code Quality
mypy                     # Статическая типизация
pylint                   # Линтер
black                    # Форматирование кода

# Testing
pytest                   # Unit тесты
pytest-asyncio          # Тесты для async кода
```

### System Requirements

- **Python**: 3.12+ (рекомендуется 3.12.9)
- **macOS**: 11.0+ (Big Sur) для .app bundle
- **Memory**: минимум 8GB RAM (рекомендуется 16GB для больших моделей)
- **Storage**: 5-50GB для моделей

---

## 📁 Структура файлов

```
lmstudio-python/
│
├── 📄 ai_gui_v3.py              # ГЛАВНЫЙ ФАЙЛ - Desktop GUI v3.0
├── 📄 telegram_bot.py           # Telegram бот
├── 📄 sync_manager.py           # Синхронизация GUI-Telegram
├── 📄 model_manager.py          # Управление моделями HuggingFace
│
├── 🚀 run_neyrolock.sh         # Запуск GUI
├── 🔧 create_app.sh            # Создание macOS .app
│
├── 📋 requirements_universal.txt
├── 📋 requirements_cli.txt
├── 📋 requirements_local.txt
│
├── 📱 NEYROLOCK.app/           # macOS приложение
│   ├── Contents/
│   │   ├── Info.plist
│   │   ├── MacOS/launcher
│   │   └── Resources/AppIcon.icns
│
├── 🎨 ai_gui_v2.py             # Предыдущая версия GUI
├── 🎨 ai_gui.py                # Оригинальная версия
│
├── 📝 ai_cli.py                # CLI версия
├── 📝 lmstudio_cli.py          # LM Studio CLI
├── 📝 universal_cli.py         # Универсальный CLI
│
└── 📚 Документация/
    ├── START_HERE.txt
    ├── PROJECT_OVERVIEW.md
    ├── QUICKSTART.md
    └── PROJECT_DOCUMENTATION.md (этот файл)
```

### Ключевые директории

```bash
~/.neyrolock/                    # Папка данных приложения
├── config.json                  # Настройки (температура, шрифт, цвет)
├── chat_history.json            # История чата
├── telegram_config.json         # Токен бота
├── app.log                      # Логи приложения
└── sync/                        # Синхронизация
    ├── messages.json            # Обмен сообщениями
    ├── status.json              # Статус компонентов
    └── stream.json              # Стриминг данные

~/.neyrolock_models/             # Скачанные модели
└── user-{username}/
    ├── Llama-3.2-3B-Q4_K_M.gguf
    └── ... другие .gguf файлы
```

---

## 🎯 Основные компоненты

### 1. ai_gui_v3.py - Desktop GUI (1800+ строк)

**Класс: `NeyrolockDashboard`**

#### Инициализация (`__init__`)

```python
def __init__(self):
    # === СОЗДАНИЕ ГЛАВНОГО ОКНА ===
    self.root = tk.Tk()                    # Tkinter root window
    self.root.title("NEYROLOCK - AI Dashboard")
    self.root.geometry("1400x900")         # Размер окна
    self.root.minsize(1200, 800)          # Минимальный размер

    # === ПАПКИ И ФАЙЛЫ ===
    self.data_dir = Path.home() / ".neyrolock"
    self.config_file = self.data_dir / "config.json"
    self.history_file = self.data_dir / "chat_history.json"

    # === СОСТОЯНИЕ МОДЕЛИ ===
    self.model = None                      # llama-cpp Llama объект
    self.backend = None                    # "local" или None
    self.chat_history = []                 # История: [{"role": "user", "content": "..."}]
    self.is_generating = False            # Флаг генерации
    self.temperature = 0.7                # Температура модели
    self.messages_count = 0               # Счетчик сообщений
    self.tokens_used = 0                  # Счетчик токенов
    self.last_model_path = ""             # Путь к последней модели

    # === ЦВЕТОВАЯ СХЕМА ===
    self.colors = {
        "bg_dark": "#0d0d1a",            # Темный фон
        "bg_card": "#1a1a2e",            # Карточки
        "sidebar": "#12121f",            # Боковая панель
        "accent_pink": "#ff6b9d",        # Розовый акцент
        "accent_purple": "#c084fc",      # Фиолетовый
        "accent_green": "#4ade80",       # Зеленый
        "accent_yellow": "#fbbf24",      # Желтый
        "accent_cyan": "#22d3ee",        # Голубой
        "text_primary": "#ffffff",       # Основной текст
        "text_secondary": "#9ca3af",     # Вторичный
        "text_muted": "#6b7280",         # Приглушенный
        "border": "#2d2d44",             # Границы
        "success": "#10b981",            # Успех
        "warning": "#f59e0b",            # Предупреждение
        "error": "#ef4444"               # Ошибка
    }

    self.cyber_font = "Menlo"             # Моноширинный шрифт
    self.current_font_size = 13

    # === СОЗДАНИЕ ИНТЕРФЕЙСА ===
    self.create_sidebar()                 # Боковая панель
    self.create_main_area()               # Основная область
    self.setup_hotkeys()                  # Горячие клавиши

    # === ЗАГРУЗКА ДАННЫХ ===
    self.load_config()                    # Загружаем настройки
    self.load_chat_history()              # Загружаем историю

    # === СИНХРОНИЗАЦИЯ ===
    self.setup_sync()                     # Запускаем sync_manager

    # === ОБРАБОТКА ЗАКРЫТИЯ ===
    self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
```

#### Боковая панель (`create_sidebar`)

```python
def create_sidebar(self):
    """
    Создание левой боковой панели (280px width).

    Секции:
    1. Логотип и версия
    2. Статус модели (🟢/⚫ + имя модели)
    3. Действия:
       - 📥 Скачать модель (download_model)
       - 📂 Загрузить модель (load_local_model)
       - 📋 Мои модели (show_downloaded_models)
       - 🔍 Поиск HuggingFace (search_models)
    4. Telegram:
       - 📱 Настроить бот (show_telegram_setup)
       - 🚀 Запустить бот (start_telegram_bot)
    5. Настройки:
       - 🎨 Размер шрифта (change_font_size)
       - 🌈 Цвет шрифта (change_font_color)
       - 🌡️ Температура (set_temperature)
       - 📝 Системный промпт (set_system_prompt)
    6. Нижние кнопки:
       - 🧪 Тест markdown (test_markdown)
       - 🗑️ Очистить чат (clear_history)
       - 💾 Сохранить (save_dialog)

    Каждая кнопка создается через create_sidebar_button()
    с эффектами hover (подсветка при наведении)
    """
    sidebar = tk.Frame(
        self.root,
        bg=self.colors["sidebar"],
        width=280
    )
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    sidebar.pack_propagate(False)  # Фиксированная ширина

    # Логотип "🧠 NEYROLOCK"
    logo_label = tk.Label(
        sidebar,
        text="🧠 NEYROLOCK",
        font=(self.cyber_font, 20, "bold"),
        bg=self.colors["sidebar"],
        fg=self.colors["accent_purple"]
    )
    logo_label.pack(pady=20)

    # Статус модели
    self.model_status = tk.Label(
        sidebar,
        text="⚫ Не загружена",
        bg=self.colors["sidebar"],
        fg=self.colors["error"]
    )
    self.model_status.pack()

    # ... кнопки создаются через create_sidebar_button()
```

#### Основная область (`create_main_area`)

```python
def create_main_area(self):
    """
    Основная область справа от sidebar.

    Структура:
    ┌─────────────────────────────────────────┐
    │  📊 Статистические карточки (top)       │
    │  [Модель] [Сообщений] [Температура]     │
    ├─────────────────────────────────────────┤
    │  ┌───────────────┐  ┌───────────────┐  │
    │  │ 💬 Чат с AI   │  │ 📊 Активность │  │
    │  │               │  │ ⌨️  Горячие кл │  │
    │  │  ScrolledText │  │ 📱 Синхрониз  │  │
    │  │               │  │               │  │
    │  │               │  │               │  │
    │  ├───────────────┤  └───────────────┘  │
    │  │ [Поле ввода]  │                     │
    │  └───────────────┘                     │
    └─────────────────────────────────────────┘

    Компоненты:
    1. Stats Panel - 4 карточки с метриками
    2. Chat Display - ScrolledText с markdown
    3. Input Field - Text widget (3 строки)
    4. Send Button - ➤ кнопка
    5. Right Column - инфо панели
    """

    # === ПАНЕЛЬ СТАТИСТИКИ ===
    stats_frame = tk.Frame(main, bg=self.colors["bg_dark"])
    stats_frame.pack(fill=tk.X, padx=20, pady=20)

    # Карточки: Модель, Сообщений, Температура, Статус
    self.stat_labels = {}  # Сохраняем ссылки для обновления

    # === ЧАТ ОБЛАСТЬ ===
    self.chat_display = scrolledtext.ScrolledText(
        chat_frame,
        wrap=tk.WORD,                           # Перенос по словам
        font=(self.cyber_font, self.current_font_size),
        state=tk.DISABLED,                      # Read-only
        bg=self.colors["bg_card"],
        fg=self.colors["text_primary"],
        insertbackground=self.colors["accent_pink"],
        selectbackground=self.colors["accent_purple"],
        bd=0,
        padx=15,
        pady=15
    )

    # Настройка тегов для форматирования
    self.setup_chat_tags()

    # Обработчик двойного клика для копирования кода
    self.chat_display.bind("<Double-Button-1>", self.copy_code_block)

    # === ПОЛЕ ВВОДА ===
    self.input_text = tk.Text(
        input_frame,
        height=3,
        font=(self.cyber_font, self.current_font_size),
        bg=self.colors["bg_dark"],
        fg=self.colors["text_primary"]
    )
    self.input_text.bind("<Return>", self.on_enter_pressed)
    # Enter = отправка, Shift+Enter = новая строка
```

#### Теги форматирования (`setup_chat_tags`)

```python
def setup_chat_tags(self):
    """
    Настройка текстовых тегов для форматирования сообщений.

    Теги применяются через chat_display.insert(tk.END, text, tag_name)
    """

    # Пользователь - голубой, жирный
    self.chat_display.tag_configure(
        "user",
        foreground=self.colors["accent_cyan"],
        font=(self.cyber_font, self.current_font_size, "bold")
    )

    # AI ассистент - зеленый
    self.chat_display.tag_configure(
        "assistant",
        foreground=self.colors["accent_green"],
        font=(self.cyber_font, self.current_font_size)
    )

    # Системные сообщения - серый, курсив
    self.chat_display.tag_configure(
        "system",
        foreground=self.colors["text_muted"],
        font=(self.cyber_font, self.current_font_size - 1, "italic")
    )

    # Inline код - желтый с фоном
    self.chat_display.tag_configure(
        "code_inline",
        foreground=self.colors["accent_yellow"],
        background="#2d2d44"
    )

    # Блоки кода - заголовок (серый)
    self.chat_display.tag_configure(
        "code_header",
        foreground="#888888",
        font=(self.cyber_font, self.current_font_size - 1)
    )

    # Блоки кода - содержимое (желтый на темном)
    self.chat_display.tag_configure(
        "code_block",
        foreground=self.colors["accent_yellow"],
        background="#1a1a1a",
        font=(self.cyber_font, self.current_font_size)
    )

    # Bold текст
    self.chat_display.tag_configure(
        "bold",
        foreground=self.colors["text_primary"],
        font=(self.cyber_font, self.current_font_size, "bold")
    )

    # Italic текст
    self.chat_display.tag_configure(
        "italic",
        foreground=self.colors["text_primary"],
        font=(self.cyber_font, self.current_font_size, "italic")
    )

    # Заголовки - розовый, крупнее
    self.chat_display.tag_configure(
        "header",
        foreground=self.colors["accent_pink"],
        font=(self.cyber_font, self.current_font_size + 2, "bold")
    )
```

#### Добавление сообщений (`add_message`)

```python
def add_message(self, role, text, update_stats=True):
    """
    Добавление сообщения в чат.

    Args:
        role (str): "user", "assistant", или "system"
        text (str): Текст сообщения
        update_stats (bool): Обновлять ли счетчики

    Процесс:
    1. Включить редактирование (NORMAL state)
    2. Вставить заголовок с timestamp и emoji
    3. Для assistant - рендерить markdown
    4. Для остальных - простой текст
    5. Прокрутить к концу
    6. Выключить редактирование (DISABLED)
    7. Обновить статистику если нужно
    """
    self.chat_display.config(state=tk.NORMAL)

    timestamp = datetime.datetime.now().strftime("%H:%M")

    # Выбор префикса и тега
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

    # Рендеринг markdown для AI ответов
    if role == "assistant" and text:
        self.render_markdown(text)
    else:
        self.chat_display.insert(tk.END, text + "\n", tag)

    self.chat_display.see(tk.END)
    self.chat_display.config(state=tk.DISABLED)

    # Обновление счетчиков
    if update_stats and role in ["user", "assistant"] and text:
        self.messages_count += 1
        self.stat_labels["Сообщений"].config(text=str(self.messages_count))
```

#### Markdown рендеринг (`render_markdown`)

```python
def render_markdown(self, text):
    """
    Парсинг и рендеринг markdown текста.

    Поддерживаемые элементы:
    - ```code blocks``` - блоки кода с языком
    - **bold** - жирный текст
    - *italic* - курсив
    - `inline code` - инлайн код
    - # Headers - заголовки (1-3 уровня)

    Алгоритм:
    1. Разбить текст на части: блоки кода и обычный текст
    2. Для блоков кода - create_code_block()
    3. Для обычного текста - render_inline_markdown()
    """
    import re

    # Паттерн для блоков кода: ```язык\nкод\n```
    parts = re.split(r'(```[\s\S]*?```)', text)

    for part in parts:
        if part.startswith('```') and part.endswith('```'):
            # Это блок кода
            code_content = part[3:-3]

            # Извлекаем язык из первой строки
            lines = code_content.split('\n', 1)
            if len(lines) > 1 and lines[0].strip() and not ' ' in lines[0].strip():
                language = lines[0].strip()  # python, bash, etc
                code = lines[1]
            else:
                language = ""
                code = code_content

            # Создаем блок с кнопкой копирования
            self.create_code_block(code.strip(), language)
        else:
            # Обычный текст - парсим inline markdown
            self.render_inline_markdown(part)
```

#### Блоки кода (`create_code_block`)

```python
def create_code_block(self, code, language=""):
    """
    Создание блока кода (оптимизированная версия).

    ВАЖНО: Не создаем Frame/Text виджеты (медленно!)
    Используем только текстовые теги.

    Формат:
    ┌─ python ─────────────────── [📋 Ctrl+Click для копирования]
    │ def hello():
    │     print("Hello")
    └────────────────────────────────────────────────────────────

    Копирование: двойной клик на блоке → copy_code_block()
    """
    # Сохраняем код для копирования
    code_id = f"code_{len(self.chat_display.get('1.0', tk.END))}"
    if not hasattr(self, 'code_blocks'):
        self.code_blocks = {}
    self.code_blocks[code_id] = code

    # Заголовок с языком
    header = f"\n┌─ {language if language else 'code'} ─────────────────── [📋 Ctrl+Click]\n"
    self.chat_display.insert(tk.END, header, "code_header")

    # Строки кода с вертикальной чертой
    for line in code.split('\n'):
        self.chat_display.insert(tk.END, f"│ {line}\n", "code_block")

    # Закрывающая линия
    self.chat_display.insert(tk.END, "└" + "─" * 60 + "\n", "code_header")
```

#### Копирование кода (`copy_code_block`)

```python
def copy_code_block(self, event):
    """
    Копирование блока кода при двойном клике.

    Алгоритм:
    1. Получить позицию клика
    2. Проверить теги (code_block или code_header)
    3. Найти начало блока (строка с ┌)
    4. Найти конец блока (строка с └)
    5. Собрать строки между ними (убрать "│ ")
    6. Скопировать в clipboard
    7. Показать уведомление
    """
    try:
        # Позиция клика
        index = self.chat_display.index(f"@{event.x},{event.y}")
        tags = self.chat_display.tag_names(index)

        if "code_block" in tags or "code_header" in tags:
            current_line = int(index.split('.')[0])

            # Ищем начало (┌)
            start_line = current_line
            for i in range(current_line, max(0, current_line - 50), -1):
                line_text = self.chat_display.get(f"{i}.0", f"{i}.end")
                if line_text.startswith("┌"):
                    start_line = i
                    break

            # Ищем конец (└)
            end_line = current_line
            total_lines = int(self.chat_display.index('end').split('.')[0])
            for i in range(current_line, min(total_lines, current_line + 100)):
                line_text = self.chat_display.get(f"{i}.0", f"{i}.end")
                if line_text.startswith("└"):
                    end_line = i
                    break

            # Собираем код
            code_lines = []
            for i in range(start_line + 1, end_line):
                line = self.chat_display.get(f"{i}.0", f"{i}.end")
                if line.startswith("│ "):
                    code_lines.append(line[2:])

            code = '\n'.join(code_lines)

            # Копируем
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.add_system_message("✅ Код скопирован!")

    except Exception as e:
        print(f"Copy error: {e}")
```

#### Горячие клавиши (`setup_hotkeys`)

```python
def setup_hotkeys(self):
    """
    Настройка глобальных горячих клавиш.

    Английские:
    - Cmd/Ctrl+S → save_dialog()
    - Cmd/Ctrl+N → clear_history()
    - Cmd/Ctrl+D → download_model()
    - Cmd/Ctrl+L → load_local_model()

    Русские (обрабатываются в handle_any_key):
    - Cmd/Ctrl+Ы → save_dialog()
    - Cmd/Ctrl+Т → clear_history()
    - Cmd/Ctrl+В → download_model()
    - Cmd/Ctrl+Д → load_local_model()
    - Cmd/Ctrl+С → Copy
    - Cmd/Ctrl+М → Paste
    """
    # Английские клавиши
    self.root.bind("<Command-s>", lambda e: self.save_dialog())
    self.root.bind("<Command-n>", lambda e: self.clear_history())
    self.root.bind("<Command-d>", lambda e: self.download_model())
    self.root.bind("<Command-l>", lambda e: self.load_local_model())

    # Control для Windows/Linux
    self.root.bind("<Control-s>", lambda e: self.save_dialog())
    self.root.bind("<Control-n>", lambda e: self.clear_history())

    # Универсальный обработчик для русской раскладки
    self.root.bind("<KeyPress>", self.handle_any_key)

def handle_any_key(self, event):
    """
    Обработка русской раскладки.

    Маппинг:
    Русская → Английская
    Ы → S (save)
    Т → N (new/clear)
    В → D (download)
    Д → L (load)
    С → C (copy)
    М → V (paste)
    """
    is_command = bool(event.state & 0x8)  # Cmd на Mac
    is_control = bool(event.state & 0x4)  # Ctrl

    if not (is_command or is_control):
        return

    # Действия
    ru_actions = {
        'ы': self.save_dialog,
        'т': self.clear_history,
        'в': self.download_model,
        'д': self.load_local_model
    }

    # Буфер обмена
    ru_clipboard = {
        'с': 'copy',
        'м': 'paste',
        'ч': 'cut',
        'я': 'undo'
    }

    char = event.char.lower() if event.char else ''

    if char in ru_actions:
        ru_actions[char]()
        return "break"
    elif char in ru_clipboard:
        focused = self.root.focus_get()
        if focused:
            action = ru_clipboard[char]
            if action == 'copy':
                focused.event_generate("<<Copy>>")
            elif action == 'paste':
                focused.event_generate("<<Paste>>")
            return "break"
```

#### Отправка сообщения (`send_message`)

```python
def send_message(self):
    """
    Обработка отправки сообщения пользователя.

    Процесс:
    1. Проверить что модель загружена
    2. Получить текст из input_text
    3. Добавить в чат и историю
    4. Отправить в SyncManager (для Telegram)
    5. Запустить генерацию в отдельном потоке
    """
    if self.is_generating:
        return  # Уже генерируем

    if not self.model:
        messagebox.showwarning(
            "Модель не загружена",
            "Сначала загрузите модель через боковую панель!"
        )
        return

    # Получаем текст
    user_text = self.input_text.get("1.0", tk.END).strip()
    if not user_text:
        return

    # Очищаем поле ввода
    self.input_text.delete("1.0", tk.END)

    # Добавляем в чат
    self.add_message("user", user_text)

    # Добавляем в историю (для контекста)
    self.chat_history.append({
        "role": "user",
        "content": user_text
    })

    # Отправляем в sync для Telegram
    if self.sync_manager:
        self.sync_manager.send_message("gui", "user", user_text)

    # Меняем статус
    self.is_generating = True
    self.stat_labels["Статус"].config(
        text="Генерация...",
        fg=self.colors["warning"]
    )

    # Запускаем генерацию в фоне
    thread = threading.Thread(
        target=self.generate_response,
        args=(user_text,)
    )
    thread.daemon = True
    thread.start()
```

#### Генерация ответа (`generate_response`)

```python
def generate_response(self, user_message):
    """
    Генерация ответа от модели (в отдельном потоке).

    Алгоритм:
    1. Добавить placeholder в чат
    2. Запустить стриминг через llama-cpp-python
    3. Обновлять текст по мере генерации
    4. После завершения - рендерить markdown
    5. Сохранить в историю и sync

    Используется root.after() для обновления GUI из потока
    """
    try:
        if self.backend == "local":
            messages = self.chat_history.copy()
            response_text = ""

            # Placeholder "🤖 печатает..."
            self.root.after(0, lambda: self.add_streaming_placeholder())

            # Стриминг генерация
            stream = self.model.create_chat_completion(
                messages=messages,
                stream=True,
                max_tokens=512,
                temperature=self.temperature
            )

            # Обрабатываем chunks
            for chunk in stream:
                if not self.is_generating:
                    break  # Остановлено пользователем

                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content = delta['content']
                        response_text += content
                        self.tokens_used += len(content.split())

                        # Обновляем GUI (thread-safe через after)
                        self.root.after(0, lambda c=content:
                            self.update_streaming_text(c))

            # Финализация - рендерим markdown
            self.root.after(0, lambda:
                self.finalize_streamed_message(response_text))

            # Сохраняем в историю
            self.chat_history.append({
                "role": "assistant",
                "content": response_text
            })

            # Отправляем в sync
            if self.sync_manager:
                self.sync_manager.send_message(
                    "gui", "assistant", response_text
                )

    except Exception as e:
        self.root.after(0, lambda:
            self.add_system_message(f"❌ Ошибка: {e}"))
    finally:
        self.root.after(0, self.finish_generation)
```

#### Загрузка модели (`load_gguf_model`)

```python
def load_gguf_model(self, path):
    """
    Загрузка .gguf модели через llama-cpp-python.

    Args:
        path (str): Полный путь к .gguf файлу

    Процесс:
    1. Импорт Llama (с обработкой ошибок архитектуры)
    2. Показать "Загрузка..." в статусе
    3. Загрузить в отдельном потоке (не блокировать GUI)
    4. При успехе - вызвать on_model_loaded()
    5. При ошибке - показать messagebox

    Параметры Llama:
    - model_path: путь к файлу
    - n_ctx: 2048 (размер контекста)
    - n_gpu_layers: -1 (все слои на GPU если доступен)
    - verbose: False (без логов)
    """
    try:
        from llama_cpp import Llama
    except ImportError:
        messagebox.showerror(
            "Ошибка",
            "Установите: pip3 install llama-cpp-python"
        )
        return
    except RuntimeError as e:
        if "incompatible architecture" in str(e):
            messagebox.showerror(
                "Ошибка архитектуры",
                "llama-cpp-python установлен для другой архитектуры.\n\n"
                "Переустановите:\n"
                "pip3 uninstall llama-cpp-python\n"
                "pip3 install llama-cpp-python --force-reinstall"
            )
        return

    self.add_system_message(f"⏳ Загрузка модели...")
    self.stat_labels["Статус"].config(
        text="Загрузка...",
        fg=self.colors["warning"]
    )

    def load():
        try:
            # Загружаем модель
            model = Llama(
                model_path=path,
                n_ctx=2048,
                n_gpu_layers=-1,  # Metal на Mac, CUDA на Windows/Linux
                verbose=False
            )

            self.model = model
            self.backend = "local"
            self.model_path = path
            name = Path(path).name

            # Обновляем GUI из главного потока
            self.root.after(0, lambda: self.on_model_loaded(name))

        except Exception as e:
            self.root.after(0, lambda:
                messagebox.showerror("Ошибка", str(e)))
            self.root.after(0, lambda:
                self.stat_labels["Статус"].config(
                    text="Ошибка",
                    fg=self.colors["error"]
                ))

    # Запускаем в фоне
    threading.Thread(target=load, daemon=True).start()
```

#### Скачивание модели (`download_model`)

```python
def download_model(self):
    """
    Окно выбора и скачивания модели с HuggingFace.

    UI:
    1. Radiobuttons для категорий (tiny, small, medium)
    2. Listbox с моделями выбранной категории
    3. Кнопка "Скачать"

    При клике на "Скачать":
    - Закрыть окно
    - Показать "⏳ Скачивание..."
    - Запустить download в отдельном потоке
    - После завершения - предложить загрузить
    """
    try:
        from model_manager import ModelManager
        self.model_manager = ModelManager()
    except ImportError:
        messagebox.showerror(
            "Ошибка",
            "Установите: pip3 install huggingface-hub"
        )
        return

    # Создаем окно
    win = tk.Toplevel(self.root)
    win.title("📥 Скачать модель")
    win.geometry("600x500")
    win.configure(bg=self.colors["bg_dark"])
    win.transient(self.root)

    # Категории
    cat_var = tk.StringVar(value="small")
    categories = [
        ("tiny", "🐣 Tiny (300-700MB)"),
        ("small", "⭐ Small (2GB)"),
        ("medium", "💪 Medium (4-5GB)")
    ]

    for cat, name in categories:
        tk.Radiobutton(
            win,
            text=name,
            variable=cat_var,
            value=cat,
            bg=self.colors["bg_dark"],
            fg=self.colors["text_primary"]
        ).pack(anchor=tk.W, padx=20)

    # Listbox с моделями
    listbox = tk.Listbox(
        win,
        font=(self.cyber_font, 11),
        bg=self.colors["bg_card"],
        fg=self.colors["text_primary"],
        height=8
    )
    listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Обновление списка при смене категории
    def update_list(*args):
        listbox.delete(0, tk.END)
        for m in self.model_manager.RECOMMENDED_MODELS.get(cat_var.get(), []):
            size = f"{m['size_mb']/1000:.1f}GB" if m['size_mb'] >= 1000 else f"{m['size_mb']}MB"
            listbox.insert(tk.END, f"{m['filename'][:40]} ({size})")

    cat_var.trace_add('write', update_list)
    update_list()

    # Функция скачивания
    def download():
        sel = listbox.curselection()
        if not sel:
            return

        info = self.model_manager.RECOMMENDED_MODELS[cat_var.get()][sel[0]]
        win.destroy()

        self.add_system_message(f"⏳ Скачивание {info['filename']}...")

        def dl():
            try:
                path = self.model_manager.download_model(
                    info['repo_id'],
                    info['filename'],
                    info['description']
                )
                if path:
                    self.root.after(0, lambda:
                        self.add_system_message(f"✅ Скачано: {info['filename']}"))

                    if messagebox.askyesno("Загрузить?", "Загрузить модель сейчас?"):
                        self.root.after(0, lambda: self.load_gguf_model(path))
            except Exception as e:
                self.root.after(0, lambda:
                    messagebox.showerror("Ошибка", str(e)))

        threading.Thread(target=dl, daemon=True).start()

    tk.Button(
        win,
        text="📥 Скачать",
        command=download,
        font=(self.cyber_font, 12, "bold"),
        bg=self.colors["accent_pink"],
        fg=self.colors["text_primary"]
    ).pack(pady=10)
```

#### HuggingFace поиск (`search_models`)

```python
def search_models(self):
    """
    Полнофункциональное окно поиска моделей на HuggingFace.

    UI (1000x700):
    ┌─────────────────────────────────────────────┐
    │ 🔍 Результаты поиска: query        ✅ Найдено: N │
    ├──────────────────┬──────────────────────────┤
    │ 📦 Найденные     │ ℹ️  Информация о модели   │
    │    модели        │                          │
    │                  │ ID: user/model           │
    │ [Listbox]        │ Скачиваний: 1000         │
    │                  │ Лайков: 50               │
    │                  │ Обновлено: 2024-11-17    │
    │                  │                          │
    │                  │ 📁 GGUF файлы:           │
    │                  │ [Listbox с .gguf]        │
    │                  │                          │
    │                  │ [📥 Скачать файл]        │
    └──────────────────┴──────────────────────────┘

    Процесс:
    1. Запрос к HfApi.list_models(search=query + " gguf")
    2. Отображение списка моделей
    3. При клике - загрузка деталей и файлов
    4. При скачивании - использование ModelManager
    """
    query = simpledialog.askstring(
        "Поиск",
        "Введите запрос для поиска GGUF моделей:"
    )
    if not query:
        return

    try:
        from huggingface_hub import HfApi
        api = HfApi()
    except ImportError:
        messagebox.showerror(
            "Ошибка",
            "Установите: pip3 install huggingface-hub"
        )
        return

    # Создаем окно
    search_win = tk.Toplevel(self.root)
    search_win.title(f"🔍 HuggingFace - Поиск: {query}")
    search_win.geometry("1000x700")
    search_win.configure(bg=self.colors["bg_dark"])

    # Левая панель - результаты
    results_listbox = tk.Listbox(...)

    # Правая панель - детали
    details_text = scrolledtext.ScrolledText(...)
    files_listbox = tk.Listbox(...)  # GGUF файлы

    # Хранилище данных
    data_store = {
        'results': [],
        'files': [],
        'current_model_idx': -1
    }

    # Обработчик выбора модели
    def update_details(event=None):
        sel = results_listbox.curselection()
        if not sel:
            return

        model = data_store['results'][sel[0]]
        data_store['current_model_idx'] = sel[0]

        # Показываем информацию
        info = f"""
        ID: {model.id}
        Скачиваний: {model.downloads:,}
        Лайков: {model.likes}
        Обновлено: {model.lastModified[:10]}
        """
        details_text.delete("1.0", tk.END)
        details_text.insert("1.0", info)

        # Загружаем GGUF файлы
        files_listbox.delete(0, tk.END)
        files_listbox.insert(tk.END, "⏳ Загрузка...")

        def load_files():
            from huggingface_hub import list_repo_files
            all_files = list_repo_files(model.id)
            gguf_files = [f for f in all_files if f.endswith('.gguf')]

            def update_files():
                files_listbox.delete(0, tk.END)
                for f in gguf_files:
                    files_listbox.insert(tk.END, f)
                    data_store['files'].append(f)

            search_win.after(0, update_files)

        threading.Thread(target=load_files, daemon=True).start()

    results_listbox.bind('<<ListboxSelect>>', update_details)

    # Кнопка скачивания
    def download_selected():
        if data_store['current_model_idx'] < 0:
            messagebox.showwarning("Ошибка", "Выберите модель!")
            return

        file_sel = files_listbox.curselection()
        if not file_sel:
            messagebox.showwarning("Ошибка", "Выберите файл!")
            return

        model = data_store['results'][data_store['current_model_idx']]
        filename = data_store['files'][file_sel[0]]

        # Скачиваем через ModelManager
        search_win.destroy()
        self.add_system_message(f"⏳ Скачивание {filename}...")

        def dl():
            mm = ModelManager()
            path = mm.download_model(model.id, filename, "Из поиска")
            if path:
                self.root.after(0, lambda:
                    self.add_system_message(f"✅ Скачано!"))
                if messagebox.askyesno("Загрузить?", "Загрузить сейчас?"):
                    self.root.after(0, lambda: self.load_gguf_model(path))

        threading.Thread(target=dl, daemon=True).start()

    download_btn.bind("<Button-1>", lambda e: download_selected())

    # Поиск в фоне
    def do_search():
        results = list(api.list_models(
            search=query + " gguf",
            sort="downloads",
            direction=-1,
            limit=50
        ))

        def update_results():
            data_store['results'] = results
            for model in results:
                results_listbox.insert(tk.END,
                    f"{model.id} ({model.downloads:,} скач.)")

            # Автовыбор первой модели
            if results:
                results_listbox.selection_set(0)
                search_win.after(100, update_details)

        search_win.after(0, update_results)

    threading.Thread(target=do_search, daemon=True).start()
```

#### Персистентность данных

```python
def save_config(self):
    """
    Сохранение настроек в ~/.neyrolock/config.json

    Сохраняемые данные:
    - temperature: 0.0-2.0
    - font_size: 10-20
    - font_color: HEX
    - last_model_path: полный путь
    - messages_count: счетчик
    - tokens_used: счетчик
    """
    config = {
        "temperature": self.temperature,
        "font_size": self.current_font_size,
        "font_color": self.colors["accent_green"],
        "last_model_path": self.last_model_path,
        "messages_count": self.messages_count,
        "tokens_used": self.tokens_used
    }
    with open(self.config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_config(self):
    """Загрузка настроек при старте"""
    if not self.config_file.exists():
        return

    with open(self.config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    self.temperature = config.get("temperature", 0.7)
    self.current_font_size = config.get("font_size", 13)
    self.colors["accent_green"] = config.get("font_color", "#4ade80")
    self.last_model_path = config.get("last_model_path", "")

    # Применяем настройки к виджетам
    self.chat_display.config(font=(self.cyber_font, self.current_font_size))
    self.input_text.config(font=(self.cyber_font, self.current_font_size))
    self.setup_chat_tags()

    # Предлагаем загрузить последнюю модель
    if self.last_model_path and Path(self.last_model_path).exists():
        self.root.after(1000, self.ask_load_last_model)

def save_chat_history(self):
    """Сохранение истории в ~/.neyrolock/chat_history.json"""
    with open(self.history_file, 'w', encoding='utf-8') as f:
        json.dump({
            "history": self.chat_history,
            "timestamp": datetime.datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

def load_chat_history(self):
    """
    Загрузка истории (оптимизированная).

    ВАЖНО: Показываем только последние 20 сообщений
    для скорости старта. Полная история хранится
    в self.chat_history для контекста модели.
    """
    if not self.history_file.exists():
        return

    with open(self.history_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    self.chat_history = data.get("history", [])

    # Показываем только последние 20
    recent = self.chat_history[-20:] if len(self.chat_history) > 20 else self.chat_history

    self.chat_display.config(state=tk.NORMAL)
    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ["user", "assistant"]:
            prefix = f"\n[...] {'👤 Вы' if role == 'user' else '🤖 AI'}\n"
            self.chat_display.insert(tk.END, prefix, role)
            self.chat_display.insert(tk.END, content + "\n", role)
    self.chat_display.see(tk.END)
    self.chat_display.config(state=tk.DISABLED)

    if len(self.chat_history) > 20:
        self.add_system_message(
            f"📜 Показаны последние 20 из {len(self.chat_history)} сообщений"
        )

def on_closing(self):
    """Обработка закрытия приложения"""
    # Сохраняем все данные
    self.save_config()
    self.save_chat_history()

    # Останавливаем синхронизацию
    if self.sync_manager:
        self.sync_manager.update_status("gui_active", False)
        self.sync_manager.stop_monitoring()

    self.root.destroy()
```

#### Синхронизация (`setup_sync`)

```python
def setup_sync(self):
    """
    Настройка синхронизации с Telegram ботом.

    Использует SyncManager для обмена через JSON файлы:
    - ~/.neyrolock/sync/messages.json
    - ~/.neyrolock/sync/status.json
    - ~/.neyrolock/sync/stream.json

    Мониторинг: проверка новых сообщений каждые 500мс
    """
    self.sync_manager = None
    try:
        from sync_manager import SyncManager
        self.sync_manager = SyncManager()
        self.sync_manager.update_status("gui_active", True)

        # Запускаем мониторинг
        self.sync_manager.start_monitoring(
            on_message=self.on_telegram_message,
            on_stream=self.on_telegram_stream
        )

        self.sync_status.config(
            text="🟢 Активна",
            fg=self.colors["success"]
        )
        self.add_system_message("📱 Синхронизация включена")
    except Exception as e:
        print(f"Sync error: {e}")
        self.sync_status.config(
            text="⚫ Не активна",
            fg=self.colors["text_muted"]
        )

def on_telegram_message(self, msg):
    """
    Callback при получении сообщения из Telegram.

    Args:
        msg (dict): {
            "id": int,
            "source": "telegram",
            "role": "user" или "assistant",
            "content": str,
            "chat_id": int,
            "timestamp": float
        }
    """
    if msg.get("source") == "telegram":
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "user":
            # Сообщение от пользователя в TG
            self.root.after(0, lambda:
                self.add_message("user", f"[TG] {content}"))
            self.root.after(0, lambda:
                self.chat_history.append({
                    "role": "user",
                    "content": content
                }))
        elif role == "assistant":
            # Ответ AI из TG
            self.root.after(0, lambda:
                self.add_message("assistant", content))
            self.root.after(0, lambda:
                self.chat_history.append({
                    "role": "assistant",
                    "content": content
                }))
```

---

### 2. telegram_bot.py - Telegram Bot (600+ строк)

**Класс: `AITelegramBot`**

```python
class AITelegramBot:
    """
    Полнофункциональный Telegram бот для NEYROLOCK.

    Возможности:
    - Скачивание моделей из HuggingFace
    - Загрузка локальных .gguf моделей
    - Диалог с AI (стриминг каждые 3 символа)
    - Синхронизация с GUI через SyncManager
    - История для каждого пользователя отдельно
    - Клавиатура с кнопками команд
    """

    def __init__(self, token: str):
        self.token = token
        self.model = None
        self.model_name = None
        self.user_histories: Dict[int, list] = {}

        # ModelManager для HuggingFace
        self.model_manager = ModelManager()

        # Папка конфигурации
        self.config_dir = Path.home() / ".neyrolock"
        self.config_dir.mkdir(exist_ok=True)

        # Сохраняем токен
        self.save_token(token)

        # Синхронизация
        try:
            from sync_manager import SyncManager
            self.sync_manager = SyncManager()
            self.sync_manager.update_status("telegram_active", True)
            print("📱 Синхронизация активирована")
        except:
            self.sync_manager = None
```

#### Команды бота

```python
async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - приветствие и инструкции
    """
    welcome_text = """
🤖 *NEYROLOCK Bot*

Добро пожаловать! Этот бот позволяет общаться с AI моделями прямо в Telegram!

*Возможности:*
• 📥 Скачивание моделей с HuggingFace
• 💬 Общение с локальными AI моделями
• 📋 Управление коллекцией моделей
• 🗑️ Очистка истории диалога

*Начало работы:*
1. Нажмите "📥 Скачать модель"
2. Выберите категорию и модель
3. Дождитесь скачивания
4. Начинайте диалог!
    """
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=self.get_main_keyboard()
    )

async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /status - информация о загруженной модели
    """
    if not self.model:
        await update.message.reply_text("⚠️ Модель не загружена")
    else:
        status = f"""
📊 *Статус*

🤖 Модель: {self.model_name}
💬 Сообщений в истории: {len(self.user_histories.get(update.effective_user.id, []))}
        """
        await update.message.reply_text(status, parse_mode="Markdown")
```

#### Диалог с AI

```python
async def chat_with_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
    """
    Генерация ответа со стримингом.

    Особенности:
    - Обновление сообщения каждые 3 символа
    - Курсор "▌" в конце при печати
    - Синхронизация через SyncManager
    - История для каждого пользователя

    Процесс:
    1. Добавить сообщение в историю пользователя
    2. Отправить в sync (для GUI)
    3. Начать стриминг через model.create_chat_completion()
    4. Обновлять Telegram сообщение каждые 3 символа
    5. Финальное обновление без курсора
    6. Отправить результат в sync
    """
    if not self.model:
        await update.message.reply_text("⚠️ Модель не загружена!")
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Инициализируем историю
    if user_id not in self.user_histories:
        self.user_histories[user_id] = []

    # Добавляем сообщение
    self.user_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Синхронизация
    if self.sync_manager:
        self.sync_manager.send_message("telegram", "user", user_message, chat_id)
        self.sync_manager.start_stream("telegram", chat_id)

    # Начальное сообщение с курсором
    bot_message = await update.message.reply_text(
        "🤖 *AI:*\n\n▌",
        parse_mode="Markdown"
    )

    response_text = ""
    chars_since_update = 0
    last_update_len = 0

    def generate_stream():
        """Генерация в отдельном потоке"""
        nonlocal response_text, chars_since_update
        try:
            stream = self.model.create_chat_completion(
                messages=self.user_histories[user_id],
                max_tokens=512,
                temperature=0.7,
                stream=True
            )

            for chunk in stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    delta = chunk['choices'][0].get('delta', {})
                    if 'content' in delta:
                        content = delta['content']
                        response_text += content
                        chars_since_update += len(content)

                        # Синхронизация
                        if self.sync_manager:
                            self.sync_manager.update_stream(content)

            return True
        except Exception as e:
            response_text = f"❌ Ошибка: {e}"
            return False

    # Запускаем генерацию
    loop = asyncio.get_event_loop()
    generate_task = loop.run_in_executor(None, generate_stream)

    # Обновляем сообщение каждые 3 символа
    update_interval = 0.3  # секунд

    while not generate_task.done():
        await asyncio.sleep(update_interval)

        # Обновляем если добавилось >= 3 символов
        if len(response_text) - last_update_len >= 3:
            try:
                display_text = response_text + "▌"  # Курсор
                await bot_message.edit_text(
                    f"🤖 *AI:*\n\n{display_text}",
                    parse_mode="Markdown"
                )
                last_update_len = len(response_text)
            except Exception:
                pass  # Rate limit - пропускаем

    # Ждем завершения
    await generate_task

    # Финальное обновление без курсора
    try:
        await bot_message.edit_text(
            f"🤖 *AI:*\n\n{response_text}",
            parse_mode="Markdown"
        )
    except:
        pass

    # Завершаем стрим
    if self.sync_manager:
        self.sync_manager.end_stream()
        self.sync_manager.send_message("telegram", "assistant", response_text, chat_id)

    # Сохраняем в историю
    self.user_histories[user_id].append({
        "role": "assistant",
        "content": response_text
    })
```

#### Скачивание моделей

```python
async def download_model_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Интерактивный процесс скачивания модели.

    Шаги:
    1. Показать категории (Inline Keyboard)
    2. После выбора - показать модели категории
    3. После выбора модели - начать скачивание
    4. Показывать прогресс
    5. После скачивания - автозагрузка
    """
    # Клавиатура с категориями
    keyboard = [
        [InlineKeyboardButton("🐣 Tiny (300-700MB)", callback_data="cat_tiny")],
        [InlineKeyboardButton("📦 Small (2GB) ⭐", callback_data="cat_small")],
        [InlineKeyboardButton("💪 Medium (4-5GB)", callback_data="cat_medium")]
    ]

    await update.message.reply_text(
        "📥 Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка нажатий Inline кнопок.

    Типы callback_data:
    - cat_{category} - выбор категории
    - model_{category}_{index} - выбор модели
    - cancel - отмена
    - back_to_cats - назад к категориям
    """
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("cat_"):
        # Показываем модели категории
        category = data[4:]  # "tiny", "small", "medium"
        models = self.model_manager.RECOMMENDED_MODELS.get(category, [])

        keyboard = []
        for i, model in enumerate(models):
            size = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']}MB"
            text = f"{model['filename'][:30]} ({size})"
            keyboard.append([
                InlineKeyboardButton(
                    text,
                    callback_data=f"model_{category}_{i}"
                )
            ])

        await query.edit_message_text(
            f"📥 Выберите модель ({category}):",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("model_"):
        # Скачиваем модель
        parts = data.split("_")
        category = parts[1]
        index = int(parts[2])

        model_info = self.model_manager.RECOMMENDED_MODELS[category][index]

        await query.edit_message_text(
            f"⏳ Скачивание {model_info['filename']}...\n\nЭто может занять несколько минут."
        )

        # Скачиваем в отдельном потоке
        loop = asyncio.get_event_loop()

        def download():
            return self.model_manager.download_model(
                model_info['repo_id'],
                model_info['filename'],
                model_info['description']
            )

        try:
            path = await loop.run_in_executor(None, download)

            if path:
                await query.edit_message_text(
                    f"✅ Модель скачана!\n\n📂 {model_info['filename']}\n\nЗагружаем..."
                )

                # Автозагрузка
                await self.load_model(path)

                await query.edit_message_text(
                    f"✅ Готово!\n\n🤖 {model_info['filename']} загружена и готова к использованию.\n\nОтправьте мне сообщение для начала диалога!"
                )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка скачивания:\n{e}"
            )
```

---

### 3. sync_manager.py - Синхронизация (220 строк)

**Класс: `SyncManager`**

```python
class SyncManager:
    """
    Менеджер синхронизации между GUI и Telegram ботом.

    Использует JSON файлы для обмена:
    - ~/.neyrolock/sync/messages.json - сообщения
    - ~/.neyrolock/sync/status.json - статусы компонентов
    - ~/.neyrolock/sync/stream.json - стриминг данные

    Потокобезопасность: использует файловые блокировки
    """

    def __init__(self):
        self.sync_dir = Path.home() / ".neyrolock" / "sync"
        self.sync_dir.mkdir(parents=True, exist_ok=True)

        self.messages_file = self.sync_dir / "messages.json"
        self.status_file = self.sync_dir / "status.json"
        self.stream_file = self.sync_dir / "stream.json"

        # Инициализируем файлы
        self._init_files()

        # Callbacks
        self.on_message_callback = None
        self.on_stream_callback = None

        # Поток мониторинга
        self.monitoring = False
        self.monitor_thread = None
        self.last_message_id = 0

    def _init_files(self):
        """Создание файлов если не существуют"""
        if not self.messages_file.exists():
            self._write_json(self.messages_file, {
                "messages": [],
                "last_id": 0
            })

        if not self.status_file.exists():
            self._write_json(self.status_file, {
                "gui_active": False,
                "telegram_active": False,
                "model_loaded": False,
                "model_name": ""
            })

        if not self.stream_file.exists():
            self._write_json(self.stream_file, {
                "is_streaming": False,
                "content": "",
                "source": "",
                "chat_id": 0
            })

    def send_message(self, source: str, role: str, content: str, chat_id: int = 0):
        """
        Отправить сообщение в синхронизированный чат.

        Args:
            source: "gui" или "telegram"
            role: "user" или "assistant"
            content: текст сообщения
            chat_id: ID чата в Telegram (0 для GUI)

        Returns:
            int: ID сообщения
        """
        data = self._read_json(self.messages_file)
        messages = data.get("messages", [])
        last_id = data.get("last_id", 0) + 1

        message = {
            "id": last_id,
            "source": source,
            "role": role,
            "content": content,
            "chat_id": chat_id,
            "timestamp": time.time()
        }

        messages.append(message)

        # Храним последние 100 сообщений
        if len(messages) > 100:
            messages = messages[-100:]

        self._write_json(self.messages_file, {
            "messages": messages,
            "last_id": last_id
        })

        return last_id

    def get_new_messages(self, since_id: int = 0) -> list:
        """Получить новые сообщения с указанного ID"""
        data = self._read_json(self.messages_file)
        messages = data.get("messages", [])
        return [m for m in messages if m.get("id", 0) > since_id]

    def start_monitoring(self, on_message=None, on_stream=None):
        """
        Начать мониторинг новых сообщений.

        Args:
            on_message: callback(message_dict)
            on_stream: callback(stream_dict)
        """
        self.on_message_callback = on_message
        self.on_stream_callback = on_stream
        self.monitoring = True

        # Получаем текущий last_id
        data = self._read_json(self.messages_file)
        self.last_message_id = data.get("last_id", 0)

        # Запускаем поток
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _monitor_loop(self):
        """
        Цикл мониторинга (оптимизированный).

        Проверяет:
        - Сообщения каждые 500мс (каждый 5-й цикл)
        - Стрим каждые 300мс (каждый 3-й цикл)

        Базовый интервал: 100мс
        """
        last_stream_chars = 0
        check_counter = 0

        while self.monitoring:
            try:
                check_counter += 1

                # Проверяем сообщения каждые 500мс
                if check_counter % 5 == 0:
                    new_messages = self.get_new_messages(self.last_message_id)
                    for msg in new_messages:
                        self.last_message_id = msg["id"]
                        if self.on_message_callback:
                            self.on_message_callback(msg)

                # Проверяем стрим каждые 300мс
                if check_counter % 3 == 0:
                    stream_data = self.get_stream_content()
                    if stream_data.get("is_streaming"):
                        current_chars = stream_data.get("chars_count", 0)
                        if current_chars > last_stream_chars:
                            last_stream_chars = current_chars
                            if self.on_stream_callback:
                                self.on_stream_callback(stream_data)
                    else:
                        last_stream_chars = 0

                time.sleep(0.1)

            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)
```

---

### 4. model_manager.py - Управление моделями (250 строк)

**Класс: `ModelManager`**

```python
class ModelManager:
    """
    Менеджер для скачивания и управления GGUF моделями.

    Возможности:
    - Скачивание с HuggingFace Hub
    - Отслеживание прогресса
    - Кэш скачанных моделей
    - Рекомендуемые модели по категориям
    """

    def __init__(self):
        # Папка для моделей
        self.models_dir = Path.home() / ".neyrolock_models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Рекомендуемые модели
        self.RECOMMENDED_MODELS = {
            "tiny": [
                {
                    "repo_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
                    "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
                    "size_mb": 352,
                    "description": "Быстрая крошечная модель"
                },
                # ... еще модели
            ],
            "small": [
                {
                    "repo_id": "bartowski/Llama-3.2-3B-Instruct-GGUF",
                    "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
                    "size_mb": 2048,
                    "description": "Llama 3.2 3B - отличный баланс"
                },
                # ... еще модели
            ],
            "medium": [
                {
                    "repo_id": "bartowski/Llama-3.1-8B-Instruct-GGUF",
                    "filename": "Llama-3.1-8B-Instruct-Q4_K_M.gguf",
                    "size_mb": 4920,
                    "description": "Llama 3.1 8B - мощная модель"
                },
                # ... еще модели
            ]
        }

    def download_model(self, repo_id: str, filename: str, description: str = "") -> Optional[Path]:
        """
        Скачивание модели с HuggingFace Hub.

        Args:
            repo_id: ID репозитория (user/model)
            filename: Имя файла (.gguf)
            description: Описание для логов

        Returns:
            Path: Путь к скачанному файлу

        Процесс:
        1. Создать папку для пользователя
        2. Проверить существует ли уже
        3. Скачать через hf_hub_download()
        4. Показать прогресс
        5. Вернуть путь
        """
        from huggingface_hub import hf_hub_download

        try:
            print(f"📥 Скачивание {filename}...")
            print(f"   Репозиторий: {repo_id}")

            # Папка для пользователя
            user = repo_id.split("/")[0]
            user_dir = self.models_dir / f"user-{user}"
            user_dir.mkdir(exist_ok=True)

            # Проверяем существует ли
            local_path = user_dir / filename
            if local_path.exists():
                print(f"✅ Модель уже скачана: {local_path}")
                return local_path

            # Скачиваем
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=user_dir,
                local_dir_use_symlinks=False,
                resume_download=True  # Продолжить если прервалось
            )

            print(f"✅ Скачано: {downloaded_path}")
            return Path(downloaded_path)

        except Exception as e:
            print(f"❌ Ошибка скачивания: {e}")
            return None

    def list_downloaded_models(self) -> List[Path]:
        """Список всех скачанных .gguf файлов"""
        return list(self.models_dir.glob("**/*.gguf"))
```

---

### 5. create_app.sh - Создание macOS .app (300 строк)

```bash
#!/bin/bash
# Создание macOS .app приложения для NEYROLOCK

APP_NAME="NEYROLOCK"
APP_DIR="$APP_NAME.app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Удаляем старое
rm -rf "$SCRIPT_DIR/$APP_DIR"

# Создаем структуру
mkdir -p "$SCRIPT_DIR/$APP_DIR/Contents/MacOS"
mkdir -p "$SCRIPT_DIR/$APP_DIR/Contents/Resources"

# Info.plist
cat > "$SCRIPT_DIR/$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>NEYROLOCK</string>
    <key>CFBundleDisplayName</key>
    <string>NEYROLOCK</string>
    <key>CFBundleIdentifier</key>
    <string>com.neyrolock.app</string>
    <key>CFBundleVersion</key>
    <string>3.0</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
</dict>
</plist>
EOF

# Launcher скрипт
cat > "$SCRIPT_DIR/$APP_DIR/Contents/MacOS/launcher" << EOF
#!/bin/bash
SCRIPT_DIR="$HOME/PycharmProjects/NEYROLOCK/lmstudio-python"
VENV_DIR="$HOME/PycharmProjects/NEYROLOCK/.venv"
LOG_FILE="\$HOME/.neyrolock/app.log"

mkdir -p "\$HOME/.neyrolock"
echo "========================================" >> "\$LOG_FILE"
echo "\$(date): Starting NEYROLOCK..." >> "\$LOG_FILE"

cd "\$SCRIPT_DIR"

PYTHON="\$VENV_DIR/bin/python3"

if [ ! -x "\$PYTHON" ]; then
    PYTHON="/opt/homebrew/bin/python3"
fi

export TK_SILENCE_DEPRECATION=1
export PATH="\$VENV_DIR/bin:/opt/homebrew/bin:\$PATH"

# Принудительно ARM64
arch -arm64 "\$PYTHON" "\$SCRIPT_DIR/ai_gui_v3.py" >> "\$LOG_FILE" 2>&1

exit \$?
EOF

chmod +x "$SCRIPT_DIR/$APP_DIR/Contents/MacOS/launcher"

# Создаем иконку через Python + Pillow
python3 << 'PYTHON_EOF'
from PIL import Image, ImageDraw
from pathlib import Path
import os

script_dir = Path(__file__).parent if '__file__' in dir() else Path.cwd()
iconset_dir = script_dir / "AppIcon.iconset"
iconset_dir.mkdir(exist_ok=True)

# Создаем иконки всех размеров
for size in [16, 32, 64, 128, 256, 512, 1024]:
    img = Image.new('RGBA', (size, size), (102, 126, 234, 255))
    draw = ImageDraw.Draw(img)

    center = size // 2
    r = size // 3

    # Мозг (два полукруга)
    draw.ellipse([center-r-r//2, center-r, center-r//4, center+r],
                 fill=(255, 107, 157, 255))
    draw.ellipse([center+r//4, center-r, center+r+r//2, center+r],
                 fill=(192, 132, 252, 255))

    # Центральная линия
    draw.rectangle([center-size//20, center-r//2, center+size//20, center+r//2],
                   fill=(255, 255, 255, 200))

    img.save(iconset_dir / f"icon_{size}x{size}.png")

    # @2x версии
    if size <= 512:
        double = size * 2
        if double <= 1024:
            img2 = Image.new('RGBA', (double, double), (102, 126, 234, 255))
            draw2 = ImageDraw.Draw(img2)
            center2 = double // 2
            r2 = double // 3
            draw2.ellipse([center2-r2-r2//2, center2-r2, center2-r2//4, center2+r2],
                         fill=(255, 107, 157, 255))
            draw2.ellipse([center2+r2//4, center2-r2, center2+r2+r2//2, center2+r2],
                         fill=(192, 132, 252, 255))
            draw2.rectangle([center2-double//20, center2-r2//2, center2+double//20, center2+r2//2],
                           fill=(255, 255, 255, 200))
            img2.save(iconset_dir / f"icon_{size}x{size}@2x.png")

print("✅ Иконки созданы")
PYTHON_EOF

# Конвертируем в .icns
iconutil -c icns "$SCRIPT_DIR/AppIcon.iconset" -o "$SCRIPT_DIR/$APP_DIR/Contents/Resources/AppIcon.icns"

# Очищаем
rm -rf "$SCRIPT_DIR/AppIcon.iconset"

# Регистрируем
touch "$SCRIPT_DIR/$APP_DIR"

echo "✅ Приложение создано: $SCRIPT_DIR/$APP_DIR"
echo ""
echo "📌 Что дальше:"
echo "   1. Дважды кликните на NEYROLOCK.app"
echo "   2. Перетащите в /Applications"
echo "   3. Добавьте в Dock"
```

---

## 📖 Использование

### Установка

```bash
# 1. Клонировать репозиторий
cd $HOME/PycharmProjects/NEYROLOCK/lmstudio-python

# 2. Создать venv
python3 -m venv ../.venv
source ../.venv/bin/activate

# 3. Установить зависимости
pip3 install -r requirements_universal.txt

# 4. Создать .app
./create_app.sh
```

### Запуск

#### Desktop GUI
```bash
./run_neyrolock.sh
# или
python3 ai_gui_v3.py
# или
open NEYROLOCK.app
```

#### Telegram Bot
```bash
python3 telegram_bot.py --token YOUR_BOT_TOKEN
```

### Первый запуск

1. Откройте NEYROLOCK.app
2. Нажмите "📥 Скачать модель"
3. Выберите категорию "Small"
4. Выберите "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
5. Дождитесь скачивания (~2GB)
6. Модель загрузится автоматически
7. Отправьте первое сообщение!

---

## 🔧 Настройка

### Изменение температуры
```python
# В коде:
self.temperature = 0.7  # 0.0-2.0

# Или через GUI: "🌡️ Температура" в боковой панели
```

### Изменение размера контекста
```python
# В load_gguf_model():
model = Llama(
    model_path=path,
    n_ctx=4096,  # Увеличить для больших диалогов
    n_gpu_layers=-1
)
```

### Добавление новой модели
```python
# В model_manager.py:
self.RECOMMENDED_MODELS = {
    "small": [
        {
            "repo_id": "user/model-name",
            "filename": "model.gguf",
            "size_mb": 2000,
            "description": "Описание модели"
        }
    ]
}
```

---

## 🐛 Отладка

### Логи приложения
```bash
tail -f ~/.neyrolock/app.log
```

### Проверка синхронизации
```bash
cat ~/.neyrolock/sync/messages.json
cat ~/.neyrolock/sync/status.json
```

### Очистка данных
```bash
rm -rf ~/.neyrolock
rm -rf ~/.neyrolock_models
```

### Переустановка llama-cpp-python
```bash
pip3 uninstall llama-cpp-python
pip3 install llama-cpp-python --force-reinstall --no-cache-dir
```

---

## 📊 Производительность

### Оптимизации в v3.0

1. **Загрузка истории**: только последние 20 сообщений при старте
2. **Синхронизация**: проверка каждые 500мс вместо 100мс
3. **Markdown**: легкие текстовые теги вместо Frame виджетов
4. **Стриминг**: обновление каждые 3 символа в Telegram

### Скорость генерации

- **Tiny модели** (0.5B): ~50-100 токенов/сек
- **Small модели** (3B): ~20-40 токенов/сек
- **Medium модели** (8B): ~10-20 токенов/сек

*На Apple Silicon M1/M2 с Metal acceleration*

---

## 📝 Лицензия

Проект NEYROLOCK - собственная разработка.

---

## 👨‍💻 Автор

Создано Рындиным Дорианом
Каримовичем для проекта NEYROLOCK.

**Версия**: 3.0
**Дата**: 17 ноября 2025
**Строк кода**: ~13500+

---

*Конец документации*
