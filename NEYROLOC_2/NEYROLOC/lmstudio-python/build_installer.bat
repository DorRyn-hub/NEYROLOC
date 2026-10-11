@echo off
REM Сборка установщика NEYROLOCK для Windows 11
REM Вызывает скрипт из installers/windows/
chcp 65001 >nul 2>&1

echo.
echo ========================================
echo   NEYROLOCK Windows Installer Builder
echo ========================================
echo.

cd /d "%~dp0"

REM Проверка наличия скрипта сборки
if not exist "installers\windows\build_windows.bat" (
    echo [ERROR] Файл installers\windows\build_windows.bat не найден!
    pause
    exit /b 1
)

echo Запуск сборки установщика...
echo.

call installers\windows\build_windows.bat

if errorlevel 1 (
    echo.
    echo [ERROR] Сборка завершилась с ошибкой!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Сборка завершена успешно!
echo ========================================
echo.
echo Установщик находится в:
echo   installers\output\NEYROLOCK-3.0.0-Windows-Setup.exe
echo.

pause
