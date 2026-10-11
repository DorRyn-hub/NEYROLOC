@echo off
REM Запуск AI GUI для Windows
chcp 65001 >nul 2>&1

echo.
echo   Запуск AI GUI...
echo.

python ai_gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при запуске!
    echo Проверьте, что Python установлен и доступен в PATH.
    pause
)
