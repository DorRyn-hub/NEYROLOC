# 🚀 Запуск БЕЗ LM Studio - Полное руководство

## ✅ Универсальное решение

Я создал `universal_cli.py` - это CLI, который работает **БЕЗ LM Studio**!

---

## 📋 Поддерживаемые backend'ы:

1. **Ollama** (локально, бесплатно) ⭐ Рекомендуется
2. **OpenAI** (облако, платно)
3. **Groq** (облако, бесплатно, быстро)
4. **Любой OpenAI-совместимый сервер**

---

## 🎯 Вариант 1: Ollama (Локально, БЕЗ интернета)

### Шаг 1: Установите зависимости Python

```bash
pip install -r requirements_universal.txt

# Или вручную:
pip install openai rich
```

### Шаг 2: Установите Ollama

#### macOS:
```bash
brew install ollama
```

#### Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Windows:
Скачайте с https://ollama.com/download

### Шаг 3: Запустите Ollama сервер

```bash
# В отдельном терминале
ollama serve
```

### Шаг 4: Загрузите модель

```bash
# Быстрая модель (1GB)
ollama pull llama3.2:1b

# Средняя модель (2GB) - рекомендуется
ollama pull llama3.2:3b

# Большая модель (4GB)
ollama pull qwen2.5:7b
```

### Шаг 5: Запустите CLI

```bash
python universal_cli.py
```

Выберите "1" (Ollama) и введите имя модели (например, `llama3.2:3b`)

✅ **Готово!** Работает полностью локально, без LM Studio!

---

## 🎯 Вариант 2: Groq (Облако, БЕСПЛАТНО, очень быстро)

### Шаг 1: Установите зависимости

```bash
pip install -r requirements_universal.txt
```

### Шаг 2: Получите бесплатный API ключ

1. Зайдите на https://console.groq.com
2. Зарегистрируйтесь (бесплатно)
3. Создайте API ключ в разделе "API Keys"

### Шаг 3: Запустите CLI

```bash
python universal_cli.py
```

Выберите "3" (Groq) и введите ваш API ключ

✅ **Готово!** Очень быстрые ответы, бесплатно!

---

## 🎯 Вариант 3: OpenAI (Облако, платно, качественно)

### Шаг 1: Установите зависимости

```bash
pip install -r requirements_universal.txt
```

### Шаг 2: Получите API ключ OpenAI

1. Зайдите на https://platform.openai.com
2. Создайте аккаунт и пополните баланс
3. Создайте API ключ

### Шаг 3: Запустите CLI

```bash
# Опционально: установите переменную окружения
export OPENAI_API_KEY="your-key-here"

python universal_cli.py
```

Выберите "2" (OpenAI)

---

## 🎮 Примеры использования

### Простое общение

```bash
python universal_cli.py
```

```
╔═══════════════════════════════════════════════════════════╗
║            UNIVERSAL LLM CLI (БЕЗ LM STUDIO)              ║
║          Работает с Ollama, OpenAI, Groq и др.            ║
╚═══════════════════════════════════════════════════════════╝

Выберите backend:
  1. Ollama (локально)
  2. OpenAI (облако, платно)
  3. Groq (облако, бесплатно)
  4. Пользовательский URL

Ваш выбор [1]: 1
✓ Выбран backend: Ollama (локально)

Введите имя модели [llama3.2:3b]:
✓ Используется модель: llama3.2:3b

👤 Вы: Привет! Как дела?

🤖 Ассистент: Здравствуйте! У меня всё хорошо, спасибо...
```

### Команды

```
/help      - Справка
/history   - Показать историю
/clear     - Очистить историю
/save      - Сохранить диалог
/exit      - Выход
```

---

## 📊 Сравнение вариантов

| Вариант | Скорость | Цена | Интернет | Установка |
|---------|----------|------|----------|-----------|
| **Ollama** | Средняя | Бесплатно | Не нужен | 2 минуты |
| **Groq** | Очень быстро | Бесплатно | Нужен | 1 минута |
| **OpenAI** | Быстро | $0.001/1K токенов | Нужен | 1 минута |
| **LM Studio** | Средняя | Бесплатно | Не нужен | 10 минут |

---

## 🔥 Быстрый старт с Ollama (3 команды)

```bash
# 1. Установите зависимости
pip install openai rich

# 2. Установите и запустите Ollama
brew install ollama && ollama serve &

# 3. Загрузите модель и запустите CLI
ollama pull llama3.2:3b && python universal_cli.py
```

---

## 🐛 Решение проблем

### Ollama: "Connection refused"

```bash
# Убедитесь, что сервер запущен
ollama serve

# Проверьте доступность
curl http://localhost:11434/api/tags
```

### Groq: "Invalid API key"

1. Проверьте ключ на https://console.groq.com
2. Убедитесь, что скопировали полностью
3. Попробуйте создать новый ключ

### OpenAI: "Insufficient quota"

Пополните баланс на https://platform.openai.com/account/billing

---

## 💡 Рекомендации

### Для начинающих:
→ Используйте **Groq** (быстро, бесплатно, просто)

### Для разработчиков:
→ Используйте **Ollama** (локально, приватно, без интернета)

### Для продакшна:
→ Используйте **OpenAI** (надежно, качественно)

---

## 📁 Структура файлов

```
universal_cli.py            - Универсальный CLI ⭐
requirements_universal.txt  - Зависимости
WITHOUT_LMSTUDIO.md        - Краткое описание
SETUP_WITHOUT_LMSTUDIO.md  - Это руководство
```

---

## ✅ Итого

Теперь у вас есть **3 способа** запустить локальную LLM **БЕЗ LM Studio**:

1. ✅ `universal_cli.py` с Ollama (локально)
2. ✅ `universal_cli.py` с Groq (облако, бесплатно)
3. ✅ `universal_cli.py` с OpenAI (облако, платно)

**Самый простой способ - Ollama!** Попробуйте прямо сейчас:

```bash
brew install ollama
ollama serve &
ollama pull llama3.2:3b
pip install openai rich
python universal_cli.py
```

---

**Готово! Работает БЕЗ LM Studio!** 🎉
