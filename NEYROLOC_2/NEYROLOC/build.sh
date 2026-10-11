#!/bin/bash
# ====================================================
# NEYROLOCK - Build Script for macOS/Linux
# Создаёт standalone приложение
# ====================================================

set -e

echo ""
echo "========================================"
echo "   NEYROLOCK Build Script"
echo "========================================"
echo ""

# Определение ОС
OS="$(uname -s)"
case "$OS" in
    Linux*)     PLATFORM="Linux";;
    Darwin*)    PLATFORM="macOS";;
    *)          PLATFORM="Unknown";;
esac

echo "Платформа: $PLATFORM"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 не найден!"
    echo "Установите Python 3.10+"
    exit 1
fi
echo "[OK] Python найден"

# Установка зависимостей
echo ""
echo "[1/3] Установка зависимостей..."
pip3 install pyinstaller rich openai --quiet
echo "[OK] Зависимости установлены"

# Очистка
echo ""
echo "[2/3] Очистка старых сборок..."
rm -rf dist build
rm -f NEYROLOCK
echo "[OK] Очистка завершена"

# Сборка
echo ""
echo "[3/3] Сборка приложения..."
echo "Это может занять 1-2 минуты..."
echo ""

python3 -m PyInstaller --clean --noconfirm neyrolock.spec

# Копируем в текущую папку
if [ -f "dist/NEYROLOCK" ]; then
    cp "dist/NEYROLOCK" "NEYROLOCK"
    chmod +x "NEYROLOCK"
fi

echo ""
echo "========================================"
echo "[SUCCESS] Сборка завершена!"
echo "========================================"
echo ""
echo "Файл создан: NEYROLOCK"
echo ""
echo "Запуск: ./NEYROLOCK"
echo ""
