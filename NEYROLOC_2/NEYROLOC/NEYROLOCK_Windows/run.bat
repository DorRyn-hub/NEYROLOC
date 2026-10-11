@echo off
chcp 65001 >nul
echo ========================================
echo    NEYROLOCK - Quick Start
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

REM Установка зависимостей
echo Установка зависимостей...
pip install rich openai --quiet

REM Запуск
echo.
echo Запуск NEYROLOCK...
echo.
python neyrolock.py

pause
