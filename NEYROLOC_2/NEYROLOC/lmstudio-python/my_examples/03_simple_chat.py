#!/usr/bin/env python
"""Простой пример чата с LLM."""

import lmstudio as lms

def simple_chat():
    """Демонстрирует базовую работу с чатом."""
    print("=" * 60)
    print("ПРОСТОЙ ЧАТ С LLM")
    print("=" * 60)

    try:
        # Получаем модель
        model = lms.llm()
        print(f"✓ Подключено к модели: {model}\n")

        # Создаем чат с системным промптом
        chat = lms.Chat("Ты полезный ассистент, который отвечает кратко и по делу на русском языке.")

        # Пример диалога
        messages = [
            "Привет! Как тебя зовут?",
            "Что ты умеешь делать?",
            "Напиши простую функцию на Python для сложения двух чисел"
        ]

        for user_message in messages:
            # Добавляем сообщение пользователя
            chat.add_user_message(user_message)

            print(f"👤 Пользователь: {user_message}")

            # Получаем ответ от модели
            response = model.respond(chat)

            # Добавляем ответ в историю
            chat.add_assistant_response(response)

            print(f"🤖 Ассистент: {response}\n")
            print("-" * 60 + "\n")

        # Выводим полную историю чата
        print("\n" + "=" * 60)
        print("ИСТОРИЯ ЧАТА:")
        print("=" * 60)
        print(chat)

    except Exception as e:
        print(f"✗ Ошибка: {e}")
        print("\nУбедитесь, что LM Studio запущен и модель загружена!")

if __name__ == "__main__":
    simple_chat()
