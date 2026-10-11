#!/bin/bash
# Rebuild NEYROLOC NEW.app + NEYROLOC NEW.dmg from source.
#
# Why a compiled launcher.c instead of a shell script or AppleScript wrapper:
# - A shell script as CFBundleExecutable gets misdetected for architecture by
#   LaunchServices on this macOS version and crashes under Rosetta translation.
# - An AppleScript `do shell script` wrapper avoids that crash, but spawns
#   Python as a *child* process (applet -> /bin/sh -> python), so the running
#   GUI process is never the bundle's own process and macOS shows "Python" in
#   the menu bar/Dock instead of the app name.
# launcher.c is a real Mach-O executable that execve()s directly into the
# venv's python (same PID), so the LaunchServices identity assigned at launch
# carries over to the interpreter that owns the window.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$(mktemp -d)"
APP="$BUILD_DIR/NEYROLOC NEW.app"

echo "Building in $BUILD_DIR"

# --- icon ---
mkdir -p "$BUILD_DIR/AppIcon.iconset"
"$PROJECT_DIR/NEYROLOCK_5/.venv/bin/python" - "$BUILD_DIR/icon_1024.png" <<'EOF'
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
m, r = size * 2 // 64, size * 17 // 64
painter.drawRoundedRect(m, m, size - 2 * m, size - 2 * m, r, r)
painter.setPen(QColor("#ffffff"))
font = QFont("Arial", int(size * 31 / 64), QFont.Weight.Bold)
painter.setFont(font)
painter.drawText(pixmap.rect(), Qt.AlignCenter, "N")
painter.end()
pixmap.save(sys.argv[1], "PNG")
EOF

for size_pair in "16 icon_16x16" "32 icon_16x16@2x" "32 icon_32x32" "64 icon_32x32@2x" \
                 "128 icon_128x128" "256 icon_128x128@2x" "256 icon_256x256" \
                 "512 icon_256x256@2x" "512 icon_512x512"; do
    set -- $size_pair
    sips -z "$1" "$1" "$BUILD_DIR/icon_1024.png" --out "$BUILD_DIR/AppIcon.iconset/$2.png" >/dev/null
done
cp "$BUILD_DIR/icon_1024.png" "$BUILD_DIR/AppIcon.iconset/icon_512x512@2x.png"
iconutil -c icns "$BUILD_DIR/AppIcon.iconset" -o "$BUILD_DIR/AppIcon.icns"

# --- native launcher ---
clang -O2 -arch arm64 -arch x86_64 -o "$BUILD_DIR/launcher" "$PROJECT_DIR/packaging/launcher.c"

# --- bundle ---
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BUILD_DIR/launcher" "$APP/Contents/MacOS/launcher"
chmod +x "$APP/Contents/MacOS/launcher"
cp "$BUILD_DIR/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"

cat > "$APP/Contents/Info.plist" <<PLIST
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
    <string>1.1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.1</string>
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

# --- install + dmg ---
rm -rf "/Applications/NEYROLOC NEW.app"
cp -R "$APP" "/Applications/"

STAGE="$BUILD_DIR/dmg_stage"
mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
rm -f "$HOME/Desktop/NEYROLOC NEW.dmg"
hdiutil create -volname "NEYROLOC NEW" -srcfolder "$STAGE" -ov -format UDZO "$HOME/Desktop/NEYROLOC NEW.dmg"

rm -rf "$BUILD_DIR"
echo "Done: installed to /Applications, dmg on Desktop."
