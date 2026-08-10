#!/bin/bash
# Build a NEYROLOC NEW local macOS bundle and DMG.
#
# The app contains the current sources and venv and resolves both relative to
# Contents/Resources.  It is intentionally a *local bundle*, not a standalone
# Python distribution: the copied venv still links to the Python.framework
# installed on the build Mac.  A distributable standalone app should migrate
# to PyInstaller or py2app in a separate packaging change.
set -euo pipefail

INSTALL_APP=false
case "${1:-}" in
    "") ;;
    --install) INSTALL_APP=true ;;
    -h|--help)
        echo "Usage: packaging/build_app.sh [--install]"
        echo "Builds into ./dist; --install also replaces /Applications/NEYROLOC NEW.app."
        exit 0
        ;;
    *)
        echo "Unknown option: $1" >&2
        exit 2
        ;;
esac

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/NEYROLOCK_5/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
DIST_DIR="${NEYROLOC_DIST_DIR:-$PROJECT_DIR/dist}"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/neyroloc-build.XXXXXX")"
APP="$BUILD_DIR/NEYROLOC NEW.app"
OUTPUT_APP="$DIST_DIR/NEYROLOC NEW.app"
OUTPUT_DMG="$DIST_DIR/NEYROLOC NEW.dmg"

cleanup() {
    rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

for tool in clang codesign hdiutil iconutil rsync sips; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Missing required macOS tool: $tool" >&2
        exit 1
    fi
done
if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Missing active environment: $VENV_PYTHON" >&2
    echo "Create it and install NEYROLOCK_5/requirements.txt first." >&2
    exit 1
fi

BASE_PYTHON="$($VENV_PYTHON -c 'import sys; print(sys._base_executable)')"
if [[ ! -x "$BASE_PYTHON" ]]; then
    echo "The venv base Python is unavailable: $BASE_PYTHON" >&2
    exit 1
fi
echo "Building local bundle in $BUILD_DIR"
echo "Runtime requirement on target Mac: $BASE_PYTHON (external Python.framework)"

# --- icon ---
mkdir -p "$BUILD_DIR/AppIcon.iconset"
QT_QPA_PLATFORM=offscreen "$VENV_PYTHON" - "$BUILD_DIR/icon_1024.png" <<'PY'
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

app = QApplication.instance() or QApplication([])
size = 1024
pixmap = QPixmap(size, size)
pixmap.fill(Qt.transparent)
painter = QPainter(pixmap)
painter.setRenderHint(QPainter.Antialiasing)
painter.setBrush(QColor("#6d8cff"))
painter.setPen(Qt.NoPen)
margin, radius = size * 2 // 64, size * 17 // 64
painter.drawRoundedRect(
    margin,
    margin,
    size - 2 * margin,
    size - 2 * margin,
    radius,
    radius,
)
painter.setPen(QColor("#ffffff"))
painter.setFont(QFont("Arial", int(size * 31 / 64), QFont.Weight.Bold))
painter.drawText(pixmap.rect(), Qt.AlignCenter, "N")
painter.end()
if not pixmap.save(sys.argv[1], "PNG"):
    raise SystemExit("failed to render app icon")
PY

for size_pair in "16 icon_16x16" "32 icon_16x16@2x" "32 icon_32x32" "64 icon_32x32@2x" \
                 "128 icon_128x128" "256 icon_128x128@2x" "256 icon_256x256" \
                 "512 icon_256x256@2x" "512 icon_512x512"; do
    set -- $size_pair
    sips -z "$1" "$1" "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/$2.png" >/dev/null
done
cp "$BUILD_DIR/icon_1024.png" "$BUILD_DIR/AppIcon.iconset/icon_512x512@2x.png"
iconutil -c icns "$BUILD_DIR/AppIcon.iconset" -o "$BUILD_DIR/AppIcon.icns"

# --- native launcher ---
clang -O2 -Wall -Wextra -Werror -arch arm64 -arch x86_64 \
    -o "$BUILD_DIR/launcher" "$PROJECT_DIR/packaging/launcher.c"

# --- app-relative source/runtime layout ---
APP_RESOURCES="$APP/Contents/Resources"
APP_SOURCE="$APP_RESOURCES/app"
mkdir -p "$APP/Contents/MacOS" "$APP_SOURCE/NEYROLOCK_5" "$APP_RESOURCES/venv"
cp "$BUILD_DIR/launcher" "$APP/Contents/MacOS/launcher"
chmod +x "$APP/Contents/MacOS/launcher"
cp "$BUILD_DIR/AppIcon.icns" "$APP_RESOURCES/AppIcon.icns"
cp "$PROJECT_DIR/main.py" "$APP_SOURCE/main.py"

rsync -a \
    --exclude '.venv' \
    --exclude '.DS_Store' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "$PROJECT_DIR/NEYROLOCK_5/" "$APP_SOURCE/NEYROLOCK_5/"
rsync -a \
    --exclude '.DS_Store' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "$VENV_DIR/" "$APP_RESOURCES/venv/"

# remote_server.py serves the APK from the project-root-compatible path.
if [[ -f "$PROJECT_DIR/packaging/android/NEYROLOC.apk" ]]; then
    mkdir -p "$APP_SOURCE/packaging/android"
    cp "$PROJECT_DIR/packaging/android/NEYROLOC.apk" \
        "$APP_SOURCE/packaging/android/NEYROLOC.apk"
fi

cat > "$APP_RESOURCES/LOCAL_BUNDLE.txt" <<TXT
This is a local NEYROLOC bundle, not a standalone Python distribution.
Its copied virtual environment requires the build Mac's external Python.framework.
Rebuild on the target Mac if that framework is unavailable.
A truly standalone release requires a dedicated PyInstaller or py2app migration.
TXT

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>NEYROLOC NEW</string>
    <key>CFBundleDisplayName</key>
    <string>NEYROLOC NEW</string>
    <key>CFBundleIdentifier</key>
    <string>ru.dorryn.neyrolocnew</string>
    <key>CFBundleVersion</key>
    <string>1.2</string>
    <key>CFBundleShortVersionString</key>
    <string>1.2</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
</dict>
</plist>
PLIST

codesign --force --deep --sign - "$APP"

# --- safe default output: project-local dist ---
mkdir -p "$DIST_DIR"
rm -rf "$OUTPUT_APP"
mv "$APP" "$OUTPUT_APP"

DMG_STAGE="$BUILD_DIR/dmg_stage"
mkdir -p "$DMG_STAGE"
cp -R "$OUTPUT_APP" "$DMG_STAGE/"
ln -s /Applications "$DMG_STAGE/Applications"
rm -f "$OUTPUT_DMG"
hdiutil create -volname "NEYROLOC NEW" -srcfolder "$DMG_STAGE" \
    -ov -format UDZO "$OUTPUT_DMG" >/dev/null

if [[ "$INSTALL_APP" == true ]]; then
    INSTALL_TARGET="/Applications/NEYROLOC NEW.app"
    rm -rf "$INSTALL_TARGET"
    cp -R "$OUTPUT_APP" "$INSTALL_TARGET"
    echo "Installed: $INSTALL_TARGET"
fi

echo "Local app bundle: $OUTPUT_APP"
echo "Disk image: $OUTPUT_DMG"
