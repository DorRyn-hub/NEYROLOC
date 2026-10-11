#!/usr/bin/env python3
"""
Создание иконок для всех платформ из .icns файла
"""

import subprocess
import os
from pathlib import Path

def create_icons():
    """Создает иконки для всех платформ"""

    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)

    icns_file = assets_dir / "icon.icns"

    if not icns_file.exists():
        print(f"❌ Файл {icns_file} не найден!")
        return False

    print("🎨 Создание иконок для всех платформ...")
    print(f"📁 Исходный файл: {icns_file}")

    # 1. Извлечь PNG из ICNS (macOS уже есть)
    print("\n1️⃣ Извлечение PNG из ICNS...")

    try:
        # Используем sips (встроенная утилита macOS) для извлечения PNG
        png_file = assets_dir / "icon.png"
        result = subprocess.run(
            ["sips", "-s", "format", "png", str(icns_file), "--out", str(png_file)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ PNG создан: {png_file}")
        else:
            print(f"⚠️ Не удалось создать PNG через sips, попробуем другой метод...")
            # Альтернативный метод - используем iconutil
            iconset_dir = assets_dir / "icon.iconset"
            subprocess.run(["iconutil", "-c", "iconset", str(icns_file), "-o", str(iconset_dir)])

            # Найти самую большую иконку
            largest = max(iconset_dir.glob("*.png"), key=lambda p: os.path.getsize(p))
            subprocess.run(["cp", str(largest), str(png_file)])
            subprocess.run(["rm", "-rf", str(iconset_dir)])
            print(f"✅ PNG создан: {png_file}")

    except Exception as e:
        print(f"❌ Ошибка при создании PNG: {e}")
        return False

    # 2. Создать ICO для Windows
    print("\n2️⃣ Создание ICO для Windows...")

    try:
        ico_file = assets_dir / "icon.ico"

        # Проверяем наличие PIL/Pillow
        try:
            from PIL import Image

            # Загружаем PNG
            img = Image.open(png_file)

            # Создаем несколько размеров для ICO
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

            # Создаем ICO файл
            img.save(
                ico_file,
                format='ICO',
                sizes=sizes
            )
            print(f"✅ ICO создан: {ico_file}")

        except ImportError:
            print("⚠️ Pillow не установлен, используем ImageMagick...")

            # Пробуем ImageMagick
            result = subprocess.run(
                ["convert", str(png_file), "-define", "icon:auto-resize=256,128,64,48,32,16", str(ico_file)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ ICO создан: {ico_file}")
            else:
                print(f"❌ ImageMagick не найден. Установите Pillow или ImageMagick")
                print("   Установка Pillow: pip install Pillow")
                print("   Установка ImageMagick: brew install imagemagick")

    except Exception as e:
        print(f"❌ Ошибка при создании ICO: {e}")

    # 3. Создать PNG разных размеров для Linux
    print("\n3️⃣ Создание PNG разных размеров для Linux...")

    try:
        from PIL import Image

        img = Image.open(png_file)

        # Стандартные размеры для Linux
        linux_sizes = {
            'icon_16x16.png': (16, 16),
            'icon_32x32.png': (32, 32),
            'icon_48x48.png': (48, 48),
            'icon_64x64.png': (64, 64),
            'icon_128x128.png': (128, 128),
            'icon_256x256.png': (256, 256),
            'icon_512x512.png': (512, 512),
        }

        for filename, size in linux_sizes.items():
            output_file = assets_dir / filename
            resized = img.resize(size, Image.Resampling.LANCZOS)
            resized.save(output_file, 'PNG')

        print(f"✅ PNG иконки для Linux созданы")

    except ImportError:
        print("⚠️ Pillow не установлен для создания PNG разных размеров")
        print("   Установка: pip install Pillow")
    except Exception as e:
        print(f"⚠️ Ошибка при создании PNG: {e}")

    print("\n" + "="*50)
    print("✨ Готово! Проверьте директорию assets/")
    print("="*50)

    # Показать созданные файлы
    print("\nСозданные файлы:")
    for file in sorted(assets_dir.glob("icon*")):
        size = os.path.getsize(file)
        print(f"  📄 {file.name} ({size:,} bytes)")

    return True

if __name__ == "__main__":
    create_icons()
