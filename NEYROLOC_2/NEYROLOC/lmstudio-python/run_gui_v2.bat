@echo off
REM Запуск NEYROLOCK v2.0 с поддержкой Telegram для Windows
chcp 65001 >nul 2>&1

echo.
echo ========================================
echo   NEYROLOCK v2.0
echo ========================================
echo.
echo   Возможности:
echo   - Красочный темный интерфейс
echo   - Горячие клавиши на русской раскладке (Ctrl+Ы, Ctrl+Т...)
echo   - Интеграция с Telegram-ботом
echo   - Улучшенные настройки шрифтов
echo.

python ai_gui_v2.py

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при запуске!
    echo Проверьте, что Python установлен и доступен в PATH.
    pause
)
