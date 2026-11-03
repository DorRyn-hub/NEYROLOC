# Разработка NEYROLOC

[Главная](../README.md) · [Установка](INSTALL.md) · [Руководство](USER_GUIDE.md) · [Версии и восстановление](../VERSIONING.md)

Активное desktop-приложение — `NEYROLOCK_5/`. Это PySide6-клиент с локальным
GGUF backend и облачными OpenAI/Groq backend. Папка `NEYROLOC_2/` — архив,
не место для новых изменений интерфейса. Всегда сверяйтесь с действующим
[AGENTS.md](../AGENTS.md) и вложенными инструкциями.

## Получить и запустить исходники

```sh
git clone --branch main https://github.com/DorRyn-hub/NEYROLOC.git
cd NEYROLOC
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r NEYROLOCK_5/requirements.txt
./.venv/bin/python main.py
```

На Windows PowerShell замените `python3` на установленный `py`, а
`./.venv/bin/python` — на `.\.venv\Scripts\python.exe`. Полные платформенные
шаги и отдельная установка `llama-cpp-python` описаны в [INSTALL.md](INSTALL.md).
`start.py` вызывает тот же launcher и подходит как Run configuration в IDE.
Рабочий каталог IDE — корень репозитория; interpreter — созданная `.venv`.

## Карта исходников

| Путь | Ответственность |
| --- | --- |
| `main.py`, `start.py` | Точка входа, QApplication, стили, главное окно |
| `NEYROLOCK_5/ui/main_window.py` | Связь интерфейса, backend, workers, истории и удалённого доступа |
| `NEYROLOCK_5/ui/workspace.py` | Навигация Graphite, заголовки, список диалогов |
| `NEYROLOCK_5/ui/sidebar.py` | Настройки подключения и параметры диалога |
| `NEYROLOCK_5/ui/chat_widget.py` | Сообщения, потоковый ответ, Markdown, код, ввод и действия |
| `NEYROLOCK_5/ui/model_library_dialog.py` | Карточки локальных моделей, рекомендации, поиск файлов |
| `NEYROLOCK_5/ui/styles.py`, `icons.py`, `typography.py` | QSS, векторные иконки и шрифты |
| `NEYROLOCK_5/backends/base.py`, `backends/__init__.py` | Контракт Backend/Message и реестр провайдеров |
| `NEYROLOCK_5/backends/local_gguf.py` | Загрузка GGUF и генерация через llama.cpp |
| `NEYROLOCK_5/backends/online/` | OpenAI-совместимые облачные backend |
| `NEYROLOCK_5/core/model_library.py` | Каталог, Hugging Face, скачивание, локальные метаданные |
| `NEYROLOCK_5/core/config.py`, `core/history.py` | Пользовательские настройки и JSON-переписки |
| `NEYROLOCK_5/core/remote_server.py`, `core/tunnel.py` | Телефонный HTTP-доступ и управление туннелем |
| `tests/` | Корневые интеграционные и регрессионные проверки |
| `NEYROLOC/`, `packaging/android/` | Отдельные мобильные обёртки; нужны соответствующие SDK |
| `deploy/`, `remote/`, `packaging/` | Инфраструктура и упаковка; desktop-запуск их не развёртывает |

## Как проходит запрос

Выбор источника → параметры подключения → получение списка моделей → подготовка
выбранной модели → доступный ввод. `PrepareWorker`, `ListModelsWorker`,
`GenerateWorker` и `DownloadModelWorker` отделяют длительные операции от UI.
Генерация выдаёт фрагменты текста в `ChatWidget`; готовый ответ добавляется
в `ChatSession`. Удалённый доступ использует общий backend и блокировку генерации.

Локальный путь: GGUF на диске → `LocalGGUFBackend` → llama.cpp → поток текста.
Hugging Face отвечает за поиск и доставку файлов, не заменяет движок инференса.
Облачный путь: настройки провайдера → OpenAI-совместимый клиент → streaming
Chat Completions. Список моделей может иметь резервный вариант: наличие списка
не подтверждает рабочий ключ или успешную генерацию.

`Config` сохраняет настройки отдельно от исходников. История — JSON-формат
`messages` с полями `role` и `content`, плюс `saved_at`; файл не содержит веса
модели. Пользовательские чаты и настройки не являются тестовыми fixtures.
Для интерфейсных проверок создавайте временный профиль и backend без сети.

## Проверки перед изменением и отправкой

```sh
git fetch origin --tags
git status
git log --oneline --decorate -10
git rev-list --left-right --count HEAD...origin/main
```

Если отстаёт только чистая `main`, выполните `git pull --ff-only origin main`.
Собственные изменения сохраняйте; при расхождении истории не заменяйте её принудительно.

Для изменения Graphite из корня на macOS/Linux:

```sh
QT_QPA_PLATFORM=offscreen ./.venv/bin/python -m unittest discover -s tests -p test_graphite_workspace.py -v
```

PowerShell:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_graphite_workspace.py -v
Remove-Item Env:QT_QPA_PLATFORM
```

Для общей проверки активного приложения запускайте корневой набор:

```sh
QT_QPA_PLATFORM=offscreen ./.venv/bin/python -m unittest discover -s tests -v
```

Не считайте `skipped` доказательством работающей функции: например, без PySide6
GUI-тесты могут пропускаться. Сравнивайте сбои с исходной версией в том же окружении.
В отчёте фиксируйте команду, результат, пропуски и непроверенные сценарии.

Offscreen-тест подтверждает программное поведение Qt, но не внешний вид на
физическом мониторе, драйвер GPU или реальный ответ модели. Для выпуска отдельно
проверьте обычный запуск, маленькую GGUF-модель, остановку ответа, сохранение и
повторное открытие JSON, смену источника и читаемость при системном масштабировании.
Телефон и облачные ключи требуют отдельных проверок с авторизованным аккаунтом.

## Сохранение и безопасность

Установите gitleaks и hooks по [VERSIONING.md](../VERSIONING.md). После проверок
добавляйте конкретные исходники, затем проверяйте **весь индекс**:

```sh
git add <проверенные-файлы>
python3 scripts/check_repository.py --index
git diff --cached --stat
git diff --cached --check
git commit -m "Описание законченного изменения"
git push origin main
```

Не добавляйте окружения, модели, сборки, журналы, реальные конфиги, чаты, базы,
ключи и резервные копии. Не обходите hooks. Для восстановления используйте
новый коммит согласно VERSIONING.md. `version-control` — центр восстановления,
обычное приложение меняется в `main`. Во внешнем репозитории iOS-исходники
должны оставаться обычными файлами: не добавляйте вложенный `.git` как gitlink.

Изменение исходников, успешный тест, сборка и развёртывание — отдельные результаты.
Отправка в GitHub не развёртывает сервисы и не публикует готовый установщик.
