#!/bin/bash
# Автоматическая установка и запуск AI CLI для Mac

set -e  # Остановить при ошибке

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         🤖 AI CLI - Автоматическая установка для Mac        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Переходим в директорию скрипта
cd "$(dirname "$0")"

# Проверка Python
echo "📋 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден!"
    echo "Установите Python 3: brew install python@3.12"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Найден: $PYTHON_VERSION"
echo ""

# Проверка наличия зависимостей
echo "📦 Проверка зависимостей..."

NEED_INSTALL=false

if ! python3 -c "import rich" 2>/dev/null; then
    echo "⚠️  rich - не установлен"
    NEED_INSTALL=true
fi

if ! python3 -c "import huggingface_hub" 2>/dev/null; then
    echo "⚠️  huggingface-hub - не установлен"
    NEED_INSTALL=true
fi

if [ "$NEED_INSTALL" = true ]; then
    echo ""
    echo "🔧 Установка недостающих зависимостей..."
    echo ""

    # Проверяем, Mac M1/M2/M3 или Intel
    ARCH=$(uname -m)

    if [ "$ARCH" = "arm64" ]; then
        echo "🍎 Обнаружен Apple Silicon (M1/M2/M3)"
        echo "Устанавливаем с поддержкой Metal (GPU ускорение)..."
        echo ""

        # Установка базовых зависимостей
        python3 -m pip install --upgrade pip --quiet
        python3 -m pip install rich huggingface-hub --quiet

        # Попытка установить llama-cpp-python с Metal
        echo "📥 Установка llama-cpp-python с Metal поддержкой..."
        echo "Это может занять несколько минут..."

        if CMAKE_ARGS="-DLLAMA_METAL=on" python3 -m pip install llama-cpp-python --quiet; then
            echo "✅ llama-cpp-python установлен с Metal поддержкой!"
        else
            echo "⚠️  Не удалось установить с Metal, устанавливаем базовую версию..."
            python3 -m pip install llama-cpp-python --quiet
        fi
    else
        echo "💻 Обнаружен Intel Mac"
        echo "Устанавливаем базовые зависимости..."
        echo ""

        python3 -m pip install --upgrade pip --quiet
        python3 -m pip install rich huggingface-hub --quiet

        echo "📥 Установка llama-cpp-python..."
        python3 -m pip install llama-cpp-python --quiet
    fi

    # Опциональные зависимости
    echo ""
    echo "📥 Установка опциональных зависимостей..."
    python3 -m pip install openai --quiet 2>/dev/null || true

    echo ""
    echo "✅ Все зависимости установлены!"
else
    echo "✅ Все зависимости уже установлены!"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Запуск AI CLI..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Запуск программы
python3 ai_cli.py
