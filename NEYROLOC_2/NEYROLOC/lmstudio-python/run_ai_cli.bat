@echo off
REM Запуск AI CLI для Windows
chcp 65001 >nul 2>&1

echo.
echo   Запуск AI CLI...
echo.

python ai_cli.py

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при запуске!
    echo Проверьте, что Python установлен и доступен в PATH.
    pause
)
