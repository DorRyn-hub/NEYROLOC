# 📦 NEYROLOCK - Система Установщиков

## ✅ Что было создано

Была создана полная система установщиков для NEYROLOCK, которая позволяет легко устанавливать приложение на **Windows, macOS и Linux**.

---

## 📂 Структура созданных файлов

```
NEYROLOCK/
│
├── setup_neyrolock.py              # Python setup script для pip установки
├── build_installer.sh              # Универсальный скрипт сборки (авто-определение ОС)
│
├── INSTALLATION_GUIDE.md           # Полное руководство по установке
├── INSTALLER_SUMMARY.md            # Этот файл - краткое описание
│
├── installers/                     # Директория установщиков
│   ├── README.md                   # Документация для разработчиков
│   ├── output/                     # Выходная директория (создается автоматически)
│   │
│   ├── pyinstaller/                # PyInstaller спецификации
│   │   ├── neyrolock_gui.spec      # Спецификация для GUI
│   │   └── neyrolock_cli.spec      # Спецификация для CLI
│   │
│   ├── windows/                    # Windows установщик
│   │   ├── build_windows.bat       # Скрипт сборки
│   │   └── neyrolock_setup.iss     # Inno Setup конфигурация
│   │
│   ├── macos/                      # macOS установщик
│   │   └── build_macos.sh          # Скрипт сборки (.app + .dmg)
│   │
│   └── linux/                      # Linux установщики
│       └── build_linux.sh          # Скрипт сборки (.deb, .rpm, .sh)
│
└── assets/                         # Ресурсы (иконки)
    └── README.md                   # Инструкции по созданию иконок
```

---

## 🎯 Поддерживаемые форматы установщиков

### 🪟 Windows
- **NEYROLOCK-3.0.0-Windows-Setup.exe** (Inno Setup)
  - ✅ Полноценный GUI установщик
  - ✅ Автоматическая установка в Program Files
  - ✅ Создание ярлыков (Desktop, Start Menu)
  - ✅ Регистрация в системе
  - ✅ Удаление через "Programs and Features"
  - ✅ Поддержка русского языка

### 🍎 macOS
- **NEYROLOCK.app** (Application Bundle)
  - ✅ Native macOS приложение
  - ✅ Поддержка Apple Silicon (M1/M2/M3) с Metal
  - ✅ Совместимость с Intel Mac
  - ✅ Standalone (все зависимости включены)

- **NEYROLOCK-3.0.0-macOS.dmg** (Disk Image)
  - ✅ Красивый drag & drop интерфейс
  - ✅ Ссылка на Applications
  - ✅ Удобная установка

### 🐧 Linux

- **neyrolock_3.0.0_amd64.deb** (Debian/Ubuntu)
  - ✅ Установка через dpkg/apt
  - ✅ Автоматические зависимости
  - ✅ Desktop entry и иконки
  - ✅ Удаление через apt remove

- **neyrolock-3.0.0-1.x86_64.rpm** (Fedora/RedHat/CentOS)
  - ✅ Установка через rpm/dnf/yum
  - ✅ Автоматические зависимости
  - ✅ Desktop entry и иконки
  - ✅ Удаление через dnf remove

- **NEYROLOCK-3.0.0-Linux-Installer.sh** (Universal)
  - ✅ Работает на любом Linux
  - ✅ Self-extracting installer
  - ✅ Не требует системы пакетов
  - ✅ Простая установка: `sudo bash installer.sh`

---

## 🚀 Как использовать

### Для пользователей

**1. Скачайте установщик для вашей ОС:**
   - Windows: `NEYROLOCK-3.0.0-Windows-Setup.exe`
   - macOS: `NEYROLOCK-3.0.0-macOS.dmg`
   - Linux: `neyrolock_3.0.0_amd64.deb` или другой формат

**2. Установите:**
   - Windows: Двойной клик → Следуйте инструкциям
   - macOS: Откройте DMG → Перетащите в Applications
   - Linux: `sudo dpkg -i neyrolock_3.0.0_amd64.deb`

**3. Запустите:**
   - Windows: Меню Пуск → NEYROLOCK
   - macOS: Applications → NEYROLOCK
   - Linux: Меню приложений → NEYROLOCK или команда `neyrolock`

**Подробные инструкции:** См. [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)

### Для разработчиков

**Сборка установщиков:**

```bash
# Автоматическая сборка (определяет ОС)
bash build_installer.sh

# Или вручную для конкретной ОС:
bash installers/windows/build_windows.bat  # Windows
bash installers/macos/build_macos.sh       # macOS
bash installers/linux/build_linux.sh       # Linux
```

**Результат:**
Все установщики будут в `installers/output/`

**Подробные инструкции:** См. [installers/README.md](installers/README.md)

---

## 🔧 Требования для сборки

### Все платформы:
- Python 3.10+
- PyInstaller (`pip install pyinstaller`)
- Зависимости проекта (`pip install -r requirements_ai_cli.txt`)

### Windows дополнительно:
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (опционально, для .exe установщика)

### macOS дополнительно:
- create-dmg (`brew install create-dmg`) - опционально, для .dmg файла

### Linux дополнительно:
- dpkg-deb (предустановлен на Debian/Ubuntu)
- rpmbuild (опционально, для .rpm пакетов)

---

## 📦 Форматы дистрибуции

### 1. Standalone Executables (PyInstaller)
**Описание:** Независимые исполняемые файлы со всеми зависимостями

**Плюсы:**
- ✅ Не требует установки Python
- ✅ Все зависимости включены
- ✅ Работает на чистой системе
- ✅ Один файл/папка

**Минусы:**
- ❌ Большой размер (~200-500 MB)
- ❌ Медленный первый запуск

**Использование:**
- Windows: `.exe` файл
- macOS: `.app` bundle
- Linux: Исполняемый файл

### 2. System Packages (Native Installers)
**Описание:** Нативные системные пакеты

**Плюсы:**
- ✅ Интеграция с системой
- ✅ Автоматическое управление зависимостями
- ✅ Легкое удаление
- ✅ Desktop shortcuts/entries

**Минусы:**
- ❌ Требует права администратора
- ❌ Специфичны для платформы

**Использование:**
- Windows: `.exe` установщик (Inno Setup)
- macOS: `.dmg` disk image
- Linux: `.deb`, `.rpm` пакеты

### 3. Python Package (pip)
**Описание:** Установка через pip/setuptools

**Плюсы:**
- ✅ Маленький размер
- ✅ Легко обновлять
- ✅ Для разработчиков

**Минусы:**
- ❌ Требует Python
- ❌ Требует установку зависимостей
- ❌ Не для обычных пользователей

**Использование:**
```bash
pip install neyrolock
# или
python setup_neyrolock.py install
```

---

## 🎨 Иконки приложения

**Статус:** Не включены (опционально)

Установщики работают без иконок, но вы можете добавить их:

1. Создайте иконки:
   - `assets/icon.png` (256x256) для Linux
   - `assets/icon.ico` (multi-size) для Windows
   - `assets/icon.icns` (multi-size) для macOS

2. См. инструкции: [assets/README.md](assets/README.md)

3. Пересоберите установщики

**Без иконок:**
- Windows: Используется default Python иконка
- macOS: Используется generic app иконка
- Linux: Используется default иконка приложения

---

## 🧪 Тестирование установщиков

### Чек-лист перед релизом:

**Windows:**
- [ ] Установщик запускается
- [ ] Установка в Program Files работает
- [ ] Ярлыки создаются (Desktop, Start Menu)
- [ ] Приложение запускается
- [ ] Удаление работает корректно
- [ ] Нет ошибок в Event Viewer

**macOS:**
- [ ] DMG открывается
- [ ] Drag & Drop в Applications работает
- [ ] Приложение запускается (с обходом Gatekeeper)
- [ ] Нет предупреждений безопасности после разрешения
- [ ] Apple Silicon: Metal ускорение работает
- [ ] Intel Mac: Приложение работает

**Linux:**
- [ ] .deb устанавливается без ошибок
- [ ] .rpm устанавливается без ошибок (если собран)
- [ ] Universal installer работает
- [ ] Desktop entry появляется
- [ ] Приложение запускается из меню и команды
- [ ] Удаление работает корректно

**Функциональность:**
- [ ] GUI запускается
- [ ] Можно скачать модель с HuggingFace
- [ ] Можно загрузить локальную модель
- [ ] Генерация текста работает
- [ ] Настройки сохраняются
- [ ] История чатов сохраняется

---

## 📋 Следующие шаги

### Для финального релиза:

1. **Создайте иконки приложения**
   - См. [assets/README.md](assets/README.md)
   - Или используйте placeholder иконки

2. **Соберите установщики**
   ```bash
   bash build_installer.sh
   ```

3. **Протестируйте на чистых системах**
   - Windows 10/11
   - macOS (Intel и Apple Silicon)
   - Ubuntu/Debian, Fedora

4. **Создайте GitHub Release**
   ```bash
   git tag v3.0.0
   git push origin v3.0.0
   ```

5. **Загрузите установщики**
   - Перейдите на GitHub Releases
   - Создайте новый релиз
   - Загрузите все файлы из `installers/output/`
   - Добавьте release notes

6. **Обновите документацию**
   - Обновите ссылки в README.md
   - Обновите ссылки в INSTALLATION_GUIDE.md
   - Добавьте скриншоты установки

### Опционально (для профессионального релиза):

**Windows:**
- Code signing (требует сертификат ~$100-500/год)
- Публикация в Microsoft Store

**macOS:**
- Code signing с Apple Developer certificate ($99/год)
- Notarization (требование Apple)
- Публикация в Mac App Store (опционально)

**Linux:**
- Публикация в Snap Store
- Публикация в Flathub
- Добавление в репозитории дистрибутивов

---

## 📊 Сравнение установщиков

| Критерий | Windows | macOS | Linux (.deb) | Linux (.rpm) | Universal |
|----------|---------|-------|--------------|--------------|-----------|
| Размер | ~300 MB | ~300 MB | ~300 MB | ~300 MB | ~300 MB |
| Требует admin | Да | Да | Да | Да | Да |
| GUI установка | Да | Нет (drag&drop) | Нет | Нет | Нет |
| Auto-update | Нет* | Нет* | Через apt | Через dnf | Нет |
| Desktop icon | Да | Да | Да | Да | Да |
| System integration | Полная | Полная | Полная | Полная | Частичная |

*Auto-update можно добавить через дополнительные инструменты (Squirrel, Sparkle)

---

## 🆘 Получение помощи

**Проблемы со сборкой:**
- См. [installers/README.md](installers/README.md) - раздел "Решение проблем"
- Откройте issue на GitHub

**Проблемы с установкой:**
- См. [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - раздел "Решение Проблем"
- Проверьте системные требования

**Вопросы:**
- GitHub Discussions
- GitHub Issues
- Email: team@neyrolock.ai

---

## 📝 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

## 🎉 Заключение

Система установщиков NEYROLOCK готова к использованию!

**Что вы получили:**
- ✅ Полноценные установщики для Windows, macOS и Linux
- ✅ Автоматические скрипты сборки
- ✅ Полную документацию
- ✅ Поддержку всех популярных форматов пакетов
- ✅ Готовую инфраструктуру для релизов

**Что делать дальше:**
1. Добавьте иконки (опционально)
2. Соберите установщики
3. Протестируйте на целевых системах
4. Создайте релиз на GitHub
5. Поделитесь с миром!

**Удачи с релизом NEYROLOCK! 🚀**
