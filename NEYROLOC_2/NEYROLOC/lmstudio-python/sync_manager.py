
#!/usr/bin/env python3
"""
Менеджер синхронизации между GUI и Telegram ботом.
Использует JSON файл для обмена сообщениями в реальном времени.
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
import threading


class SyncManager:
    """Синхронизация чатов между GUI и Telegram."""

    def __init__(self):
        self.sync_dir = Path.home() / ".neyrolock" / "sync"
        self.sync_dir.mkdir(parents=True, exist_ok=True)

        self.messages_file = self.sync_dir / "messages.json"
        self.status_file = self.sync_dir / "status.json"
        self.stream_file = self.sync_dir / "stream.json"

        # Инициализируем файлы
        self._init_files()

        # Callback для получения сообщений
        self.on_message_callback = None
        self.on_stream_callback = None

        # Поток для мониторинга
        self.monitoring = False
        self.monitor_thread = None
        self.last_message_id = 0

    def _init_files(self):
        """Инициализация файлов синхронизации."""
        if not self.messages_file.exists():
            self._write_json(self.messages_file, {"messages": [], "last_id": 0})

        if not self.status_file.exists():
            self._write_json(self.status_file, {
                "gui_active": False,
                "telegram_active": False,
                "model_loaded": False,
                "model_name": ""
            })

        if not self.stream_file.exists():
            self._write_json(self.stream_file, {
                "is_streaming": False,
                "content": "",
                "source": "",
                "chat_id": 0
            })

    def _write_json(self, file_path: Path, data: dict):
        """Записать JSON файл."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _read_json(self, file_path: Path) -> dict:
        """Прочитать JSON файл."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    # ==================== Сообщения ====================

    def send_message(self, source: str, role: str, content: str, chat_id: int = 0):
        """
        Отправить сообщение в синхронизированный чат.

        Args:
            source: "gui" или "telegram"
            role: "user" или "assistant"
            content: текст сообщения
            chat_id: ID чата в Telegram (0 для GUI)
        """
        data = self._read_json(self.messages_file)
        messages = data.get("messages", [])
        last_id = data.get("last_id", 0) + 1

        message = {
            "id": last_id,
            "source": source,
            "role": role,
            "content": content,
            "chat_id": chat_id,
            "timestamp": time.time()
        }

        messages.append(message)

        # Храним последние 100 сообщений
        if len(messages) > 100:
            messages = messages[-100:]

        self._write_json(self.messages_file, {
            "messages": messages,
            "last_id": last_id
        })

        return last_id

    def get_new_messages(self, since_id: int = 0) -> list:
        """Получить новые сообщения с указанного ID."""
        data = self._read_json(self.messages_file)
        messages = data.get("messages", [])
        return [m for m in messages if m.get("id", 0) > since_id]

    # ==================== Стриминг ====================

    def start_stream(self, source: str, chat_id: int = 0):
        """Начать стриминг ответа."""
        self._write_json(self.stream_file, {
            "is_streaming": True,
            "content": "",
            "source": source,
            "chat_id": chat_id,
            "chars_count": 0
        })

    def update_stream(self, new_content: str):
        """Обновить стрим (добавить символы)."""
        data = self._read_json(self.stream_file)
        data["content"] += new_content
        data["chars_count"] = len(data["content"])
        self._write_json(self.stream_file, data)

    def get_stream_content(self) -> dict:
        """Получить текущий контент стрима."""
        return self._read_json(self.stream_file)

    def end_stream(self):
        """Завершить стриминг."""
        data = self._read_json(self.stream_file)
        data["is_streaming"] = False
        self._write_json(self.stream_file, data)

    # ==================== Статус ====================

    def update_status(self, key: str, value: Any):
        """Обновить статус."""
        data = self._read_json(self.status_file)
        data[key] = value
        self._write_json(self.status_file, data)

    def get_status(self) -> dict:
        """Получить статус."""
        return self._read_json(self.status_file)

    # ==================== Мониторинг ====================

    def start_monitoring(self, on_message=None, on_stream=None):
        """
        Начать мониторинг новых сообщений.

        Args:
            on_message: callback(message_dict)
            on_stream: callback(stream_dict)
        """
        self.on_message_callback = on_message
        self.on_stream_callback = on_stream
        self.monitoring = True

        # Получаем текущий last_id
        data = self._read_json(self.messages_file)
        self.last_message_id = data.get("last_id", 0)

        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Остановить мониторинг."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def _monitor_loop(self):
        """Цикл мониторинга (оптимизированный)."""
        last_stream_chars = 0
        check_counter = 0

        while self.monitoring:
            try:
                check_counter += 1

                # Проверяем сообщения каждые 500мс (каждый 5-й цикл)
                if check_counter % 5 == 0:
                    new_messages = self.get_new_messages(self.last_message_id)
                    for msg in new_messages:
                        self.last_message_id = msg["id"]
                        if self.on_message_callback:
                            self.on_message_callback(msg)

                # Проверяем стрим каждые 300мс (каждый 3-й цикл)
                if check_counter % 3 == 0:
                    stream_data = self.get_stream_content()
                    if stream_data.get("is_streaming"):
                        current_chars = stream_data.get("chars_count", 0)
                        if current_chars > last_stream_chars:
                            last_stream_chars = current_chars
                            if self.on_stream_callback:
                                self.on_stream_callback(stream_data)
                    else:
                        last_stream_chars = 0

                time.sleep(0.1)  # Базовый интервал 100мс

            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)

    def clear_all(self):
        """Очистить все данные синхронизации."""
        self._init_files()
        self.last_message_id = 0
