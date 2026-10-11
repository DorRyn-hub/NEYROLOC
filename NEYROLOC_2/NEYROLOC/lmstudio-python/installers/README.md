# 🏗️ NEYROLOCK Installers

Эта директория содержит все необходимое для сборки установщиков NEYROLOCK для Windows, macOS и Linux.

## 📂 Структура

```
installers/
├── README.md                    # Этот файл
├── output/                      # Выходная директория для собранных установщиков
│
├── pyinstaller/                 # PyInstaller спецификации
│   ├── neyrolock_gui.spec       # Спецификация для GUI приложения
│   └── neyrolock_cli.spec       # Спецификация для CLI приложения
│
├── windows/                     # Windows установщик
│   ├── build_windows.bat        # Скрипт сборки для Windows
│   └── neyrolock_setup.iss      # Inno Setup конфигурация
│
├── macos/                       # macOS установщик
│   └── build_macos.sh           # Скрипт сборки для macOS
│
└── linux/                       # Linux установщики
    └── build_linux.sh           # Скрипт сборки для Linux (.deb, .rpm, universal)
```

## 🚀 Быстрый старт

### Автоматическая сборка (рекомендуется)

Из корня проекта запустите:

```bash
# Автоматически определяет ОС и собирает соответствующий установщик
bash build_installer.sh
```

### Ручная сборка

#### Windows

```batch
cd installers\windows
build_windows.bat
```

**Требования:**
- Python 3.10+
- PyInstaller (`pip install pyinstaller`)
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (опционально, для создания .exe установщика)

**Результат:**
- `installers/output/NEYROLOCK-3.0.0-Windows-Setup.exe`

#### macOS

```bash
cd installers/macos
bash build_macos.sh
```

**Требования:**
- Python 3.10+
- PyInstaller (`pip install pyinstaller`)
- create-dmg (`brew install create-dmg`) - опционально, для создания .dmg

**Результат:**
- `installers/output/NEYROLOCK.app` - приложение для macOS
- `installers/output/NEYROLOCK-3.0.0-macOS.dmg` - DMG установщик

#### Linux

```bash
cd installers/linux
bash build_linux.sh
```

**Требования:**
- Python 3.10+
- PyInstaller (`pip install pyinstaller`)
- dpkg-deb (предустановлен на Debian/Ubuntu)
- rpmbuild (опционально, для .rpm пакетов)

**Результат:**
- `installers/output/neyrolock_3.0.0_amd64.deb` - Debian/Ubuntu пакет
- `installers/output/neyrolock-3.0.0-1.x86_64.rpm` - Fedora/RedHat/CentOS пакет
- `installers/output/NEYROLOCK-3.0.0-Linux-Installer.sh` - Универсальный установщик

## 📦 Форматы установщиков

### Windows
- **Setup.exe** (Inno Setup) - Полноценный установщик с GUI
  - Автоматическая установка в Program Files
  - Создание ярлыков (рабочий стол, меню Пуск)
  - Регистрация в системе
  - Удаление через "Programs and Features"

### macOS
- **.app** - Native macOS приложение
  - Standalone приложение (все зависимости включены)
  - Поддержка Apple Silicon (M1/M2/M3) с Metal ускорением
  - Совместимость с Intel Mac
- **.dmg** - Disk Image для распространения
  - Drag & Drop установка
  - Красивый интерфейс установки

### Linux
- **.deb** - Debian/Ubuntu пакет
  - Установка через `dpkg` или `apt`
  - Автоматическое управление зависимостями
  - Интеграция с системой (desktop entry, иконки)
  - Удаление через `apt remove`

- **.rpm** - Fedora/RedHat/CentOS пакет
  - Установка через `rpm` или `dnf`/`yum`
  - Автоматическое управление зависимостями
  - Интеграция с системой

- **.sh** - Универсальный self-extracting installer
  - Работает на любом Linux
  - Не требует системы пакетов
  - Простая установка: `sudo bash installer.sh`

## 🔧 Как работает сборка

### Этап 1: PyInstaller

PyInstaller создает standalone исполняемый файл:

1. Анализирует зависимости Python
2. Собирает все необходимые библиотеки
3. Упаковывает Python интерпретатор
4. Создает один исполняемый файл или директорию

**Особенности:**
- Windows: создает `.exe` файл
- macOS: создает `.app` bundle
- Linux: создает исполняемый файл

### Этап 2: Создание установщика

#### Windows (Inno Setup)
- Берет вывод PyInstaller
- Создает MSI-подобный установщик
- Добавляет ярлыки и регистрацию

#### macOS (create-dmg / hdiutil)
- Берет `.app` bundle от PyInstaller
- Создает DMG с красивым интерфейсом
- Добавляет ссылку на Applications

#### Linux (dpkg-deb / rpmbuild)
- Берет вывод PyInstaller
- Создает структуру пакета
- Добавляет metadata и scripts
- Компилирует в `.deb` или `.rpm`

## 🎨 Иконки и Ресурсы

Установщики требуют следующие файлы в директории `assets/`:

- `icon.ico` - Иконка для Windows (256x256)
- `icon.icns` - Иконка для macOS (содержит несколько размеров)
- `icon.png` - Иконка для Linux (256x256)

Если эти файлы отсутствуют, установщики будут собраны без иконок (будут использованы дефолтные иконки).

### Создание иконок

Если у вас есть PNG изображение (512x512 или больше):

**Windows (.ico):**
```bash
# Используйте онлайн конвертер или ImageMagick
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

**macOS (.icns):**
```bash
# Создайте iconset
mkdir MyIcon.iconset
sips -z 16 16     icon.png --out MyIcon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out MyIcon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out MyIcon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out MyIcon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out MyIcon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out MyIcon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out MyIcon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out MyIcon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out MyIcon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out MyIcon.iconset/icon_512x512@2x.png

# Создайте icns
iconutil -c icns MyIcon.iconset
```

## 🐛 Решение проблем сборки

### PyInstaller не находит модули

```bash
# Добавьте hidden imports в .spec файл
hiddenimports=['missing_module', 'another_module']
```

### Windows: "UPX is not available"

```
Решение: Установите UPX или отключите его в .spec файле (upx=False)
```

### macOS: "create-dmg not found"

```bash
brew install create-dmg
```

### Linux: "dpkg-deb: command not found"

```bash
sudo apt install dpkg-dev
```

### Большой размер установщика

**Причины:**
- Включены ненужные библиотеки
- Не оптимизирован код

**Решения:**
- Используйте `--exclude-module` в PyInstaller
- Включите UPX compression
- Удалите ненужные зависимости из requirements

### Установщик не запускается

**Проверьте:**
1. Правильные пути в .spec файлах
2. Все зависимости установлены
3. Python версия 3.10+
4. Логи сборки на ошибки

## 📝 Кастомизация

### Изменение версии

Обновите версию в файлах:
- `setup_neyrolock.py` (line 14)
- `installers/windows/neyrolock_setup.iss` (line 4)
- `installers/macos/build_macos.sh` (line 71)
- `installers/linux/build_linux.sh` (line 45, 125, 228)
- `installers/pyinstaller/neyrolock_gui.spec` (line 97)

### Изменение названия приложения

Обновите название в:
- Все файлы выше
- Desktop entry файлы (.desktop)
- Info.plist (macOS)
- Control files (.deb, .rpm)

### Добавление файлов в установщик

Обновите `datas` в `.spec` файлах:

```python
datas=[
    ('../../my_file.txt', '.'),
    ('../../my_folder', 'my_folder'),
],
```

## 🚢 Релиз

После сборки всех установщиков:

1. **Тестирование:**
   - Протестируйте на чистой системе каждой ОС
   - Проверьте установку и удаление
   - Убедитесь, что приложение работает

2. **Создание релиза на GitHub:**
   ```bash
   git tag v3.0.0
   git push origin v3.0.0
   ```

3. **Загрузка на GitHub Releases:**
   - Создайте новый релиз
   - Загрузите все установщики из `installers/output/`
   - Добавьте release notes

4. **Проверка:**
   - Проверьте ссылки для скачивания
   - Обновите `INSTALLATION_GUIDE.md` с правильными ссылками

## 📚 Дополнительные ресурсы

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [create-dmg GitHub](https://github.com/create-dmg/create-dmg)
- [Debian Packaging Guide](https://www.debian.org/doc/manuals/maint-guide/)
- [RPM Packaging Guide](https://rpm-packaging-guide.github.io/)

---

**Удачной сборки! 🎉**
