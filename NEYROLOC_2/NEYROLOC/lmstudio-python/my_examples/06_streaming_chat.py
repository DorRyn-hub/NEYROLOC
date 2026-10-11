#!/usr/bin/env python
"""Интерактивный чат с потоковыми ответами."""

import readline
import lmstudio as lms

def streaming_chat():
    """Интерактивный чат с ответами в реальном времени."""
    print("=" * 60)
    print("ИНТЕРАКТИВНЫЙ ЧАТ С ПОТОКОВЫМИ ОТВЕТАМИ")
    print("=" * 60)
    print("Введите сообщение или 'exit' для выхода")
    print("=" * 60 + "\n")

    try:
        # Получаем модель
        model = lms.llm()
        print(f"✓ Подключено к модели: {model}\n")

        # Создаем чат
        chat = lms.Chat(
            "Ты полезный ассистент. Отвечай на русском языке, "
            "будь информативным и дружелюбным."
        )

        while True:
            try:
                # Получаем ввод
                user_input = input("👤 Вы: ").strip()

                if not user_input or user_input.lower() == 'exit':
                    print("\nДо свидания!")
                    break

                # Добавляем сообщение
                chat.add_user_message(user_input)

                # Выводим начало ответа
                print("🤖 Бот: ", end="", flush=True)

                # Получаем потоковый ответ
                # on_message=chat.append автоматически добавит ответ в историю
                for fragment in model.respond_stream(chat, on_message=chat.append):
                    print(fragment.content, end="", flush=True)

                print("\n")  # Переход на новую строку после ответа

            except EOFError:
                print("\n\nДо свидания!")
                break
            except KeyboardInterrupt:
                print("\n\nПрервано. До свидания!")
                break

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        print("Убедитесь, что LM Studio запущен и модель загружена!")

if __name__ == "__main__":
    streaming_chat()
