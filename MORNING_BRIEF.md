# Утренняя сводка — NEYROLOC NEW

_Обновлено: 2026-08-10 · локальная ветка `main` · публикация через audit-ветку_

## 1. Статус git

В рабочем дереве находится единый проверяемый набор изменений полного аудита:
desktop, PWA, backend-ы, broker, Android, macOS packaging и документация.
Вложенный каталог `NEYROLOC` является отдельным iOS-репозиторием и публикуется
отдельно как приватный submodule.

Старый локальный history содержит закоммиченный `.venv` и бинарники размером
свыше лимита GitHub. Поэтому удалённая ветка формируется как чистый source-only
snapshot поверх приватного `origin/main`; старые локальные данные и каталог
`NEYROLOC_2` не удаляются с машины, но в product tree не публикуются.

## 2. Что менялось за сутки

Новых локальных коммитов до начала аудита за последние 24 часа не было. В
текущем change set:

- устранены гонки между desktop/phone generation, переключением backend-а и
  закрытием Qt-потоков;
- config, история, tunnel-конфиг и broker registry переведены на атомарную
  запись с приватными правами и проверкой схемы;
- HTTP/PWA усилены лимитами, rate limiting, HttpOnly-сессией, CSP и запретом
  повторного использования pairing-кода как постоянного API-токена;
- Android WebView ограничен исходным origin, target SDK поднят до API 36,
  добавлены release-signing параметры и тесты URL logic;
- iOS WebView ограничен исходным origin, ATS сужен до web content, deployment
  target установлен на iOS 16, добавлены тесты URL logic;
- добавлена автономная macOS-сборка через Nuitka с включёнными ресурсами;
- добавлен набор автоматических тестов и актуализирована документация.

## 3. Невыполненные TODO в коде

Маркеры `TODO|FIXME|XXX|HACK` в активных `NEYROLOCK_5`, `deploy`, `packaging`,
`tests` и корневых launcher-файлах не найдены.

Оставшиеся релизные действия не являются скрытыми TODO в коде: нужны Android
release-keystore, Apple Developer ID/notarization, iOS device signing и
контролируемое развёртывание VPS после резервной копии.

## 4. Состояние тестов

- `python3 -m unittest discover -s tests -v` — **25 тестов обнаружено:
  23 OK, 2 Qt UI-теста пропущены** без установленного PySide6.
- Полный набор в активном `NEYROLOCK_5/.venv` с PySide6 — **25/25 OK**,
  включая адаптивную геометрию окна 640×480–1764×1148.
- Android Java URL tests и компиляция `MainActivity` против API 36 — **OK**.
- Android APK — target API 36, zipalign/apksigner verification — **OK**;
  текущий артефакт подписан debug-ключом.
- iOS unit/UI/launch/performance tests на симуляторе — **OK**; повторный
  `xcodebuild build` для target iOS 16 — **BUILD SUCCEEDED**.
- Реальный HTTP smoke-test сопряжения, сессии, streaming и oversized body —
  **OK**.
- Qt offscreen worker/lifecycle smoke-test — **OK**.
- Автономный arm64 macOS bundle — **BUILD/CODESIGN/8s SMOKE OK**; все Mach-O
  совместимы с заявленным минимумом macOS 15, размер локального `.app` — 256 МБ.

Финальные Ruff, Python/JS/shell/C/plist syntax, diff check и secret-scan именно
публикуемого source-only дерева — **OK**.
