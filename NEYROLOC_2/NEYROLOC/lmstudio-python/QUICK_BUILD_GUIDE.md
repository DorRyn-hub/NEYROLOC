# ⚡ NEYROLOCK - Быстрый Гайд по Сборке

Краткое руководство для быстрой сборки установщиков.

---

## 🎯 Сборка за 5 минут

### Шаг 1: Подготовка

```bash
# Убедитесь, что вы в корне проекта
cd /path/to/neyrolock

# Установите PyInstaller
pip install pyinstaller
```

### Шаг 2: Сборка

```bash
# Автоматическая сборка (определяет вашу ОС)
bash build_installer.sh
```

### Шаг 3: Готово!

Установщики будут в `installers/output/`

---

## 📦 Что будет собрано

### На Windows:
- `NEYROLOCK-3.0.0-Windows-Setup.exe` (если установлен Inno Setup)
- Или standalone executable в `installers/pyinstaller/dist/`

### На macOS:
- `NEYROLOCK.app` - приложение
- `NEYROLOCK-3.0.0-macOS.dmg` - установщик (если установлен create-dmg)

### На Linux:
- `neyrolock_3.0.0_amd64.deb` - Debian/Ubuntu пакет
- `neyrolock-3.0.0-1.x86_64.rpm` - Fedora/RedHat пакет (если установлен rpmbuild)
- `NEYROLOCK-3.0.0-Linux-Installer.sh` - Универсальный установщик

---

## 🔧 Требования

### Минимальные (для всех ОС):
```bash
pip install pyinstaller
pip install -r requirements_ai_cli.txt
```

### Опциональные:

**Windows:**
- [Inno Setup 6](https://jrsoftware.org/isdl.php) - для .exe установщика

**macOS:**
```bash
brew install create-dmg  # для .dmg файла
```

**Linux:**
```bash
# Для .rpm пакетов (опционально)
sudo apt install rpm        # Ubuntu/Debian
sudo dnf install rpm-build  # Fedora
```

---

## 🐛 Если что-то пошло не так

### Ошибка: "pyinstaller: command not found"
```bash
pip install pyinstaller
# или
pip3 install pyinstaller
```

### Ошибка: "No module named 'llama_cpp'"
```bash
pip install -r requirements_ai_cli.txt
```

### Ошибка на macOS: "CMAKE_ARGS not set"
```bash
# Для Apple Silicon (M1/M2/M3)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python --no-cache-dir
```

### Windows: "Inno Setup not found"
- Установите [Inno Setup](https://jrsoftware.org/isdl.php)
- Или соберите только PyInstaller executable (будет работать)

---

## 📋 Ручная сборка (если авто не работает)

### Windows:
```batch
cd installers\windows
build_windows.bat
```

### macOS:
```bash
cd installers/macos
bash build_macos.sh
```

### Linux:
```bash
cd installers/linux
bash build_linux.sh
```

---

## 🎨 Иконки (опционально)

Без иконок установщики будут работать, но с дефолтными иконками.

Для добавления своих иконок:

1. **Создайте placeholder иконку:**
   ```bash
   python create_placeholder_icon.py
   ```

2. **Конвертируйте SVG в нужные форматы:**
   - PNG: Используйте онлайн конвертер
   - ICO: https://icoconvert.com/
   - ICNS: https://cloudconvert.com/png-to-icns

3. **Поместите в assets/:**
   ```
   assets/
   ├── icon.png  (для Linux)
   ├── icon.ico  (для Windows)
   └── icon.icns (для macOS)
   ```

4. **Пересоберите:**
   ```bash
   bash build_installer.sh
   ```

---

## ✅ Проверка сборки

После сборки проверьте:

```bash
# Посмотрите созданные файлы
ls -lh installers/output/

# Проверьте размеры (должны быть ~200-500 MB)
du -h installers/output/*
```

---

## 🚀 Тестирование

1. **Установите на чистой системе** (виртуалка или другой компьютер)
2. **Проверьте запуск приложения**
3. **Проверьте базовую функциональность**
4. **Проверьте удаление**

---

## 📚 Дополнительная документация

- **Полное руководство:** [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **Для разработчиков:** [installers/README.md](installers/README.md)
- **Описание системы:** [INSTALLER_SUMMARY.md](INSTALLER_SUMMARY.md)
- **Проект:** [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)

---

## 💡 Советы

1. **Первая сборка может занять 5-10 минут** (PyInstaller анализирует зависимости)
2. **Повторные сборки быстрее** (~2-3 минуты)
3. **Используйте виртуальное окружение** для чистоты зависимостей
4. **Тестируйте на чистой системе** перед релизом
5. **Для Apple Silicon** обязательно используйте CMAKE_ARGS

---

## 🆘 Помощь

Если ничего не работает:

1. Откройте issue на GitHub с описанием ошибки
2. Приложите вывод команды сборки
3. Укажите ОС и версию Python

---

**Удачи со сборкой! 🎉**
