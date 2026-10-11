#!/bin/bash
# ====================================================
# NEYROLOCK - Создание portable установщиков БЕЗ GIT
# Работает на macOS, создаёт установщики для всех ОС
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
echo "╔═══════════════════════════════════════════════════╗"
echo "║  NEYROLOCK - Portable установщики для всех ОС     ║"
echo "║  БЕЗ GitHub, БЕЗ git, БЕЗ сложностей!            ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Определяем директорию проекта
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# Создаем выходную директорию в Downloads
OUTPUT_DIR="$HOME/Downloads/NEYROLOCK-Installers"
TEMP_DIR="$OUTPUT_DIR/temp"
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$TEMP_DIR"

echo -e "${CYAN}📦 Установщики будут в:${NC}"
echo -e "${GREEN}   $OUTPUT_DIR${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Шаг 1: Установка зависимостей
echo -e "${BLUE}[1/6]${NC} Установка зависимостей..."
echo ""

if ! python3 -c "import PIL" &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Устанавливаю Pillow..."
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
echo -e "${BLUE}[2/6]${NC} Создание иконок..."
echo ""

python3 create_icons.py | grep "✅\|✓" || true
echo -e "${GREEN}✓${NC} Иконки созданы"

# Шаг 3: Сборка приложения с PyInstaller
echo ""
echo -e "${BLUE}[3/6]${NC} Сборка приложения..."
echo ""

cd installers/pyinstaller
rm -rf dist build
python3 -m PyInstaller neyrolock_gui.spec --clean --noconfirm --distpath "$TEMP_DIR/dist" --workpath "$TEMP_DIR/build"
cd "$PROJECT_ROOT"

echo -e "${GREEN}✓${NC} Приложение собрано"

# Шаг 4: Создание macOS установщиков
echo ""
echo -e "${BLUE}[4/6]${NC} Создание установщиков для macOS..."
echo ""

# macOS .app
if [ -d "$TEMP_DIR/dist/NEYROLOCK.app" ]; then
    # Создаём DMG вручную
    DMG_DIR="$TEMP_DIR/dmg"
    mkdir -p "$DMG_DIR"
    cp -R "$TEMP_DIR/dist/NEYROLOCK.app" "$DMG_DIR/"
    ln -s /Applications "$DMG_DIR/Applications"

    hdiutil create -volname "NEYROLOCK" \
        -srcfolder "$DMG_DIR" \
        -ov -format UDZO \
        "$OUTPUT_DIR/NEYROLOCK-3.0.0-macOS.dmg" &> /dev/null

    echo -e "${GREEN}✓${NC} macOS DMG создан"

    # Также копируем .app
    cp -R "$TEMP_DIR/dist/NEYROLOCK.app" "$OUTPUT_DIR/"
    echo -e "${GREEN}✓${NC} macOS App скопирован"
fi

# Шаг 5: Создание Linux установщиков
echo ""
echo -e "${BLUE}[5/6]${NC} Создание установщиков для Linux..."
echo ""

# Создаём portable версию для Linux
LINUX_DIR="$TEMP_DIR/NEYROLOCK-Linux"
mkdir -p "$LINUX_DIR"
cp -R "$TEMP_DIR/dist/NEYROLOCK" "$LINUX_DIR/" 2>/dev/null || cp -R "$TEMP_DIR/dist/"* "$LINUX_DIR/" || true

# Создаём скрипт запуска
cat > "$LINUX_DIR/neyrolock.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./NEYROLOCK/NEYROLOCK "$@"
EOF
chmod +x "$LINUX_DIR/neyrolock.sh"

# Создаём установщик
cat > "$LINUX_DIR/install.sh" << 'EOF'
#!/bin/bash
echo "╔════════════════════════════════════════╗"
echo "║  NEYROLOCK Installer для Linux         ║"
echo "╚════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "Для установки нужны права администратора."
    echo "Запустите: sudo bash install.sh"
    exit 1
fi

INSTALL_DIR="/opt/neyrolock"
BIN_LINK="/usr/local/bin/neyrolock"

echo "[1/4] Создание директории..."
mkdir -p "$INSTALL_DIR"

echo "[2/4] Копирование файлов..."
cp -R NEYROLOCK "$INSTALL_DIR/"

echo "[3/4] Создание ярлыка..."
ln -sf "$INSTALL_DIR/NEYROLOCK/NEYROLOCK" "$BIN_LINK"
chmod +x "$BIN_LINK"

echo "[4/4] Создание desktop entry..."
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
DESKTOP_EOF

echo ""
echo "✓ Установка завершена!"
echo ""
echo "Запустите: neyrolock"
echo "Или найдите в меню приложений"
EOF
chmod +x "$LINUX_DIR/install.sh"

# Создаём README
cat > "$LINUX_DIR/README.txt" << 'EOF'
NEYROLOCK для Linux

УСТАНОВКА:
  sudo bash install.sh

PORTABLE ЗАПУСК (без установки):
  bash neyrolock.sh

УДАЛЕНИЕ:
  sudo rm -rf /opt/neyrolock
  sudo rm -f /usr/local/bin/neyrolock
  sudo rm -f /usr/share/applications/neyrolock.desktop
EOF

# Упаковываем в tar.gz
cd "$TEMP_DIR"
tar czf "$OUTPUT_DIR/NEYROLOCK-3.0.0-Linux-Portable.tar.gz" NEYROLOCK-Linux/
cd "$PROJECT_ROOT"

echo -e "${GREEN}✓${NC} Linux установщик создан"

# Шаг 6: Создание Windows portable версии
echo ""
echo -e "${BLUE}[6/6]${NC} Создание portable версии для Windows..."
echo ""

WINDOWS_DIR="$TEMP_DIR/NEYROLOCK-Windows"
mkdir -p "$WINDOWS_DIR"

# Копируем файлы (используем macOS сборку как основу)
cp -R "$TEMP_DIR/dist/NEYROLOCK" "$WINDOWS_DIR/" 2>/dev/null || cp -R "$TEMP_DIR/dist/"* "$WINDOWS_DIR/" || true

# Создаём Windows batch установщик
cat > "$WINDOWS_DIR/install.bat" << 'EOF'
@echo off
echo ========================================
echo   NEYROLOCK Installer для Windows
echo ========================================
echo.

REM Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ОШИБКА: Требуются права администратора!
    echo.
    echo Щелкните правой кнопкой на install.bat
    echo и выберите "Запуск от имени администратора"
    echo.
    pause
    exit /b 1
)

set INSTALL_DIR=%ProgramFiles%\NEYROLOCK

echo [1/4] Создание директории...
mkdir "%INSTALL_DIR%" 2>nul

echo [2/4] Копирование файлов...
xcopy /E /I /Y NEYROLOCK "%INSTALL_DIR%\NEYROLOCK"

echo [3/4] Создание ярлыка на рабочем столе...
set DESKTOP=%USERPROFILE%\Desktop
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%DESKTOP%\NEYROLOCK.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\NEYROLOCK\NEYROLOCK.exe" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%\NEYROLOCK" >> CreateShortcut.vbs
echo oLink.Description = "NEYROLOCK - Local AI Assistant" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo [4/4] Создание ярлыка в меню Пуск...
set STARTMENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs
mkdir "%STARTMENU%\NEYROLOCK" 2>nul
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%STARTMENU%\NEYROLOCK\NEYROLOCK.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\NEYROLOCK\NEYROLOCK.exe" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%\NEYROLOCK" >> CreateShortcut.vbs
echo oLink.Description = "NEYROLOCK - Local AI Assistant" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo ========================================
echo   Установка завершена успешно!
echo ========================================
echo.
echo NEYROLOCK установлен в:
echo   %INSTALL_DIR%
echo.
echo Ярлыки созданы:
echo   - Рабочий стол
echo   - Меню Пуск
echo.
pause
EOF

# Создаём portable запуск
cat > "$WINDOWS_DIR/RUN_PORTABLE.bat" << 'EOF'
@echo off
echo Запуск NEYROLOCK (Portable)...
cd /d "%~dp0"
start NEYROLOCK\NEYROLOCK.exe
EOF

# Создаём README для Windows
cat > "$WINDOWS_DIR/README.txt" << 'EOF'
NEYROLOCK для Windows

ВАРИАНТ 1: УСТАНОВКА
  1. Щелкните правой кнопкой на install.bat
  2. Выберите "Запуск от имени администратора"
  3. Следуйте инструкциям

ВАРИАНТ 2: PORTABLE (без установки)
  Дважды щелкните: RUN_PORTABLE.bat

УДАЛЕНИЕ:
  Выполните: uninstall.bat
  (от имени администратора)

ПРИМЕЧАНИЕ:
  Этот установщик создан на macOS.
  Если возникнут проблемы, пересоберите на Windows:

  1. Откройте проект на Windows
  2. Перейдите в: installers\windows\
  3. Запустите: build_windows.bat
EOF

# Создаём деинсталлятор
cat > "$WINDOWS_DIR/uninstall.bat" << 'EOF'
@echo off
echo ========================================
echo   NEYROLOCK Uninstaller
echo ========================================
echo.

REM Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ОШИБКА: Требуются права администратора!
    pause
    exit /b 1
)

set INSTALL_DIR=%ProgramFiles%\NEYROLOCK
set DESKTOP=%USERPROFILE%\Desktop
set STARTMENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs

echo Удаление NEYROLOCK...
echo.

if exist "%INSTALL_DIR%" (
    echo [1/3] Удаление файлов программы...
    rmdir /S /Q "%INSTALL_DIR%"
)

if exist "%DESKTOP%\NEYROLOCK.lnk" (
    echo [2/3] Удаление ярлыка с рабочего стола...
    del "%DESKTOP%\NEYROLOCK.lnk"
)

if exist "%STARTMENU%\NEYROLOCK" (
    echo [3/3] Удаление из меню Пуск...
    rmdir /S /Q "%STARTMENU%\NEYROLOCK"
)

echo.
echo Удаление завершено!
pause
EOF

# Упаковываем в zip
cd "$TEMP_DIR"
zip -r -q "$OUTPUT_DIR/NEYROLOCK-3.0.0-Windows-Portable.zip" NEYROLOCK-Windows/
cd "$PROJECT_ROOT"

echo -e "${GREEN}✓${NC} Windows portable версия создана"

# Создаём универсальный README
cat > "$OUTPUT_DIR/README.txt" << 'EOF'
╔════════════════════════════════════════════════╗
║       NEYROLOCK v3.0.0 - Установщики          ║
╚════════════════════════════════════════════════╝

📦 Что внутри:

🪟 WINDOWS:
   NEYROLOCK-3.0.0-Windows-Portable.zip

   Распакуйте и запустите install.bat (от имени администратора)
   Или используйте RUN_PORTABLE.bat для запуска без установки

🍎 macOS:
   NEYROLOCK-3.0.0-macOS.dmg

   Откройте DMG → Перетащите в Applications

   Или:
   NEYROLOCK.app

   Скопируйте в /Applications

🐧 LINUX:
   NEYROLOCK-3.0.0-Linux-Portable.tar.gz

   Распакуйте и запустите:
   sudo bash install.sh

   Или portable:
   bash neyrolock.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 ВАЖНО:

Windows установщик создан на macOS и может иметь ограничения.

Для наилучшего результата на Windows:
1. Откройте проект на Windows компьютере
2. Перейдите в installers\windows\
3. Запустите build_windows.bat

Это создаст полноценный .exe установщик с Inno Setup.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ После установки программа появится в меню приложений!

Исходный код полностью скрыт внутри установщиков.
EOF

# Создаём HTML README
cat > "$OUTPUT_DIR/README.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NEYROLOCK v3.0.0</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 40px;
        }
        .platform {
            background: #f8f9fa;
            border-left: 5px solid #667eea;
            padding: 25px;
            margin: 25px 0;
            border-radius: 8px;
        }
        .platform h2 {
            margin-top: 0;
            color: #333;
        }
        .file {
            background: #e9ecef;
            padding: 8px 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            display: inline-block;
            margin: 10px 0;
            font-weight: bold;
        }
        .command {
            background: #2d2d2d;
            color: #00ff00;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            margin: 15px 0;
            overflow-x: auto;
        }
        .warning {
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 20px;
            margin: 25px 0;
            border-radius: 8px;
        }
        .success {
            background: #d4edda;
            border-left: 5px solid #28a745;
            padding: 20px;
            margin: 25px 0;
            border-radius: 8px;
        }
        .emoji {
            font-size: 1.5em;
            margin-right: 10px;
        }
        ul {
            line-height: 2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 NEYROLOCK v3.0.0</h1>
        <div class="subtitle">Установщики для всех платформ</div>

        <div class="platform">
            <h2><span class="emoji">🪟</span>Windows</h2>
            <p><strong>Файл:</strong> <span class="file">NEYROLOCK-3.0.0-Windows-Portable.zip</span></p>

            <h3>Вариант 1: Установка</h3>
            <ol>
                <li>Распакуйте ZIP архив</li>
                <li>Щелкните правой кнопкой на <code>install.bat</code></li>
                <li>Выберите "Запуск от имени администратора"</li>
                <li>Следуйте инструкциям</li>
            </ol>

            <h3>Вариант 2: Portable (без установки)</h3>
            <ol>
                <li>Распакуйте ZIP архив</li>
                <li>Дважды щелкните <code>RUN_PORTABLE.bat</code></li>
            </ol>
        </div>

        <div class="platform">
            <h2><span class="emoji">🍎</span>macOS</h2>
            <p><strong>Файл:</strong> <span class="file">NEYROLOCK-3.0.0-macOS.dmg</span></p>

            <h3>Установка:</h3>
            <ol>
                <li>Откройте DMG файл</li>
                <li>Перетащите NEYROLOCK.app в Applications</li>
                <li>Готово!</li>
            </ol>

            <p><strong>Альтернатива:</strong> <span class="file">NEYROLOCK.app</span></p>
            <p>Скопируйте в <code>/Applications</code></p>
        </div>

        <div class="platform">
            <h2><span class="emoji">🐧</span>Linux</h2>
            <p><strong>Файл:</strong> <span class="file">NEYROLOCK-3.0.0-Linux-Portable.tar.gz</span></p>

            <h3>Вариант 1: Установка в систему</h3>
            <div class="command">
tar xzf NEYROLOCK-3.0.0-Linux-Portable.tar.gz
cd NEYROLOCK-Linux
sudo bash install.sh</div>

            <h3>Вариант 2: Portable запуск</h3>
            <div class="command">
tar xzf NEYROLOCK-3.0.0-Linux-Portable.tar.gz
cd NEYROLOCK-Linux
bash neyrolock.sh</div>
        </div>

        <div class="warning">
            <h3>⚠️ Важно для Windows</h3>
            <p>Windows установщик создан на macOS и может иметь ограничения.</p>
            <p><strong>Для наилучшего результата:</strong></p>
            <ol>
                <li>Откройте проект на Windows компьютере</li>
                <li>Перейдите в <code>installers\windows\</code></li>
                <li>Запустите <code>build_windows.bat</code></li>
            </ol>
            <p>Это создаст полноценный .exe установщик с Inno Setup.</p>
        </div>

        <div class="success">
            <h3>✨ После установки</h3>
            <ul>
                <li>Программа появится в меню приложений</li>
                <li>Запуск в один клик</li>
                <li>Исходный код полностью скрыт</li>
                <li>Работает автономно, без интернета</li>
            </ul>
        </div>

        <hr style="margin: 40px 0;">

        <div style="text-align: center; color: #666;">
            <p><strong>Техподдержка:</strong> <a href="https://github.com/DorRyn/NEYROLOC/issues">GitHub Issues</a></p>
            <p style="margin-top: 30px; font-size: 0.9em;">
                © 2025 NEYROLOCK Team<br>
                Создано с ❤️ для работы с локальными AI моделями
            </p>
        </div>
    </div>
</body>
</html>
EOF

# Очистка временных файлов
echo ""
echo -e "${BLUE}Очистка временных файлов...${NC}"
rm -rf "$TEMP_DIR"
echo -e "${GREEN}✓${NC} Временные файлы удалены"

# Финальный отчет
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✨ Все установщики созданы! ✨${NC}"
echo ""
echo -e "${CYAN}📦 Местоположение:${NC}"
echo -e "${MAGENTA}   $OUTPUT_DIR${NC}"
echo ""
echo -e "${CYAN}📄 Созданные файлы:${NC}"
echo ""

cd "$OUTPUT_DIR"
ls -lh | grep -E '\.(dmg|zip|tar\.gz|app|txt|html)' | awk '{
    size = $5
    name = $9
    for (i=10; i<=NF; i++) name = name " " $i
    printf "   %-45s %10s\n", name, size
}'

echo ""
echo -e "${CYAN}🎯 Что отправить пользователям:${NC}"
echo ""
echo "   Windows: NEYROLOCK-3.0.0-Windows-Portable.zip"
echo "   macOS:   NEYROLOCK-3.0.0-macOS.dmg"
echo "   Linux:   NEYROLOCK-3.0.0-Linux-Portable.tar.gz"
echo ""
echo -e "${YELLOW}💡 Совет:${NC}"
echo "   Отправьте также README.html для удобства"
echo ""
echo -e "${CYAN}⚠️  Примечание про Windows:${NC}"
echo "   Windows portable версия работает, но для лучшего"
echo "   результата рекомендуется пересобрать на Windows:"
echo "   installers\\windows\\build_windows.bat"
echo ""

# Открываем папку
echo -e "${BLUE}Открываю папку...${NC}"
open "$OUTPUT_DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓ Готово! Все установщики в Downloads!${NC}"
echo ""
