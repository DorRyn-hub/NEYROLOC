# 🚀 Быстрый старт

Это краткое руководство для мгновенного запуска LM Studio CLI.

## За 3 шага

### 1️⃣ Запустите LM Studio

```bash
# Скачайте и установите LM Studio с https://lmstudio.ai
# Откройте LM Studio
# Загрузите любую модель (например, Llama 3.2 3B)
# Убедитесь, что модель загружена (не просто скачана!)
```

### 2️⃣ Установите зависимости

```bash
# Быстрая установка
pip install lmstudio rich

# Или через requirements
pip install -r requirements_cli.txt
```

### 3️⃣ Запустите CLI

```bash
python lmstudio_cli.py
```

## 🎉 Готово!

Теперь вы можете общаться с моделью прямо в терминале!

### Первые команды

```
👤 Вы: Привет! Как дела?
🤖 Ассистент: [ответ модели...]

👤 Вы: /help
[показывает все доступные команды]

👤 Вы: /models
[показывает список загруженных моделей]
```

## ⚡ Автоматическая установка (macOS/Linux)

```bash
# Сделайте скрипт исполняемым
chmod +x setup_cli.sh

# Запустите установку
./setup_cli.sh
```

## 🐛 Если что-то пошло не так

### Ошибка: "LM Studio is not reachable"

1. Откройте LM Studio
2. Убедитесь, что модель **загружена** (не просто скачана)
3. Проверьте, что сервер запущен (обычно порт 1234)

### Ошибка: "No module named 'rich'"

```bash
pip install rich
```

### Ошибка: "No module named 'lmstudio'"

```bash
pip install lmstudio
```

## 📚 Дальнейшее изучение

- Полная документация: [CLI_README.md](CLI_README.md)
- Примеры: папка `my_examples/`
- Основной README: [README.md](README.md)

---

**Вопросы?** Используйте команду `/help` в CLI или читайте [CLI_README.md](CLI_README.md)
