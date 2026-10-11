# 🧪 NEYROLOCK - Полное Руководство по Тестированию и Публикации

Детальное пошаговое руководство по тестированию установщиков на всех операционных системах и публикации приложения.

---

## 📋 Содержание

1. [Подготовка к тестированию](#подготовка-к-тестированию)
2. [Тестирование на Windows](#тестирование-на-windows)
3. [Тестирование на macOS](#тестирование-на-macos)
4. [Тестирование на Linux](#тестирование-на-linux)
5. [Публикация на GitHub](#публикация-на-github)
6. [Публикация в магазинах приложений](#публикация-в-магазинах-приложений)
7. [Code Signing и Notarization](#code-signing-и-notarization)
8. [CI/CD автоматизация](#cicd-автоматизация)
9. [Чек-листы](#чек-листы)

---

# 1. Подготовка к тестированию

## 1.1. Сборка установщиков

### Шаг 1: Убедитесь, что все изменения закоммичены

```bash
# Проверьте статус git
git status

# Закоммитьте все изменения
git add .
git commit -m "Prepare for release v3.0.0"
```

### Шаг 2: Обновите версию везде

Убедитесь, что версия одинакова во всех файлах:

**Файлы для проверки:**
- `setup_neyrolock.py` → line 14: `version="3.0.0"`
- `installers/windows/neyrolock_setup.iss` → line 4: `#define MyAppVersion "3.0.0"`
- `installers/macos/build_macos.sh` → line 71: `DMG_NAME="NEYROLOCK-3.0.0-macOS"`
- `installers/linux/build_linux.sh` → строки с версией
- `installers/pyinstaller/neyrolock_gui.spec` → если указана версия

**Автоматическая проверка:**
```bash
# Найдите все упоминания версии
grep -r "3\.0\.0" installers/ setup_neyrolock.py
```

### Шаг 3: Создайте иконки (если еще не создали)

```bash
# Создайте placeholder иконку
python3 create_placeholder_icon.py

# Проверьте статус иконок
python3 create_placeholder_icon.py check
```

**Если нужны профессиональные иконки:**
- Наймите дизайнера на Fiverr ($10-50)
- Используйте онлайн генераторы
- См. подробности в `assets/README.md`

### Шаг 4: Соберите установщики на КАЖДОЙ платформе

#### Windows (на Windows машине):

```batch
REM Откройте Command Prompt или PowerShell
cd C:\path\to\neyrolock

REM Установите зависимости
pip install pyinstaller
pip install -r requirements_ai_cli.txt

REM Соберите
cd installers\windows
build_windows.bat

REM Проверьте результат
dir ..\output\
```

**Ожидаемый результат:**
- `installers/output/NEYROLOCK-3.0.0-Windows-Setup.exe` (~300-500 MB)

#### macOS (на Mac машине):

```bash
# Откройте Terminal
cd /path/to/neyrolock

# Установите зависимости
pip3 install pyinstaller
pip3 install -r requirements_ai_cli.txt

# Для Apple Silicon (M1/M2/M3)
CMAKE_ARGS="-DLLAMA_METAL=on" pip3 install llama-cpp-python --no-cache-dir

# Установите create-dmg (опционально)
brew install create-dmg

# Соберите
cd installers/macos
bash build_macos.sh

# Проверьте результат
ls -lh ../output/
```

**Ожидаемый результат:**
- `installers/output/NEYROLOCK.app` (папка)
- `installers/output/NEYROLOCK-3.0.0-macOS.dmg` (~300-500 MB)

#### Linux (на Linux машине):

```bash
# Откройте Terminal
cd /path/to/neyrolock

# Установите зависимости системы
sudo apt install python3 python3-pip python3-tk  # Debian/Ubuntu
# или
sudo dnf install python3 python3-pip python3-tkinter  # Fedora

# Установите Python зависимости
pip3 install pyinstaller
pip3 install -r requirements_ai_cli.txt

# Соберите
cd installers/linux
bash build_linux.sh

# Проверьте результат
ls -lh ../output/
```

**Ожидаемый результат:**
- `installers/output/neyrolock_3.0.0_amd64.deb` (~300-500 MB)
- `installers/output/neyrolock-3.0.0-1.x86_64.rpm` (~300-500 MB)
- `installers/output/NEYROLOCK-3.0.0-Linux-Installer.sh` (~300-500 MB)

### Шаг 5: Соберите контрольные суммы

Для проверки целостности файлов:

```bash
cd installers/output

# На Linux/macOS:
sha256sum * > SHA256SUMS.txt

# На Windows (PowerShell):
Get-ChildItem | Get-FileHash -Algorithm SHA256 | Format-List > SHA256SUMS.txt

# Или используйте онлайн инструменты
```

---

# 2. Тестирование на Windows

## 2.1. Подготовка тестовой среды

### Вариант 1: Виртуальная машина (Рекомендуется)

**Скачайте официальную VM от Microsoft:**
- Перейдите на: https://developer.microsoft.com/en-us/windows/downloads/virtual-machines/
- Скачайте "Windows 11 development environment"
- Или используйте свою Windows VM

**Создайте VM с помощью VirtualBox/VMware:**
1. Скачайте [VirtualBox](https://www.virtualbox.org/) (бесплатно)
2. Создайте новую VM:
   - OS: Windows 10/11
   - RAM: 8 GB минимум
   - HDD: 50 GB
3. Установите Windows (можно использовать trial версию)

### Вариант 2: Чистая установка Windows

Используйте физический компьютер с чистой установкой Windows.

### Вариант 3: Windows Sandbox

**Для Windows 10/11 Pro/Enterprise:**

1. Включите Windows Sandbox:
   ```
   Настройки → Приложения → Дополнительные компоненты → Песочница Windows
   ```

2. Запустите Sandbox из меню Пуск

3. Скопируйте установщик в Sandbox (drag & drop)

## 2.2. Тестирование установки

### Шаг 1: Перенесите установщик

```batch
REM Скопируйте NEYROLOCK-3.0.0-Windows-Setup.exe на тестовую машину
REM Через USB, сеть, или облако
```

### Шаг 2: Запустите установщик

1. **Двойной клик** на `NEYROLOCK-3.0.0-Windows-Setup.exe`

2. **Если появляется "Windows protected your PC":**
   - Это нормально (установщик не подписан)
   - Нажмите "More info"
   - Нажмите "Run anyway"

3. **Следуйте мастеру установки:**
   - ✅ Проверьте: Корректное отображение названия и версии
   - ✅ Проверьте: Русский язык работает (если выбран)
   - ✅ Выберите директорию установки (по умолчанию: `C:\Program Files\NEYROLOCK`)
   - ✅ Выберите опции:
     - [x] Создать ярлык на рабочем столе
     - [x] Создать ярлык в меню Пуск
   - ✅ Нажмите "Install"

4. **Дождитесь завершения установки**
   - Должно занять 1-3 минуты
   - ✅ Проверьте: Нет ошибок во время установки
   - ✅ Проверьте: Прогресс бар работает корректно

5. **Завершите установку:**
   - ✅ Проверьте: Опция "Launch NEYROLOCK" отображается
   - Снимите галочку (запустим вручную)
   - Нажмите "Finish"

### Шаг 3: Проверьте установленные файлы

```batch
REM Откройте Command Prompt или PowerShell

REM Проверьте директорию установки
dir "C:\Program Files\NEYROLOCK"

REM Проверьте размер
dir "C:\Program Files\NEYROLOCK" /s

REM Проверьте ярлыки
dir "%USERPROFILE%\Desktop\NEYROLOCK.lnk"
dir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\NEYROLOCK"
```

**Ожидаемые файлы:**
- ✅ `NEYROLOCK.exe` (основной исполняемый файл)
- ✅ Папка `_internal/` или похожая (библиотеки PyInstaller)
- ✅ `PROJECT_DOCUMENTATION.md`
- ✅ `README.md`
- ✅ `LICENSE`

### Шаг 4: Проверьте регистрацию в системе

1. **Откройте "Settings" → "Apps" → "Apps & features"**
2. **Найдите "NEYROLOCK"**
   - ✅ Проверьте: Приложение отображается в списке
   - ✅ Проверьте: Версия 3.0.0 указана
   - ✅ Проверьте: Размер соответствует (~300-500 MB)
   - ✅ Проверьте: Кнопка "Uninstall" доступна

### Шаг 5: Первый запуск приложения

1. **Запустите NEYROLOCK:**
   - Из ярлыка на рабочем столе (двойной клик)
   - Или из меню Пуск
   - Или из `C:\Program Files\NEYROLOCK\NEYROLOCK.exe`

2. **Если появляется предупреждение Windows Defender:**
   - Нажмите "More info"
   - Нажмите "Run anyway"
   - (Это нормально для неподписанных приложений)

3. **Дождитесь загрузки приложения:**
   - ✅ Проверьте: Окно приложения открывается (может занять 5-15 секунд при первом запуске)
   - ✅ Проверьте: Нет crash'ей или ошибок
   - ✅ Проверьте: GUI отображается корректно

### Шаг 6: Функциональное тестирование

**Базовые функции:**

1. **Проверьте интерфейс:**
   - ✅ Все элементы GUI видны и корректны
   - ✅ Кнопки работают
   - ✅ Текстовые поля доступны
   - ✅ Меню открываются

2. **Проверьте настройки:**
   - ✅ Откройте настройки
   - ✅ Измените настройку
   - ✅ Сохраните
   - ✅ Перезапустите приложение
   - ✅ Проверьте: Настройки сохранились

3. **Проверьте скачивание модели:**
   - ✅ Откройте поиск моделей HuggingFace
   - ✅ Найдите небольшую модель (например, "TinyLlama-1.1B")
   - ✅ Попробуйте скачать (можно отменить через 1-2%)
   - ✅ Проверьте: Прогресс отображается
   - ✅ Проверьте: Можно отменить загрузку

4. **Проверьте загрузку локальной модели (если есть):**
   - ✅ Выберите файл модели (.gguf)
   - ✅ Загрузите модель
   - ✅ Проверьте: Модель загружается без ошибок

5. **Проверьте генерацию текста (если модель загружена):**
   - ✅ Введите тестовый промпт ("Привет, как дела?")
   - ✅ Нажмите отправить
   - ✅ Проверьте: Генерация начинается
   - ✅ Проверьте: Текст отображается
   - ✅ Проверьте: Нет crash'ей

6. **Проверьте сохранение истории:**
   - ✅ Создайте несколько сообщений
   - ✅ Закройте приложение
   - ✅ Откройте снова
   - ✅ Проверьте: История сохранилась

### Шаг 7: Проверьте создание файлов конфигурации

```batch
REM Проверьте директорию конфигурации
dir "%USERPROFILE%\.neyrolock"

REM Или в AppData
dir "%APPDATA%\NEYROLOCK"
dir "%LOCALAPPDATA%\NEYROLOCK"
```

**Ожидаемые файлы:**
- ✅ `config.json` (настройки)
- ✅ `chat_history.json` (история чатов)
- ✅ Возможно другие файлы

### Шаг 8: Тестирование производительности

1. **Откройте Task Manager** (Ctrl+Shift+Esc)
2. **Запустите NEYROLOCK**
3. **Проверьте использование ресурсов:**
   - ✅ CPU: Не должен быть 100% в idle
   - ✅ RAM: Разумное потребление (~200-500 MB в idle)
   - ✅ Disk: Нет постоянной активности
   - ✅ Network: Активность только при скачивании

4. **При генерации текста:**
   - ✅ CPU: Может быть высоким (50-100%) - это нормально
   - ✅ RAM: Зависит от размера модели
   - ✅ Нет утечек памяти (не растет бесконечно)

### Шаг 9: Тестирование стабильности

1. **Стресс-тест:**
   - ✅ Отправьте 10-20 сообщений подряд
   - ✅ Быстро переключайтесь между вкладками
   - ✅ Изменяйте настройки во время генерации
   - ✅ Проверьте: Нет crash'ей

2. **Long-running тест:**
   - ✅ Оставьте приложение открытым на 1-2 часа
   - ✅ Проверьте: Нет утечек памяти
   - ✅ Проверьте: Приложение остается отзывчивым

### Шаг 10: Тестирование удаления

1. **Откройте "Settings" → "Apps" → "Apps & features"**
2. **Найдите "NEYROLOCK" и нажмите "Uninstall"**
3. **Подтвердите удаление**
4. **Дождитесь завершения:**
   - ✅ Проверьте: Процесс завершается без ошибок
   - ✅ Проверьте: Прогресс отображается

5. **Проверьте, что файлы удалены:**

```batch
REM Проверьте директорию установки
dir "C:\Program Files\NEYROLOCK"
REM Должно быть: "File Not Found" или пустая папка

REM Проверьте ярлыки
dir "%USERPROFILE%\Desktop\NEYROLOCK.lnk"
REM Должно быть: "File Not Found"

dir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\NEYROLOCK"
REM Должно быть: "File Not Found"
```

6. **Проверьте регистрацию:**
   - ✅ Откройте "Apps & features" снова
   - ✅ Проверьте: NEYROLOCK больше не в списке

7. **Проверьте пользовательские данные:**

```batch
REM Эти файлы МОГУТ остаться (это нормально)
dir "%USERPROFILE%\.neyrolock"
dir "%APPDATA%\NEYROLOCK"
```

**Примечание:** Обычно пользовательские данные не удаляются автоматически.

## 2.3. Тестирование на разных версиях Windows

**Тестируйте на:**

| Версия | Приоритет | Примечания |
|--------|-----------|------------|
| Windows 11 (latest) | ⭐⭐⭐ Обязательно | Самая новая ОС |
| Windows 10 (21H2 или новее) | ⭐⭐⭐ Обязательно | Самая популярная |
| Windows 10 (1909) | ⭐⭐ Желательно | Старая но используемая |
| Windows Server 2019/2022 | ⭐ Опционально | Для enterprise |

**Как получить тестовые VM:**
- Microsoft Developer VMs: https://developer.microsoft.com/en-us/windows/downloads/virtual-machines/
- Windows Insider Program (для новых версий)
- Собственные VM с trial лицензиями (90 дней)

## 2.4. Тестирование на разных конфигурациях

**Тестируйте на:**

1. **Разные разрешения экрана:**
   - 1920x1080 (Full HD) - стандарт
   - 1366x768 (ноутбуки)
   - 3840x2160 (4K)
   - ✅ Проверьте: GUI масштабируется корректно

2. **Разные DPI настройки:**
   - 100% (стандарт)
   - 125%, 150% (высокий DPI)
   - ✅ Проверьте: Текст и элементы четкие

3. **Разные языки системы:**
   - Английский
   - Русский
   - ✅ Проверьте: Нет проблем с кодировкой

4. **С антивирусом:**
   - Windows Defender (встроенный)
   - Сторонние антивирусы (Kaspersky, Avast, etc.)
   - ✅ Проверьте: Нет ложных срабатываний

## 2.5. Проверка логов и ошибок

**Проверьте Windows Event Viewer:**

1. Откройте Event Viewer (`eventvwr.msc`)
2. Перейдите в "Windows Logs" → "Application"
3. Найдите события от NEYROLOCK
4. ✅ Проверьте: Нет критических ошибок (Error/Critical)

**Проверьте логи приложения:**

```batch
REM Если приложение создает логи
dir "%LOCALAPPDATA%\NEYROLOCK\logs"
type "%LOCALAPPDATA%\NEYROLOCK\logs\app.log"
```

---

# 3. Тестирование на macOS

## 3.1. Подготовка тестовой среды

### Вариант 1: Физический Mac (Идеально)

**Тестируйте на двух типах Mac:**

1. **Apple Silicon (M1/M2/M3)** - Обязательно!
   - Проверяет работу Metal ускорения
   - Проверяет ARM64 совместимость

2. **Intel Mac** - Желательно
   - Проверяет x86_64 совместимость
   - Проверяет работу без Metal

### Вариант 2: Виртуальная машина (Ограничения)

**На Mac хосте (с VMware Fusion или Parallels):**
- Можно создать macOS VM
- НО: Нет доступа к Metal в VM
- НО: Медленная производительность

**Примечание:** Официально Apple разрешает виртуализацию macOS только на Mac оборудовании.

### Вариант 3: Hackintosh (Не рекомендуется)

Технически возможно, но нарушает лицензию Apple.

## 3.2. Тестирование установки из DMG

### Шаг 1: Перенесите DMG на Mac

```bash
# Скопируйте NEYROLOCK-3.0.0-macOS.dmg на Mac
# Через AirDrop, USB, облако, или сеть
```

### Шаг 2: Откройте DMG

```bash
# Двойной клик на DMG файл
# Или через Terminal:
open NEYROLOCK-3.0.0-macOS.dmg
```

**Проверки:**
- ✅ DMG монтируется без ошибок
- ✅ Открывается окно Finder с содержимым
- ✅ Видно NEYROLOCK.app и ссылку на Applications
- ✅ Дизайн окна корректен (если настроен)

### Шаг 3: Установите приложение

1. **Перетащите NEYROLOCK.app в Applications:**
   - Drag & Drop из DMG окна
   - Дождитесь окончания копирования
   - ✅ Проверьте: Копирование занимает 10-60 секунд
   - ✅ Проверьте: Нет ошибок при копировании

2. **Размонтируйте DMG:**
   ```bash
   # Нажмите Eject в Finder
   # Или через Terminal:
   hdiutil detach /Volumes/NEYROLOCK
   ```

3. **Проверьте установленное приложение:**
   ```bash
   ls -lh /Applications/NEYROLOCK.app
   du -sh /Applications/NEYROLOCK.app
   ```

**Ожидаемый размер:** ~300-500 MB

### Шаг 4: Первый запуск (важно!)

**На macOS есть защита Gatekeeper:**

1. **НЕ запускайте через двойной клик сразу!**

2. **Правильный способ первого запуска:**
   - Откройте Finder
   - Перейдите в Applications
   - **Правой кнопкой** на NEYROLOCK.app
   - Выберите "Open"
   - Появится диалог: "NEYROLOCK.app is from an unidentified developer. Are you sure you want to open it?"
   - Нажмите "Open"

3. **Альтернативный способ (если не работает):**
   ```bash
   # Снимите quarantine attribute
   xattr -cr /Applications/NEYROLOCK.app

   # Затем запустите
   open /Applications/NEYROLOCK.app
   ```

4. **Если появляется "NEYROLOCK.app is damaged":**
   ```bash
   # Снимите quarantine
   xattr -cr /Applications/NEYROLOCK.app

   # Разрешите запуск в настройках безопасности
   # System Preferences → Security & Privacy → General
   # Нажмите "Open Anyway"
   ```

5. **Дождитесь загрузки:**
   - ✅ Проверьте: Приложение запускается (5-15 секунд)
   - ✅ Проверьте: Окно появляется
   - ✅ Проверьте: Нет crash'ей

### Шаг 5: Проверьте интеграцию с системой

1. **Проверьте в Launchpad:**
   - Откройте Launchpad (F4 или жест)
   - ✅ Найдите иконку NEYROLOCK
   - ✅ Проверьте: Иконка отображается корректно
   - ✅ Запустите из Launchpad

2. **Проверьте в Spotlight:**
   - Нажмите Cmd+Space
   - Введите "NEYROLOCK"
   - ✅ Проверьте: Приложение находится
   - ✅ Проверьте: Можно запустить

3. **Проверьте в Dock:**
   - Запустите приложение
   - ✅ Проверьте: Иконка появляется в Dock
   - ✅ Правой кнопкой → Options → Keep in Dock
   - ✅ Проверьте: Иконка остается после закрытия

### Шаг 6: Функциональное тестирование

**Базовые функции (как на Windows):**

1. **Проверьте интерфейс:**
   - ✅ Все элементы GUI видны
   - ✅ Соответствует macOS design guidelines
   - ✅ Cmd+Q закрывает приложение
   - ✅ Cmd+W закрывает окно
   - ✅ Cmd+, открывает настройки (если реализовано)

2. **Проверьте настройки:**
   - ✅ Откройте настройки
   - ✅ Измените настройку
   - ✅ Сохраните (Cmd+S если доступно)
   - ✅ Перезапустите
   - ✅ Проверьте: Настройки сохранились

3. **Проверьте скачивание модели:**
   - ✅ Откройте поиск HuggingFace
   - ✅ Найдите модель
   - ✅ Начните скачивание
   - ✅ Проверьте: Прогресс отображается
   - ✅ Можно отменить

4. **Проверьте загрузку модели:**
   - ✅ Выберите .gguf файл
   - ✅ Загрузите
   - ✅ Проверьте: Загружается без ошибок

5. **Проверьте генерацию:**
   - ✅ Введите промпт
   - ✅ Отправьте
   - ✅ Проверьте: Генерация работает
   - ✅ Проверьте: Текст отображается

6. **ВАЖНО - Проверьте Metal ускорение (на Apple Silicon):**

```bash
# Запустите приложение и проверьте Activity Monitor
# Applications → Utilities → Activity Monitor
# Найдите NEYROLOCK
# Проверьте колонку "GPU" - должна быть активность при генерации
```

**Признаки работы Metal:**
- ✅ Быстрая генерация (>10-20 tokens/sec на M1 для 7B модели)
- ✅ GPU показывает активность в Activity Monitor
- ✅ CPU не на 100% (часть работы на GPU)

**Если Metal не работает:**
- Генерация медленная (<5 tokens/sec)
- CPU на 100%
- Нужно пересобрать с правильными флагами

### Шаг 7: Проверьте файлы конфигурации

```bash
# Проверьте домашнюю директорию
ls -la ~/.neyrolock

# Или в Library
ls -la ~/Library/Application\ Support/NEYROLOCK
```

**Ожидаемые файлы:**
- ✅ `config.json`
- ✅ `chat_history.json`
- ✅ Возможно другие

### Шаг 8: Тестирование производительности

1. **Откройте Activity Monitor** (Applications → Utilities)
2. **Запустите NEYROLOCK**
3. **Проверьте:**
   - ✅ CPU: Низкое в idle (<5%)
   - ✅ Memory: Разумное (~200-500 MB idle)
   - ✅ Energy: Низкое в idle
   - ✅ При генерации: CPU или GPU активны

4. **Проверьте температуру (опционально):**
   - Установите Intel Power Gadget или iStat Menus
   - ✅ Проверьте: Нет перегрева при длительной работе

### Шаг 9: Тестирование на разных версиях macOS

**Тестируйте на:**

| Версия | Приоритет | Примечания |
|--------|-----------|------------|
| macOS Sonoma (14.x) | ⭐⭐⭐ Обязательно | Последняя версия |
| macOS Ventura (13.x) | ⭐⭐⭐ Обязательно | Популярная |
| macOS Monterey (12.x) | ⭐⭐ Желательно | Старые Mac |
| macOS Big Sur (11.x) | ⭐ Опционально | Минимальная? |

**Важно:** Проверьте минимальную версию в Info.plist

### Шаг 10: Удаление приложения

```bash
# Метод 1: Простое удаление
rm -rf /Applications/NEYROLOCK.app

# Метод 2: Полное удаление с данными
rm -rf /Applications/NEYROLOCK.app
rm -rf ~/.neyrolock
rm -rf ~/Library/Application\ Support/NEYROLOCK
rm -rf ~/Library/Preferences/ai.neyrolock.*
rm -rf ~/Library/Caches/NEYROLOCK

# Проверьте что все удалено
ls -la /Applications/NEYROLOCK.app  # Должно быть: No such file
```

## 3.3. Тестирование .app bundle напрямую

Если у вас только .app без DMG:

```bash
# Скопируйте в Applications
cp -R NEYROLOCK.app /Applications/

# Снимите quarantine
xattr -cr /Applications/NEYROLOCK.app

# Запустите
open /Applications/NEYROLOCK.app
```

Дальше тестирование как обычно.

## 3.4. Проверка подписи и notarization (если применимо)

```bash
# Проверьте подпись
codesign -dv --verbose=4 /Applications/NEYROLOCK.app

# Проверьте notarization
spctl -a -vv /Applications/NEYROLOCK.app

# Проверьте entitlements
codesign -d --entitlements - /Applications/NEYROLOCK.app
```

**Если не подписано:**
- Будет сообщение о неподписанном приложении
- Это нормально для дистрибуции без Apple Developer Account

---

# 4. Тестирование на Linux

## 4.1. Подготовка тестовых сред

### Тестируйте на нескольких дистрибутивах:

| Дистрибутив | Формат | Приоритет | Примечания |
|-------------|--------|-----------|------------|
| Ubuntu 22.04 LTS | .deb | ⭐⭐⭐ Обязательно | Самый популярный |
| Ubuntu 24.04 LTS | .deb | ⭐⭐⭐ Обязательно | Новая LTS |
| Debian 12 | .deb | ⭐⭐ Желательно | Стабильная база |
| Linux Mint | .deb | ⭐⭐ Желательно | Популярный desktop |
| Fedora 39/40 | .rpm | ⭐⭐ Желательно | RPM семейство |
| CentOS/RHEL 9 | .rpm | ⭐ Опционально | Enterprise |
| Arch Linux | universal | ⭐ Опционально | Rolling release |
| Pop!_OS | .deb | ⭐ Опционально | Популярный gaming |

### Создание тестовых VM:

**Используйте:**
- VirtualBox (бесплатно): https://www.virtualbox.org/
- VMware Workstation Player (бесплатно для личного использования)
- QEMU/KVM (для Linux хостов)

**Конфигурация VM:**
- RAM: 4-8 GB минимум
- HDD: 30 GB
- CPU: 2-4 ядра

## 4.2. Тестирование .deb пакета (Ubuntu/Debian)

### Шаг 1: Подготовьте чистую систему

```bash
# Обновите систему
sudo apt update
sudo apt upgrade -y

# Убедитесь что старые версии удалены
sudo apt remove neyrolock -y
rm -rf ~/.neyrolock
```

### Шаг 2: Перенесите .deb пакет

```bash
# Скопируйте neyrolock_3.0.0_amd64.deb на тестовую машину
# Через USB, scp, или облако

# Например через scp:
scp neyrolock_3.0.0_amd64.deb user@test-machine:~/
```

### Шаг 3: Проверьте пакет

```bash
# Проверьте содержимое пакета
dpkg -c neyrolock_3.0.0_amd64.deb

# Проверьте информацию о пакете
dpkg -I neyrolock_3.0.0_amd64.deb

# Проверьте контрольные скрипты
dpkg -e neyrolock_3.0.0_amd64.deb temp-control
cat temp-control/control
cat temp-control/postinst
cat temp-control/postrm
rm -rf temp-control
```

**Проверки:**
- ✅ Package: neyrolock
- ✅ Version: 3.0.0
- ✅ Architecture: amd64
- ✅ Dependencies указаны корректно
- ✅ Maintainer указан
- ✅ Description корректное

### Шаг 4: Установите пакет

```bash
# Метод 1: Через dpkg (может потребовать ручную установку зависимостей)
sudo dpkg -i neyrolock_3.0.0_amd64.deb

# Если есть проблемы с зависимостями:
sudo apt-get install -f

# Метод 2: Через apt (рекомендуется, автоматически разрешает зависимости)
sudo apt install ./neyrolock_3.0.0_amd64.deb

# Метод 3: Через gdebi (если установлен)
sudo gdebi neyrolock_3.0.0_amd64.deb
```

**Проверки во время установки:**
- ✅ Установка завершается без ошибок
- ✅ Все зависимости установлены
- ✅ Postinst скрипт выполнился успешно
- ✅ Появилось сообщение об успешной установке

### Шаг 5: Проверьте установленные файлы

```bash
# Проверьте какие файлы установлены
dpkg -L neyrolock

# Должны быть примерно такие файлы:
# /opt/neyrolock/
# /opt/neyrolock/NEYROLOCK
# /opt/neyrolock/_internal/...
# /usr/bin/neyrolock или /usr/local/bin/neyrolock
# /usr/share/applications/neyrolock.desktop
# /usr/share/icons/.../neyrolock.png
```

**Проверки:**
- ✅ Основной исполняемый файл установлен
- ✅ Библиотеки в /opt/neyrolock/
- ✅ Символическая ссылка создана
- ✅ Desktop entry создан
- ✅ Иконка установлена

### Шаг 6: Проверьте регистрацию пакета

```bash
# Проверьте что пакет в системе
dpkg -l | grep neyrolock

# Проверьте статус
dpkg -s neyrolock

# Проверьте версию
dpkg -s neyrolock | grep Version
```

**Ожидаемый вывод:**
```
Package: neyrolock
Status: install ok installed
Version: 3.0.0
...
```

### Шаг 7: Первый запуск

**Метод 1: Через GUI (Applications Menu):**
1. Откройте Applications Menu (или Activities в GNOME)
2. Найдите "NEYROLOCK" (может быть в категории Utilities или Science)
3. ✅ Проверьте: Иконка отображается
4. Кликните на иконку
5. ✅ Проверьте: Приложение запускается

**Метод 2: Через Terminal:**
```bash
# Запустите через символическую ссылку
neyrolock

# Или напрямую
/opt/neyrolock/NEYROLOCK
```

**Проверки:**
- ✅ Приложение запускается (5-15 секунд)
- ✅ Окно открывается
- ✅ GUI отображается корректно
- ✅ Нет ошибок в терминале

### Шаг 8: Проверьте логи (если есть ошибки)

```bash
# Проверьте системный лог
journalctl -xe | grep -i neyrolock

# Проверьте логи приложения
cat ~/.neyrolock/logs/*.log

# Проверьте stdout/stderr если запускали из терминала
```

### Шаг 9: Функциональное тестирование

**Базовые функции (как на Windows/macOS):**

1. **Проверьте интерфейс:**
   - ✅ Все элементы видны
   - ✅ Соответствует GTK/Qt теме
   - ✅ Масштабирование корректно

2. **Проверьте настройки, скачивание моделей, генерацию** (как раньше)

3. **Проверьте интеграцию с системой:**
   ```bash
   # Desktop entry
   cat /usr/share/applications/neyrolock.desktop

   # Иконка
   ls -lh /usr/share/icons/**/neyrolock.png

   # Исполняемый файл
   which neyrolock
   ```

### Шаг 10: Тестирование удаления

```bash
# Удалите пакет
sudo apt remove neyrolock

# Или полностью с конфигурацией
sudo apt purge neyrolock

# Проверьте что пакет удален
dpkg -l | grep neyrolock

# Проверьте файлы
ls -la /opt/neyrolock  # Должно быть: No such file
ls -la /usr/bin/neyrolock  # Должно быть: No such file
cat /usr/share/applications/neyrolock.desktop  # Должно быть: No such file
```

**Проверки:**
- ✅ Пакет удален из системы
- ✅ Файлы приложения удалены
- ✅ Desktop entry удален
- ✅ Символическая ссылка удалена
- ✅ Пользовательские данные могут остаться (это нормально)

## 4.3. Тестирование .rpm пакета (Fedora/RHEL/CentOS)

### Шаг 1: Подготовьте систему

```bash
# Fedora
sudo dnf update -y
sudo dnf remove neyrolock -y

# RHEL/CentOS
sudo yum update -y
sudo yum remove neyrolock -y

# Очистите данные
rm -rf ~/.neyrolock
```

### Шаг 2: Проверьте пакет

```bash
# Проверьте информацию о пакете
rpm -qip neyrolock-3.0.0-1.x86_64.rpm

# Проверьте содержимое
rpm -qlp neyrolock-3.0.0-1.x86_64.rpm

# Проверьте скрипты
rpm -qp --scripts neyrolock-3.0.0-1.x86_64.rpm
```

### Шаг 3: Установите пакет

```bash
# Fedora (рекомендуется)
sudo dnf install ./neyrolock-3.0.0-1.x86_64.rpm

# Или через rpm (может требовать ручную установку зависимостей)
sudo rpm -ivh neyrolock-3.0.0-1.x86_64.rpm

# Если нужны зависимости
sudo dnf install python3 python3-tkinter

# RHEL/CentOS
sudo yum install ./neyrolock-3.0.0-1.x86_64.rpm
```

**Проверки:**
- ✅ Установка без ошибок
- ✅ Зависимости установлены
- ✅ Post-install скрипты выполнились

### Шаг 4: Проверьте установку

```bash
# Проверьте что пакет установлен
rpm -qa | grep neyrolock

# Проверьте информацию
rpm -qi neyrolock

# Проверьте файлы
rpm -ql neyrolock
```

### Шаг 5: Тестирование (как для .deb)

Выполните те же тесты что и для .deb пакета.

### Шаг 6: Удаление

```bash
# Удалите пакет
sudo dnf remove neyrolock

# Или через rpm
sudo rpm -e neyrolock

# Проверьте
rpm -qa | grep neyrolock  # Должно быть пусто
```

## 4.4. Тестирование универсального установщика

### Шаг 1: Подготовьте систему

```bash
# Убедитесь что старые версии удалены
sudo rm -rf /opt/neyrolock
sudo rm -f /usr/local/bin/neyrolock
sudo rm -f /usr/share/applications/neyrolock.desktop

# Очистите данные
rm -rf ~/.neyrolock
```

### Шаг 2: Проверьте установщик

```bash
# Сделайте исполняемым
chmod +x NEYROLOCK-3.0.0-Linux-Installer.sh

# Проверьте содержимое (первые строки)
head -n 100 NEYROLOCK-3.0.0-Linux-Installer.sh
```

### Шаг 3: Запустите установщик

```bash
# Запустите с sudo (требуется для установки в /opt)
sudo bash NEYROLOCK-3.0.0-Linux-Installer.sh
```

**Проверки во время установки:**
- ✅ Отображается приветственное сообщение
- ✅ Извлечение файлов происходит без ошибок
- ✅ Создается символическая ссылка
- ✅ Создается desktop entry
- ✅ Отображается сообщение об успехе

### Шаг 4: Проверьте установку

```bash
# Проверьте файлы
ls -lh /opt/neyrolock/
ls -lh /usr/local/bin/neyrolock
cat /usr/share/applications/neyrolock.desktop

# Проверьте что команда работает
which neyrolock
neyrolock --version  # Если поддерживается
```

### Шаг 5: Тестирование (как обычно)

Выполните стандартные функциональные тесты.

### Шаг 6: Удаление

```bash
# Удалите вручную (установщик обычно не предоставляет uninstaller)
sudo rm -rf /opt/neyrolock
sudo rm -f /usr/local/bin/neyrolock
sudo rm -f /usr/share/applications/neyrolock.desktop

# Опционально: удалите пользовательские данные
rm -rf ~/.neyrolock

# Проверьте
ls -la /opt/neyrolock  # Должно быть: No such file
```

## 4.5. Тестирование на разных desktop окружениях

**Тестируйте на:**

| Desktop | Дистрибутив | Приоритет | Примечания |
|---------|-------------|-----------|------------|
| GNOME | Ubuntu, Fedora | ⭐⭐⭐ | Самое популярное |
| KDE Plasma | Kubuntu, Fedora KDE | ⭐⭐ | Второе по популярности |
| XFCE | Xubuntu, Linux Mint | ⭐⭐ | Легковесное |
| Cinnamon | Linux Mint | ⭐ | Популярное в Mint |
| MATE | Ubuntu MATE | ⭐ | Классическое |

**Проверки:**
- ✅ Приложение запускается
- ✅ Иконка отображается в меню
- ✅ GUI тема соответствует системе
- ✅ Все функции работают

---

# 5. Публикация на GitHub

## 5.1. Подготовка релиза

### Шаг 1: Финальная проверка

```bash
# Убедитесь что все изменения закоммичены
git status

# Проверьте текущую ветку
git branch

# Убедитесь что на main/master
git checkout main
```

### Шаг 2: Создайте и загрузите тег

```bash
# Создайте аннотированный тег
git tag -a v3.0.0 -m "Release version 3.0.0"

# Проверьте тег
git tag -l
git show v3.0.0

# Загрузите тег на GitHub
git push origin v3.0.0

# Также загрузите все изменения
git push origin main
```

### Шаг 3: Подготовьте файлы для релиза

```bash
cd installers/output

# Убедитесь что все установщики собраны
ls -lh

# Создайте контрольные суммы
sha256sum * > SHA256SUMS.txt

# Или на macOS
shasum -a 256 * > SHA256SUMS.txt

# Проверьте
cat SHA256SUMS.txt
```

### Шаг 4: Подготовьте Release Notes

Создайте файл `RELEASE_NOTES_v3.0.0.md`:

```markdown
# NEYROLOCK v3.0.0 - Release Notes

## 🎉 What's New

### Major Features
- 🖥️ Modern dark GUI interface with dashboard
- 📱 Telegram Bot with full synchronization
- 🔄 Message sync between GUI and Telegram
- 📥 HuggingFace model search and download
- 💾 Persistent history and settings
- 🎨 Markdown rendering with code highlighting
- 🌐 Russian keyboard layout support

### Improvements
- Optimized model loading performance
- Better error handling
- Improved UI/UX
- Enhanced stability

## 📦 Installation

### Windows
Download and run `NEYROLOCK-3.0.0-Windows-Setup.exe`

### macOS
Download `NEYROLOCK-3.0.0-macOS.dmg`, open it, and drag NEYROLOCK.app to Applications

### Linux
**Ubuntu/Debian:**
```bash
sudo dpkg -i neyrolock_3.0.0_amd64.deb
```

**Fedora/RHEL:**
```bash
sudo dnf install neyrolock-3.0.0-1.x86_64.rpm
```

**Universal:**
```bash
sudo bash NEYROLOCK-3.0.0-Linux-Installer.sh
```

## 📚 Documentation
- [Installation Guide](INSTALLATION_GUIDE.md)
- [Project Documentation](PROJECT_DOCUMENTATION.md)
- [Quick Start](QUICK_BUILD_GUIDE.md)

## 🐛 Known Issues
- Windows: First launch may trigger Windows Defender warning (click "Run anyway")
- macOS: Requires "Open" from context menu on first launch
- Linux: Some themes may have minor display issues

## 🆘 Support
- [GitHub Issues](https://github.com/neyrolock/neyrolock/issues)
- [Documentation](https://github.com/neyrolock/neyrolock)

## 📝 Checksums
See SHA256SUMS.txt for file integrity verification

## 🙏 Contributors
Thanks to everyone who contributed to this release!

---

**Full Changelog**: https://github.com/neyrolock/neyrolock/compare/v2.0.0...v3.0.0
```

## 5.2. Создание GitHub Release

### Через Web Interface (Рекомендуется):

1. **Откройте GitHub репозиторий:**
   - Перейдите на https://github.com/ВАШ_USERNAME/neyrolock

2. **Перейдите в Releases:**
   - Кликните на "Releases" (справа на главной странице)
   - Или перейдите на: https://github.com/ВАШ_USERNAME/neyrolock/releases

3. **Создайте новый релиз:**
   - Нажмите "Draft a new release"

4. **Заполните информацию:**
   - **Tag version:** Выберите `v3.0.0` (тег который вы создали)
   - **Release title:** `NEYROLOCK v3.0.0` или `NEYROLOCK v3.0.0 - Full Release`
   - **Description:** Скопируйте содержимое `RELEASE_NOTES_v3.0.0.md`

5. **Загрузите файлы:**

   Перетащите (drag & drop) файлы в область "Attach binaries":

   ```
   ✅ NEYROLOCK-3.0.0-Windows-Setup.exe
   ✅ NEYROLOCK-3.0.0-macOS.dmg
   ✅ neyrolock_3.0.0_amd64.deb
   ✅ neyrolock-3.0.0-1.x86_64.rpm
   ✅ NEYROLOCK-3.0.0-Linux-Installer.sh
   ✅ SHA256SUMS.txt
   ```

   **Дождитесь загрузки всех файлов** (может занять 5-30 минут)

6. **Настройте опции:**
   - [ ] This is a pre-release (НЕ отмечайте для стабильного релиза)
   - [x] Set as the latest release (Отметьте)
   - [x] Create a discussion for this release (Опционально)

7. **Публикуйте:**
   - Нажмите "Publish release"

### Через GitHub CLI (gh):

```bash
# Установите GitHub CLI (если нет)
# macOS: brew install gh
# Linux: см. https://github.com/cli/cli#installation
# Windows: см. https://github.com/cli/cli#installation

# Авторизуйтесь
gh auth login

# Создайте релиз
cd /path/to/neyrolock

gh release create v3.0.0 \
  --title "NEYROLOCK v3.0.0" \
  --notes-file RELEASE_NOTES_v3.0.0.md \
  installers/output/NEYROLOCK-3.0.0-Windows-Setup.exe \
  installers/output/NEYROLOCK-3.0.0-macOS.dmg \
  installers/output/neyrolock_3.0.0_amd64.deb \
  installers/output/neyrolock-3.0.0-1.x86_64.rpm \
  installers/output/NEYROLOCK-3.0.0-Linux-Installer.sh \
  installers/output/SHA256SUMS.txt

# Проверьте релиз
gh release view v3.0.0
```

## 5.3. После публикации

### Проверьте релиз:

1. **Откройте страницу релиза:**
   - https://github.com/ВАШ_USERNAME/neyrolock/releases/tag/v3.0.0

2. **Проверьте:**
   - ✅ Все файлы загружены и доступны
   - ✅ Размеры файлов корректны
   - ✅ Release notes отображаются правильно
   - ✅ Marked as "Latest release"
   - ✅ Ссылки для скачивания работают

3. **Протестируйте скачивание:**
   ```bash
   # Попробуйте скачать один из файлов
   wget https://github.com/ВАШ_USERNAME/neyrolock/releases/download/v3.0.0/SHA256SUMS.txt

   # Проверьте что скачалось
   cat SHA256SUMS.txt
   ```

### Обновите документацию:

1. **Обновите README.md:**
   - Добавьте badges (если нужно)
   - Обновите ссылки на latest release
   - Обновите инструкции по установке

2. **Обновите INSTALLATION_GUIDE.md:**
   - Замените placeholder ссылки на реальные
   - Например: `https://github.com/neyrolock/neyrolock/releases/download/v3.0.0/...`

3. **Закоммитьте изменения:**
   ```bash
   git add README.md INSTALLATION_GUIDE.md
   git commit -m "Update documentation with v3.0.0 release links"
   git push origin main
   ```

### Анонсируйте релиз:

1. **GitHub Discussions** (если включено):
   - Создайте пост в Announcements

2. **Социальные сети** (опционально):
   - Twitter/X
   - Reddit (r/selfhosted, r/LocalLLaMA, etc.)
   - Telegram каналы

3. **Email рассылка** (если есть):
   - Отправьте уведомление подписчикам

---

# 6. Публикация в магазинах приложений

## 6.1. Microsoft Store (Windows)

### Требования:
- Microsoft Developer Account ($19 единоразовый платеж)
- MSIX пакет (нужно пересобрать)
- Прохождение сертификации Microsoft

### Процесс:

1. **Зарегистрируйтесь:**
   - https://partner.microsoft.com/dashboard
   - Оплатите $19

2. **Конвертируйте в MSIX:**
   ```powershell
   # Используйте MSIX Packaging Tool
   # Или Desktop Bridge
   # Подробнее: https://docs.microsoft.com/en-us/windows/msix/
   ```

3. **Создайте submission:**
   - Partner Center → Apps and games → New product
   - Заполните все поля
   - Загрузите MSIX
   - Укажите описание, скриншоты, etc.

4. **Пройдите сертификацию:**
   - Обычно занимает 1-3 дня
   - Могут попросить исправить проблемы

5. **Публикуйте:**
   - После одобрения нажмите "Publish"

**Примерное время:** 1-2 недели

**Стоит ли:** Удобно для пользователей, но требует MSIX упаковки

## 6.2. Mac App Store (macOS)

### Требования:
- Apple Developer Program ($99/год)
- Code signing с Developer ID
- Notarization
- Sandbox требования
- Специфичная упаковка

### Процесс:

1. **Зарегистрируйтесь в Apple Developer Program:**
   - https://developer.apple.com/programs/
   - $99/год

2. **Подпишите приложение:**
   ```bash
   # Создайте сертификаты в Keychain
   # Подпишите приложение
   codesign --deep --force --verify --verbose \
     --sign "Developer ID Application: YOUR NAME" \
     NEYROLOCK.app
   ```

3. **Notarize приложение:**
   ```bash
   # Создайте DMG
   # Отправьте на notarization
   xcrun notarytool submit NEYROLOCK.dmg \
     --apple-id "your@email.com" \
     --password "app-specific-password" \
     --team-id "YOUR_TEAM_ID"

   # Дождитесь одобрения (10-30 минут)
   # Staple ticket
   xcrun stapler staple NEYROLOCK.dmg
   ```

4. **Создайте submission в App Store Connect:**
   - https://appstoreconnect.apple.com/
   - Заполните все поля
   - Загрузите через Xcode или Transporter
   - Добавьте скриншоты, описание

5. **Пройдите App Review:**
   - Обычно занимает 1-7 дней
   - Могут отклонить по разным причинам

**Примерное время:** 2-4 недели

**Стоит ли:** Удобно для пользователей, но строгие требования

**Альтернатива:** Homebrew Cask (см. ниже)

## 6.3. Snap Store (Linux)

### Простой способ дистрибуции для Linux!

### Требования:
- Ubuntu One account (бесплатно)
- Snapcraft

### Процесс:

1. **Зарегистрируйтесь:**
   - https://snapcraft.io/
   - Используйте Ubuntu One account

2. **Создайте snapcraft.yaml:**

```yaml
name: neyrolock
version: '3.0.0'
summary: Local AI Models Desktop Application
description: |
  NEYROLOCK is a desktop application for working with local AI models.
  Features include GUI interface, Telegram bot integration, and model management.

base: core22
confinement: strict
grade: stable

apps:
  neyrolock:
    command: bin/NEYROLOCK
    plugs:
      - home
      - network
      - desktop
      - desktop-legacy
      - wayland
      - x11

parts:
  neyrolock:
    plugin: dump
    source: installers/pyinstaller/dist/NEYROLOCK/
    stage-packages:
      - python3
      - python3-tk
```

3. **Соберите snap:**
   ```bash
   # Установите snapcraft
   sudo snap install snapcraft --classic

   # Соберите
   snapcraft

   # Тестируйте
   sudo snap install neyrolock_3.0.0_amd64.snap --dangerous
   ```

4. **Загрузите:**
   ```bash
   # Авторизуйтесь
   snapcraft login

   # Загрузите
   snapcraft upload neyrolock_3.0.0_amd64.snap

   # Релиз
   snapcraft release neyrolock 3.0.0 stable
   ```

**Примерное время:** 1-2 дня

**Стоит ли:** ДА! Очень просто и покрывает много дистрибутивов

## 6.4. Flathub (Linux)

### Еще один способ для Linux

### Требования:
- GitHub account
- Flathub submission

### Процесс:

1. **Создайте manifest:**
   - Создайте `ai.neyrolock.NEYROLOCK.json`
   - См. примеры на https://github.com/flathub/flathub

2. **Создайте PR в Flathub:**
   - Fork https://github.com/flathub/flathub
   - Добавьте ваш manifest
   - Создайте Pull Request

3. **Пройдите review:**
   - Maintainers проверят ваш PR
   - Могут попросить исправления

4. **После merge:**
   - Приложение автоматически появится в Flathub

**Примерное время:** 1-2 недели

**Стоит ли:** ДА! Flathub очень популярен

## 6.5. Homebrew (macOS/Linux)

### Популярный пакетный менеджер

### Процесс:

1. **Создайте tap (свой репозиторий формул):**
   ```bash
   # Создайте репозиторий на GitHub: homebrew-neyrolock
   # Клонируйте его
   git clone https://github.com/ВАШ_USERNAME/homebrew-neyrolock
   cd homebrew-neyrolock
   ```

2. **Создайте формулу:**

   `neyrolock.rb`:
   ```ruby
   class Neyrolock < Formula
     desc "Local AI Models Desktop Application"
     homepage "https://github.com/neyrolock/neyrolock"
     url "https://github.com/neyrolock/neyrolock/releases/download/v3.0.0/NEYROLOCK-3.0.0-macOS.dmg"
     sha256 "ВАШ_SHA256_HASH"
     version "3.0.0"

     def install
       prefix.install Dir["*"]
       bin.install_symlink prefix/"NEYROLOCK.app/Contents/MacOS/NEYROLOCK" => "neyrolock"
     end

     def caveats
       <<~EOS
         NEYROLOCK has been installed.
         Run 'neyrolock' to start the application.
       EOS
     end
   end
   ```

3. **Закоммитьте и загрузите:**
   ```bash
   git add neyrolock.rb
   git commit -m "Add NEYROLOCK formula"
   git push origin main
   ```

4. **Теперь пользователи могут установить:**
   ```bash
   brew tap ВАШ_USERNAME/neyrolock
   brew install neyrolock
   ```

5. **Опционально: Добавьте в основной Homebrew:**
   - Создайте PR в https://github.com/Homebrew/homebrew-cask
   - Требует популярности и качества

**Примерное время:** 1 день для tap, недели для основного Homebrew

**Стоит ли:** ДА! Очень популярно среди разработчиков

## 6.6. AUR (Arch Linux)

### Для пользователей Arch Linux

### Процесс:

1. **Создайте PKGBUILD:**
   ```bash
   # PKGBUILD файл
   pkgname=neyrolock
   pkgver=3.0.0
   pkgrel=1
   pkgdesc="Local AI Models Desktop Application"
   arch=('x86_64')
   url="https://github.com/neyrolock/neyrolock"
   license=('MIT')
   depends=('python' 'tk')
   source=("https://github.com/neyrolock/neyrolock/releases/download/v${pkgver}/NEYROLOCK-${pkgver}-Linux-Installer.sh")
   sha256sums=('YOUR_SHA256')

   package() {
     # Installation logic
   }
   ```

2. **Загрузите в AUR:**
   ```bash
   # Клонируйте AUR репозиторий
   git clone ssh://aur@aur.archlinux.org/neyrolock.git
   cd neyrolock

   # Добавьте PKGBUILD
   cp PKGBUILD PKGBUILD.template

   # Создайте .SRCINFO
   makepkg --printsrcinfo > .SRCINFO

   # Загрузите
   git add PKGBUILD .SRCINFO
   git commit -m "Initial commit of NEYROLOCK"
   git push
   ```

3. **Пользователи установят через AUR helper:**
   ```bash
   yay -S neyrolock
   # или
   paru -S neyrolock
   ```

**Примерное время:** 1-2 часа

**Стоит ли:** ДА! Arch пользователи ожидают пакеты в AUR

---

# 7. Code Signing и Notarization

## 7.1. Windows Code Signing

### Зачем нужно:
- Убирает предупреждения Windows Defender
- Повышает доверие пользователей
- Требуется для Microsoft Store

### Получение сертификата:

1. **Купите сертификат:**
   - DigiCert: ~$400/год
   - Sectigo: ~$200/год
   - GlobalSign: ~$250/год

2. **Для EV сертификата:**
   - Требуется физическая USB токен
   - Более строгая верификация
   - Дороже (~$500/год)
   - Убирает SmartScreen warnings сразу

3. **Установите сертификат:**
   - Следуйте инструкциям провайдера
   - Импортируйте в Windows Certificate Store

### Подписание:

```powershell
# Найдите signtool.exe (из Windows SDK)
# Обычно: C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe

# Подпишите EXE
signtool sign /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 /a NEYROLOCK-3.0.0-Windows-Setup.exe

# Проверьте подпись
signtool verify /pa NEYROLOCK-3.0.0-Windows-Setup.exe
```

### Примечание о SmartScreen:

- Даже с подписью, новые приложения будут блокироваться SmartScreen
- Нужна "репутация" (много загрузок/установок)
- EV сертификат помогает, но не полностью решает проблему
- Со временем (недели/месяцы) репутация растет

## 7.2. macOS Code Signing и Notarization

### Зачем нужно:
- Убирает предупреждения Gatekeeper
- Требуется для App Store
- Показывает профессионализм

### Требования:
- Apple Developer Program ($99/год)
- Xcode или Command Line Tools

### Процесс:

1. **Получите сертификаты:**
   ```bash
   # Войдите в Xcode с вашим Apple ID
   # Xcode → Preferences → Accounts → Manage Certificates
   # Или создайте через:
   https://developer.apple.com/account/resources/certificates/list
   ```

2. **Подпишите приложение:**
   ```bash
   # Найдите ваш сертификат
   security find-identity -v -p codesigning

   # Подпишите
   codesign --deep --force --verify --verbose \
     --sign "Developer ID Application: YOUR NAME (TEAM_ID)" \
     --options runtime \
     --timestamp \
     NEYROLOCK.app

   # Проверьте
   codesign -dv --verbose=4 NEYROLOCK.app
   spctl -a -vv NEYROLOCK.app
   ```

3. **Создайте DMG:**
   ```bash
   # Используйте create-dmg или hdiutil
   create-dmg \
     --volname "NEYROLOCK" \
     --window-size 800 400 \
     --app-drop-link 600 185 \
     NEYROLOCK-3.0.0-macOS.dmg \
     NEYROLOCK.app

   # Подпишите DMG
   codesign --sign "Developer ID Application: YOUR NAME (TEAM_ID)" \
     NEYROLOCK-3.0.0-macOS.dmg
   ```

4. **Notarize:**
   ```bash
   # Создайте app-specific password
   # https://appleid.apple.com/account/manage → App-Specific Passwords

   # Отправьте на notarization
   xcrun notarytool submit NEYROLOCK-3.0.0-macOS.dmg \
     --apple-id "your@email.com" \
     --password "xxxx-xxxx-xxxx-xxxx" \
     --team-id "YOUR_TEAM_ID" \
     --wait

   # После успеха, staple ticket
   xcrun stapler staple NEYROLOCK-3.0.0-macOS.dmg

   # Проверьте
   xcrun stapler validate NEYROLOCK-3.0.0-macOS.dmg
   ```

5. **Проверьте финальный DMG:**
   ```bash
   spctl -a -vv -t install NEYROLOCK-3.0.0-macOS.dmg
   # Должно показать: accepted
   ```

### Troubleshooting:

- Если notarization fails, проверьте логи:
  ```bash
  xcrun notarytool log SUBMISSION_ID \
    --apple-id "your@email.com" \
    --password "xxxx-xxxx-xxxx-xxxx" \
    --team-id "YOUR_TEAM_ID"
  ```

- Распространенные проблемы:
  - Hardened Runtime не включен
  - Неправильные entitlements
  - Неподписанные библиотеки

---

# 8. CI/CD Автоматизация

## 8.1. GitHub Actions

### Автоматическая сборка на всех платформах

**Создайте `.github/workflows/build-installers.yml`:**

```yaml
name: Build Installers

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyinstaller
          pip install -r requirements_ai_cli.txt

      - name: Build with PyInstaller
        run: |
          cd installers/pyinstaller
          pyinstaller neyrolock_gui.spec --clean --noconfirm

      - name: Install Inno Setup
        run: choco install innosetup -y

      - name: Build installer
        run: |
          cd installers/windows
          & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" neyrolock_setup.iss

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: windows-installer
          path: installers/output/*.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip3 install pyinstaller
          pip3 install -r requirements_ai_cli.txt
          CMAKE_ARGS="-DLLAMA_METAL=on" pip3 install llama-cpp-python --no-cache-dir

      - name: Install create-dmg
        run: brew install create-dmg

      - name: Build
        run: |
          cd installers/macos
          bash build_macos.sh

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: macos-installer
          path: installers/output/*.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y python3-tk rpm

      - name: Install Python dependencies
        run: |
          pip3 install pyinstaller
          pip3 install -r requirements_ai_cli.txt

      - name: Build
        run: |
          cd installers/linux
          bash build_linux.sh

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: linux-installers
          path: |
            installers/output/*.deb
            installers/output/*.rpm
            installers/output/*.sh

  create-release:
    needs: [build-windows, build-macos, build-linux]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')

    steps:
      - uses: actions/checkout@v3

      - name: Download all artifacts
        uses: actions/download-artifact@v3

      - name: Create checksums
        run: |
          cd windows-installer
          sha256sum * > SHA256SUMS.txt
          cd ../macos-installer
          sha256sum * >> SHA256SUMS.txt
          cd ../linux-installers
          sha256sum * >> SHA256SUMS.txt

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            windows-installer/*
            macos-installer/*
            linux-installers/*
            */SHA256SUMS.txt
          body_path: RELEASE_NOTES_${{ github.ref_name }}.md
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Использование:

```bash
# Создайте тег
git tag v3.0.0
git push origin v3.0.0

# GitHub Actions автоматически:
# 1. Соберет на Windows, macOS, Linux
# 2. Создаст релиз
# 3. Загрузит все файлы
```

---

# 9. Чек-листы

## 9.1. Чек-лист перед релизом

**Код и версия:**
- [ ] Все изменения закоммичены
- [ ] Версия обновлена везде (setup.py, .spec, .iss, и т.д.)
- [ ] Тесты проходят (если есть)
- [ ] Нет TODO или FIXME в критичных местах
- [ ] Changelog/Release notes подготовлены

**Документация:**
- [ ] README.md обновлен
- [ ] INSTALLATION_GUIDE.md обновлен
- [ ] Все ссылки работают
- [ ] Скриншоты актуальны

**Иконки и ресурсы:**
- [ ] Иконки созданы (или placeholder готов)
- [ ] Все файлы на месте в assets/
- [ ] Лицензии на ресурсы проверены

**Сборка:**
- [ ] Windows установщик собран
- [ ] macOS DMG собран
- [ ] Linux .deb собран
- [ ] Linux .rpm собран (опционально)
- [ ] Linux universal installer собран
- [ ] Контрольные суммы созданы

## 9.2. Чек-лист тестирования Windows

**Установка:**
- [ ] Установщик запускается
- [ ] Прогресс отображается корректно
- [ ] Выбор директории работает
- [ ] Ярлыки создаются
- [ ] Регистрация в системе работает
- [ ] Установка завершается успешно

**Первый запуск:**
- [ ] Приложение запускается
- [ ] GUI отображается корректно
- [ ] Нет критических ошибок
- [ ] Создаются файлы конфигурации

**Функциональность:**
- [ ] Все элементы GUI работают
- [ ] Настройки сохраняются
- [ ] Скачивание моделей работает
- [ ] Генерация текста работает
- [ ] История сохраняется

**Производительность:**
- [ ] Нормальное потребление CPU/RAM
- [ ] Нет утечек памяти
- [ ] Отзывчивый интерфейс

**Удаление:**
- [ ] Удаление работает без ошибок
- [ ] Файлы удаляются
- [ ] Регистрация очищается

**Дополнительно:**
- [ ] Протестировано на Windows 10
- [ ] Протестировано на Windows 11
- [ ] Разные разрешения экрана
- [ ] Разные DPI настройки

## 9.3. Чек-лист тестирования macOS

**Установка:**
- [ ] DMG монтируется
- [ ] Drag & Drop работает
- [ ] Копирование в Applications успешно

**Gatekeeper:**
- [ ] Первый запуск через "Open" работает
- [ ] Или quarantine успешно снимается
- [ ] Нет ошибок "damaged"

**Функциональность:**
- [ ] Все базовые функции работают
- [ ] Cmd клавиши работают
- [ ] Интеграция с Launchpad
- [ ] Интеграция с Spotlight
- [ ] Dock интеграция

**Metal (Apple Silicon):**
- [ ] Metal ускорение активно
- [ ] Быстрая генерация
- [ ] GPU показывает активность

**Дополнительно:**
- [ ] Протестировано на Apple Silicon
- [ ] Протестировано на Intel Mac
- [ ] Разные версии macOS

## 9.4. Чек-лист тестирования Linux

**Установка (.deb):**
- [ ] Пакет устанавливается
- [ ] Зависимости разрешаются
- [ ] Desktop entry создается
- [ ] Символическая ссылка работает

**Установка (.rpm):**
- [ ] Пакет устанавливается
- [ ] Зависимости разрешаются

**Universal installer:**
- [ ] Установщик запускается
- [ ] Файлы извлекаются корректно
- [ ] Символическая ссылка создается

**Функциональность:**
- [ ] Запуск из GUI меню
- [ ] Запуск из terminal
- [ ] Все функции работают

**Desktop окружения:**
- [ ] GNOME
- [ ] KDE Plasma
- [ ] XFCE
- [ ] Другие (опционально)

**Дистрибутивы:**
- [ ] Ubuntu 22.04
- [ ] Ubuntu 24.04
- [ ] Fedora
- [ ] Другие (опционально)

**Удаление:**
- [ ] apt/dnf remove работает
- [ ] Файлы удаляются

## 9.5. Чек-лист публикации

**GitHub:**
- [ ] Тег создан и загружен
- [ ] Release создан
- [ ] Все файлы загружены
- [ ] Release notes заполнены
- [ ] Marked as latest release
- [ ] Ссылки работают

**Документация:**
- [ ] README обновлен с ссылками на релиз
- [ ] INSTALLATION_GUIDE обновлен
- [ ] Все ссылки протестированы

**Анонсирование:**
- [ ] GitHub Discussions/Announcement
- [ ] Социальные сети (опционально)
- [ ] Email (опционально)

**Магазины (опционально):**
- [ ] Microsoft Store
- [ ] Mac App Store
- [ ] Snap Store
- [ ] Flathub
- [ ] Homebrew
- [ ] AUR

---

# 10. Заключение

## Итоговый процесс:

1. ✅ **Подготовка** (1 день)
   - Обновите версии
   - Создайте иконки
   - Подготовьте release notes

2. ✅ **Сборка** (1-2 часа)
   - Соберите на Windows
   - Соберите на macOS
   - Соберите на Linux
   - Создайте контрольные суммы

3. ✅ **Тестирование** (2-5 дней)
   - Тестируйте на Windows (все версии)
   - Тестируйте на macOS (Intel и ARM)
   - Тестируйте на Linux (разные дистрибутивы)
   - Исправьте найденные проблемы

4. ✅ **Публикация на GitHub** (1 час)
   - Создайте тег
   - Создайте release
   - Загрузите файлы
   - Обновите документацию

5. ✅ **Публикация в магазинах** (опционально, 1-4 недели)
   - Snap Store (просто)
   - Homebrew (средне)
   - App Stores (сложно)

6. ✅ **Code Signing** (опционально, зависит от бюджета)
   - Windows ($200-500/год)
   - macOS ($99/год)

7. ✅ **Анонсирование** (1 день)
   - GitHub
   - Социальные сети
   - Email

## Временные затраты:

| Задача | Первый раз | Последующие релизы |
|--------|------------|-------------------|
| Подготовка | 1 день | 2-4 часа |
| Сборка | 2-4 часа | 1 час |
| Тестирование | 3-7 дней | 1-2 дня |
| Публикация GitHub | 2 часа | 30 минут |
| Магазины приложений | 2-4 недели | 1-2 дня |
| **TOTAL** | **1-2 месяца** | **2-5 дней** |

## Рекомендации:

**Для первого релиза:**
1. ✅ Фокус на GitHub Releases
2. ✅ Тщательное тестирование
3. ❌ Не усложняйте с App Stores
4. ❌ Code signing опционально

**Для последующих релизов:**
1. ✅ Автоматизируйте через CI/CD
2. ✅ Используйте чек-листы
3. ✅ Добавляйте магазины постепенно
4. ✅ Собирайте feedback от пользователей

---

**Удачи с релизом NEYROLOCK! 🚀**

Если возникнут вопросы, создайте issue на GitHub или обратитесь к документации.
