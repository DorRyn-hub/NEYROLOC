@echo off
chcp 65001 >nul
REM ====================================================
REM NEYROLOCK - Build Script for Windows
REM Создаёт standalone .exe файл
REM ====================================================

echo.
echo ========================================
echo    NEYROLOCK Windows Build Script
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python не найден!
    echo.
    echo Установите Python 3.10+ с https://python.org
    echo При установке выберите "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
echo [OK] Python найден

REM Установка зависимостей
echo.
echo [1/3] Установка зависимостей...
pip install pyinstaller rich openai --quiet
if errorlevel 1 (
    echo [ERROR] Ошибка установки зависимостей!
    pause
    exit /b 1
)
echo [OK] Зависимости установлены

REM Очистка старых сборок
echo.
echo [2/3] Очистка старых сборок...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "NEYROLOCK.exe" del /q "NEYROLOCK.exe"
echo [OK] Очистка завершена

REM Сборка
echo.
echo [3/3] Сборка приложения...
echo Это может занять 1-2 минуты...
echo.

python -m PyInstaller --clean --noconfirm neyrolock.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка при сборке!
    pause
    exit /b 1
)

REM Копируем exe в текущую папку
if exist "dist\NEYROLOCK.exe" (
    copy "dist\NEYROLOCK.exe" "NEYROLOCK.exe" >nul
)

echo.
echo ========================================
echo [SUCCESS] Сборка завершена!
echo ========================================
echo.
echo Файл создан: NEYROLOCK.exe
echo.
echo Теперь вы можете:
echo   1. Запустить NEYROLOCK.exe
echo   2. Скопировать его на другой компьютер
echo.
echo Для работы нужен LM Studio, Ollama или Groq API ключ.
echo.

pause
