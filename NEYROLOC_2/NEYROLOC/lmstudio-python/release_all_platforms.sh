#!/bin/bash
# ====================================================
# NEYROLOCK - Создание релиза для ВСЕХ платформ
# Использует GitHub Actions для сборки на всех ОС
# ====================================================

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo ""
echo "╔═════════════════════════════════════════════════╗"
echo "║  NEYROLOCK - Автоматическая сборка для всех ОС  ║"
echo "╚═════════════════════════════════════════════════╝"
echo ""

# Проверяем, что мы в git репозитории
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Это не git репозиторий!${NC}"
    echo ""
    echo "Инициализируем git..."
    git init
    git add .
    git commit -m "Initial commit"
    echo ""
fi

# Запрашиваем версию
echo -e "${CYAN}Введите версию релиза (например, 3.0.0):${NC}"
read -r VERSION

if [ -z "$VERSION" ]; then
    VERSION="3.0.0"
    echo -e "${YELLOW}Используется версия по умолчанию: $VERSION${NC}"
fi

TAG="v$VERSION"

echo ""
echo -e "${BLUE}Создаём релиз версии: $TAG${NC}"
echo ""

# Проверяем, есть ли уже такой тег
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Тег $TAG уже существует!${NC}"
    echo "Удалить существующий тег? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        git tag -d "$TAG"
        git push origin ":refs/tags/$TAG" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Старый тег удалён"
    else
        echo "Отменено."
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Шаги для создания релиза:${NC}"
echo ""
echo "1️⃣  Создам git тег $TAG"
echo "2️⃣  Отправлю на GitHub"
echo "3️⃣  GitHub Actions автоматически:"
echo "    - Соберёт установщик для Windows (.exe)"
echo "    - Соберёт установщик для macOS (.dmg)"
echo "    - Соберёт установщики для Linux (.deb, .rpm, .sh)"
echo "    - Создаст GitHub Release со всеми файлами"
echo ""
echo -e "${CYAN}Продолжить? (y/n)${NC}"
read -r response

if [ "$response" != "y" ]; then
    echo "Отменено."
    exit 0
fi

echo ""
echo -e "${BLUE}[1/4]${NC} Коммит всех изменений..."

git add .
git commit -m "Release $TAG" || echo "Нет изменений для коммита"

echo -e "${GREEN}✓${NC} Изменения закоммичены"

echo ""
echo -e "${BLUE}[2/4]${NC} Создание тега $TAG..."

git tag -a "$TAG" -m "Release $VERSION"

echo -e "${GREEN}✓${NC} Тег создан"

echo ""
echo -e "${BLUE}[3/4]${NC} Отправка на GitHub..."

# Проверяем, есть ли remote
if ! git remote | grep -q origin; then
    echo -e "${YELLOW}⚠️  Remote 'origin' не настроен!${NC}"
    echo ""
    echo "Введите URL вашего GitHub репозитория:"
    echo "(например: https://github.com/username/repo.git)"
    read -r REPO_URL

    git remote add origin "$REPO_URL"
    echo -e "${GREEN}✓${NC} Remote добавлен"
fi

# Отправляем на GitHub
git push origin main || git push origin master || {
    echo -e "${YELLOW}⚠️  Не удалось определить главную ветку${NC}"
    echo "Введите название ветки (обычно main или master):"
    read -r BRANCH
    git push origin "$BRANCH"
}

git push origin "$TAG"

echo -e "${GREEN}✓${NC} Код и тег отправлены на GitHub"

echo ""
echo -e "${BLUE}[4/4]${NC} GitHub Actions начал сборку..."
echo ""

# Получаем URL репозитория
REPO_URL=$(git config --get remote.origin.url)
REPO_URL=${REPO_URL%.git}
REPO_URL=${REPO_URL#https://github.com/}
REPO_URL=${REPO_URL#git@github.com:}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✨ Готово!${NC}"
echo ""
echo -e "${CYAN}Что происходит сейчас:${NC}"
echo ""
echo "1. GitHub Actions собирает установщики на серверах GitHub:"
echo "   - Windows (Windows Server)"
echo "   - macOS (macOS Latest)"
echo "   - Linux (Ubuntu Latest)"
echo ""
echo "2. Это займёт ~10-15 минут"
echo ""
echo "3. После завершения будет создан Release с установщиками"
echo ""
echo -e "${CYAN}Проверьте статус сборки:${NC}"
echo ""
echo "   🌐 https://github.com/$REPO_URL/actions"
echo ""
echo -e "${CYAN}После завершения скачайте установщики:${NC}"
echo ""
echo "   📦 https://github.com/$REPO_URL/releases/tag/$TAG"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}💡 Совет:${NC} Откройте страницу Actions, чтобы следить за прогрессом"
echo ""

# Пытаемся открыть браузер
if command -v open &> /dev/null; then
    echo "Открываю страницу Actions в браузере..."
    open "https://github.com/$REPO_URL/actions"
fi

echo ""
echo -e "${GREEN}✓ Всё запущено!${NC}"
echo ""
