# 🎨 NEYROLOCK Assets

Эта директория содержит ресурсы для приложения NEYROLOCK.

## ⚡ Быстрый способ (рекомендуется)

```bash
# Из корня проекта
python3 create_icons.py
```

Этот скрипт автоматически создаст все необходимые иконки из существующего `icon.icns`.

---

## 📋 Требуемые файлы

### Иконки приложения

- **icon.png** - Основная иконка (256x256 или больше)
  - Используется для Linux desktop entry
  - Должна быть в формате PNG с прозрачностью

- **icon.ico** - Иконка для Windows
  - Многослойная иконка (16x16, 32x32, 48x48, 256x256)
  - Используется для .exe файла и ярлыков

- **icon.icns** - Иконка для macOS
  - Содержит несколько размеров (16x16 до 1024x1024)
  - Используется для .app bundle

## 🛠️ Создание иконок вручную

Если у вас есть исходная PNG иконка (рекомендуется 512x512 или больше):

### Создание icon.ico (Windows)

**Вариант 1: Используя ImageMagick (Linux/macOS)**
```bash
convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

**Вариант 2: Используя онлайн конвертер**
- https://icoconvert.com/
- https://convertio.co/png-ico/
- https://cloudconvert.com/png-to-ico

**Вариант 3: Используя GIMP**
1. Откройте icon.png в GIMP
2. File → Export As
3. Выберите .ico формат
4. Выберите размеры (16, 32, 48, 256)

### Создание icon.icns (macOS)

**На macOS (встроенные инструменты):**

```bash
#!/bin/bash
# Создайте iconset директорию
mkdir MyIcon.iconset

# Создайте все требуемые размеры
sips -z 16 16     icon.png --out MyIcon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out MyIcon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out MyIcon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out MyIcon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out MyIcon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out MyIcon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out MyIcon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out MyIcon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out MyIcon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out MyIcon.iconset/icon_512x512@2x.png

# Создайте .icns файл
iconutil -c icns MyIcon.iconset

# Переместите результат
mv MyIcon.icns icon.icns

# Очистите временные файлы
rm -rf MyIcon.iconset
```

**На Linux/Windows:**
- Используйте онлайн конвертер: https://cloudconvert.com/png-to-icns
- Или используйте `png2icns` (Linux): `png2icns icon.icns icon.png`

### Создание icon.png (Linux)

Если у вас уже есть .ico или .icns:

```bash
# Из .ico
convert icon.ico[0] -resize 256x256 icon.png

# Из .icns (на macOS)
sips -s format png icon.icns --out icon.png -z 256 256
```

## 🎨 Рекомендации по дизайну иконки

### Технические требования:
- **Размер**: 512x512 или 1024x1024 (для масштабирования)
- **Формат**: PNG с прозрачностью (alpha channel)
- **Цветовое пространство**: RGB или sRGB
- **Стиль**: Простой, узнаваемый, читаемый при маленьких размерах

### Дизайн рекомендации:
1. **Простота**: Иконка должна быть узнаваемой даже при 16x16
2. **Контраст**: Используйте контрастные цвета
3. **Центрирование**: Основной элемент должен быть в центре
4. **Padding**: Оставьте ~10% отступ от краев
5. **Тестирование**: Проверьте на разных размерах и фонах

### Тематика для NEYROLOCK:
- 🧠 Мозг (нейронные сети)
- 🔐 Замок (безопасность, локальность)
- 🤖 Робот/AI символ
- 💬 Чат баббл
- ⚡ Молния (скорость)
- 🎯 Комбинация символов

## 📦 Placeholder иконки

Если у вас нет готовых иконок, вы можете:

1. **Использовать временную текстовую иконку:**
   - Создайте простую иконку с буквой "N"
   - Используйте онлайн генераторы: https://favicon.io/

2. **Использовать стандартные иконки Python/Tkinter:**
   - Установщики будут работать без custom иконок
   - Будут использованы системные default иконки

3. **Нанять дизайнера:**
   - Fiverr, Upwork, 99designs
   - Стоимость: $10-50 для простой иконки

## 🔍 Проверка иконок

После создания проверьте:

```bash
# Проверьте размер и формат
file icon.png icon.ico icon.icns

# Проверьте размеры в PNG
identify icon.png

# Проверьте содержимое .ico
identify icon.ico

# Проверьте содержимое .icns (macOS)
iconutil -c iconset icon.icns -o test.iconset
ls -la test.iconset
```

## 📝 Лицензия иконок

Убедитесь, что у вас есть права на использование иконок:
- Созданы вами: ✅ OK
- Free icons (с attribution): ✅ OK (добавьте attribution в README)
- Stock icons (купленные): ✅ OK (проверьте лицензию)
- Скопированные из интернета: ❌ NOT OK

### Ресурсы для бесплатных иконок:
- https://icons8.com/ (бесплатно с attribution)
- https://flaticon.com/ (бесплатно с attribution)
- https://iconduck.com/ (полностью бесплатно)
- https://remixicon.com/ (open source)

---

**Если у вас нет иконок, установщики все равно соберутся и будут работать!**
