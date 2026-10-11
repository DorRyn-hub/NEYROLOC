#!/bin/bash
# START_NEYROLOCK.command - Запуск NEYROLOCK v3.0 Dashboard
#
# macOS: Двойной клик на этот файл в Finder запустит приложение.

# Переход в директорию lmstudio-python (рядом с START)
cd "$(dirname "$0")/../lmstudio-python"

echo "NEYROLOCK v3.0 Dashboard"
echo "========================"
echo ""

python3 ai_gui_v3.py
