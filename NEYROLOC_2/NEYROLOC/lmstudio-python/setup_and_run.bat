@echo off
REM Автоматическая установка и запуск NEYROLOCK для Windows 11
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo ========================================================
echo      NEYROLOCK - Автоматическая установка для Windows
echo ========================================================
echo.

REM Переход в директорию скрипта
cd /d "%~dp0"

REM Проверка Python
echo [1/5] Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python не найден!
    echo.
    echo Установите Python 3.10 или выше:
    echo   1. Скачайте с https://python.org/downloads/
    echo   2. Или установите из Microsoft Store: winget install Python.Python.3.12
    echo.
    echo ВАЖНО: При установке отметьте "Add Python to PATH"!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo    [OK] Найден Python %PYTHON_VER%
echo.

REM Проверка зависимостей
echo [2/5] Проверка зависимостей...

set NEED_INSTALL=false

python -c "import rich" >nul 2>&1
if errorlevel 1 (
    echo    [!] rich - не установлен
    set NEED_INSTALL=true
)

python -c "import huggingface_hub" >nul 2>&1
if errorlevel 1 (
    echo    [!] huggingface-hub - не установлен
    set NEED_INSTALL=true
)

python -c "import llama_cpp" >nul 2>&1
if errorlevel 1 (
    echo    [!] llama-cpp-python - не установлен
    set NEED_INSTALL=true
)

if "%NEED_INSTALL%"=="true" (
    echo.
    echo [3/5] Установка зависимостей...
    echo.

    echo    Обновление pip...
    python -m pip install --upgrade pip --quiet

    echo    Установка базовых библиотек...
    python -m pip install rich huggingface-hub --quiet

    echo    Установка llama-cpp-python...
    echo    Это может занять несколько минут...
    python -m pip install llama-cpp-python --quiet

    if errorlevel 1 (
        echo.
        echo    [WARNING] Не удалось установить llama-cpp-python.
        echo    Возможно, нужен Visual Studio Build Tools.
        echo    Скачайте: https://visualstudio.microsoft.com/visual-cpp-build-tools/
        echo.
    ) else (
        echo    [OK] llama-cpp-python установлен
    )

    echo.
    echo    Установка опциональных библиотек...
    python -m pip install openai python-telegram-bot --quiet 2>nul

    echo.
    echo    [OK] Зависимости установлены!
) else (
    echo    [OK] Все зависимости уже установлены!
)

echo.
echo [4/5] Проверка GPU...

python -c "from llama_cpp import Llama; print('CUDA available' if hasattr(Llama, 'n_gpu_layers') else 'CPU only')" 2>nul
if errorlevel 1 (
    echo    [INFO] GPU ускорение недоступно (CPU режим)
) else (
    echo    [OK] llama-cpp-python готов к работе
)

echo.
echo ========================================================
echo.
echo [5/5] Запуск NEYROLOCK v3.0...
echo.
echo ========================================================
echo.

python ai_gui_v3.py

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при запуске!
    pause
)
