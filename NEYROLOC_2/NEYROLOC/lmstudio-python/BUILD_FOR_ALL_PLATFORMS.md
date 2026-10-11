# 🚀 Сборка установщиков для ВСЕХ платформ (включая Windows!)

## ⚡ Один клик - все установщики готовы!

Теперь вы можете создать установщики для **Windows, macOS и Linux** одной командой, даже находясь на Mac!

---

## 🎯 Способ 1: Автоматическая сборка через GitHub (РЕКОМЕНДУЕТСЯ)

### Шаг 1: Настройка (один раз)

1. **Создайте репозиторий на GitHub** (если ещё не создали):
   - Зайдите на https://github.com
   - Нажмите "New repository"
   - Назовите: `neyrolock` или любое другое имя
   - Создайте репозиторий

2. **Подключите проект к GitHub:**
   ```bash
   cd $HOME/PycharmProjects/NEYROLOCK/lmstudio-python

   # Инициализируем git (если ещё не сделали)
   git init
   git add .
   git commit -m "Initial commit"

   # Подключаем к GitHub (замените на свой URL)
   git remote add origin https://github.com/DorRyn/NEYROLOC.git
   git push -u origin main
   ```

### Шаг 2: Создание релиза со всеми установщиками

**Одна команда:**

```bash
bash release_all_platforms.sh
```

Скрипт спросит версию (например, `3.0.0`) и автоматически:

1. ✅ Создаст git тег
2. ✅ Отправит на GitHub
3. ✅ Запустит GitHub Actions
4. ✅ GitHub соберёт установщики на своих серверах:
   - **Windows** (на Windows Server)
   - **macOS** (на macOS Latest)
   - **Linux** (на Ubuntu Latest)
5. ✅ Создаст Release со всеми установщиками

### Шаг 3: Скачивание готовых установщиков

Через ~10-15 минут:

1. Откройте: `https://github.com/ВАШ_USERNAME/neyrolock/releases`
2. Скачайте все установщики
3. Готово! 🎉

---

## 🎯 Способ 2: Локальная сборка (без Windows)

Если не хотите использовать GitHub Actions:

```bash
bash build_all_installers.sh
```

Это создаст установщики для **macOS и Linux**, но **не для Windows**.

**Для Windows** нужно будет отдельно:
- Открыть проект на Windows компьютере
- Запустить `installers\windows\build_windows.bat`

---

## 📦 Что вы получите

После завершения GitHub Actions, в релизе будут:

```
NEYROLOCK-3.0.0-Windows-Setup.exe     (~180 MB)  🪟 Windows
NEYROLOCK-3.0.0-macOS.dmg              (~180 MB)  🍎 macOS
neyrolock_3.0.0_amd64.deb              (~120 MB)  🐧 Linux (Debian/Ubuntu)
neyrolock-3.0.0-1.x86_64.rpm           (~115 MB)  🐧 Linux (Fedora/RedHat)
NEYROLOCK-3.0.0-Linux-Installer.sh     (~125 MB)  🐧 Linux (Универсальный)
```

---

## 🔍 Мониторинг сборки

После запуска `release_all_platforms.sh`:

1. **Откроется браузер** с GitHub Actions
2. **Следите за прогрессом** сборки (3 параллельных задачи)
3. **Дождитесь завершения** (~10-15 минут)
4. **Скачайте** установщики из Releases

**Прогресс в реальном времени:**
```
✓ build-windows  (Windows Server)
✓ build-macos    (macOS Latest)
✓ build-linux    (Ubuntu Latest)
✓ create-release (Создание релиза)
```

---

## 🎁 Бонус: Автоматическое обновление

Каждый раз при создании нового тега (например, `v3.0.1`, `v3.1.0`):
- GitHub Actions автоматически соберёт установщики
- Создаст новый релиз
- Добавит все файлы

**Команда для нового релиза:**
```bash
bash release_all_platforms.sh
# Введите новую версию: 3.0.1
```

---

## ✅ Сравнение способов

| Способ | Windows | macOS | Linux | Сложность |
|--------|---------|-------|-------|-----------|
| **GitHub Actions** | ✅ | ✅ | ✅ | Легко |
| **Локальная сборка** | ❌ | ✅ | ✅ | Средне |
| **Сборка на Windows** | ✅ | ❌ | ❌ | Средне |

---

## 💡 Рекомендации

### Для разработки:
```bash
# Локальная сборка для тестирования
bash build_all_installers.sh
```

### Для публичного релиза:
```bash
# Автоматическая сборка через GitHub
bash release_all_platforms.sh
```

---

## 🐛 Решение проблем

### "git remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/ВАШ_USERNAME/neyrolock.git
```

### "GitHub Actions не запускается"
1. Проверьте, что файл `.github/workflows/build-installers.yml` существует
2. Убедитесь, что тег создан: `git tag -l`
3. Проверьте, что тег отправлен: `git push origin --tags`

### "Windows установщик не создался"
1. Откройте GitHub Actions
2. Проверьте логи задачи `build-windows`
3. Возможно, нужно подождать дольше

---

## 📚 Дополнительно

- **Просмотр Actions**: `https://github.com/ВАШ_USERNAME/neyrolock/actions`
- **Просмотр Releases**: `https://github.com/ВАШ_USERNAME/neyrolock/releases`
- **Логи сборки**: Кликните на конкретную задачу в Actions

---

## 🎉 Готово!

Теперь у вас есть **полностью автоматическая** система сборки установщиков для всех платформ!

**Одна команда → Все установщики готовы через 15 минут!** 🚀

```bash
bash release_all_platforms.sh
```
