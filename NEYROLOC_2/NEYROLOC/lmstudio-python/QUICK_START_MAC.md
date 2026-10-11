# 🚀 Быстрый старт для Mac

## Для пользователей Mac (важно!)

На Mac используйте `python3` вместо `python`:

```bash
# ✅ Правильно (Mac)
python3 ai_cli.py

# ❌ Неправильно
python ai_cli.py  # Это не работает на Mac!
```

---

## 🎯 Быстрый запуск (3 способа)

### Способ 1: Через скрипт (самый простой)

```bash
./run_ai_cli.sh
```

### Способ 2: Через python3

```bash
python3 ai_cli.py
```

### Способ 3: Из любой папки

```bash
cd $HOME/PycharmProjects/NEYROLOCK/lmstudio-python
python3 ai_cli.py
```

---

## 📦 Установка зависимостей для Mac

### Для Mac M1/M2/M3 (Apple Silicon):

```bash
# 1. Установка llama-cpp-python с поддержкой Metal
CMAKE_ARGS="-DLLAMA_METAL=on" pip3 install llama-cpp-python

# 2. Остальные зависимости
pip3 install rich huggingface-hub

# 3. Опциональные (для разных backend)
pip3 install lmstudio openai
```

### Для Intel Mac:

```bash
# Установка всех зависимостей
pip3 install -r requirements_ai_cli.txt
```

### Единой командой:

```bash
pip3 install -r requirements_ai_cli.txt
```

---

## 🎮 Первый запуск

```bash
# 1. Перейдите в папку проекта
cd $HOME/PycharmProjects/NEYROLOCK/lmstudio-python

# 2. Запустите AI CLI
python3 ai_cli.py

# 3. Выберите "6" (Скачать модель)
# 4. Выберите "small" (Маленькие модели)
# 5. Выберите "1" (Llama 3.2 3B - 2GB)
# 6. Дождитесь скачивания
# 7. Готово! Начинайте общаться!
```

---

## 🔧 Если что-то не работает

### Проблема: "command not found: python3"

```bash
# Проверьте установлен ли Python
which python3

# Если не установлен, установите через Homebrew
brew install python@3.12
```

### Проблема: "pip3: command not found"

```bash
# Используйте python3 -m pip вместо pip3
python3 -m pip install -r requirements_ai_cli.txt
```

### Проблема: "Permission denied"

```bash
# Сделайте скрипт исполняемым
chmod +x run_ai_cli.sh
```

### Проблема: Модель не помещается в память

```bash
# Выберите модель поменьше:
# - "tiny" категория (300-700MB)
# - Qwen 0.5B или Llama 1B
```

---

## 📱 Все доступные CLI для Mac

```bash
# AI CLI (универсальный) ⭐
python3 ai_cli.py

# Local Model CLI (GGUF модели)
python3 local_model_cli.py

# LM Studio CLI
python3 lmstudio_cli.py

# Universal CLI (Ollama, Groq, OpenAI)
python3 universal_cli.py

# Менеджер моделей
python3 model_manager.py
```

---

## 💡 Полезные алиасы для Mac

Добавьте в `~/.zshrc` для быстрого запуска:

```bash
# Откройте файл
nano ~/.zshrc

# Добавьте в конец:
alias ai='cd $HOME/PycharmProjects/NEYROLOCK/lmstudio-python && python3 ai_cli.py'
alias ailocal='cd $HOME/PycharmProjects/NEYROLOCK/lmstudio-python && python3 local_model_cli.py'

# Сохраните (Ctrl+O, Enter, Ctrl+X)

# Примените изменения
source ~/.zshrc

# Теперь можно запускать просто:
ai
```

---

## 🎓 Рекомендуемый порядок для Mac M1/M2/M3

```bash
# 1. Установка зависимостей с поддержкой Metal (GPU)
CMAKE_ARGS="-DLLAMA_METAL=on" pip3 install llama-cpp-python
pip3 install rich huggingface-hub

# 2. Запуск
python3 ai_cli.py

# 3. Скачивание модели
→ Выбрать "6"
→ Выбрать "small"
→ Выбрать "1" (Llama 3.2 3B)

# 4. При загрузке модели:
→ Размер контекста: 2048 (Enter)
→ Слои на GPU: -1 (Enter - все на GPU/Metal)

# 5. Готово! На M1/M2/M3 будет очень быстро! 🚀
```

---

## ✨ Преимущества на Apple Silicon (M1/M2/M3)

✅ **Очень быстро** - Metal ускорение
✅ **Энергоэффективно** - низкое энергопотребление
✅ **Тихо** - кулеры почти не работают
✅ **Полностью локально** - приватность

---

## 📊 Рекомендуемые модели для Mac

### Для Mac M1 (8GB RAM):
- Qwen 0.5B (300MB) - очень быстро
- Llama 3.2 1B (700MB) - быстро
- Llama 3.2 3B (2GB) - оптимально ⭐

### Для Mac M1 Pro/Max (16GB+ RAM):
- Llama 3.2 3B (2GB) - быстро ⭐
- Qwen 2.5 7B (4.4GB) - отлично
- Llama 3.1 8B (4.9GB) - топ

### Для Mac M2/M3 (16GB+ RAM):
- Любые модели до 7-8B работают отлично! 🔥

---

## 🎉 Готово!

Теперь запускайте:

```bash
python3 ai_cli.py
```

или

```bash
./run_ai_cli.sh
```

**Приятного использования на Mac! 🍎**
