#!/usr/bin/env python
"""
🤖 NEYROLOCK Telegram Bot - Телеграм бот для работы с AI моделями
Полный функционал как в GUI версии
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict
import threading

# Telegram
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
except ImportError:
    print("❌ Установите: pip3 install python-telegram-bot")
    exit(1)

# AI модели
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

try:
    from model_manager import ModelManager
except ImportError:
    ModelManager = None


class AITelegramBot:
    """Telegram бот для работы с AI."""

    def __init__(self, token: str):
        """Инициализация бота."""
        self.token = token
        self.model = None
        self.model_name = None
        self.model_path = None
        self.user_histories: Dict[int, list] = {}  # История для каждого пользователя
        self.model_manager = ModelManager() if ModelManager else None

        # Конфигурация
        self.config_dir = Path.home() / ".neyrolock"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Сохраняем токен
        self.save_token(token)

        # Синхронизация с GUI
        try:
            from sync_manager import SyncManager
            self.sync_manager = SyncManager()
            self.sync_manager.update_status("telegram_active", True)
            print("📱 Синхронизация с GUI активирована")
        except ImportError:
            self.sync_manager = None

    def save_token(self, token: str):
        """Сохранение токена."""
        config_file = self.config_dir / "telegram_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump({"token": token}, f)
        except Exception as e:
            print(f"Ошибка сохранения токена: {e}")

    def get_main_keyboard(self):
        """Главная клавиатура."""
        keyboard = [
            [KeyboardButton("💬 Начать диалог"), KeyboardButton("📥 Скачать модель")],
            [KeyboardButton("📂 Загрузить модель"), KeyboardButton("📋 Мои модели")],
            [KeyboardButton("🗑️ Очистить историю"), KeyboardButton("ℹ️ Статус")],
            [KeyboardButton("❓ Помощь")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    def get_category_keyboard(self):
        """Клавиатура выбора категории."""
        keyboard = [
            [InlineKeyboardButton("🐣 Tiny (300-700MB)", callback_data="cat_tiny")],
            [InlineKeyboardButton("📦 Small (2GB) ⭐", callback_data="cat_small")],
            [InlineKeyboardButton("💪 Medium (4-5GB)", callback_data="cat_medium")],
            [InlineKeyboardButton("🎨 Multimodal (4GB)", callback_data="cat_multimodal")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_models_keyboard(self, category: str):
        """Клавиатура выбора модели."""
        if not self.model_manager:
            return None

        models = self.model_manager.RECOMMENDED_MODELS.get(category, [])
        keyboard = []

        for i, model in enumerate(models):
            size = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']}MB"
            text = f"{model['filename'].split('.')[0][:30]} ({size})"
            keyboard.append([InlineKeyboardButton(text, callback_data=f"model_{category}_{i}")])

        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_cats")])
        return InlineKeyboardMarkup(keyboard)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start."""
        welcome_text = """
🤖 *NEYROLOCK Bot*

Добро пожаловать! Этот бот позволяет общаться с AI моделями прямо в Telegram!

*Возможности:*
• 📥 Скачивание моделей с HuggingFace
• 💬 Общение с локальными AI моделями
• 📋 Управление коллекцией моделей
• 🗑️ Очистка истории диалога

*Начало работы:*
1. Нажмите "📥 Скачать модель"
2. Выберите категорию и модель
3. Дождитесь скачивания
4. Начинайте диалог!

Используйте кнопки ниже для навигации 👇
        """
        await update.message.reply_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=self.get_main_keyboard()
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда помощи."""
        help_text = """
❓ *Помощь*

*Команды:*
/start - Главное меню
/status - Статус модели
/clear - Очистить историю
/help - Эта справка

*Кнопки:*
• 💬 Начать диалог - режим общения
• 📥 Скачать модель - скачать с HuggingFace
• 📂 Загрузить модель - выбрать скачанную
• 📋 Мои модели - список скачанных
• 🗑️ Очистить историю - сбросить диалог
• ℹ️ Статус - информация о модели

*Как использовать:*
1. Скачайте или загрузите модель
2. Просто пишите сообщения боту
3. Бот ответит от имени AI модели

*Рекомендации:*
• Начните с модели Llama 3.2 3B (2GB)
• Для быстрых тестов - Qwen 0.5B (300MB)
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статус модели."""
        user_id = update.effective_user.id

        if not self.model:
            status = "⚠️ *Модель не загружена*\n\nИспользуйте '📥 Скачать модель' или '📂 Загрузить модель'"
        else:
            history_len = len(self.user_histories.get(user_id, []))
            status = f"""
ℹ️ *Статус*

*Модель:* {self.model_name}
*Путь:* {self.model_path}
*Сообщений в истории:* {history_len}

✅ Готов к работе!
            """

        await update.message.reply_text(status, parse_mode="Markdown")

    async def clear_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Очистка истории."""
        user_id = update.effective_user.id
        self.user_histories[user_id] = []
        await update.message.reply_text("🗑️ История диалога очищена!")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений."""
        text = update.message.text
        user_id = update.effective_user.id

        # Обработка кнопок меню
        if text == "💬 Начать диалог":
            if not self.model:
                await update.message.reply_text(
                    "⚠️ Сначала загрузите модель!\n\n"
                    "Нажмите '📥 Скачать модель' или '📂 Загрузить модель'"
                )
            else:
                await update.message.reply_text(
                    f"✅ Готов к диалогу!\n\n"
                    f"Модель: *{self.model_name}*\n\n"
                    f"Просто напишите сообщение 💬",
                    parse_mode="Markdown"
                )

        elif text == "📥 Скачать модель":
            await self.show_download_menu(update, context)

        elif text == "📂 Загрузить модель":
            await self.show_downloaded_models(update, context)

        elif text == "📋 Мои модели":
            await self.list_models(update, context)

        elif text == "🗑️ Очистить историю":
            await self.clear_history(update, context)

        elif text == "ℹ️ Статус":
            await self.status_command(update, context)

        elif text == "❓ Помощь":
            await self.help_command(update, context)

        else:
            # Обычное сообщение - отправляем модели
            await self.chat_with_model(update, context, text)

    async def show_download_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню скачивания."""
        if not self.model_manager:
            await update.message.reply_text(
                "❌ Менеджер моделей недоступен.\n"
                "Установите: pip3 install huggingface-hub"
            )
            return

        text = """
📥 *Скачивание модели с HuggingFace*

Выберите категорию модели:

🐣 *Tiny* - для быстрых тестов (300-700MB)
📦 *Small* - рекомендуется (2GB) ⭐
💪 *Medium* - лучшее качество (4-5GB)
🎨 *Multimodal* - текст + изображения (4GB)
        """

        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=self.get_category_keyboard()
        )

    async def show_downloaded_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать скачанные модели."""
        if not self.model_manager:
            await update.message.reply_text("❌ Менеджер моделей недоступен")
            return

        models = self.model_manager.list_downloaded_models()

        if not models:
            await update.message.reply_text(
                "📋 *Нет скачанных моделей*\n\n"
                "Используйте '📥 Скачать модель' чтобы скачать",
                parse_mode="Markdown"
            )
            return

        keyboard = []
        for i, model in enumerate(models):
            size = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']:.0f}MB"
            text = f"{model['filename'][:35]} ({size})"
            keyboard.append([InlineKeyboardButton(text, callback_data=f"load_{i}")])

        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])

        await update.message.reply_text(
            "📂 *Выберите модель для загрузки:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def list_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Список скачанных моделей."""
        if not self.model_manager:
            await update.message.reply_text("❌ Менеджер моделей недоступен")
            return

        models = self.model_manager.list_downloaded_models()

        if not models:
            text = "📋 *Скачанные модели:*\n\nПусто. Используйте '📥 Скачать модель'"
        else:
            text = "📋 *Скачанные модели:*\n\n"
            for i, model in enumerate(models, 1):
                size = f"{model['size_mb']/1000:.1f}GB" if model['size_mb'] >= 1000 else f"{model['size_mb']:.0f}MB"
                text += f"{i}. *{model['filename']}*\n   Размер: {size}\n\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий inline-кнопок."""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "cancel":
            await query.edit_message_text("❌ Отменено")

        elif data == "back_to_cats":
            await query.edit_message_text(
                "📥 Выберите категорию модели:",
                reply_markup=self.get_category_keyboard()
            )

        elif data.startswith("cat_"):
            category = data.replace("cat_", "")
            await query.edit_message_text(
                f"📦 Модели в категории *{category}*:\n\nВыберите модель:",
                parse_mode="Markdown",
                reply_markup=self.get_models_keyboard(category)
            )

        elif data.startswith("model_"):
            parts = data.split("_")
            category = parts[1]
            index = int(parts[2])

            # Скачиваем модель
            await self.download_model(query, category, index)

        elif data.startswith("load_"):
            index = int(data.replace("load_", ""))
            await self.load_downloaded_model(query, index)

    async def download_model(self, query, category: str, index: int):
        """Скачивание модели."""
        if not self.model_manager:
            await query.edit_message_text("❌ Менеджер моделей недоступен")
            return

        model_info = self.model_manager.RECOMMENDED_MODELS[category][index]
        size_gb = model_info['size_mb'] / 1000

        await query.edit_message_text(
            f"📥 *Скачивание модели...*\n\n"
            f"*Файл:* {model_info['filename']}\n"
            f"*Размер:* {size_gb:.1f} GB\n\n"
            f"⏳ Это может занять несколько минут...",
            parse_mode="Markdown"
        )

        # Скачиваем в отдельном потоке
        def download_thread():
            try:
                path = self.model_manager.download_model(
                    repo_id=model_info['repo_id'],
                    filename=model_info['filename'],
                    description=model_info['description']
                )
                return path
            except Exception as e:
                return str(e)

        # Запускаем скачивание
        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(None, download_thread)

        if path and isinstance(path, Path):
            # Загружаем модель
            success = await self.load_model(str(path))

            if success:
                await query.edit_message_text(
                    f"✅ *Модель загружена!*\n\n"
                    f"*Файл:* {model_info['filename']}\n\n"
                    f"Теперь можете начать диалог! 💬",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    f"⚠️ Модель скачана, но не удалось загрузить\n\n"
                    f"Путь: {path}"
                )
        else:
            await query.edit_message_text(f"❌ Ошибка скачивания: {path}")

    async def load_downloaded_model(self, query, index: int):
        """Загрузка скачанной модели."""
        if not self.model_manager:
            await query.edit_message_text("❌ Менеджер моделей недоступен")
            return

        models = self.model_manager.list_downloaded_models()
        if index >= len(models):
            await query.edit_message_text("❌ Модель не найдена")
            return

        model_info = models[index]
        model_path = str(model_info['path'])

        await query.edit_message_text(
            f"⏳ *Загрузка модели...*\n\n"
            f"*Файл:* {model_info['filename']}\n\n"
            f"Это может занять несколько секунд...",
            parse_mode="Markdown"
        )

        success = await self.load_model(model_path)

        if success:
            await query.edit_message_text(
                f"✅ *Модель загружена!*\n\n"
                f"*Файл:* {model_info['filename']}\n\n"
                f"Теперь можете начать диалог! 💬",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Не удалось загрузить модель")

    async def load_model(self, model_path: str) -> bool:
        """Загрузка модели."""
        if not Llama:
            return False

        def load_thread():
            try:
                model = Llama(
                    model_path=model_path,
                    n_ctx=2048,
                    n_gpu_layers=-1,
                    verbose=False
                )
                return model
            except Exception as e:
                print(f"Ошибка загрузки: {e}")
                return None

        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(None, load_thread)

        if model:
            self.model = model
            self.model_path = model_path
            self.model_name = Path(model_path).name
            return True

        return False

    async def chat_with_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_message: str):
        """Общение с моделью со стримингом (обновление каждые 3 символа)."""
        if not self.model:
            await update.message.reply_text(
                "⚠️ Модель не загружена!\n\n"
                "Используйте '📥 Скачать модель' или '📂 Загрузить модель'"
            )
            return

        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Инициализируем историю для пользователя
        if user_id not in self.user_histories:
            self.user_histories[user_id] = []

        # Добавляем сообщение в историю
        self.user_histories[user_id].append({
            "role": "user",
            "content": user_message
        })

        # Синхронизируем с GUI
        if self.sync_manager:
            self.sync_manager.send_message("telegram", "user", user_message, chat_id)
            self.sync_manager.start_stream("telegram", chat_id)

        # Отправляем начальное сообщение
        bot_message = await update.message.reply_text("🤖 *AI:*\n\n▌", parse_mode="Markdown")

        # Стриминг генерации
        response_text = ""
        chars_since_update = 0
        last_update_len = 0

        def generate_stream():
            nonlocal response_text, chars_since_update
            try:
                stream = self.model.create_chat_completion(
                    messages=self.user_histories[user_id],
                    max_tokens=512,
                    temperature=0.7,
                    stream=True
                )

                for chunk in stream:
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        if 'content' in delta:
                            content = delta['content']
                            response_text += content
                            chars_since_update += len(content)

                            # Синхронизируем с GUI
                            if self.sync_manager:
                                self.sync_manager.update_stream(content)

                return True
            except Exception as e:
                response_text = f"❌ Ошибка: {e}"
                return False

        # Запускаем генерацию в отдельном потоке
        loop = asyncio.get_event_loop()

        # Создаем задачу для стриминга
        generate_task = loop.run_in_executor(None, generate_stream)

        # Обновляем сообщение каждые 3 символа
        update_interval = 0.3  # секунд

        while not generate_task.done():
            await asyncio.sleep(update_interval)

            # Обновляем сообщение если добавилось >= 3 символов
            if len(response_text) - last_update_len >= 3:
                try:
                    # Добавляем курсор в конце для эффекта печати
                    display_text = response_text + "▌"
                    await bot_message.edit_text(
                        f"🤖 *AI:*\n\n{display_text}",
                        parse_mode="Markdown"
                    )
                    last_update_len = len(response_text)
                except Exception:
                    pass  # Игнорируем ошибки редактирования (rate limit)

        # Ждем завершения генерации
        await generate_task

        # Финальное обновление без курсора
        try:
            await bot_message.edit_text(
                f"🤖 *AI:*\n\n{response_text}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

        # Завершаем стрим
        if self.sync_manager:
            self.sync_manager.end_stream()
            self.sync_manager.send_message("telegram", "assistant", response_text, chat_id)

        # Добавляем ответ в историю
        self.user_histories[user_id].append({
            "role": "assistant",
            "content": response_text
        })

    def run(self):
        """Запуск бота."""
        print("🤖 Запуск Telegram бота...")

        app = Application.builder().token(self.token).build()

        # Команды
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("clear", self.clear_history))

        # Кнопки
        app.add_handler(CallbackQueryHandler(self.button_callback))

        # Текстовые сообщения
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        print("✅ Бот запущен! Отправьте /start в Telegram")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Точка входа."""
    import argparse

    parser = argparse.ArgumentParser(description="NEYROLOCK Telegram Bot")
    parser.add_argument("--token", type=str, help="Telegram bot token")
    args = parser.parse_args()

    # Получаем токен из аргументов, env переменной или интерактивно
    token = args.token or os.environ.get("TELEGRAM_BOT_TOKEN", "")

    if not token:
        print("🤖 NEYROLOCK Telegram Bot Setup")
        print("=" * 50)
        token = input("\nВведите токен Telegram бота: ").strip()

    if not token:
        print("❌ Токен не указан")
        return

    # Запускаем бота
    bot = AITelegramBot(token)
    bot.run()


if __name__ == "__main__":
    main()
