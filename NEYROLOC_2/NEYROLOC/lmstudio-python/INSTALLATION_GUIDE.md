# 📦 NEYROLOCK - Руководство по Установке

Полное руководство по установке NEYROLOCK на Windows, macOS и Linux.

## 📋 Содержание

1. [Системные Требования](#системные-требования)
2. [Установка на Windows](#установка-на-windows)
3. [Установка на macOS](#установка-на-macos)
4. [Установка на Linux](#установка-на-linux)
5. [Установка из исходников](#установка-из-исходников)
6. [Сборка Установщиков](#сборка-установщиков)
7. [Решение Проблем](#решение-проблем)

---

## 🖥️ Системные Требования

### Минимальные требования:
- **Процессор**: 4-ядерный CPU (x86_64 или ARM64)
- **Память**: 8 GB RAM (минимум)
- **Диск**: 10 GB свободного места
- **ОС**:
  - Windows 10/11 (64-bit)
  - macOS 10.14 (Mojave) или новее
  - Linux (Ubuntu 20.04+, Fedora 35+, или эквивалент)

### Рекомендуемые требования:
- **Процессор**: 8-ядерный CPU (Intel i7/AMD Ryzen 7 или лучше)
- **Память**: 16 GB RAM или больше
- **Диск**: 50 GB свободного места (для моделей)
- **GPU**: Поддержка Metal (macOS M1/M2/M3), CUDA (NVIDIA), или ROCm (AMD) для ускорения

---

## 🪟 Установка на Windows

### Вариант 1: Установщик (Рекомендуется)

1. **Скачайте установщик:**
   - Перейдите на [страницу релизов](https://github.com/neyrolock/neyrolock/releases)
   - Скачайте `NEYROLOCK-3.0.0-Windows-Setup.exe`

2. **Запустите установщик:**
   ```
   Двойной клик на NEYROLOCK-3.0.0-Windows-Setup.exe
   ```

3. **Следуйте инструкциям мастера установки:**
   - Выберите директорию установки (по умолчанию: `C:\Program Files\NEYROLOCK`)
   - Выберите опции (ярлык на рабочем столе, меню Пуск)
   - Нажмите "Установить"

4. **Запустите приложение:**
   - Из меню Пуск: `NEYROLOCK`
   - Или с рабочего стола (если выбрали эту опцию)

### Вариант 2: Портативная версия

1. **Скачайте архив:**
   - `NEYROLOCK-3.0.0-Windows-Portable.zip`

2. **Распакуйте в любую папку**

3. **Запустите:**
   ```
   NEYROLOCK.exe
   ```

### Требования для Windows:
- Не требует установки Python (все включено)
- Может потребоваться установка [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

---

## 🍎 Установка на macOS

### Вариант 1: DMG Installer (Рекомендуется)

1. **Скачайте DMG:**
   - [NEYROLOCK-3.0.0-macOS.dmg](https://github.com/neyrolock/neyrolock/releases)

2. **Откройте DMG файл:**
   ```bash
   open NEYROLOCK-3.0.0-macOS.dmg
   ```

3. **Перетащите NEYROLOCK.app в Applications:**
   - Откроется окно с иконкой приложения и папкой Applications
   - Перетащите NEYROLOCK.app в Applications

4. **Запустите приложение:**
   - Из Launchpad или Applications
   - Или через Spotlight: `Cmd+Space` → введите "NEYROLOCK"

5. **Первый запуск (важно!):**
   - При первом запуске может появиться предупреждение безопасности
   - Откройте `System Preferences` → `Security & Privacy`
   - Нажмите "Open Anyway" для NEYROLOCK

### Вариант 2: Homebrew (для опытных пользователей)

```bash
# Скоро будет доступно
brew install --cask neyrolock
```

### Вариант 3: Из исходников

```bash
# Клонируйте репозиторий
git clone https://github.com/neyrolock/neyrolock.git
cd neyrolock

# Установите зависимости
python3 -m pip install -r requirements_ai_cli.txt

# Для Apple Silicon (M1/M2/M3) установите llama-cpp-python с Metal
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir

# Запустите приложение
python3 ai_gui_v3.py
```

### Требования для macOS:
- macOS 10.14 (Mojave) или новее
- Для Apple Silicon (M1/M2/M3): автоматическое ускорение через Metal
- Для Intel Mac: работает, но медленнее

---

## 🐧 Установка на Linux

### Вариант 1: Debian/Ubuntu (.deb пакет)

```bash
# Скачайте .deb пакет
wget https://github.com/neyrolock/neyrolock/releases/download/v3.0.0/neyrolock_3.0.0_amd64.deb

# Установите
sudo dpkg -i neyrolock_3.0.0_amd64.deb

# Установите зависимости (если нужно)
sudo apt-get install -f

# Запустите
neyrolock
```

### Вариант 2: Fedora/RedHat/CentOS (.rpm пакет)

```bash
# Скачайте .rpm пакет
wget https://github.com/neyrolock/neyrolock/releases/download/v3.0.0/neyrolock-3.0.0-1.x86_64.rpm

# Установите
sudo rpm -i neyrolock-3.0.0-1.x86_64.rpm

# Или через dnf
sudo dnf install neyrolock-3.0.0-1.x86_64.rpm

# Запустите
neyrolock
```

### Вариант 3: Универсальный установщик (любой Linux)

```bash
# Скачайте установщик
wget https://github.com/neyrolock/neyrolock/releases/download/v3.0.0/NEYROLOCK-3.0.0-Linux-Installer.sh

# Сделайте исполняемым
chmod +x NEYROLOCK-3.0.0-Linux-Installer.sh

# Запустите с правами root
sudo ./NEYROLOCK-3.0.0-Linux-Installer.sh

# Запустите приложение
neyrolock
```

### Вариант 4: Из исходников

```bash
# Установите зависимости системы
sudo apt install python3 python3-pip python3-tk  # Debian/Ubuntu
sudo dnf install python3 python3-pip python3-tkinter  # Fedora
sudo pacman -S python python-pip tk  # Arch Linux

# Клонируйте репозиторий
git clone https://github.com/neyrolock/neyrolock.git
cd neyrolock

# Установите Python зависимости
pip3 install -r requirements_ai_cli.txt

# Запустите приложение
python3 ai_gui_v3.py
```

### Требования для Linux:
- Python 3.10 или новее
- Tkinter (обычно включен в Python)
- libgomp (для llama-cpp-python)

---

## 🛠️ Установка из исходников (для разработчиков)

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/neyrolock/neyrolock.git
cd neyrolock
```

### Шаг 2: Создание виртуального окружения (рекомендуется)

```bash
# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте его
# На Windows:
venv\Scripts\activate
# На macOS/Linux:
source venv/bin/activate
```

### Шаг 3: Установка зависимостей

```bash
# Базовые зависимости
pip install -r requirements_ai_cli.txt

# Для Apple Silicon (M1/M2/M3)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir

# Для разработки (опционально)
pip install -e ".[dev]"
```

### Шаг 4: Запуск приложения

```bash
# GUI приложение
python3 ai_gui_v3.py

# CLI версия
python3 ai_cli.py

# Telegram бот
python3 telegram_bot.py
```

---

## 🏗️ Сборка Установщиков

Если вы хотите собрать установщики самостоятельно:

### Автоматическая сборка (Universal)

```bash
# Запустите универсальный скрипт сборки
bash build_installer.sh

# Или для конкретной платформы:
bash installers/windows/build_windows.bat  # Windows
bash installers/macos/build_macos.sh       # macOS
bash installers/linux/build_linux.sh       # Linux
```

### Windows

**Требования:**
- Python 3.10+
- PyInstaller
- Inno Setup 6

**Сборка:**
```batch
cd installers\windows
build_windows.bat
```

**Результат:**
- `installers/output/NEYROLOCK-3.0.0-Windows-Setup.exe`

### macOS

**Требования:**
- Python 3.10+
- PyInstaller
- create-dmg (опционально, через Homebrew)

**Сборка:**
```bash
cd installers/macos
bash build_macos.sh
```

**Результат:**
- `installers/output/NEYROLOCK.app`
- `installers/output/NEYROLOCK-3.0.0-macOS.dmg`

### Linux

**Требования:**
- Python 3.10+
- PyInstaller
- dpkg-deb (для .deb)
- rpmbuild (для .rpm, опционально)

**Сборка:**
```bash
cd installers/linux
bash build_linux.sh
```

**Результат:**
- `installers/output/neyrolock_3.0.0_amd64.deb`
- `installers/output/neyrolock-3.0.0-1.x86_64.rpm`
- `installers/output/NEYROLOCK-3.0.0-Linux-Installer.sh`

---

## 🔧 Решение Проблем

### Windows

**Проблема: "Windows protected your PC"**
```
Решение:
1. Нажмите "More info"
2. Нажмите "Run anyway"
(Установщик не подписан цифровой подписью, но безопасен)
```

**Проблема: "DLL not found"**
```
Решение: Установите Visual C++ Redistributable
https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### macOS

**Проблема: "NEYROLOCK.app is damaged"**
```bash
# Решение: Снимите карантин
xattr -cr /Applications/NEYROLOCK.app
```

**Проблема: "NEYROLOCK.app can't be opened"**
```
Решение:
1. System Preferences → Security & Privacy
2. Нажмите "Open Anyway"
```

**Проблема: Медленная работа на Intel Mac**
```
Решение: Intel Mac работает медленнее Apple Silicon.
Рекомендуется использовать меньшие модели (до 7B параметров)
```

### Linux

**Проблема: "tkinter module not found"**
```bash
# Debian/Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

**Проблема: "libgomp.so.1: cannot open shared object"**
```bash
# Debian/Ubuntu
sudo apt install libgomp1

# Fedora
sudo dnf install libgomp

# Arch
sudo pacman -S gcc-libs
```

**Проблема: Permission denied**
```bash
# Сделайте файл исполняемым
chmod +x neyrolock

# Или запустите с sudo
sudo neyrolock
```

### Общие проблемы

**Проблема: Недостаточно памяти**
```
Решение: Используйте меньшие модели (3B-7B параметров)
или увеличьте swap на Linux
```

**Проблема: Модель не загружается**
```
Решение:
1. Проверьте путь к модели
2. Убедитесь, что модель в формате GGUF
3. Проверьте доступное место на диске
```

**Проблема: Ошибка при скачивании модели**
```
Решение:
1. Проверьте интернет-соединение
2. Попробуйте другую модель
3. Используйте VPN если HuggingFace заблокирован
```

---

## 📞 Поддержка

Если у вас возникли проблемы:

1. **Проверьте FAQ**: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)
2. **Issues на GitHub**: [github.com/neyrolock/neyrolock/issues](https://github.com/neyrolock/neyrolock/issues)
3. **Документация**: [README.md](README.md)

---

## 📝 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

## 🎉 Готово!

После установки вы можете:
- ✅ Запустить GUI приложение
- ✅ Скачать модели с HuggingFace
- ✅ Начать работу с локальными AI моделями
- ✅ Настроить Telegram бота
- ✅ Синхронизировать чаты между GUI и ботом

**Приятного использования NEYROLOCK! 🚀**
