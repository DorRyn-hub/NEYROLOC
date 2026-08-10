# NEYROLOC NEW

NEYROLOC NEW — desktop-клиент на PySide6 для локальных GGUF-моделей и
OpenAI-совместимых облачных API. Активный код находится в `NEYROLOCK_5`.
Локальный `NEYROLOC_2` сохранён на машине только как архив предыдущего
поколения и не публикуется, а `NEYROLOC` — отдельный приватный iOS-проект.

## Быстрый запуск

Нужен Python 3.10 или новее. Из корня проекта:

```bash
python3 -m venv NEYROLOCK_5/.venv
NEYROLOCK_5/.venv/bin/python -m pip install -r NEYROLOCK_5/requirements.txt
./START_NEYROLOC_NEW.command
```

Launcher сначала использует `NEYROLOCK_5/.venv`, затем корневой `.venv` и не
зависит от окружения архивного `NEYROLOC_2`. Другой Python можно указать явно:

```bash
NEYROLOC_PYTHON=/полный/путь/к/python ./START_NEYROLOC_NEW.command
```

Прямой эквивалент запуска:

```bash
NEYROLOCK_5/.venv/bin/python main.py
```

### Локальный GGUF inference

`llama-cpp-python` устанавливается отдельно, потому что параметры сборки
зависят от платформы. Для Apple Silicon:

```bash
CMAKE_ARGS="-DLLAMA_METAL=on" NEYROLOCK_5/.venv/bin/python -m pip install "llama-cpp-python>=0.2.0"
```

## Backend-ы

- `Local GGUF` — offline inference через `llama-cpp-python`; библиотека моделей
  скачивает GGUF с Hugging Face в `~/.neyrolock_models`.
- `OpenAI` — OpenAI API или совместимый endpoint через настраиваемый `base_url`.
- `Groq` — OpenAI-совместимый Groq API.

LM Studio, Ollama и старый Hugging Face backend не входят в активный реестр.

## Удалённый доступ с телефона

Desktop поднимает ограниченный HTTP-сервер на порту `8765`:

- в локальной сети используется `http://IP-КОМПЬЮТЕРА:8765`;
- публичный tunnel использует HTTPS-адрес личного поддомена;
- шестизначный код нужен только для первичного сопряжения;
- после сопряжения браузер получает временную HttpOnly-сессию, а постоянная
  передача pairing-кода в API не поддерживается;
- сервер ограничивает размер запросов, истории, ответа, частоту запросов и
  число одновременно обслуживаемых соединений.

PWA хранит локальные чаты и интерфейсные настройки на телефоне, но не хранит
pairing-код. Android и iOS WebView разрешают навигацию внутри исходного origin;
чужие ссылки открываются только после явного действия пользователя.

## Сборки

### macOS

Для быстрой локальной упаковки, привязанной к Python.framework этого Mac:

```bash
packaging/build_app.sh
```

Для автономного приложения используется Nuitka — тот же backend, который
использует официальный `pyside6-deploy`:

```bash
packaging/build_standalone_macos.sh
```

При первом запуске скрипт создаёт отдельное gitignored-окружение
`packaging/.venv` на стабильном Python 3.10–3.13 и устанавливает зависимости из
`packaging/requirements-macos-build.txt`. Python 3.14 намеренно отклоняется,
поскольку поддержка этой версии в закреплённом Nuitka 4.0 экспериментальная.
Другой совместимый интерпретатор можно указать через
`NEYROLOC_BUILD_BOOTSTRAP_PYTHON`. Минимальная версия собранного arm64-приложения
— macOS 15: это фактический target свежего PySide6 6.11; скрипт проверяет target
каждого Mach-O-файла и не позволяет случайно привязать bundle к более новой
системе сборщика.

Скрипт собирает `deployment/main.app`, включает Python, Qt, активные backend-ы,
PWA-ресурсы и Android APK. Если локальный gitignored-файл
`NEYROLOCK_5/resources/bin/frpc` установлен, он тоже включается. Результат
проверяется через `codesign`, но подписывается ad-hoc; для распространения вне
машины сборки всё ещё нужны Apple Developer ID и notarization.

Команду без сборки можно посмотреть так:

```bash
packaging/build_standalone_macos.sh --dry-run
```

### Android

Android WebView-оболочка находится в `packaging/android`, требует JDK, Android
SDK Platform 36 и Build Tools 36.0.0:

```bash
ANDROID_SDK_ROOT=/путь/к/android-sdk packaging/android/build_apk.sh
```

Без release-keystore скрипт создаёт debug-подписанный `NEYROLOC.apk`, пригодный
для локальной установки, но не для магазина. Для release-подписи используются
переменные `NEYROLOC_KEYSTORE`, `NEYROLOC_KEY_ALIAS`,
`NEYROLOC_KEYSTORE_PASS` и `NEYROLOC_KEY_PASS`; их значения нельзя сохранять в
репозитории.

### iOS

Нативный Xcode-проект расположен в `NEYROLOC`, имеет deployment target iOS 16,
QR-сканер и WKWebView-оболочку. Локальный HTTP разрешён только для web content;
остальные сетевые API остаются под стандартными правилами ATS. Для реального
устройства и App Store нужны действующая Apple signing team и release archive.

## Проверки

Быстрый набор не запускает реальную модель или внешний VPS:

```bash
python3 -m unittest discover -s tests -v
```

Он проверяет launcher/import, конфигурацию и историю во временных каталогах,
HTTP-сервер и сопряжение, broker и Android URL logic. Дополнительно перед
релизом выполняются Java-компиляция, проверка подписи APK, Xcode tests,
offscreen Qt smoke-test и запуск автономного macOS bundle.

## Структура

- `main.py`, `start.py`, `START_NEYROLOC_NEW.command` — точки запуска.
- `NEYROLOCK_5/backends` — активные backend-ы и общий контракт.
- `NEYROLOCK_5/core` — config/history, библиотека моделей, remote server и tunnel.
- `NEYROLOCK_5/ui` — PySide6-интерфейс.
- `packaging/android` — Android WebView и сборка APK.
- `packaging` — локальная и автономная macOS-сборки.
- `NEYROLOC` — отдельный iOS-проект.
- `deploy` — broker и ручной VPS deploy публичного tunnel.
- `tests` — быстрые кроссплатформенные проверки.

Настройки и API-ключи сохраняются локально в
`~/.neyrolock_5/config.json` с приватными правами. Файлы с секретами, ключами,
сертификатами и локальными tunnel-конфигами не должны публиковаться.
`deploy/deploy_phase2.sh` изменяет systemd, Caddy и frps на сервере и поэтому
запускается только вручную после проверки конфигурации и резервной копии.
