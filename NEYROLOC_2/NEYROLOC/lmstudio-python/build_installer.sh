#!/bin/bash
# ====================================================
# NEYROLOCK Universal Installer Builder
# Автоматически определяет ОС и создает установщик
# ====================================================

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

clear
echo ""
echo "╔════════════════════════════════════════╗"
echo "║  NEYROLOCK Universal Installer Builder ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Detect operating system
OS="$(uname -s)"
case "$OS" in
    Linux*)     PLATFORM="linux";;
    Darwin*)    PLATFORM="macos";;
    CYGWIN*|MINGW*|MSYS*) PLATFORM="windows";;
    *)          PLATFORM="unknown";;
esac

echo -e "${CYAN}Обнаружена платформа:${NC} ${MAGENTA}$PLATFORM${NC}"
echo ""

# Show ASCII art based on platform
case "$PLATFORM" in
    linux)
        echo "    🐧 Linux Build"
        ;;
    macos)
        echo "    🍎 macOS Build"
        ;;
    windows)
        echo "    🪟 Windows Build"
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build based on platform
case "$PLATFORM" in
    linux)
        echo -e "${GREEN}▶${NC} Запуск сборки для Linux..."
        echo ""
        sleep 1
        bash installers/linux/build_linux.sh
        ;;

    macos)
        echo -e "${GREEN}▶${NC} Запуск сборки для macOS..."
        echo ""
        sleep 1
        bash installers/macos/build_macos.sh
        ;;

    windows)
        echo -e "${YELLOW}⚠${NC}  Windows обнаружена"
        echo ""
        echo "Для сборки на Windows запустите:"
        echo ""
        echo -e "  ${CYAN}installers\\windows\\build_windows.bat${NC}"
        echo ""
        echo "Примечание: Скрипт должен быть запущен из"
        echo "Command Prompt или PowerShell"
        echo ""
        exit 1
        ;;

    unknown)
        echo -e "${RED}✗${NC} Неизвестная операционная система: $OS"
        echo ""
        echo "Пожалуйста, запустите скрипт сборки вручную:"
        echo ""
        echo "  Windows:  installers\\windows\\build_windows.bat"
        echo "  macOS:    bash installers/macos/build_macos.sh"
        echo "  Linux:    bash installers/linux/build_linux.sh"
        echo ""
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓ Сборка завершена!${NC}"
echo ""
echo "Проверьте директорию: ${CYAN}installers/output/${NC}"
echo ""
