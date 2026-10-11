@echo off
REM Установка и настройка NEYROLOCK CLI для Windows 11
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo ========================================================
echo       NEYROLOCK CLI - Установка и настройка
echo ========================================================
echo.

REM Переход в директорию скрипта
cd /d "%~dp0"

REM Проверка Python
echo [1/4] Проверка версии Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    [ERROR] Python не найден!
    echo    Установите Python 3.10 или выше с python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo    [OK] Найден Python %PYTHON_VER%
echo.

REM Установка зависимостей
echo [2/4] Установка зависимостей...

if exist requirements_cli.txt (
    pip install -q -r requirements_cli.txt
    if errorlevel 1 (
        echo    [ERROR] Ошибка установки зависимостей
        pause
        exit /b 1
    )
    echo    [OK] Зависимости установлены
) else (
    echo    [WARNING] requirements_cli.txt не найден
    echo    Устанавливаю базовые зависимости...
    pip install rich httpx httpx-ws --quiet
)
echo.

REM Проверка LM Studio
echo [3/4] Проверка подключения к LM Studio...

if exist test_connection.py (
    python test_connection.py >nul 2>&1
    if errorlevel 1 (
        echo    [WARNING] LM Studio не доступен
        echo    Убедитесь, что:
        echo       - LM Studio запущен
        echo       - Модель загружена
        echo       - Сервер активен (порт 1234)
    ) else (
        echo    [OK] LM Studio доступен
    )
) else (
    echo    [INFO] Файл test_connection.py не найден, пропускаю проверку
)

echo.
echo [4/4] Готово к запуску!
echo.
echo ========================================================
echo              Установка завершена!
echo ========================================================
echo.
echo Для запуска CLI выполните:
echo   python lmstudio_cli.py
echo.

set /p RESPONSE="Запустить сейчас? (y/n): "
if /i "%RESPONSE%"=="y" (
    echo.
    python lmstudio_cli.py
)
if /i "%RESPONSE%"=="yes" (
    echo.
    python lmstudio_cli.py
)
