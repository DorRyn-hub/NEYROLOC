#!/bin/bash
# Скрипт для быстрой установки и запуска LM Studio CLI

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        NEYROLOCK CLI - Установка и настройка              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Проверка версии Python
echo "[1/4] Проверка версии Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.10 или выше"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "   ✓ Найден Python $PYTHON_VERSION"

# Установка зависимостей
echo ""
echo "[2/4] Установка зависимостей..."
pip install -q -r requirements_cli.txt

if [ $? -eq 0 ]; then
    echo "   ✓ Зависимости установлены"
else
    echo "   ❌ Ошибка установки зависимостей"
    exit 1
fi

# Проверка LM Studio
echo ""
echo "[3/4] Проверка подключения к LM Studio..."
python3 test_connection.py > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✓ LM Studio доступен"
else
    echo "   ⚠  LM Studio не доступен"
    echo "   Убедитесь, что:"
    echo "      - LM Studio запущен"
    echo "      - Модель загружена"
    echo "      - Сервер активен (порт 1234)"
fi

# Запуск CLI
echo ""
echo "[4/4] Готов к запуску!"
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    Установка завершена!                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Для запуска CLI выполните:"
echo "  python3 lmstudio_cli.py"
echo ""
echo "Или запустите сейчас? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    python3 lmstudio_cli.py
fi
