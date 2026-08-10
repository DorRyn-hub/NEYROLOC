"""Главное окно — связывает sidebar, chat и backend."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from backends import ALL_BACKENDS, Backend
from backends.base import BackendConfig, Message
from core.config import Config
from core.history import HISTORY_DIR, ChatSession, load_session
from core.json_store import atomic_write_json
from core.model_library import ModelLibrary
from core.remote_server import (
    DEFAULT_PORT,
    RemoteBridge,
    RemoteServer,
    local_ip,
    tailscale_ip,
)
from core.tunnel import Tunnel
from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QWidget,
)

from ui.chat_widget import ChatWidget
from ui.model_library_dialog import ModelLibraryDialog
from ui.remote_dialog import RemoteAccessDialog
from ui.sidebar import Sidebar


class PrepareWorker(QThread):
    """Поток подготовки модели — скачивание / загрузка в память."""

    progress = Signal(str)
    finishedOk = Signal()
    failed = Signal(str)

    def __init__(self, backend: Backend, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._backend = backend

    def run(self) -> None:  # noqa: D401 — Qt API
        try:
            self._backend.prepare(progress=self.progress.emit)
            self.finishedOk.emit()
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class ListModelsWorker(QThread):
    """Поток запроса списка моделей — не блокирует UI при недоступном сервере."""

    finishedOk = Signal(list)
    failed = Signal(str)

    def __init__(self, backend: Backend, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._backend = backend

    def run(self) -> None:  # noqa: D401 — Qt API
        try:
            models = self._backend.list_models()
            self.finishedOk.emit(models)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class GenerateWorker(QThread):
    """Поток генерации ответа — стримит фрагменты через сигнал chunk."""

    chunk = Signal(str)
    finishedOk = Signal()
    failed = Signal(str)

    def __init__(
        self,
        backend: Backend,
        messages: list[Message],
        temperature: float,
        lock=None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._backend = backend
        self._messages = messages
        self._temperature = temperature
        self._lock = lock
        self._stop = False

    def stop(self) -> None:
        self._stop = True
        self._backend.cancel()

    @property
    def stop_requested(self) -> bool:
        return self._stop

    def run(self) -> None:  # noqa: D401 — Qt API
        # Общий замок с сервером удалённого доступа: одна генерация на модель,
        # иначе одновременный запрос с телефона уронит llama.cpp.
        if self._lock is not None and not self._lock.acquire(timeout=0.5):
            self.failed.emit(
                "Модель занята — идёт генерация с телефона. Подождите её завершения."
            )
            return
        if self._stop:
            if self._lock is not None:
                self._lock.release()
            self.finishedOk.emit()
            return
        gen = None
        error: str | None = None
        try:
            gen = self._backend.generate(self._messages, self._temperature)
            for piece in gen:
                if self._stop:
                    break
                self.chunk.emit(piece)
        except Exception as exc:  # backend может бросать что угодно
            if not self._stop:
                error = f"{type(exc).__name__}: {exc}"
        finally:
            if gen is not None:
                try:
                    gen.close()
                except Exception:
                    pass
            if self._lock is not None:
                self._lock.release()
        if error is not None:
            self.failed.emit(error)
        else:
            self.finishedOk.emit()


class DownloadModelWorker(QThread):
    """Поток скачивания GGUF модели из HuggingFace."""

    progress = Signal(str)
    # (процент 0-100, скачано байт, всего байт) — для живого прогресс-бара.
    progressPercent = Signal(int, int, int)
    finishedOk = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        library: ModelLibrary,
        repo_id: str,
        filename: str,
        description: str,
        token: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._library = library
        self._repo_id = repo_id
        self._filename = filename
        self._description = description
        self._token = token or None
        self._last_percent = -1

    def _on_progress_bytes(self, done: int, total: int) -> None:
        percent = int(done * 100 / total) if total else 0
        if percent == self._last_percent:
            return
        self._last_percent = percent
        self.progressPercent.emit(percent, done, total)

    def run(self) -> None:  # noqa: D401 — Qt API
        try:
            path = self._library.download_model(
                repo_id=self._repo_id,
                filename=self._filename,
                description=self._description,
                token=self._token,
                progress=self.progress.emit,
                progress_bytes=self._on_progress_bytes,
            )
            self.finishedOk.emit(str(path))
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NEYROLOC NEW")
        self.resize(1280, 800)
        self.setMinimumSize(640, 480)

        self.config = Config()
        self.session = ChatSession(self.config.system_prompt)
        self.backend: Backend | None = None
        self._worker: GenerateWorker | None = None
        self._prepare_worker: PrepareWorker | None = None
        self._pending_model: str | None = None  # модель, выбранная пока шёл prepare
        self._system_prompt_save_timer = QTimer(self)
        self._system_prompt_save_timer.setInterval(400)
        self._system_prompt_save_timer.setSingleShot(True)
        self._system_prompt_save_timer.timeout.connect(self._flush_system_prompt)
        self._download_worker: DownloadModelWorker | None = None
        self._list_worker: ListModelsWorker | None = None
        self._stale_list_workers: list[ListModelsWorker] = []
        self._close_pending = False
        self._model_library_dialog: ModelLibraryDialog | None = None
        self.model_library = ModelLibrary()

        # --- удалённый доступ с телефона ---
        self._remote_bridge = RemoteBridge()
        self._remote_bridge.system_prompt = self.config.system_prompt
        self._remote_bridge.temperature = self.config.temperature
        self._remote_bridge.pair_code = self._remote_pair_code()
        self._remote_bridge.statusChanged.connect(self._set_status)
        self._remote_bridge.modelChanged.connect(self._on_remote_model_changed)
        self._remote_server = RemoteServer(self._remote_bridge)
        # Публичный адрес (работает вне домашней Wi-Fi) — через свой FRP-туннель.
        self._tunnel = Tunnel(self.config, DEFAULT_PORT, parent=self)
        self._tunnel.statusChanged.connect(self._set_status)

        # --- центральный виджет ---
        central = QWidget()
        central.setObjectName("central")
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        self.sidebar = Sidebar()
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setObjectName("sidebarScroll")
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QScrollArea.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setWidget(self.sidebar)
        # The old fixed 360 px width made the splitter decorative and left the
        # chat unusably narrow in compact windows.  Keep sensible bounds while
        # allowing the user to tune the balance.
        # Leave room for the vertical scrollbar as well as Sidebar's own
        # 280 px minimum; otherwise compact windows silently crop its right
        # edge while horizontal scrolling is disabled.
        sidebar_scroll.setMinimumWidth(292)
        sidebar_scroll.setMaximumWidth(420)
        self._sidebar_scroll = sidebar_scroll
        self.chat = ChatWidget()
        splitter.addWidget(sidebar_scroll)
        splitter.addWidget(self.chat)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setChildrenCollapsible(False)
        splitter.setSizes([320, 960])
        layout.addWidget(splitter)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())
        self.statusBar().setAccessibleName("Состояние приложения")
        self._build_menus()

        # --- сигналы ---
        self.sidebar.backendActivated.connect(self._on_backend_activated)
        self.sidebar.applyClicked.connect(self._on_apply_clicked)
        self.sidebar.modelChanged.connect(self._on_model_changed)
        self.sidebar.temperatureChanged.connect(self._on_temperature_changed)
        self.sidebar.systemPromptChanged.connect(self._on_system_prompt_changed)
        self.sidebar.modelLibraryClicked.connect(self._on_model_library)
        self.sidebar.newChatClicked.connect(self._on_new_chat)
        self.sidebar.saveChatClicked.connect(self._on_save_chat)
        self.sidebar.loadChatClicked.connect(self._on_load_chat)

        self.chat.sendRequested.connect(self._on_send)
        self.chat.stopRequested.connect(self._on_stop)
        self.chat.regenerateRequested.connect(self._on_regenerate)
        self.chat.set_input_enabled(False)

        # --- восстановление состояния ---
        self.sidebar.set_temperature(self.config.temperature)
        self.sidebar.set_system_prompt(self.config.system_prompt)
        restored_backend = self.config.active_backend
        if restored_backend and self._backend_class(restored_backend) is None:
            # Backend из старого config.json (например, убранный LM Studio/
            # Ollama/HuggingFace GGUF) больше не зарегистрирован — откатываемся
            # на Local GGUF вместо пустого сайдбара.
            restored_backend = "local_gguf"
            self.config.active_backend = restored_backend
        if restored_backend:
            self.sidebar.set_active_backend(restored_backend)
            self._load_config_into_form(restored_backend)
            cls = self._backend_class(restored_backend)
            if cls is not None:
                self._update_backend_selection_ui(cls)
        else:
            self._set_status("Готов. Выберите backend.")

    # ----- helpers -----

    def _set_status(self, text: str) -> None:
        self.statusBar().showMessage(text)

    def _backend_class(self, backend_id: str) -> type[Backend] | None:
        return next((c for c in ALL_BACKENDS if c.id == backend_id), None)

    def _load_config_into_form(self, backend_id: str) -> None:
        values = self.config.backend_config(backend_id)
        self.sidebar.set_config_values(values)

    def _update_backend_selection_ui(self, cls: type[Backend]) -> None:
        if not cls.is_available():
            self._set_status(
                f"{cls.display_name}: библиотека не установлена. См. requirements.txt."
            )
            self.sidebar.set_apply_enabled(False)
            return
        self._set_status(
            f"Выбран {cls.display_name}. Заполните параметры и нажмите «Подключить»."
        )
        self.sidebar.set_apply_enabled(True)

    # ----- сигналы sidebar -----

    def _on_backend_activated(self, backend_id: str) -> None:
        # Результат незавершённого запроса моделей относится к прежнему выбору.
        self._cancel_list_worker()
        self.config.active_backend = backend_id
        self._load_config_into_form(backend_id)

        cls = self._backend_class(backend_id)
        if cls is None:
            return
        self._update_backend_selection_ui(cls)

    def _on_apply_clicked(self) -> None:
        backend_id = self.sidebar.current_backend_id
        if not backend_id:
            return
        cls = self._backend_class(backend_id)
        if cls is None:
            return

        values = self.sidebar.get_config_values()
        self.config.set_backend_config(backend_id, values)

        # Закрыть предыдущий backend, если был. Во время генерации/prepare/
        # сетевого запроса teardown небезопасен, поэтому просим повторить после
        # завершения операции, не закрывая объект из-под рабочего потока.
        if not self._teardown_backend():
            return

        backend = cls(BackendConfig(values=dict(values)))
        self.backend = backend
        self._remote_bridge.backend = backend
        self._remote_bridge.backend_name = cls.display_name

        self.sidebar.set_apply_enabled(False)
        self._set_status(f"{cls.display_name}: загрузка списка моделей…")
        self._list_worker = ListModelsWorker(backend, parent=self)
        self._list_worker.finishedOk.connect(self._on_models_listed)
        self._list_worker.failed.connect(self._on_models_failed)
        self._list_worker.start()

    def _on_models_listed(self, models: list) -> None:
        if self.sender() is not self._list_worker:
            return
        self._list_worker = None
        self.sidebar.set_apply_enabled(True)
        self._remote_bridge.available_models = list(models)

        backend_id = self.sidebar.current_backend_id
        cls = self._backend_class(backend_id) if backend_id else None
        name = cls.display_name if cls else "Backend"

        if not models:
            self._set_status(
                f"{name}: модели не найдены. "
                "Проверьте, что сервер запущен и модель загружена."
            )
            self.sidebar.set_models([], None)
            self.chat.set_input_enabled(False)
            return

        last = self.config.last_model(backend_id) if backend_id else None
        # Авто-подхват prepare только если модель уже подтверждена пользователем ранее.
        # Иначе (особенно для HuggingFace) не начинаем качать 5 ГБ без явного выбора.
        if last and last in models:
            self.sidebar.set_models(models, last, auto_emit=True)
            self._set_status(f"{name}: подключено. Загружаю модель «{last}»…")
        else:
            self.sidebar.set_models(models, models[0], auto_emit=False)
            self.chat.set_input_enabled(False)
            self._set_status(f"{name}: моделей {len(models)}. Выберите модель.")

    def _on_models_failed(self, error: str) -> None:
        if self.sender() is not self._list_worker:
            return
        self._list_worker = None
        self.sidebar.set_apply_enabled(True)
        self._show_error("Не удалось получить список моделей", error)
        self._set_status("Ошибка подключения.")

    def _on_model_changed(self, model: str) -> None:
        if not self.backend or not model:
            return
        if self._worker is not None or self._remote_bridge.generation_lock.locked():
            self.sidebar.set_models(
                self._remote_bridge.available_models,
                self.backend.current_model,
                auto_emit=False,
            )
            self._set_status("Нельзя менять модель во время генерации.")
            return
        # Если уже подготовлена та же модель — ничего не делаем.
        if self.backend.current_model == model and self._prepare_worker is None:
            return

        self.backend.set_model(model)
        if self.sidebar.current_backend_id:
            self.config.set_last_model(self.sidebar.current_backend_id, model)

        # Prepare уже идёт — запоминаем выбор, запустим после завершения.
        if self._prepare_worker is not None:
            self._pending_model = model
            return

        self._pending_model = None
        self.chat.set_input_enabled(False)
        self._prepare_worker = PrepareWorker(self.backend, parent=self)
        self._prepare_worker.progress.connect(self._set_status)
        self._prepare_worker.finishedOk.connect(self._on_prepare_finished)
        self._prepare_worker.failed.connect(self._on_prepare_failed)
        self._set_status(f"Подготовка модели «{model}»…")
        self._prepare_worker.start()

    def _on_prepare_finished(self) -> None:
        # Stale-сигнал после _teardown_backend (сигнал уже был в очереди Qt).
        if self._prepare_worker is None:
            return
        self._prepare_worker = None

        # Пока шла загрузка, пользователь выбрал другую модель — загружаем её.
        pending = self._pending_model
        self._pending_model = None
        if pending:
            self._on_model_changed(pending)
            return

        self.chat.set_input_enabled(True)
        model = self.backend.current_model if self.backend else "?"
        self._set_status(f"Модель готова: {model}")

    def _on_prepare_failed(self, error: str) -> None:
        # Stale-сигнал после _teardown_backend.
        if self._prepare_worker is None:
            return
        self._prepare_worker = None
        self._pending_model = None
        self.chat.set_input_enabled(False)
        self._show_error("Не удалось подготовить модель", error)
        self._set_status("Ошибка подготовки модели.")

    def _on_temperature_changed(self, value: float) -> None:
        self.config.temperature = value
        self._remote_bridge.temperature = value

    def _on_system_prompt_changed(self, text: str) -> None:
        # Обновляем сессию сразу (нужно для точной генерации).
        if self.session.messages and self.session.messages[0].role == "system":
            if text:
                self.session.messages[0] = Message("system", text)
            else:
                self.session.messages.pop(0)
        elif text:
            self.session.messages.insert(0, Message("system", text))
        # Запись на диск — debounce 400 мс, чтобы не писать на каждый символ.
        self.config.data["system_prompt"] = text
        self._remote_bridge.system_prompt = text
        self._system_prompt_save_timer.start()

    def _flush_system_prompt(self) -> None:
        self.config.save()

    def _on_model_library(self) -> None:
        dialog = ModelLibraryDialog(self.model_library, self)
        dialog.useModelRequested.connect(self._use_local_model)
        dialog.downloadRequested.connect(self._download_model)
        self._model_library_dialog = dialog
        try:
            dialog.exec()
        finally:
            self._model_library_dialog = None

    def _use_local_model(self, path: str) -> None:
        if self._worker is not None or (
            self._prepare_worker is not None and self._prepare_worker.isRunning()
        ):
            self._set_status("Дождитесь завершения текущей операции с моделью.")
            return
        backend_id = "local_gguf"
        self.sidebar.set_active_backend(backend_id)
        self._on_backend_activated(backend_id)

        values = self.config.backend_config(backend_id)
        values["model_path"] = path
        values.setdefault("n_ctx", "8192")
        values.setdefault("n_gpu_layers", "-1")
        self.sidebar.set_config_values(values)
        self.config.set_backend_config(backend_id, values)
        self.config.set_last_model(backend_id, Path(path).name)
        self._set_status(f"Выбрана локальная модель: {Path(path).name}")

        cls = self._backend_class(backend_id)
        if cls is not None and cls.is_available():
            self._on_apply_clicked()

    def _download_model(
        self, repo_id: str, filename: str, description: str, token: str = ""
    ) -> None:
        if self._download_worker is not None:
            self._set_status("Скачивание уже выполняется.")
            if self._model_library_dialog is not None:
                self._model_library_dialog.set_download_status("Скачивание уже выполняется.")
            return

        self._download_worker = DownloadModelWorker(
            self.model_library,
            repo_id,
            filename,
            description,
            token=token,
            parent=self,
        )
        self._download_worker.progress.connect(self._set_status)
        self._download_worker.finishedOk.connect(self._on_download_finished)
        self._download_worker.failed.connect(self._on_download_failed)

        # Диалог модальный и закрывает собой статус-бар главного окна —
        # дублируем прогресс прямо в диалог, чтобы пользователь его видел.
        dialog = self._model_library_dialog
        if dialog is not None:
            self._download_worker.progress.connect(dialog.set_download_status)
            self._download_worker.progressPercent.connect(dialog.set_download_progress)
            dialog.set_downloading(True)

        self._set_status(f"Скачивание модели: {filename}")
        self._download_worker.start()

    def _on_download_finished(self, path: str) -> None:
        self._download_worker = None
        self._set_status(f"Модель скачана: {path}")
        dialog = self._model_library_dialog
        if dialog is not None:
            dialog.set_downloading(False)
            dialog.set_download_status(f"Готово! Модель скачана: {Path(path).name}")
            dialog.refresh()
        self._use_local_model(path)

    def _on_download_failed(self, error: str) -> None:
        self._download_worker = None
        dialog = self._model_library_dialog
        if dialog is not None:
            dialog.set_downloading(False)
            dialog.set_download_status(f"Ошибка скачивания: {error}")
        self._show_error("Не удалось скачать модель", error)
        self._set_status("Ошибка скачивания модели.")

    # ----- меню -----

    def _build_menus(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Файл")
        new_chat_action = QAction("Новый чат", self)
        new_chat_action.setShortcut(QKeySequence.New)
        new_chat_action.triggered.connect(self._on_new_chat)
        file_menu.addAction(new_chat_action)

        open_chat_action = QAction("Открыть чат…", self)
        open_chat_action.setShortcut(QKeySequence.Open)
        open_chat_action.triggered.connect(self._on_load_chat)
        file_menu.addAction(open_chat_action)

        save_chat_action = QAction("Сохранить чат…", self)
        save_chat_action.setShortcut(QKeySequence.Save)
        save_chat_action.triggered.connect(self._on_save_chat)
        file_menu.addAction(save_chat_action)

        file_menu.addSeparator()

        library_action = QAction("Библиотека моделей…", self)
        library_action.setShortcuts(
            [QKeySequence("Ctrl+L"), QKeySequence("Meta+L")]
        )
        library_action.triggered.connect(self._on_model_library)
        file_menu.addAction(library_action)

        file_menu.addSeparator()

        remote_action = QAction("Удалённый доступ с телефона…", self)
        remote_action.setShortcuts(
            [QKeySequence("Ctrl+R"), QKeySequence("Meta+R")]
        )
        remote_action.triggered.connect(self._on_remote_access)
        file_menu.addAction(remote_action)

        view_menu = menu_bar.addMenu("Вид")
        self._toggle_sidebar_action = QAction("Показывать боковую панель", self)
        self._toggle_sidebar_action.setCheckable(True)
        self._toggle_sidebar_action.setChecked(True)
        self._toggle_sidebar_action.setShortcuts(
            [QKeySequence("Ctrl+Alt+S"), QKeySequence("Meta+Alt+S")]
        )
        self._toggle_sidebar_action.toggled.connect(self._sidebar_scroll.setVisible)
        view_menu.addAction(self._toggle_sidebar_action)

        help_menu = menu_bar.addMenu("Справка")
        about_action = QAction("О программе NEYROLOC NEW", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    # ----- удалённый доступ -----

    def _remote_pair_code(self) -> str:
        """Постоянный 6-значный код сопряжения (генерируется один раз)."""
        code = self.config.data.get("remote_pair_code")
        if not code:
            import secrets

            code = f"{secrets.randbelow(1_000_000):06d}"
            self.config.data["remote_pair_code"] = code
            self.config.save()
        return str(code)

    def _on_remote_access(self) -> None:
        lan_url = f"http://{local_ip()}:{DEFAULT_PORT}"
        ts_ip = tailscale_ip()
        remote_url = f"http://{ts_ip}:{DEFAULT_PORT}" if ts_ip else None
        dialog = RemoteAccessDialog(
            is_running=lambda: self._remote_server.running,
            start=self._remote_server.start,
            stop=self._remote_server.stop,
            lan_url=lan_url,
            pair_code=self._remote_bridge.pair_code,
            remote_url=remote_url,
            parent=self,
            tunnel=self._tunnel,
        )
        dialog.exec()

    def _on_remote_model_changed(self, model: str) -> None:
        # Модель сменили с телефона — отражаем в сайдбаре без повторного emit.
        self.sidebar.set_models(self._remote_bridge.available_models, model, auto_emit=False)
        backend_id = self.sidebar.current_backend_id
        if backend_id:
            self.config.set_last_model(backend_id, model)
        self._set_status(f"Модель переключена с телефона: {model}")

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "О программе NEYROLOC NEW",
            "<b>NEYROLOC NEW</b><br>"
            "Настольный чат-клиент для локальных и облачных LLM.<br><br>"
            "Backend'ы: Local GGUF (offline, llama.cpp) · OpenAI · Groq.<br>"
            "История чатов и настройки хранятся в <code>~/.neyrolock_5/</code>.",
        )

    def _on_new_chat(self) -> None:
        if self._worker is not None:
            self._on_stop()
            self._set_status(
                "Останавливаю генерацию. Создайте новый чат после завершения остановки."
            )
            return
        self.session = ChatSession(self.config.system_prompt)
        self.chat.clear_messages()
        self._set_status("Новый чат.")

    def _on_save_chat(self) -> None:
        if self._worker is not None:
            self._set_status("Дождитесь завершения генерации перед сохранением чата.")
            return
        if not self.session.messages:
            self._set_status("История пуста — нечего сохранять.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить чат",
            "chat.json",
            "JSON (*.json)",
        )
        if not path:
            return

        target = Path(path)
        try:
            atomic_write_json(target, self.session.to_dict(), mode=0o600)
        except OSError as exc:
            self._show_error("Не удалось сохранить чат", str(exc))
            return
        self._set_status(f"Сохранено: {target}")

    def _on_load_chat(self) -> None:
        if self._worker is not None:
            self._on_stop()
            self._set_status(
                "Останавливаю генерацию. Откройте чат после завершения остановки."
            )
            return
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть чат",
            str(HISTORY_DIR),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            self.session = load_session(Path(path))
        except Exception as exc:
            self._show_error("Не удалось открыть чат", str(exc))
            return

        system_prompt = next(
            (m.content for m in self.session.messages if m.role == "system"),
            self.config.system_prompt,
        )
        self.sidebar.set_system_prompt(system_prompt)
        self.chat.set_messages(self.session.messages)
        self._set_status(f"Открыт чат: {Path(path).name}")

    # ----- сигналы chat -----

    def _backend_ready(self) -> bool:
        if self.backend is None:
            self._show_error("Backend не подключён", "Сначала выберите backend и нажмите «Подключить».")
            return False
        if not self.backend.current_model:
            self._show_error("Модель не выбрана", "Выберите модель в боковой панели.")
            return False
        return True

    def _start_generation(self) -> None:
        """Запустить генерацию по текущему содержимому сессии."""
        if self._worker is not None:
            return
        self.chat.begin_streaming_assistant()
        self.chat.set_busy(True)
        self.sidebar.setEnabled(False)

        self._worker = GenerateWorker(
            backend=self.backend,
            messages=list(self.session.messages),
            temperature=self.config.temperature,
            lock=self._remote_bridge.generation_lock,
        )
        self._worker.chunk.connect(self.chat.append_streaming_chunk)
        self._worker.finishedOk.connect(self._on_generation_finished)
        self._worker.failed.connect(self._on_generation_failed)
        self._set_status("Генерация…")
        self._worker.start()

    def _on_send(self, text: str) -> None:
        if not self._backend_ready():
            return

        self.session.add_user(text)
        self.chat.add_user_message(text)
        self._start_generation()

    def _on_regenerate(self) -> None:
        """«Повторить» под последним ответом: убрать его и сгенерировать заново."""
        if self._worker is not None or not self._backend_ready():
            return
        while self.session.messages and self.session.messages[-1].role == "assistant":
            self.session.messages.pop()
        if not self.session.messages or self.session.messages[-1].role != "user":
            self._show_error("Нечего повторять", "Последним сообщением должен быть вопрос пользователя.")
            return
        self.chat.set_messages(self.session.messages)
        self._start_generation()

    def _on_stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._set_status("Остановка…")

    def _on_generation_finished(self) -> None:
        worker = self.sender()
        if worker is not self._worker:
            return
        text = self.chat.end_streaming()
        if text:
            self.session.add_assistant(text)
        self.chat.set_busy(False)
        self.sidebar.setEnabled(True)
        self._worker = None
        self._set_status("Остановлено." if worker.stop_requested else "Готово.")

    def _on_generation_failed(self, error: str) -> None:
        if self.sender() is not self._worker:
            return
        text = self.chat.end_streaming()
        if text:
            # Пузырь с частичным ответом уже показан — сохраняем его и в
            # сессии, чтобы UI и экспорт истории не расходились.
            self.session.add_assistant(text)
        self.chat.set_busy(False)
        self.sidebar.setEnabled(True)
        self._worker = None
        self._show_error("Ошибка генерации", error)
        self._set_status("Ошибка.")

    # ----- очистка -----

    def _cancel_list_worker(self) -> None:
        # Прервать сам сетевой запрос нечем — отвязываем сигналы и перекладываем
        # поток в _stale_list_workers, чтобы дождаться его в closeEvent.
        if self._list_worker is not None:
            try:
                self._list_worker.finishedOk.disconnect()
                self._list_worker.failed.disconnect()
            except (TypeError, RuntimeError):
                pass
            worker = self._list_worker
            self._stale_list_workers.append(worker)
            worker.finished.connect(lambda w=worker: self._on_stale_list_finished(w))
            self._list_worker = None
            self.sidebar.set_apply_enabled(True)
        # Убираем уже завершившиеся потоки, чтобы список не рос бесконечно.
        self._stale_list_workers = [w for w in self._stale_list_workers if w.isRunning()]

    def _on_stale_list_finished(self, worker: ListModelsWorker) -> None:
        if worker in self._stale_list_workers:
            self._stale_list_workers.remove(worker)
        if worker._backend is not self.backend:
            try:
                worker._backend.close()
            except Exception:
                pass

    def _teardown_backend(self) -> bool:
        if self._worker is not None:
            self._set_status("Сначала остановите текущую генерацию.")
            return False
        if self._prepare_worker is not None and self._prepare_worker.isRunning():
            self._set_status("Дождитесь завершения подготовки модели.")
            return False
        list_workers = [self._list_worker, *self._stale_list_workers]
        if any(
            worker is not None
            and worker.isRunning()
            and worker._backend is self.backend
            for worker in list_workers
        ):
            self._set_status("Дождитесь завершения запроса списка моделей.")
            return False
        if not self._remote_bridge.generation_lock.acquire(timeout=0.2):
            self._set_status("Backend занят запросом с телефона. Повторите после завершения.")
            return False

        try:
            self._cancel_list_worker()
            self._pending_model = None
            if self._prepare_worker is not None:
                try:
                    self._prepare_worker.progress.disconnect()
                    self._prepare_worker.finishedOk.disconnect()
                    self._prepare_worker.failed.disconnect()
                except (TypeError, RuntimeError):
                    pass
                self._prepare_worker = None

            backend = self.backend
            # Сначала убираем backend из HTTP-моста: новый телефонный запрос
            # уже не начнётся. Замок generation_lock исключает гонку с текущим.
            self._remote_bridge.backend = None
            self.backend = None
            if backend is not None:
                try:
                    backend.close()
                except Exception:
                    pass
            self._remote_bridge.backend_name = ""
            self._remote_bridge.available_models = []
            return True
        finally:
            self._remote_bridge.generation_lock.release()

    def _running_qthreads(self) -> list[QThread]:
        """Все дочерние QThread, включая уже отвязанные stale-workers."""
        return [thread for thread in self.findChildren(QThread) if thread.isRunning()]

    def _close_when_idle(self) -> None:
        if self._close_pending and not self._running_qthreads():
            QTimer.singleShot(0, self.close)

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt API
        if not self._close_pending:
            self._close_pending = True
            self._tunnel.stop()  # иначе frpc остался бы висеть фоновым процессом
            self._remote_server.stop()
            if self._worker is not None:
                self._worker.stop()

        running = self._running_qthreads()
        if running:
            for thread in running:
                try:
                    thread.finished.connect(self._close_when_idle)
                except (TypeError, RuntimeError):
                    pass
            self._set_status("Завершаю фоновые операции перед выходом…")
            event.ignore()
            return

        if not self._teardown_backend():
            event.ignore()
            QTimer.singleShot(250, self.close)
            return
        self._close_pending = False
        super().closeEvent(event)

    # ----- утилиты -----

    def _show_error(self, title: str, text: str) -> None:
        QMessageBox.warning(self, title, text)
