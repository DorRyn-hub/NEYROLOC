@echo off
REM Запуск NEYROLOCK v3.0 Dashboard для Windows
chcp 65001 >nul 2>&1

echo.
echo ========================================
echo   NEYROLOCK v3.0 Dashboard
echo ========================================
echo.
echo   Современный интерфейс:
echo   - Боковая панель навигации
echo   - Карточки со статистикой
echo   - Темный дизайн с градиентами
echo   - Горячие клавиши RU/EN (Ctrl+S, Ctrl+Ы)
echo.

python ai_gui_v3.py

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при запуске!
    echo Проверьте, что Python установлен и доступен в PATH.
    pause
)
