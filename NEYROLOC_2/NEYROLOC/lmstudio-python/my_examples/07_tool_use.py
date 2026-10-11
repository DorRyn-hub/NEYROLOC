#!/usr/bin/env python
"""Пример использования инструментов (function calling)."""

import lmstudio as lms
import datetime
import random

# Определяем инструменты (функции), которые модель может вызывать

def get_current_time() -> str:
    """Возвращает текущее время."""
    return datetime.datetime.now().strftime("%H:%M:%S")

def get_current_date() -> str:
    """Возвращает текущую дату."""
    return datetime.datetime.now().strftime("%d.%m.%Y")

def calculate(a: float, b: float, operation: str) -> float:
    """
    Выполняет математические операции.

    Args:
        a: Первое число
        b: Второе число
        operation: Операция (add, subtract, multiply, divide)
    """
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else float('inf')
    }
    return operations.get(operation, 0)

def roll_dice(sides: int = 6) -> int:
    """
    Бросает кубик с заданным количеством граней.

    Args:
        sides: Количество граней (по умолчанию 6)
    """
    return random.randint(1, sides)

def tool_use_demo():
    """Демонстрирует использование инструментов."""
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ ИСПОЛЬЗОВАНИЯ ИНСТРУМЕНТОВ")
    print("=" * 60 + "\n")

    try:
        # Получаем модель (желательно использовать модель с поддержкой function calling)
        model = lms.llm()
        print(f"✓ Подключено к модели: {model}\n")

        # Создаем чат
        chat = lms.Chat(
            "Ты полезный ассистент с доступом к различным инструментам. "
            "Используй их, когда это необходимо для ответа на вопросы."
        )

        # Список инструментов
        tools = [get_current_time, get_current_date, calculate, roll_dice]

        # Примеры запросов
        queries = [
            "Какое сейчас время?",
            "Какая сегодня дата?",
            "Сколько будет 156 умножить на 73?",
            "Брось кубик с 20 гранями"
        ]

        for query in queries:
            print(f"👤 Вопрос: {query}")

            # Используем метод act для автоматического вызова инструментов
            response = model.act(
                query,
                tools,
                on_message=chat.append
            )

            print(f"🤖 Ответ: {response}\n")
            print("-" * 60 + "\n")

    except Exception as e:
        print(f"✗ Ошибка: {e}")
        print("\nПримечание: Не все модели поддерживают function calling.")
        print("Рекомендуемые модели: qwen2.5, llama-3.1 и другие современные модели.")

if __name__ == "__main__":
    tool_use_demo()
