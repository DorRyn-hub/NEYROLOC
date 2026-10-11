#!/usr/bin/env python
"""
START_NEYROLOCK.pyw - Запуск NEYROLOCK v3.0 Dashboard

Windows: Двойной клик на этот файл запустит приложение БЕЗ консольного окна.
"""
import subprocess
import sys
from pathlib import Path

# Получаем директорию проекта (lmstudio-python рядом с START)
project_dir = Path(__file__).parent.parent / "lmstudio-python"

# Запускаем основной GUI
subprocess.Popen([sys.executable, str(project_dir / "ai_gui_v3.py")])
