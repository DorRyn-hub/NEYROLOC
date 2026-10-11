#!/bin/bash
# ====================================================
# NEYROLOCK macOS Installer Build Script
# Создает .app bundle и .dmg установщик для macOS
# ====================================================

set -e  # Exit on error

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода прогресса
print_step() {
    echo -e "\n${BLUE}[$1/$2]${NC} $3"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo ""
echo "========================================"
echo "   NEYROLOCK macOS Installer Builder   "
echo "========================================"
echo ""

# Check if Python is installed
print_step "1" "6" "Проверка зависимостей..."
echo ""

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 не найден!"
    echo "Установите Python 3.10+ с https://www.python.org/"
    exit 1
fi

print_success "Python $(python3 --version | cut -d' ' -f2) найден"

# Navigate to project root
cd "$(dirname "$0")/../.."
PROJECT_ROOT=$(pwd)

# Check PyInstaller
if ! python3 -c "import PyInstaller" &> /dev/null; then
    print_warning "PyInstaller не установлен, устанавливаю..."
    python3 -m pip install pyinstaller
fi

print_success "PyInstaller готов"

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    print_success "Обнаружен Apple Silicon ($ARCH) - будет использоваться Metal ускорение"
else
    print_success "Обнаружен Intel ($ARCH)"
fi

print_step "2" "6" "Очистка старых сборок..."
echo ""

rm -rf dist build
rm -rf installers/output/NEYROLOCK.app
rm -f installers/output/NEYROLOCK-3.0.0-macOS.dmg

print_success "Очистка завершена"

print_step "3" "6" "Установка зависимостей..."
echo ""

# Install dependencies
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet pyinstaller

# For macOS M1/M2/M3, install llama-cpp-python with Metal support
if [[ "$ARCH" == "arm64" ]]; then
    print_warning "Установка llama-cpp-python с Metal поддержкой..."
    CMAKE_ARGS="-DLLAMA_METAL=on" python3 -m pip install --quiet --upgrade --force-reinstall llama-cpp-python --no-cache-dir
    print_success "Metal поддержка установлена"
fi

print_success "Зависимости установлены"

print_step "4" "6" "Сборка .app bundle с PyInstaller..."
echo ""
echo "Это может занять несколько минут..."
echo ""

cd installers/pyinstaller

# Show progress during build
python3 -m PyInstaller neyrolock_gui.spec --clean --noconfirm 2>&1 | while IFS= read -r line; do
    if [[ "$line" == *"Building"* ]] || [[ "$line" == *"Analyzing"* ]]; then
        echo "  → $line"
    fi
done

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    print_error "Ошибка при сборке с PyInstaller!"
    exit 1
fi

print_success "PyInstaller завершил сборку"

# Move .app to output directory
mkdir -p ../output
cp -R dist/NEYROLOCK.app ../output/

print_success ".app bundle создан: installers/output/NEYROLOCK.app"

print_step "5" "6" "Создание DMG установщика..."
echo ""

cd ../macos

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    print_warning "create-dmg не найден, пытаюсь установить..."

    if command -v brew &> /dev/null; then
        brew install create-dmg || {
            print_warning "Не удалось установить create-dmg через brew"
            print_warning "Буду использовать hdiutil вместо этого"
        }
    else
        print_warning "Homebrew не найден, буду использовать hdiutil"
    fi
fi

# Create DMG
DMG_NAME="NEYROLOCK-3.0.0-macOS"
DMG_OUTPUT="../output/${DMG_NAME}.dmg"

# Remove old DMG if exists
rm -f "$DMG_OUTPUT"

if command -v create-dmg &> /dev/null; then
    print_success "Использую create-dmg для создания красивого установщика..."

    # Create DMG with create-dmg
    create-dmg \
        --volname "NEYROLOCK" \
        --volicon "${PROJECT_ROOT}/assets/icon.icns" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "NEYROLOCK.app" 200 190 \
        --hide-extension "NEYROLOCK.app" \
        --app-drop-link 600 185 \
        --no-internet-enable \
        "$DMG_OUTPUT" \
        "../output/NEYROLOCK.app" 2>&1 | grep -E "^(Creating|Adding|Copying|Finalizing)" || true

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "DMG создан с create-dmg"
    else
        print_warning "create-dmg не справился, использую hdiutil..."
        USE_HDIUTIL=1
    fi
else
    USE_HDIUTIL=1
fi

if [ -n "$USE_HDIUTIL" ]; then
    print_warning "Использую hdiutil для создания DMG..."

    # Create temporary directory for DMG contents
    DMG_TMP=$(mktemp -d)
    cp -R "../output/NEYROLOCK.app" "$DMG_TMP/"
    ln -s /Applications "$DMG_TMP/Applications"

    # Create DMG
    hdiutil create -volname "NEYROLOCK" \
        -srcfolder "$DMG_TMP" \
        -ov -format UDZO \
        "$DMG_OUTPUT" &> /dev/null

    # Cleanup
    rm -rf "$DMG_TMP"

    print_success "DMG создан с hdiutil"
fi

print_step "6" "6" "Проверка результатов..."
echo ""

# Get file sizes
APP_SIZE=$(du -sh "../output/NEYROLOCK.app" | cut -f1)
DMG_SIZE=$(du -sh "$DMG_OUTPUT" | cut -f1)

print_success "App bundle: ${APP_SIZE}"
print_success "DMG installer: ${DMG_SIZE}"

echo ""
echo "========================================"
echo -e "${GREEN}✨ Сборка завершена успешно! ✨${NC}"
echo "========================================"
echo ""
echo "Созданные файлы:"
echo "  📦 installers/output/NEYROLOCK.app"
echo "  💿 installers/output/${DMG_NAME}.dmg"
echo ""
echo "Теперь вы можете:"
echo "  1. Запустить: open installers/output/NEYROLOCK.app"
echo "  2. Установить из DMG: open installers/output/${DMG_NAME}.dmg"
echo "  3. Распространять DMG файл"
echo ""
echo "Пользователи увидят только красивую иконку программы,"
echo "исходный код будет скрыт внутри .app bundle."
echo ""

# Code signing reminder
if command -v codesign &> /dev/null; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💡 Совет: Для публичного распространения:"
    echo ""
    echo "  1. Подпишите приложение:"
    echo "     codesign --deep --force --sign \"Developer ID\" \\"
    echo "       installers/output/NEYROLOCK.app"
    echo ""
    echo "  2. Нотаризуйте с Apple:"
    echo "     xcrun altool --notarize-app --file ${DMG_NAME}.dmg"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi
