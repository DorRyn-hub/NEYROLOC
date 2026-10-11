#!/bin/bash
# Запуск NEYROLOCK с поддержкой русских горячих клавиш и Telegram

cd "$(dirname "$0")"

echo "🚀 Запуск NEYROLOCK v2.0..."
echo ""
echo "✨ Возможности:"
echo "   • 🎨 Красочный темный интерфейс"
echo "   • ⌨️  Горячие клавиши на русской раскладке (⌘Ы, ⌘Й, ⌘В...)"
echo "   • 📱 Интеграция с Telegram-ботом"
echo "   • 🔧 Улучшенные настройки шрифтов"
echo ""

python3 ai_gui_v2.py
