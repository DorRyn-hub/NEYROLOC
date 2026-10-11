#!/bin/bash
# Создание macOS .app приложения для NEYROLOCK

APP_NAME="NEYROLOCK"
APP_DIR="$APP_NAME.app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Создание приложения $APP_NAME.app..."

# Удаляем старое приложение если есть
rm -rf "$SCRIPT_DIR/$APP_DIR"

# Создаем структуру .app
mkdir -p "$SCRIPT_DIR/$APP_DIR/Contents/MacOS"
mkdir -p "$SCRIPT_DIR/$APP_DIR/Contents/Resources"

# Создаем Info.plist
cat > "$SCRIPT_DIR/$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>NEYROLOCK</string>
    <key>CFBundleDisplayName</key>
    <string>NEYROLOCK</string>
    <key>CFBundleIdentifier</key>
    <string>com.neyrolock.app</string>
    <key>CFBundleVersion</key>
    <string>3.0</string>
    <key>CFBundleShortVersionString</key>
    <string>3.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF

# Создаем launcher скрипт
cat > "$SCRIPT_DIR/$APP_DIR/Contents/MacOS/launcher" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
exec python3 "$SCRIPT_DIR/ai_gui_v3.py"
EOF

chmod +x "$SCRIPT_DIR/$APP_DIR/Contents/MacOS/launcher"

# Создаем иконку (простой PNG -> ICNS)
echo "🎨 Создание иконки..."

# Создаем временную директорию для иконки
ICONSET_DIR="$SCRIPT_DIR/AppIcon.iconset"
mkdir -p "$ICONSET_DIR"

# Создаем простую иконку с помощью Python
python3 << 'PYTHON_EOF'
import subprocess
import os
from pathlib import Path

script_dir = Path(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd())

# Создаем SVG иконку
svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024" height="1024" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea"/>
      <stop offset="100%" style="stop-color:#764ba2"/>
    </linearGradient>
    <linearGradient id="brain" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ff6b9d"/>
      <stop offset="100%" style="stop-color:#c084fc"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect x="64" y="64" width="896" height="896" rx="200" fill="url(#bg)"/>

  <!-- Brain icon -->
  <g transform="translate(512, 512) scale(0.6)">
    <!-- Left hemisphere -->
    <path d="M-200,-250 C-350,-250 -400,-100 -400,0 C-400,150 -300,250 -150,280 C-100,290 -50,280 0,250"
          fill="url(#brain)" stroke="#ffffff" stroke-width="20"/>
    <!-- Right hemisphere -->
    <path d="M200,-250 C350,-250 400,-100 400,0 C400,150 300,250 150,280 C100,290 50,280 0,250"
          fill="url(#brain)" stroke="#ffffff" stroke-width="20"/>
    <!-- Connection -->
    <rect x="-50" y="-100" width="100" height="200" rx="20" fill="#ffffff" opacity="0.8"/>
    <!-- Neural dots -->
    <circle cx="-250" cy="-100" r="30" fill="#ffffff"/>
    <circle cx="-300" cy="50" r="25" fill="#ffffff"/>
    <circle cx="-200" cy="150" r="20" fill="#ffffff"/>
    <circle cx="250" cy="-100" r="30" fill="#ffffff"/>
    <circle cx="300" cy="50" r="25" fill="#ffffff"/>
    <circle cx="200" cy="150" r="20" fill="#ffffff"/>
  </g>

  <!-- Lock icon at bottom -->
  <g transform="translate(512, 750)">
    <rect x="-60" y="-20" width="120" height="80" rx="10" fill="#4ade80"/>
    <path d="M-30,-20 L-30,-50 C-30,-80 30,-80 30,-50 L30,-20"
          fill="none" stroke="#4ade80" stroke-width="20"/>
    <circle cx="0" cy="20" r="15" fill="#0d0d1a"/>
  </g>
</svg>'''

svg_path = script_dir / "icon.svg"
with open(svg_path, 'w') as f:
    f.write(svg_content)

print("✅ SVG иконка создана")

# Конвертируем SVG в PNG разных размеров с помощью sips или qlmanage
# Сначала попробуем с помощью встроенных инструментов macOS

# Если есть rsvg-convert (homebrew: librsvg)
try:
    for size in [16, 32, 64, 128, 256, 512, 1024]:
        png_name = f"icon_{size}x{size}.png"
        subprocess.run([
            "rsvg-convert", "-w", str(size), "-h", str(size),
            str(svg_path), "-o", str(script_dir / "AppIcon.iconset" / png_name)
        ], check=True, capture_output=True)
    print("✅ PNG иконки созданы через rsvg-convert")
except Exception:
    # Fallback: создаем простой PNG через Python
    print("⚠️ rsvg-convert не найден, создаем базовую PNG иконку...")

    # Создаем простой цветной квадрат как fallback
    for size in [16, 32, 64, 128, 256, 512, 1024]:
        png_name = f"icon_{size}x{size}.png"
        # Используем sips для создания пустого изображения
        pass

PYTHON_EOF

# Проверяем есть ли rsvg-convert
if command -v rsvg-convert &> /dev/null; then
    echo "✅ Найден rsvg-convert"
    for size in 16 32 64 128 256 512 1024; do
        rsvg-convert -w $size -h $size "$SCRIPT_DIR/icon.svg" -o "$ICONSET_DIR/icon_${size}x${size}.png"
        if [ $size -le 512 ]; then
            # Создаем @2x версии
            double=$((size * 2))
            if [ $double -le 1024 ]; then
                rsvg-convert -w $double -h $double "$SCRIPT_DIR/icon.svg" -o "$ICONSET_DIR/icon_${size}x${size}@2x.png"
            fi
        fi
    done
else
    echo "⚠️ rsvg-convert не найден. Установите: brew install librsvg"
    echo "   Или создайте иконку вручную"

    # Создаем пустую иконку как placeholder
    # Используем Python с PIL если доступен
    python3 << 'FALLBACK_ICON'
try:
    from PIL import Image, ImageDraw
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
    iconset_dir = os.path.join(script_dir, "AppIcon.iconset")

    for size in [16, 32, 64, 128, 256, 512, 1024]:
        img = Image.new('RGBA', (size, size), (102, 126, 234, 255))
        draw = ImageDraw.Draw(img)

        # Рисуем простой мозг
        center = size // 2
        r = size // 3

        # Два полукруга
        draw.ellipse([center-r-r//2, center-r, center-r//4, center+r], fill=(255, 107, 157, 255))
        draw.ellipse([center+r//4, center-r, center+r+r//2, center+r], fill=(192, 132, 252, 255))

        # Центральная линия
        draw.rectangle([center-size//20, center-r//2, center+size//20, center+r//2], fill=(255, 255, 255, 200))

        img.save(os.path.join(iconset_dir, f"icon_{size}x{size}.png"))

        # @2x версии
        if size <= 512:
            double = size * 2
            if double <= 1024:
                img2 = Image.new('RGBA', (double, double), (102, 126, 234, 255))
                draw2 = ImageDraw.Draw(img2)
                center2 = double // 2
                r2 = double // 3
                draw2.ellipse([center2-r2-r2//2, center2-r2, center2-r2//4, center2+r2], fill=(255, 107, 157, 255))
                draw2.ellipse([center2+r2//4, center2-r2, center2+r2+r2//2, center2+r2], fill=(192, 132, 252, 255))
                draw2.rectangle([center2-double//20, center2-r2//2, center2+double//20, center2+r2//2], fill=(255, 255, 255, 200))
                img2.save(os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png"))

    print("✅ Иконки созданы через Pillow")
except ImportError:
    print("⚠️ Pillow не установлен. Устанавливаем...")
    import subprocess
    subprocess.run(["pip3", "install", "Pillow"])
    print("   Перезапустите скрипт")
except Exception as e:
    print(f"❌ Ошибка: {e}")
FALLBACK_ICON
fi

# Конвертируем iconset в icns
if [ -d "$ICONSET_DIR" ] && [ "$(ls -A $ICONSET_DIR)" ]; then
    iconutil -c icns "$ICONSET_DIR" -o "$SCRIPT_DIR/$APP_DIR/Contents/Resources/AppIcon.icns" 2>/dev/null || {
        echo "⚠️ Не удалось создать .icns файл"
    }
fi

# Очищаем временные файлы
rm -rf "$ICONSET_DIR"
rm -f "$SCRIPT_DIR/icon.svg"

# Регистрируем приложение
touch "$SCRIPT_DIR/$APP_DIR"

echo ""
echo "✅ Приложение создано: $SCRIPT_DIR/$APP_DIR"
echo ""
echo "📌 Что дальше:"
echo "   1. Дважды кликните на NEYROLOCK.app чтобы запустить"
echo "   2. Перетащите в папку Applications для постоянной установки"
echo "   3. Добавьте в Dock для быстрого доступа"
echo ""
echo "🎯 Если иконка не отображается:"
echo "   touch $SCRIPT_DIR/$APP_DIR"
echo "   killall Finder"
echo ""

# Открываем папку с приложением
open "$SCRIPT_DIR"
