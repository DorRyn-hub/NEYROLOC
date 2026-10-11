#!/bin/bash
# ====================================================
# NEYROLOCK Linux Installer Build Script
# Создает .deb, .rpm и универсальный установщик
# ====================================================

set -e  # Exit on error

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для вывода
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

print_info() {
    echo -e "${CYAN}[ℹ]${NC} $1"
}

echo ""
echo "========================================"
echo "   NEYROLOCK Linux Installer Builder   "
echo "========================================"
echo ""

# Check if Python is installed
print_step "1" "7" "Проверка зависимостей..."
echo ""

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 не найден!"
    echo "Установите Python 3.10+ с вашего пакетного менеджера"
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

# Check dpkg-deb
if ! command -v dpkg-deb &> /dev/null; then
    print_warning "dpkg-deb не найден - .deb пакеты не будут созданы"
else
    print_success "dpkg-deb найден"
fi

print_step "2" "7" "Очистка старых сборок..."
echo ""

rm -rf dist build
rm -rf installers/linux/neyrolock_*_amd64
rm -f installers/output/*.deb
rm -f installers/output/*.rpm
rm -f installers/output/*-Linux-Installer.sh

print_success "Очистка завершена"

print_step "3" "7" "Установка зависимостей..."
echo ""

python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet pyinstaller

print_success "Зависимости установлены"

print_step "4" "7" "Сборка приложения с PyInstaller..."
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

# Create output directory
mkdir -p ../output

print_step "5" "7" "Создание .deb пакета (Debian/Ubuntu)..."
echo ""

cd ../linux

# Create .deb package structure
DEB_NAME="neyrolock_3.0.0_amd64"
DEB_DIR="${DEB_NAME}"

if command -v dpkg-deb &> /dev/null; then
    rm -rf "$DEB_DIR"
    mkdir -p "$DEB_DIR/DEBIAN"
    mkdir -p "$DEB_DIR/opt/neyrolock"
    mkdir -p "$DEB_DIR/usr/share/applications"
    mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$DEB_DIR/usr/bin"

    print_info "Копирование файлов приложения..."
    cp -R ../pyinstaller/dist/NEYROLOCK/* "$DEB_DIR/opt/neyrolock/"

    print_info "Создание метаданных пакета..."
    # Create control file
    cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: neyrolock
Version: 3.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.10), python3-tk
Maintainer: NEYROLOCK Team <team@neyrolock.ai>
Description: Local AI Models Desktop Application
 NEYROLOCK is a desktop application for working with local AI models.
 Features include GUI interface, Telegram bot integration, and model management.
Homepage: https://github.com/neyrolock/neyrolock
EOF

    # Create postinst script
    cat > "$DEB_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
ln -sf /opt/neyrolock/NEYROLOCK /usr/bin/neyrolock
chmod +x /usr/bin/neyrolock
echo ""
echo "========================================"
echo "  NEYROLOCK установлен успешно!"
echo "========================================"
echo ""
echo "Запустите 'neyrolock' в терминале"
echo "или найдите в меню приложений"
echo ""
EOF
    chmod 755 "$DEB_DIR/DEBIAN/postinst"

    # Create postrm script
    cat > "$DEB_DIR/DEBIAN/postrm" << 'EOF'
#!/bin/bash
rm -f /usr/bin/neyrolock
EOF
    chmod 755 "$DEB_DIR/DEBIAN/postrm"

    # Create desktop entry
    cat > "$DEB_DIR/usr/share/applications/neyrolock.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NEYROLOCK
Comment=Local AI Models Desktop Application
Exec=/opt/neyrolock/NEYROLOCK
Icon=neyrolock
Terminal=false
Categories=Utility;Science;ArtificialIntelligence;
Keywords=ai;llm;chatbot;local;models;
EOF

    # Copy icon if exists
    if [ -f "${PROJECT_ROOT}/assets/icon_256x256.png" ]; then
        cp "${PROJECT_ROOT}/assets/icon_256x256.png" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/neyrolock.png"
    elif [ -f "${PROJECT_ROOT}/assets/icon.png" ]; then
        cp "${PROJECT_ROOT}/assets/icon.png" "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/neyrolock.png"
    fi

    print_info "Сборка .deb пакета..."
    dpkg-deb --build "$DEB_DIR" &> /dev/null
    mv "${DEB_NAME}.deb" "../output/"
    rm -rf "$DEB_DIR"

    DEB_SIZE=$(du -sh "../output/${DEB_NAME}.deb" | cut -f1)
    print_success ".deb пакет создан (${DEB_SIZE})"
else
    print_warning ".deb пакет пропущен (dpkg-deb не найден)"
fi

print_step "6" "7" "Создание .rpm пакета (Fedora/RedHat)..."
echo ""

if command -v rpmbuild &> /dev/null; then
    RPM_NAME="neyrolock-3.0.0-1.x86_64"

    print_info "Настройка RPM build структуры..."
    mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

    # Create source tarball
    cd ../pyinstaller/dist
    tar czf ~/rpmbuild/SOURCES/neyrolock-3.0.0.tar.gz NEYROLOCK/ 2>/dev/null
    cd ../../linux

    print_info "Создание RPM spec файла..."
    # Create spec file (abbreviated for brevity)
    cat > ~/rpmbuild/SPECS/neyrolock.spec << 'EOF'
Name:           neyrolock
Version:        3.0.0
Release:        1%{?dist}
Summary:        Local AI Models Desktop Application

License:        MIT
URL:            https://github.com/neyrolock/neyrolock

Requires:       python3 >= 3.10

%description
NEYROLOCK - Local AI Models Desktop Application

%prep
%setup -q

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/neyrolock
cp -R * $RPM_BUILD_ROOT/opt/neyrolock/

%post
ln -sf /opt/neyrolock/NEYROLOCK /usr/bin/neyrolock
chmod +x /usr/bin/neyrolock

%postun
rm -f /usr/bin/neyrolock

%files
/opt/neyrolock

%changelog
* $(date +"%a %b %d %Y") NEYROLOCK Team - 3.0.0-1
- Initial release
EOF

    print_info "Сборка RPM пакета..."
    rpmbuild -ba ~/rpmbuild/SPECS/neyrolock.spec &> /dev/null || true

    if [ -f ~/rpmbuild/RPMS/x86_64/${RPM_NAME}.rpm ]; then
        cp ~/rpmbuild/RPMS/x86_64/${RPM_NAME}.rpm ../output/
        RPM_SIZE=$(du -sh "../output/${RPM_NAME}.rpm" | cut -f1)
        print_success ".rpm пакет создан (${RPM_SIZE})"
    else
        print_warning ".rpm сборка завершена, но файл не найден"
    fi
else
    print_warning ".rpm пакет пропущен (rpmbuild не найден)"
fi

print_step "7" "7" "Создание универсального установщика..."
echo ""

INSTALLER_NAME="NEYROLOCK-3.0.0-Linux-Installer.sh"

print_info "Создание самораспаковывающегося установщика..."

cat > "../output/$INSTALLER_NAME" << 'INSTALLER_EOF'
#!/bin/bash
# ====================================================
# NEYROLOCK Universal Linux Installer
# Самораспаковывающийся установщик для любого Linux
# ====================================================

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear
echo ""
echo "========================================"
echo "   NEYROLOCK Installer v3.0.0"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Для установки требуются права администратора.${NC}"
    echo "Введите пароль для продолжения..."
    echo ""
    sudo bash "$0" "$@"
    exit $?
fi

INSTALL_DIR="/opt/neyrolock"
BIN_LINK="/usr/local/bin/neyrolock"

echo -e "${BLUE}[1/4]${NC} Подготовка к установке..."
mkdir -p "$INSTALL_DIR"

echo -e "${BLUE}[2/4]${NC} Распаковка файлов приложения..."
ARCHIVE=$(awk '/^__PAYLOAD__/ {print NR + 1; exit 0; }' "$0")
tail -n +${ARCHIVE} "$0" | tar xzf - -C "$INSTALL_DIR"

echo -e "${BLUE}[3/4]${NC} Создание системных ссылок..."
ln -sf "$INSTALL_DIR/NEYROLOCK/NEYROLOCK" "$BIN_LINK"
chmod +x "$BIN_LINK"

echo -e "${BLUE}[4/4]${NC} Регистрация в системе..."
mkdir -p /usr/share/applications
cat > /usr/share/applications/neyrolock.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=NEYROLOCK
Comment=Local AI Models Desktop Application
Exec=/opt/neyrolock/NEYROLOCK/NEYROLOCK
Icon=neyrolock
Terminal=false
Categories=Utility;Science;ArtificialIntelligence;
Keywords=ai;llm;chatbot;local;models;
DESKTOP_EOF

echo ""
echo "========================================"
echo -e "${GREEN}✓ Установка завершена успешно!${NC}"
echo "========================================"
echo ""
echo "Запустите 'neyrolock' в терминале"
echo "или найдите в меню приложений"
echo ""
echo "Для удаления:"
echo "  sudo rm -rf /opt/neyrolock"
echo "  sudo rm -f /usr/local/bin/neyrolock"
echo "  sudo rm -f /usr/share/applications/neyrolock.desktop"
echo ""

exit 0

__PAYLOAD__
INSTALLER_EOF

# Append the application archive
cd ../pyinstaller/dist
tar czf - NEYROLOCK/ >> "../../output/$INSTALLER_NAME"
cd ../../linux

# Make installer executable
chmod +x "../output/$INSTALLER_NAME"

INSTALLER_SIZE=$(du -sh "../output/$INSTALLER_NAME" | cut -f1)
print_success "Универсальный установщик создан (${INSTALLER_SIZE})"

echo ""
echo "========================================"
echo -e "${GREEN}✨ Сборка завершена успешно! ✨${NC}"
echo "========================================"
echo ""
echo "Созданные пакеты:"
echo ""

if [ -f "../output/${DEB_NAME}.deb" ]; then
    echo "  📦 installers/output/${DEB_NAME}.deb"
    echo "     Установка: sudo dpkg -i ${DEB_NAME}.deb"
    echo ""
fi

if [ -f "../output/${RPM_NAME}.rpm" ]; then
    echo "  📦 installers/output/${RPM_NAME}.rpm"
    echo "     Установка: sudo rpm -i ${RPM_NAME}.rpm"
    echo ""
fi

echo "  📦 installers/output/${INSTALLER_NAME}"
echo "     Установка: sudo bash ${INSTALLER_NAME}"
echo ""

echo "Пользователи увидят только иконку программы в меню,"
echo "исходный код будет скрыт внутри пакета."
echo ""
