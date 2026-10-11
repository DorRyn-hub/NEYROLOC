# 🚀 AI CLI - Быстрая справка

## ⚡ Одна команда для запуска

```bash
cd $HOME/PycharmProjects/NEYROLOCK/lmstudio-python && ./setup_and_run.sh
```

Эта команда автоматически:
- ✅ Проверит зависимости
- ✅ Установит недостающие
- ✅ Запустит AI CLI

---

## 📱 После установки просто:

```bash
cd $HOME/PycharmProjects/NEYROLOCK/lmstudio-python
python3 ai_cli.py
```

---

## 🎯 Первый запуск - 5 шагов:

1. **Запустите**: `python3 ai_cli.py`
2. **Выберите**: "6" (Скачать модель)
3. **Категория**: "small"
4. **Модель**: "1" (Llama 3.2 3B)
5. **Готово!** Начинайте общаться

---

## 💡 Полезные файлы:

| Файл | Описание |
|------|----------|
| `ГОТОВО_ЗАПУСКАЙ.txt` | ✅ Все установлено - читай здесь |
| `НАЧНИ_ЗДЕСЬ.txt` | 📋 Инструкции для первого запуска |
| `COPY_PASTE_THIS.txt` | 📋 Команда для копирования |
| `QUICK_START_MAC.md` | 🍎 Подробно для Mac |
| `AI_CLI_README.md` | 📖 Полное руководство |
| `NEW_FEATURES.md` | ✨ Новые возможности |

---

## 🔧 Доступные программы:

```bash
python3 ai_cli.py          # ⭐ Универсальный (рекомендуется)
python3 local_model_cli.py # 📦 Локальные GGUF модели
python3 lmstudio_cli.py    # 🖥️  LM Studio
python3 universal_cli.py   # ☁️  Groq, OpenAI
python3 model_manager.py   # 🛠️  Менеджер моделей
```

---

## 📖 Команды внутри программы:

```
/download  - Скачать модель с HuggingFace
/models    - Показать скачанные модели
/search    - Найти модель
/switch    - Сменить backend
/help      - Справка
/exit      - Выход
```

---

## ❓ Проблемы?

### "command not found: python"
➜ Используйте `python3` вместо `python`

### "command not found: pip"
➜ Используйте `python3 -m pip` вместо `pip`

### Модель не помещается в памяти
➜ Выберите модель поменьше (категория "tiny" - 300-700MB)

---

## 🎉 Быстрый старт:

**Вариант 1 (автоматический):**
```bash
./setup_and_run.sh
```

**Вариант 2 (ручной):**
```bash
python3 ai_cli.py
```

---

**Готово! Начинайте работать! 🚀**
