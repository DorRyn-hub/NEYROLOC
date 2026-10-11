#!/usr/bin/env python
"""Пример потоковой генерации ответов (как ChatGPT)."""

import time
import lmstudio as lms

def streaming_demo():
    """Демонстрирует потоковую генерацию текста."""
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ СТРИМИНГА ОТВЕТОВ")
    print("=" * 60 + "\n")

    try:
        # Получаем модель
        model = lms.llm()
        print(f"✓ Подключено к модели: {model}\n")

        # Создаем чат
        chat = lms.Chat("Ты креативный помощник, который пишет интересные истории.")

        # Запрос
        prompt = "Напиши короткую историю о роботе, который научился мечтать."

        print(f"👤 Запрос: {prompt}\n")
        print("🤖 Ответ (потоково):\n")
        print("-" * 60)

        # Добавляем сообщение пользователя
        chat.add_user_message(prompt)

        # Получаем поток ответов
        start_time = time.time()
        full_response = ""

        # respond_stream возвращает генератор фрагментов
        for fragment in model.respond_stream(chat, on_message=chat.append):
            # Выводим каждый фрагмент сразу же
            print(fragment.content, end="", flush=True)
            full_response += fragment.content

        end_time = time.time()

        print("\n" + "-" * 60)
        print(f"\n✓ Генерация завершена за {end_time - start_time:.2f} секунд")
        print(f"   Всего символов: {len(full_response)}")

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        print("Убедитесь, что LM Studio запущен и модель загружена!")

if __name__ == "__main__":
    streaming_demo()
