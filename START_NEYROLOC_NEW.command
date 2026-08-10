#!/bin/zsh
set -eu

PROJECT_DIR="${0:A:h}"
cd "$PROJECT_DIR"

# Явный override полезен для CI и для окружений, созданных вне репозитория.
if [[ -n "${NEYROLOC_PYTHON:-}" ]]; then
    PYTHON="$NEYROLOC_PYTHON"
elif [[ -x "$PROJECT_DIR/NEYROLOCK_5/.venv/bin/python" ]]; then
    PYTHON="$PROJECT_DIR/NEYROLOCK_5/.venv/bin/python"
elif [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1 \
        && python3 -c 'import PySide6' >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
else
    print -u2 "NEYROLOC: не найдено рабочее Python-окружение."
    print -u2 "Создайте NEYROLOCK_5/.venv и установите зависимости из NEYROLOCK_5/requirements.txt."
    exit 1
fi

exec "$PYTHON" "$PROJECT_DIR/main.py" "$@"
