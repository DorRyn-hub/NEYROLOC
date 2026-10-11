# NEYROLOCK - Руководство для Windows 11

Полное руководство по установке и использованию NEYROLOCK на Windows 11.

## Системные требования

- **ОС:** Windows 10 (версия 1903+) или Windows 11
- **Python:** 3.10 или выше
- **RAM:** минимум 8 GB (рекомендуется 16 GB для больших моделей)
- **Диск:** минимум 10 GB свободного места
- **GPU (опционально):** NVIDIA с поддержкой CUDA для ускорения

## Установка

### Шаг 1: Установка Python

#### Вариант A: Через Microsoft Store (рекомендуется)
```cmd
winget install Python.Python.3.12
```

#### Вариант B: С официального сайта
1. Скачайте Python с [python.org/downloads](https://python.org/downloads/)
2. **ВАЖНО:** При установке отметьте галочку **"Add Python to PATH"**
3. Завершите установку

#### Проверка установки
```cmd
python --version
```
Должно показать `Python 3.10.x` или выше.

### Шаг 2: Установка зависимостей

#### Автоматическая установка (рекомендуется)
Дважды кликните на файл `setup_and_run.bat` - он установит все зависимости и запустит приложение.

#### Ручная установка
```cmd
pip install rich huggingface-hub llama-cpp-python
pip install python-telegram-bot openai
```

### Шаг 3: Установка Visual Studio Build Tools (для llama-cpp-python)

Если `llama-cpp-python` не устанавливается:

1. Скачайте [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Установите компонент **"C++ Build Tools"**
3. Перезапустите терминал и повторите установку:
   ```cmd
   pip install llama-cpp-python
   ```

### Шаг 4 (опционально): GPU ускорение с CUDA

Для NVIDIA видеокарт:

1. Установите [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
2. Установите llama-cpp-python с CUDA:
   ```cmd
   set CMAKE_ARGS=-DLLAMA_CUDA=on
   pip install llama-cpp-python --force-reinstall --no-cache-dir
   ```

## Запуск

### GUI приложения

| Файл | Описание |
|------|----------|
| `run_neyrolock.bat` | NEYROLOCK v3.0 Dashboard (рекомендуется) |
| `run_gui_v2.bat` | NEYROLOCK v2.0 с Telegram |
| `run_gui.bat` | Базовая версия GUI |

Или через командную строку:
```cmd
python ai_gui_v3.py
```

### CLI приложения

| Файл | Описание |
|------|----------|
| `run_ai_cli.bat` | AI CLI интерфейс |
| `setup_cli.bat` | Установка и запуск LM Studio CLI |

## Горячие клавиши

### Основные сочетания

| Действие | Windows | Русская раскладка |
|----------|---------|-------------------|
| Сохранить диалог | `Ctrl+S` | `Ctrl+Ы` |
| Очистить историю | `Ctrl+N` | `Ctrl+Т` |
| Скачать модель | `Ctrl+D` | `Ctrl+В` |
| Загрузить модель | `Ctrl+L` | `Ctrl+Д` |
| Выход | `Ctrl+Q` или `Alt+F4` | `Ctrl+Й` |
| Telegram настройки | `Ctrl+T` | `Ctrl+Е` |

### Стандартные Windows-комбинации

| Действие | Сочетание |
|----------|-----------|
| Копировать | `Ctrl+C` |
| Вставить | `Ctrl+V` |
| Вырезать | `Ctrl+X` |
| Отменить | `Ctrl+Z` |

## Сборка установщика

### Требования
- PyInstaller: `pip install pyinstaller`
- Inno Setup 6: [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)

### Сборка

```cmd
build_installer.bat
```

Или вручную:
```cmd
cd installers\windows
build_windows.bat
```

Установщик появится в: `installers\output\NEYROLOCK-3.0.0-Windows-Setup.exe`

## Решение проблем

### Python не найден

**Симптом:** `'python' is not recognized as an internal or external command`

**Решение:**
1. Переустановите Python с отмеченной галочкой "Add Python to PATH"
2. Или добавьте вручную:
   - Нажмите Win+X → Система → Дополнительные параметры системы
   - Переменные среды → Path → Добавить путь к Python

### llama-cpp-python не устанавливается

**Симптом:** Ошибка компиляции при `pip install llama-cpp-python`

**Решение:**
1. Установите Visual Studio Build Tools
2. Выберите компонент "C++ Build Tools"
3. Перезапустите терминал и повторите

### Нет GPU ускорения

**Симптом:** Генерация медленная даже с NVIDIA картой

**Решение:**
1. Установите CUDA Toolkit
2. Переустановите llama-cpp-python с CUDA:
   ```cmd
   set CMAKE_ARGS=-DLLAMA_CUDA=on
   pip install llama-cpp-python --force-reinstall --no-cache-dir
   ```

### Ошибка кодировки (кракозябры)

**Симптом:** Вместо русского текста отображаются странные символы

**Решение:**
1. В bat-файлах уже добавлено `chcp 65001`
2. Для PowerShell: `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`

### Модель не загружается

**Симптом:** Ошибка при загрузке GGUF файла

**Решение:**
1. Проверьте, что файл полностью скачан
2. Убедитесь, что достаточно RAM
3. Попробуйте меньшую модель (3B вместо 7B)

## Структура проекта

```
lmstudio-python/
├── ai_gui_v3.py          # Основной GUI (Dashboard v3.0)
├── ai_gui_v2.py          # GUI v2.0 с Telegram
├── ai_gui.py             # Базовый GUI
├── ai_cli.py             # CLI интерфейс
│
├── run_neyrolock.bat     # Запуск Dashboard v3.0
├── run_gui_v2.bat        # Запуск GUI v2.0
├── run_gui.bat           # Запуск базового GUI
├── run_ai_cli.bat        # Запуск CLI
├── setup_and_run.bat     # Установка + запуск
├── setup_cli.bat         # Настройка CLI
├── build_installer.bat   # Сборка установщика
│
└── installers/
    └── windows/
        ├── build_windows.bat     # Скрипт сборки
        └── neyrolock_setup.iss   # Конфигурация Inno Setup
```

## Контакты и поддержка

- GitHub Issues: Сообщайте об ошибках через GitHub
- Документация: См. `PROJECT_DOCUMENTATION.md`
