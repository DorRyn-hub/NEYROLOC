@echo off
REM ====================================================
REM NEYROLOCK Windows Installer Build Script
REM Создает установщик с прогресс-баром для Windows
REM ====================================================

echo.
echo ========================================
echo NEYROLOCK Windows Installer Builder
echo ========================================
echo.

REM Переход в корень проекта
cd /d "%~dp0..\.."

echo [1/5] Проверка зависимостей...
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден! Установите Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python найден

REM Проверка PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INSTALLING] Установка PyInstaller...
    pip install pyinstaller
)
echo [OK] PyInstaller готов

echo.
echo [2/5] Очистка старых сборок...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "installers\output\NEYROLOCK-3.0.0-Windows-Setup.exe" del /q "installers\output\NEYROLOCK-3.0.0-Windows-Setup.exe"
echo [OK] Очистка завершена

echo.
echo [3/5] Сборка приложения с PyInstaller...
echo Это может занять несколько минут...
echo.

python -m PyInstaller ^
    --clean ^
    --noconfirm ^
    installers\pyinstaller\neyrolock_gui.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при сборке с PyInstaller!
    pause
    exit /b 1
)

echo.
echo [OK] PyInstaller завершил сборку

echo.
echo [4/5] Проверка наличия Inno Setup...

set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% (
    set INNO_SETUP="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist %INNO_SETUP% (
    echo.
    echo [WARNING] Inno Setup не найден!
    echo.
    echo Приложение собрано в: dist\NEYROLOCK\
    echo.
    echo Для создания установщика:
    echo 1. Скачайте Inno Setup: https://jrsoftware.org/isdl.php
    echo 2. Установите Inno Setup
    echo 3. Запустите этот скрипт снова
    echo.
    pause
    exit /b 0
)

echo [OK] Inno Setup найден

echo.
echo [5/5] Создание установщика с Inno Setup...
echo.

%INNO_SETUP% installers\windows\neyrolock_setup.iss

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при создании установщика!
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Установщик создан успешно!
echo ========================================
echo.
echo Файл установщика:
echo   installers\output\NEYROLOCK-3.0.0-Windows-Setup.exe
echo.
echo Теперь вы можете распространять этот установщик.
echo Пользователи увидят только иконку программы,
echo исходный код будет скрыт внутри установщика.
echo.

pause
