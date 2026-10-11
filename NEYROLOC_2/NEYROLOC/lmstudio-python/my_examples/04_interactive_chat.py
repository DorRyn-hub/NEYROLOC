#!/usr/bin/env python
"""Интерактивный чат-бот с поддержкой истории диалога."""

import readline  # Включает редактирование строки ввода
import lmstudio as lms

def interactive_chat():
    """Запускает интерактивную чат-сессию."""
    print("=" * 60)
    print("ИНТЕРАКТИВНЫЙ ЧАТ-БОТ")
    print("=" * 60)
    print("Команды:")
    print("  - Просто пишите сообщения для общения")
    print("  - Пустая строка или 'exit' для выхода")
    print("  - 'history' для просмотра истории")
    print("  - 'clear' для очистки истории")
    print("=" * 60 + "\n")

    try:
        # Получаем модель
        model = lms.llm()
        print(f"✓ Подключено к модели: {model}\n")

        # Создаем чат
        chat = lms.Chat(
            "Ты дружелюбный ассистент, который помогает пользователям. "
            "Отвечай на русском языке, будь вежливым и полезным."
        )

        while True:
            try:
                # Получаем ввод пользователя
                user_input = input("👤 Вы: ").strip()

                # Проверяем команды выхода
                if not user_input or user_input.lower() == 'exit':
                    print("\nДо свидания!")
                    break

                # Команда просмотра истории
                if user_input.lower() == 'history':
                    print("\n" + "=" * 60)
                    print("ИСТОРИЯ ЧАТА:")
                    print("=" * 60)
                    print(chat)
                    print("=" * 60 + "\n")
                    continue

                # Команда очистки истории
                if user_input.lower() == 'clear':
                    chat = lms.Chat(
                        "Ты дружелюбный ассистент, который помогает пользователям. "
                        "Отвечай на русском языке, будь вежливым и полезным."
                    )
                    print("✓ История очищена\n")
                    continue

                # Добавляем сообщение в чат
                chat.add_user_message(user_input)

                # Получаем ответ
                print("🤖 Бот: ", end="", flush=True)
                response = model.respond(chat)

                # Добавляем ответ в историю
                chat.add_assistant_response(response)

                # Выводим ответ
                print(response + "\n")

            except EOFError:
                print("\n\nДо свидания!")
                break
            except KeyboardInterrupt:
                print("\n\nПрервано пользователем. До свидания!")
                break

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        print("Убедитесь, что LM Studio запущен и модель загружена!")

if __name__ == "__main__":
    interactive_chat()
