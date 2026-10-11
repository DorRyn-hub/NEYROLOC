#!/usr/bin/env python
"""Скрипт для получения подробной информации о сервере и доступных моделях."""

import lmstudio as lms

def print_server_info():
    """Выводит детальную информацию о сервере."""
    try:
        client = lms.Client()

        print("=" * 70)
        print("ИНФОРМАЦИЯ О LM STUDIO СЕРВЕРЕ")
        print("=" * 70)

        # Информация о системе
        print("\n📊 СИСТЕМНАЯ ИНФОРМАЦИЯ:")
        try:
            system_info = client.system.get()
            print(f"   Версия SDK: {lms.__version__ if hasattr(lms, '__version__') else 'Unknown'}")
        except:
            print("   Не удалось получить системную информацию")

        # Список всех доступных моделей (не загруженных)
        print("\n📦 ДОСТУПНЫЕ МОДЕЛИ (скачанные, но не загруженные):")
        try:
            downloaded_models = client.llm.list_downloaded()
            if downloaded_models:
                for i, model in enumerate(downloaded_models, 1):
                    print(f"   {i}. {model.path}")
                    print(f"      Тип: {model.type if hasattr(model, 'type') else 'unknown'}")
            else:
                print("   Нет скачанных моделей")
        except Exception as e:
            print(f"   Ошибка: {e}")

        # Список загруженных моделей
        print("\n🚀 ЗАГРУЖЕННЫЕ МОДЕЛИ (готовы к использованию):")
        try:
            loaded_models = client.llm.list_loaded()
            if loaded_models:
                for i, model in enumerate(loaded_models, 1):
                    print(f"   {i}. {model.identifier}")
                    if hasattr(model, 'architecture'):
                        print(f"      Архитектура: {model.architecture}")
                    if hasattr(model, 'size'):
                        print(f"      Размер: {model.size}")
            else:
                print("   ⚠ Нет загруженных моделей")
                print("   Загрузите модель в LM Studio для начала работы")
        except Exception as e:
            print(f"   Ошибка: {e}")

        print("\n" + "=" * 70)

        client.disconnect()

    except ConnectionError as e:
        print(f"\n✗ Не удалось подключиться к серверу: {e}")
        print("\nПроверьте:")
        print("  • LM Studio запущен")
        print("  • Сервер активен (обычно http://localhost:1234)")
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")

if __name__ == "__main__":
    print_server_info()
