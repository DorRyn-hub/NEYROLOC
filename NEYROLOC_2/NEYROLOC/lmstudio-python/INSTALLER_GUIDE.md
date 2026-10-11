# 📦 Руководство по установщикам NEYROLOCK

Это руководство объясняет, как собрать и использовать установщики NEYROLOCK для Windows, macOS и Linux.

## 🎯 Что включено

Установщики NEYROLOCK созданы для **простого распространения** приложения:

✅ **Скрытие исходного кода** - весь код упакован в исполняемый файл
✅ **Красивая иконка** - пользователи видят только иконку программы
✅ **Прогресс установки** - детальный прогресс-бар на каждом шаге
✅ **Автоматическая установка** - установка в один клик
✅ **Поддержка всех ОС** - Windows, macOS, Linux

---

## 🚀 Быстрый старт

### Универсальная сборка (рекомендуется)

```bash
# Автоматически определяет вашу ОС и собирает установщик
bash build_installer.sh
```

Скрипт автоматически:
1. Определит вашу операционную систему
2. Проверит зависимости
3. Соберет установщик с прогресс-баром
4. Создаст готовый к распространению файл

---

## 📋 Системные требования

### Для сборки установщиков:

**Все платформы:**
- Python 3.10 или выше
- PyInstaller (устанавливается автоматически)

**Windows:**
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (опционально, для .exe установщика)

**macOS:**
- Xcode Command Line Tools
- `create-dmg` (устанавливается через Homebrew, опционально)

**Linux:**
- `dpkg-deb` (для .deb пакетов)
- `rpmbuild` (для .rpm пакетов, опционально)

---

## 🪟 Windows

### Сборка установщика

```batch
cd installers\windows
build_windows.bat
```

#### Что происходит при сборке:

```
[1/5] Проверка зависимостей...
      ✓ Python найден
      ✓ PyInstaller готов

[2/5] Очистка старых сборок...
      ✓ Очистка завершена

[3/5] Сборка приложения с PyInstaller...
      Это может занять несколько минут...
      ✓ PyInstaller завершил сборку

[4/5] Проверка наличия Inno Setup...
      ✓ Inno Setup найден

[5/5] Создание установщика с Inno Setup...
      ✓ Установщик создан!
```

### Результат:

```
installers/output/NEYROLOCK-3.0.0-Windows-Setup.exe
```

### Установка для пользователей:

1. Запустить `NEYROLOCK-3.0.0-Windows-Setup.exe`
2. Следовать инструкциям установщика
3. Программа появится в меню "Пуск" и на рабочем столе (опционально)

### Удаление:

- Через "Параметры" → "Приложения"
- Или через "Панель управления" → "Программы и компоненты"

---

## 🍎 macOS

### Сборка установщика

```bash
cd installers/macos
bash build_macos.sh
```

#### Что происходит при сборке:

```
[1/6] Проверка зависимостей...
      ✓ Python 3.11.5 найден
      ✓ PyInstaller готов
      ✓ Обнаружен Apple Silicon (arm64)

[2/6] Очистка старых сборок...
      ✓ Очистка завершена

[3/6] Установка зависимостей...
      ✓ Зависимости установлены

[4/6] Сборка .app bundle с PyInstaller...
      Это может занять несколько минут...
      ✓ PyInstaller завершил сборку
      ✓ .app bundle создан

[5/6] Создание DMG установщика...
      ✓ DMG создан

[6/6] Проверка результатов...
      ✓ App bundle: 250M
      ✓ DMG installer: 180M

✨ Сборка завершена успешно! ✨
```

### Результат:

```
installers/output/NEYROLOCK.app          # Приложение
installers/output/NEYROLOCK-3.0.0-macOS.dmg  # DMG установщик
```

### Установка для пользователей:

**Способ 1: Из DMG (рекомендуется)**
1. Открыть `NEYROLOCK-3.0.0-macOS.dmg`
2. Перетащить `NEYROLOCK.app` в папку `Applications`
3. Готово!

**Способ 2: Прямая копия**
1. Скопировать `NEYROLOCK.app` в папку `Applications`
2. Готово!

### Удаление:

Просто переместить `NEYROLOCK.app` в корзину

### Подпись кода (для распространения):

```bash
# Подпись приложения
codesign --deep --force --sign "Developer ID" \
  installers/output/NEYROLOCK.app

# Нотаризация (требуется Apple Developer аккаунт)
xcrun altool --notarize-app \
  --file NEYROLOCK-3.0.0-macOS.dmg \
  --primary-bundle-id "ai.neyrolock.desktop"
```

---

## 🐧 Linux

### Сборка установщиков

```bash
cd installers/linux
bash build_linux.sh
```

#### Что происходит при сборке:

```
[1/7] Проверка зависимостей...
      ✓ Python 3.10.12 найден
      ✓ PyInstaller готов
      ✓ dpkg-deb найден

[2/7] Очистка старых сборок...
      ✓ Очистка завершена

[3/7] Установка зависимостей...
      ✓ Зависимости установлены

[4/7] Сборка приложения с PyInstaller...
      ✓ PyInstaller завершил сборку

[5/7] Создание .deb пакета (Debian/Ubuntu)...
      ℹ Копирование файлов приложения...
      ℹ Создание метаданных пакета...
      ℹ Сборка .deb пакета...
      ✓ .deb пакет создан (120M)

[6/7] Создание .rpm пакета (Fedora/RedHat)...
      ✓ .rpm пакет создан (115M)

[7/7] Создание универсального установщика...
      ✓ Универсальный установщик создан (125M)

✨ Сборка завершена успешно! ✨
```

### Результат:

```
installers/output/neyrolock_3.0.0_amd64.deb          # Debian/Ubuntu
installers/output/neyrolock-3.0.0-1.x86_64.rpm       # Fedora/RedHat
installers/output/NEYROLOCK-3.0.0-Linux-Installer.sh # Универсальный
```

### Установка для пользователей:

**Debian/Ubuntu (.deb):**
```bash
sudo dpkg -i neyrolock_3.0.0_amd64.deb
sudo apt-get install -f  # Установить зависимости, если нужно
```

**Fedora/RedHat/CentOS (.rpm):**
```bash
sudo rpm -i neyrolock-3.0.0-1.x86_64.rpm
```

**Универсальный установщик (любой Linux):**
```bash
sudo bash NEYROLOCK-3.0.0-Linux-Installer.sh
```

#### Прогресс универсального установщика:

```
======================================
   NEYROLOCK Installer v3.0.0
======================================

[1/4] Подготовка к установке...
[2/4] Распаковка файлов приложения...
[3/4] Создание системных ссылок...
[4/4] Регистрация в системе...

======================================
✓ Установка завершена успешно!
======================================

Запустите 'neyrolock' в терминале
или найдите в меню приложений
```

### Запуск:

```bash
neyrolock  # Из терминала
```

Или найти в меню приложений

### Удаление:

**Debian/Ubuntu:**
```bash
sudo apt remove neyrolock
```

**Fedora/RedHat/CentOS:**
```bash
sudo rpm -e neyrolock
```

**Универсальный установщик:**
```bash
sudo rm -rf /opt/neyrolock
sudo rm -f /usr/local/bin/neyrolock
sudo rm -f /usr/share/applications/neyrolock.desktop
```

---

## 🎨 Иконки

Все установщики используют иконку из `assets/`:

- **Windows**: `assets/icon.ico` (78 KB, 256×256)
- **macOS**: `assets/icon.icns` (2 MB, multiple sizes)
- **Linux**: `assets/icon_256x256.png` (56 KB, 256×256)

### Создание иконок:

Если вы хотите изменить иконку:

```bash
# 1. Поместите новую иконку (PNG, ≥512×512) в:
assets/icon.png

# 2. Запустите скрипт конвертации:
python3 create_icons.py

# 3. Иконки для всех платформ будут созданы автоматически
```

---

## 📝 Настройка

### Изменение версии:

Обновите версию в следующих файлах:

1. `setup_neyrolock.py` (строка 14)
2. `installers/windows/neyrolock_setup.iss` (строка 5)
3. `installers/macos/build_macos.sh` (строка 143)
4. `installers/linux/build_linux.sh` (строки 124, 213, 279)
5. `installers/pyinstaller/neyrolock_gui.spec` (строка 105)

### Изменение названия приложения:

Аналогично, обновите во всех перечисленных файлах.

---

## 🔧 Решение проблем

### Проблема: PyInstaller не находит модули

**Решение:** Добавьте модули в `hiddenimports` в файле `.spec`:

```python
hiddenimports=[
    'missing_module',
    'another_module',
]
```

### Проблема: Большой размер установщика

**Причины:**
- Включены ненужные библиотеки
- Не включена компрессия

**Решения:**
- Используйте `--exclude-module` в PyInstaller
- Включите UPX compression (`upx=True` в .spec)
- Удалите ненужные зависимости

### Проблема: Windows - Inno Setup не найден

**Решение:**
1. Скачайте [Inno Setup 6](https://jrsoftware.org/isdl.php)
2. Установите
3. Запустите build_windows.bat снова

### Проблема: macOS - create-dmg не найден

**Решение:**
```bash
brew install create-dmg
```

Или скрипт автоматически использует `hdiutil` вместо `create-dmg`.

### Проблема: Linux - dpkg-deb не найден

**Решение:**
```bash
sudo apt install dpkg-dev  # Debian/Ubuntu
```

---

## 📊 Размеры установщиков

Примерные размеры готовых установщиков:

| Платформа | Тип | Размер |
|-----------|-----|--------|
| Windows | .exe (Setup) | ~180 MB |
| macOS | .app bundle | ~250 MB |
| macOS | .dmg | ~180 MB |
| Linux | .deb | ~120 MB |
| Linux | .rpm | ~115 MB |
| Linux | Universal .sh | ~125 MB |

*Размеры зависят от количества зависимостей и включенных модулей*

---

## ✅ Что получают пользователи

После установки пользователи видят:

1. **Красивую иконку** в меню приложений
2. **Простой запуск** в один клик
3. **Полностью работающее приложение** без видимого кода
4. **Автоматическую деинсталляцию** через системные инструменты

**Исходный код полностью скрыт** внутри установщика!

---

## 🚢 Распространение

После сборки установщиков:

1. **Протестируйте** на чистой системе
2. **Создайте релиз** на GitHub
3. **Загрузите** установщики в GitHub Releases
4. **Поделитесь** ссылками с пользователями

### Пример GitHub Release:

```markdown
## NEYROLOCK v3.0.0

### Установка

**Windows:**
Скачайте и запустите `NEYROLOCK-3.0.0-Windows-Setup.exe`

**macOS:**
Скачайте `NEYROLOCK-3.0.0-macOS.dmg`, откройте и перетащите в Applications

**Linux:**
- Ubuntu/Debian: `sudo dpkg -i neyrolock_3.0.0_amd64.deb`
- Fedora/RedHat: `sudo rpm -i neyrolock-3.0.0-1.x86_64.rpm`
- Универсальный: `sudo bash NEYROLOCK-3.0.0-Linux-Installer.sh`
```

---

## 💡 Советы

1. **Тестируйте** установщики на чистых виртуальных машинах
2. **Подписывайте** код (особенно для macOS и Windows)
3. **Используйте версионирование** для отслеживания релизов
4. **Документируйте** изменения в каждой версии
5. **Автоматизируйте** сборку через CI/CD (GitHub Actions)

---

## 📚 Дополнительные ресурсы

- [PyInstaller документация](https://pyinstaller.org/)
- [Inno Setup документация](https://jrsoftware.org/ishelp/)
- [create-dmg на GitHub](https://github.com/create-dmg/create-dmg)
- [Debian Packaging Guide](https://www.debian.org/doc/manuals/maint-guide/)

---

## ❓ Вопросы?

Если у вас возникли проблемы:

1. Проверьте `installers/README.md` для подробностей
2. Изучите логи сборки
3. Откройте issue на GitHub

---

**Удачной сборки! 🎉**
