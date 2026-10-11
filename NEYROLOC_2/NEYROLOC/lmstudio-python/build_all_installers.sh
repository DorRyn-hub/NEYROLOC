#!/bin/bash
# ====================================================
# NEYROLOCK - Сборка ВСЕХ установщиков одной командой
# Результат будет в папке ~/Downloads/NEYROLOCK-Installers/
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
echo "╔════════════════════════════════════════════════╗"
echo "║  NEYROLOCK - Сборка установщиков для всех ОС   ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Определяем директорию проекта
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# Создаем выходную директорию в Downloads
OUTPUT_DIR="$HOME/Downloads/NEYROLOCK-Installers"
mkdir -p "$OUTPUT_DIR"

echo -e "${CYAN}📦 Установщики будут сохранены в:${NC}"
echo -e "${GREEN}   $OUTPUT_DIR${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Шаг 1: Установка Pillow для создания иконок
echo -e "${BLUE}[1/5]${NC} Установка зависимостей..."
echo ""

if ! python3 -c "import PIL" &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Устанавливаю Pillow для создания иконок..."
    pip3 install Pillow --quiet
    echo -e "${GREEN}✓${NC} Pillow установлен"
else
    echo -e "${GREEN}✓${NC} Pillow уже установлен"
fi

if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Устанавливаю PyInstaller..."
    pip3 install pyinstaller --quiet
    echo -e "${GREEN}✓${NC} PyInstaller установлен"
else
    echo -e "${GREEN}✓${NC} PyInstaller уже установлен"
fi

# Шаг 2: Создание иконок
echo ""
echo -e "${BLUE}[2/5]${NC} Создание иконок для всех платформ..."
echo ""

python3 create_icons.py | grep "✅\|✓\|📄"

echo -e "${GREEN}✓${NC} Иконки созданы"

# Шаг 3: Сборка для macOS
echo ""
echo -e "${BLUE}[3/5]${NC} Сборка установщика для macOS..."
echo ""

bash installers/macos/build_macos.sh

# Копируем macOS установщики
if [ -d "installers/output/NEYROLOCK.app" ]; then
    cp -R "installers/output/NEYROLOCK.app" "$OUTPUT_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Скопирован: NEYROLOCK.app"
fi

if [ -f "installers/output/NEYROLOCK-3.0.0-macOS.dmg" ]; then
    cp "installers/output/NEYROLOCK-3.0.0-macOS.dmg" "$OUTPUT_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Скопирован: NEYROLOCK-3.0.0-macOS.dmg"
fi

# Шаг 4: Сборка для Linux
echo ""
echo -e "${BLUE}[4/5]${NC} Сборка установщиков для Linux..."
echo ""

bash installers/linux/build_linux.sh

# Копируем Linux установщики
if [ -f "installers/output/neyrolock_3.0.0_amd64.deb" ]; then
    cp "installers/output/neyrolock_3.0.0_amd64.deb" "$OUTPUT_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Скопирован: neyrolock_3.0.0_amd64.deb"
fi

if [ -f "installers/output/neyrolock-3.0.0-1.x86_64.rpm" ]; then
    cp "installers/output/neyrolock-3.0.0-1.x86_64.rpm" "$OUTPUT_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Скопирован: neyrolock-3.0.0-1.x86_64.rpm"
fi

if [ -f "installers/output/NEYROLOCK-3.0.0-Linux-Installer.sh" ]; then
    cp "installers/output/NEYROLOCK-3.0.0-Linux-Installer.sh" "$OUTPUT_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Скопирован: NEYROLOCK-3.0.0-Linux-Installer.sh"
fi

# Шаг 5: Создание README для пользователей
echo ""
echo -e "${BLUE}[5/5]${NC} Создание инструкций для пользователей..."
echo ""

cat > "$OUTPUT_DIR/README.txt" << 'EOF'
╔════════════════════════════════════════════════╗
║       NEYROLOCK v3.0.0 - Установщики          ║
╚════════════════════════════════════════════════╝

Выберите файл для вашей операционной системы:

🪟 WINDOWS:
   Файл: NEYROLOCK-3.0.0-Windows-Setup.exe
   Установка: Двойной клик → Следовать инструкциям

   ⚠️  ВНИМАНИЕ: Windows установщик нужно собрать на Windows!
   Этот файл можно создать только на компьютере с Windows.
   См. инструкции ниже.

🍎 macOS:
   Файл: NEYROLOCK-3.0.0-macOS.dmg
   Установка: Открыть DMG → Перетащить в Applications

   Альтернатива: NEYROLOCK.app
   Установка: Скопировать в /Applications

🐧 LINUX:

   Debian/Ubuntu:
   Файл: neyrolock_3.0.0_amd64.deb
   Установка: sudo dpkg -i neyrolock_3.0.0_amd64.deb

   Fedora/RedHat/CentOS:
   Файл: neyrolock-3.0.0-1.x86_64.rpm
   Установка: sudo rpm -i neyrolock-3.0.0-1.x86_64.rpm

   Универсальный (любой Linux):
   Файл: NEYROLOCK-3.0.0-Linux-Installer.sh
   Установка: sudo bash NEYROLOCK-3.0.0-Linux-Installer.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Как создать Windows установщик:

1. На компьютере с Windows откройте проект
2. Перейдите в: installers\windows\
3. Запустите: build_windows.bat
4. Готовый файл: installers\output\NEYROLOCK-3.0.0-Windows-Setup.exe

Или используйте виртуальную машину / GitHub Actions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ После установки:

- Программа появится в меню приложений
- Запуск в один клик
- Исходный код скрыт внутри установщика

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Техподдержка:
https://github.com/neyrolock/neyrolock/issues

EOF

echo -e "${GREEN}✓${NC} Создан README.txt с инструкциями"

# Создаем HTML версию README для красоты
cat > "$OUTPUT_DIR/README.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NEYROLOCK v3.0.0 - Установщики</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .os-section {
            margin: 30px 0;
            padding: 20px;
            background: #f9f9f9;
            border-left: 4px solid #4CAF50;
            border-radius: 5px;
        }
        .file {
            font-family: 'Courier New', monospace;
            background: #e8e8e8;
            padding: 5px 10px;
            border-radius: 3px;
            display: inline-block;
            margin: 5px 0;
        }
        .command {
            font-family: 'Courier New', monospace;
            background: #2d2d2d;
            color: #0f0;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            display: block;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .icon {
            font-size: 24px;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 NEYROLOCK v3.0.0 - Установщики</h1>

        <p>Выберите файл для вашей операционной системы:</p>

        <div class="os-section">
            <h2><span class="icon">🪟</span>Windows</h2>
            <p><strong>Файл:</strong> <span class="file">NEYROLOCK-3.0.0-Windows-Setup.exe</span></p>
            <p><strong>Установка:</strong> Двойной клик → Следовать инструкциям</p>

            <div class="warning">
                <strong>⚠️ ВНИМАНИЕ:</strong> Windows установщик нужно собрать на Windows!<br>
                Этот файл можно создать только на компьютере с Windows.
            </div>
        </div>

        <div class="os-section">
            <h2><span class="icon">🍎</span>macOS</h2>
            <p><strong>Файл:</strong> <span class="file">NEYROLOCK-3.0.0-macOS.dmg</span></p>
            <p><strong>Установка:</strong> Открыть DMG → Перетащить в Applications</p>
            <br>
            <p><strong>Альтернатива:</strong> <span class="file">NEYROLOCK.app</span></p>
            <p><strong>Установка:</strong> Скопировать в /Applications</p>
        </div>

        <div class="os-section">
            <h2><span class="icon">🐧</span>Linux</h2>

            <h3>Debian/Ubuntu</h3>
            <p><strong>Файл:</strong> <span class="file">neyrolock_3.0.0_amd64.deb</span></p>
            <code class="command">sudo dpkg -i neyrolock_3.0.0_amd64.deb</code>

            <h3>Fedora/RedHat/CentOS</h3>
            <p><strong>Файл:</strong> <span class="file">neyrolock-3.0.0-1.x86_64.rpm</span></p>
            <code class="command">sudo rpm -i neyrolock-3.0.0-1.x86_64.rpm</code>

            <h3>Универсальный (любой Linux)</h3>
            <p><strong>Файл:</strong> <span class="file">NEYROLOCK-3.0.0-Linux-Installer.sh</span></p>
            <code class="command">sudo bash NEYROLOCK-3.0.0-Linux-Installer.sh</code>
        </div>

        <hr>

        <h2>📝 Как создать Windows установщик</h2>
        <ol>
            <li>На компьютере с Windows откройте проект</li>
            <li>Перейдите в: <code>installers\windows\</code></li>
            <li>Запустите: <code>build_windows.bat</code></li>
            <li>Готовый файл: <code>installers\output\NEYROLOCK-3.0.0-Windows-Setup.exe</code></li>
        </ol>

        <hr>

        <h2>✨ После установки</h2>
        <ul>
            <li>Программа появится в меню приложений</li>
            <li>Запуск в один клик</li>
            <li>Исходный код скрыт внутри установщика</li>
        </ul>

        <p style="text-align: center; margin-top: 40px; color: #666;">
            Техподдержка: <a href="https://github.com/neyrolock/neyrolock/issues">GitHub Issues</a>
        </p>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}✓${NC} Создан README.html (откройте в браузере)"

# Финальный отчет
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✨ Сборка завершена! ✨${NC}"
echo ""
echo -e "${CYAN}📦 Все установщики в:${NC}"
echo -e "${MAGENTA}   $OUTPUT_DIR${NC}"
echo ""
echo -e "${CYAN}📄 Созданные файлы:${NC}"

# Показываем размеры файлов
cd "$OUTPUT_DIR"
ls -lh | grep -v "^total" | grep -v "^d" | awk '{print "   " $9 " (" $5 ")"}'

echo ""
echo -e "${YELLOW}⚠️  Примечание:${NC}"
echo -e "   Windows установщик (.exe) можно создать только на Windows."
echo -e "   Все остальные установщики (macOS, Linux) готовы!"
echo ""
echo -e "${CYAN}🚀 Что дальше:${NC}"
echo ""
echo "   1. Откройте: $OUTPUT_DIR"
echo "   2. Прочитайте README.txt или README.html"
echo "   3. Отправьте нужные файлы пользователям"
echo ""
echo -e "${GREEN}   Для Windows установщика:${NC}"
echo "      - Используйте Windows компьютер или виртуальную машину"
echo "      - Или настройте GitHub Actions для автоматической сборки"
echo ""

# Открываем папку в Finder
echo -e "${BLUE}Открываю папку с установщиками...${NC}"
sleep 1
open "$OUTPUT_DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓ Готово!${NC}"
echo ""
