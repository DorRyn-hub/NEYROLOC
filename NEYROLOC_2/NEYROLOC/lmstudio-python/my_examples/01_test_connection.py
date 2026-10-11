#!/usr/bin/env python
"""Скрипт для проверки подключения к LM Studio или альтернативному серверу."""

import sys
import lmstudio as lms

def test_connection():
    """Проверяет подключение к серверу и выводит информацию о нем."""
    print("=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К LLM СЕРВЕРУ")
    print("=" * 60)

    try:
        # Создаем клиент с явным указанием параметров
        print("\n[1/4] Создание клиента...")
        client = lms.Client()
        print("    ✓ Клиент создан")

        # Получаем информацию о загруженных моделях
        print("\n[2/4] Получение списка загруженных моделей...")
        models = client.llm.list_loaded()

        if not models:
            print("    ⚠ Нет загруженных моделей!")
            print("    Загрузите модель в LM Studio перед использованием")
            return False

        print(f"    ✓ Найдено моделей: {len(models)}")
        for i, model in enumerate(models, 1):
            print(f"      {i}. {model.identifier}")

        # Получаем первую загруженную модель
        print("\n[3/4] Подключение к модели...")
        model = client.llm.get()
        print(f"    ✓ Подключено к модели: {model}")

        # Простой тест генерации
        print("\n[4/4] Тест генерации текста...")
        response = model.complete("Скажи привет на русском", max_tokens=20)
        print(f"    ✓ Ответ модели: {response.strip()}")

        print("\n" + "=" * 60)
        print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)

        client.disconnect()
        return True

    except ConnectionError as e:
        print(f"\n✗ ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
        print("\nВозможные решения:")
        print("  1. Запустите LM Studio")
        print("  2. Убедитесь, что сервер активен (обычно порт 1234)")
        print("  3. Загрузите модель в LM Studio")
        return False

    except Exception as e:
        print(f"\n✗ НЕОЖИДАННАЯ ОШИБКА: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
