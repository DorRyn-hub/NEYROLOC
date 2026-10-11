#!/usr/bin/env python
"""Тестовый скрипт для проверки подключения к LM Studio."""

import lmstudio as lms

try:
    print("Попытка подключения к LM Studio...")

    # Попробуем получить загруженную модель
    model = lms.llm()

    print("✓ Подключение успешно!")
    print(f"Модель: {model}")

    # Простой тест
    print("\nТест генерации текста:")
    response = model.complete("Привет! Как дела?", max_tokens=50)
    print(f"Ответ: {response}")

except Exception as e:
    print(f"✗ Ошибка подключения: {e}")
    print("\nВозможные причины:")
    print("1. LM Studio не запущен")
    print("2. В LM Studio не загружена модель")
    print("3. LM Studio работает на другом порту")
    print("\nЧтобы использовать SDK, вам нужно:")
    print("  - Запустить LM Studio")
    print("  - Загрузить модель в LM Studio")
    print("  - Убедиться, что сервер LM Studio активен")
