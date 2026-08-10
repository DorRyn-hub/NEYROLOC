"""Model library dialog: downloaded, recommended and manual HuggingFace GGUF."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.model_library import DownloadedModel, ModelLibrary, RecommendedModel

# GGUF-файлы, разбитые на части ("...-00001-of-00002.gguf") нельзя скачать
# одним файлом через hf_hub_download — приложение пока не умеет их собирать,
# поэтому такие варианты не показываем вовсе, чтобы не подсовывать
# нерабочий вариант обычному пользователю.
_SPLIT_FILE_RE = re.compile(r"-\d{5}-of-\d{5}\.gguf$", re.IGNORECASE)

# Кадры вращающегося индикатора загрузки (без внешних ассетов/gif).
_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Порядок предпочтения квантований: сначала — лучший баланс размера/качества
# для большинства пользователей (Q4_K_M), в конце — большие/точные (Q8, FP16…).
_QUANT_PRIORITY = [
    "q4_k_m", "q4_k_s", "q5_k_m", "q5_k_s", "q4_0", "q5_0",
    "q6_k", "q3_k_m", "q3_k_s", "iq4", "q8_0", "q2_k",
]


def _quant_rank(filename: str) -> int:
    lower = filename.lower()
    for i, tag in enumerate(_QUANT_PRIORITY):
        if tag in lower:
            return i
    return len(_QUANT_PRIORITY)  # неизвестное/неквантованное (fp16, bf16, f32…)


def _format_size(num_bytes: int) -> str:
    if num_bytes >= 1024**3:
        return f"{num_bytes / 1024**3:.1f} GB"
    if num_bytes >= 1024**2:
        return f"{num_bytes / 1024**2:.0f} MB"
    if num_bytes > 0:
        return f"{num_bytes / 1024:.0f} KB"
    return ""


class _HfTaskSignals(QObject):
    """Queued delivery from a HuggingFace request running off the GUI thread."""

    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()


class _HfTask(QRunnable):
    """Small background job for the two network-bound library searches."""

    def __init__(self, operation: str, value: str, token: str = "") -> None:
        super().__init__()
        self.operation = operation
        self.value = value
        self.token = token or None
        self.signals = _HfTaskSignals()

    @Slot()
    def run(self) -> None:
        try:
            from huggingface_hub import HfApi

            api = HfApi(token=self.token)
            if self.operation == "models":
                results = list(
                    api.list_models(
                        search=self.value,
                        filter="gguf",
                        sort="downloads",
                        limit=30,
                    )
                )
                payload = [
                    (
                        model.id,
                        getattr(model, "downloads", None) or 0,
                        getattr(model, "likes", None) or 0,
                    )
                    for model in results
                ]
            else:
                from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError

                try:
                    info = api.model_info(self.value, files_metadata=True)
                # GatedRepoError наследуется от RepositoryNotFoundError, поэтому
                # более конкретный случай обязан проверяться первым.
                except GatedRepoError:
                    self.signals.failed.emit(
                        "Доступ к репозиторию требует токен (gated). "
                        "Укажите HF token и повторите."
                    )
                    return
                except RepositoryNotFoundError:
                    self.signals.failed.emit(f"Репозиторий не найден: {self.value}")
                    return

                files: list[tuple[str, int]] = []
                skipped_split = 0
                for sibling in info.siblings or []:
                    name = sibling.rfilename
                    if not name.lower().endswith(".gguf"):
                        continue
                    if _SPLIT_FILE_RE.search(name):
                        skipped_split += 1
                        continue
                    files.append((name, sibling.size or 0))
                files.sort(key=lambda item: (_quant_rank(item[0]), item[1]))
                payload = (files, skipped_split)
            self.signals.succeeded.emit(payload)
        except ImportError:
            self.signals.failed.emit(
                "Не установлен huggingface-hub. Выполните: pip install huggingface-hub"
            )
        except Exception as exc:  # noqa: BLE001 — ошибка показывается пользователю
            self.signals.failed.emit(f"Ошибка поиска: {exc}")
        finally:
            self.signals.finished.emit()


class ModelLibraryDialog(QDialog):
    useModelRequested = Signal(str)
    downloadRequested = Signal(str, str, str, str)  # repo_id, filename, description, token

    def __init__(self, library: ModelLibrary, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("modelLibraryDialog")
        self.setWindowTitle("Библиотека моделей")
        self.resize(920, 600)
        self.setMinimumSize(680, 440)
        self._library = library
        self._downloaded: list[DownloadedModel] = []
        self._recommended: list[RecommendedModel] = []
        self._filename_display_to_raw: dict[str, str] = {}
        self._search_task: _HfTask | None = None
        self._downloading = False

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("Локальные и HuggingFace GGUF модели")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        tabs = QTabWidget()
        tabs.setObjectName("modelLibraryTabs")
        tabs.setAccessibleName("Разделы библиотеки моделей")
        tabs.addTab(self._build_downloaded_tab(), "Скачанные")
        tabs.addTab(self._build_recommended_tab(), "Рекомендованные")
        tabs.addTab(self._build_search_tab(), "Поиск HuggingFace")
        root.addWidget(tabs, 1)

        # Панель скачивания — общая для всех вкладок и всегда на виду, даже
        # если модальный диалог закрывает собой статус-бар главного окна.
        # Крутящийся значок + текст + процентная шкала — видно, что модель
        # реально качается, а не "зависло".
        self._download_panel = QFrame()
        self._download_panel.setObjectName("downloadPanel")
        self._download_panel.setVisible(False)
        panel_layout = QVBoxLayout(self._download_panel)
        panel_layout.setContentsMargins(12, 10, 12, 10)
        panel_layout.setSpacing(6)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self._download_spinner = QLabel(_SPINNER_FRAMES[0])
        self._download_spinner.setObjectName("downloadSpinner")
        self._download_spinner.setFixedWidth(16)
        self._download_spinner.setVisible(False)
        status_row.addWidget(self._download_spinner)
        self._download_status_label = QLabel("")
        self._download_status_label.setObjectName("downloadStatusText")
        self._download_status_label.setAccessibleName("Состояние скачивания")
        self._download_status_label.setWordWrap(True)
        status_row.addWidget(self._download_status_label, 1)
        panel_layout.addLayout(status_row)

        self._download_progress = QProgressBar()
        self._download_progress.setObjectName("downloadProgress")
        self._download_progress.setRange(0, 100)
        self._download_progress.setValue(0)
        self._download_progress.setTextVisible(True)
        self._download_progress.setFormat("%p%")
        self._download_progress.setFixedHeight(16)
        self._download_progress.setAccessibleName("Прогресс скачивания модели")
        self._download_progress.setVisible(False)
        panel_layout.addWidget(self._download_progress)

        root.addWidget(self._download_panel)

        self._spinner_frame = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(90)
        self._spinner_timer.timeout.connect(self._advance_spinner)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_btn = buttons.button(QDialogButtonBox.Close)
        if close_btn is not None:
            close_btn.setText("Закрыть")
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.refresh()

    def _build_downloaded_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)

        self._downloaded_table = QTableWidget(0, 4)
        self._downloaded_table.setAccessibleName("Скачанные модели")
        self._downloaded_table.setHorizontalHeaderLabels(
            ["Модель", "Размер", "Источник", "Путь"]
        )
        self._downloaded_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._downloaded_table.setSelectionMode(QTableWidget.SingleSelection)
        self._downloaded_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._downloaded_table.setShowGrid(False)
        self._downloaded_table.doubleClicked.connect(self._use_selected_downloaded)
        downloaded_header = self._downloaded_table.horizontalHeader()
        downloaded_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        downloaded_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        downloaded_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        downloaded_header.setSectionResizeMode(3, QHeaderView.Stretch)
        self._downloaded_table.verticalHeader().setVisible(False)
        self._downloaded_table.setAlternatingRowColors(True)
        self._downloaded_table.itemSelectionChanged.connect(self._sync_action_states)
        layout.addWidget(self._downloaded_table, 1)

        row = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh)
        self._downloaded_use_btn = QPushButton("Использовать")
        self._downloaded_use_btn.setObjectName("primary")
        self._downloaded_use_btn.setToolTip("Использовать выбранную локальную модель")
        self._downloaded_use_btn.clicked.connect(self._use_selected_downloaded)
        row.addWidget(refresh_btn)
        row.addStretch(1)
        row.addWidget(self._downloaded_use_btn)
        layout.addLayout(row)

        return tab

    def _build_recommended_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)

        self._recommended_table = QTableWidget(0, 5)
        self._recommended_table.setAccessibleName("Рекомендованные модели")
        self._recommended_table.setHorizontalHeaderLabels(
            ["Категория", "Файл", "Размер", "Repo", "Описание"]
        )
        self._recommended_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._recommended_table.setSelectionMode(QTableWidget.SingleSelection)
        self._recommended_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._recommended_table.setShowGrid(False)
        self._recommended_table.doubleClicked.connect(self._download_selected_recommended)
        recommended_header = self._recommended_table.horizontalHeader()
        recommended_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        recommended_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        recommended_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        recommended_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        recommended_header.setSectionResizeMode(4, QHeaderView.Stretch)
        self._recommended_table.verticalHeader().setVisible(False)
        self._recommended_table.setAlternatingRowColors(True)
        self._recommended_table.itemSelectionChanged.connect(self._sync_action_states)
        layout.addWidget(self._recommended_table, 1)

        row = QHBoxLayout()
        hint = QLabel("Скачивание может занять время: модели весят от сотен MB до нескольких GB.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        self._recommended_download_btn = QPushButton("Скачать выбранную")
        self._recommended_download_btn.setObjectName("primary")
        self._recommended_download_btn.setToolTip("Скачать выбранную рекомендацию")
        self._recommended_download_btn.clicked.connect(self._download_selected_recommended)
        row.addWidget(hint, 1)
        row.addWidget(self._recommended_download_btn)
        layout.addLayout(row)

        return tab

    def _build_search_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(10)

        intro = QLabel(
            "Не знаете точный репозиторий? Введите, что ищете (например «llama 8b» "
            "или «qwen coder») — ниже появится список подходящих моделей с HuggingFace."
        )
        intro.setObjectName("hint")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        query_row = QHBoxLayout()
        query_row.setSpacing(6)
        self._query_edit = QLineEdit()
        self._query_edit.setPlaceholderText("например: llama 8b instruct")
        self._query_edit.setAccessibleName("Поисковый запрос HuggingFace")
        self._query_edit.returnPressed.connect(self._search_hf_models)
        self._query_btn = QPushButton("Искать модели")
        self._query_btn.setObjectName("primary")
        self._query_btn.clicked.connect(self._search_hf_models)
        query_row.addWidget(self._query_edit, 1)
        query_row.addWidget(self._query_btn)
        layout.addLayout(query_row)

        self._models_table = QTableWidget(0, 3)
        self._models_table.setAccessibleName("Результаты поиска HuggingFace")
        self._models_table.setHorizontalHeaderLabels(["Модель (repo)", "Скачиваний", "Лайков"])
        self._models_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._models_table.setSelectionMode(QTableWidget.SingleSelection)
        self._models_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._models_table.setShowGrid(False)
        self._models_table.doubleClicked.connect(self._pick_searched_model)
        models_header = self._models_table.horizontalHeader()
        models_header.setSectionResizeMode(0, QHeaderView.Stretch)
        models_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        models_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._models_table.verticalHeader().setVisible(False)
        self._models_table.setAlternatingRowColors(True)
        self._models_table.setMaximumHeight(180)
        layout.addWidget(self._models_table)

        self._search_status = QLabel("")
        self._search_status.setObjectName("hint")
        self._search_status.setWordWrap(True)
        layout.addWidget(self._search_status)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setContentsMargins(0, 4, 0, 0)
        form.setSpacing(10)
        # Поля должны занимать всю доступную ширину, иначе Repo ID сжимается
        # в узкую полоску и текст в нём наезжает.
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._repo_edit = QLineEdit()
        self._repo_edit.setPlaceholderText("выберите модель выше или введите repo вручную")
        self._repo_edit.setAccessibleName("Repo ID")
        self._repo_edit.setMinimumWidth(280)
        self._repo_edit.returnPressed.connect(self._search_repo_files)
        self._hf_token_edit = QLineEdit()
        self._hf_token_edit.setEchoMode(QLineEdit.Password)
        self._hf_token_edit.setAccessibleName("HF token")
        self._hf_token_edit.setPlaceholderText("нужен только для приватных/gated репо")

        repo_row = QHBoxLayout()
        repo_row.setContentsMargins(0, 0, 0, 0)
        repo_row.setSpacing(6)
        repo_row.addWidget(self._repo_edit, 1)
        self._search_btn = QPushButton("Искать файлы")
        self._search_btn.clicked.connect(self._search_repo_files)
        repo_row.addWidget(self._search_btn, 0)
        repo_row_widget = QWidget()
        repo_row_widget.setLayout(repo_row)

        self._filename_combo = QComboBox()
        self._filename_combo.setEditable(True)
        self._filename_combo.setAccessibleName("GGUF-файл")
        self._filename_combo.setPlaceholderText("файл появится после выбора модели или поиска")
        self._filename_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._filename_combo.setMinimumWidth(280)

        form.addRow("Repo ID", repo_row_widget)
        form.addRow("HF token", self._hf_token_edit)
        form.addRow("Файл (.gguf)", self._filename_combo)
        layout.addWidget(form_widget)

        row = QHBoxLayout()
        hint = QLabel("После скачивания модель появится на вкладке «Скачанные».")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        self._search_download_btn = QPushButton("Скачать")
        self._search_download_btn.setObjectName("primary")
        self._search_download_btn.clicked.connect(self._download_manual)
        self._repo_edit.textChanged.connect(self._sync_action_states)
        self._filename_combo.currentTextChanged.connect(self._sync_action_states)
        row.addWidget(hint, 1)
        row.addWidget(self._search_download_btn)
        layout.addLayout(row)

        self._sync_action_states()

        return tab

    def _search_hf_models(self) -> None:
        query = self._query_edit.text().strip()
        if not query:
            self._search_status.setText("Введите, что ищете, например «llama 8b».")
            return

        if self._search_task is not None:
            self._search_status.setText("Дождитесь завершения текущего поиска.")
            return

        self._search_status.setText("Ищу модели на HuggingFace…")
        self._models_table.setRowCount(0)
        task = _HfTask("models", query, self._hf_token_edit.text().strip())
        self._start_search_task(task, self._on_hf_models_found)

    def _on_hf_models_found(self, results: object) -> None:
        rows = list(results) if isinstance(results, list) else []
        self._models_table.setRowCount(len(rows))
        for row, model in enumerate(rows):
            model_id, downloads, likes = model
            for col, value in enumerate([model_id, f"{downloads:,}", f"{likes:,}"]):
                item = QTableWidgetItem(value)
                item.setToolTip(model_id)
                self._models_table.setItem(row, col, item)
        if rows:
            self._models_table.selectRow(0)
            self._search_status.setText(
                f"Найдено моделей: {len(rows)}. Выберите одну ниже."
            )
        else:
            self._search_status.setText("Ничего не нашлось. Попробуйте другой запрос.")

    def _pick_searched_model(self) -> None:
        rows = self._models_table.selectionModel().selectedRows()
        if not rows:
            return
        item = self._models_table.item(rows[0].row(), 0)
        if item is None:
            return
        self._repo_edit.setText(item.text())
        self._search_repo_files()

    def _search_repo_files(self) -> None:
        repo = self._repo_edit.text().strip()
        if not repo:
            self._search_status.setText("Укажите Repo ID.")
            return

        if self._search_task is not None:
            self._search_status.setText("Дождитесь завершения текущего поиска.")
            return

        self._search_status.setText("Ищу .gguf файлы…")
        self._filename_combo.clear()
        self._filename_display_to_raw.clear()
        task = _HfTask("files", repo, self._hf_token_edit.text().strip())
        self._start_search_task(task, self._on_repo_files_found)

    def _on_repo_files_found(self, result: object) -> None:
        if not isinstance(result, tuple) or len(result) != 2:
            self._search_status.setText("Не удалось разобрать ответ HuggingFace.")
            return
        files, skipped_split = result
        for name, size in files:
            size_label = _format_size(size)
            display = f"{name}   —   {size_label}" if size_label else name
            self._filename_combo.addItem(display)
            self._filename_display_to_raw[display] = name

        if files:
            self._filename_combo.setCurrentIndex(0)
            note = f"Найдено файлов: {len(files)}."
            if skipped_split:
                note += f" ({skipped_split} многочастевых пропущено — их пока нельзя скачать.)"
            note += " Уже выбран рекомендуемый вариант — можно сразу нажать «Скачать»."
            self._search_status.setText(note)
        elif skipped_split:
            self._search_status.setText(
                "В этом репозитории только многочастевые GGUF-файлы — "
                "приложение пока не умеет их скачивать одним файлом."
            )
        else:
            self._search_status.setText("В этом репозитории нет файлов .gguf.")
        self._sync_action_states()

    def _start_search_task(self, task: _HfTask, success_slot) -> None:
        self._search_task = task
        self._query_btn.setEnabled(False)
        self._search_btn.setEnabled(False)
        self.setCursor(QCursor(Qt.WaitCursor))
        task.signals.succeeded.connect(success_slot)
        task.signals.failed.connect(self._on_search_failed)
        task.signals.finished.connect(lambda: self._finish_search_task(task))
        QThreadPool.globalInstance().start(task)

    def _on_search_failed(self, message: str) -> None:
        self._search_status.setText(message)

    def _finish_search_task(self, task: _HfTask) -> None:
        if self._search_task is not task:
            return
        self._search_task = None
        self.unsetCursor()
        self._query_btn.setEnabled(True)
        self._search_btn.setEnabled(True)

    def refresh(self) -> None:
        self._downloaded = self._library.list_downloaded()
        self._recommended = self._library.recommended()
        self._fill_downloaded()
        self._fill_recommended()

    def _fill_downloaded(self) -> None:
        self._downloaded_table.setRowCount(len(self._downloaded))
        for row, model in enumerate(self._downloaded):
            values = [
                model.filename,
                model.size_label,
                model.repo_id,
                str(model.path),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self._downloaded_table.setItem(row, col, item)
        self._downloaded_table.resizeColumnsToContents()
        if self._downloaded:
            self._downloaded_table.selectRow(0)
        self._sync_action_states()

    def _fill_recommended(self) -> None:
        self._recommended_table.setRowCount(len(self._recommended))
        for row, model in enumerate(self._recommended):
            values = [
                model.category,
                model.filename,
                model.size_label,
                model.repo_id,
                model.description,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self._recommended_table.setItem(row, col, item)
        self._recommended_table.resizeColumnsToContents()
        if self._recommended:
            self._recommended_table.selectRow(0)
        self._sync_action_states()

    def _sync_action_states(self) -> None:
        """Keep primary actions truthful instead of silently doing nothing."""
        if hasattr(self, "_downloaded_use_btn"):
            self._downloaded_use_btn.setEnabled(
                not self._downloading and self._selected_downloaded() is not None
            )
        if hasattr(self, "_recommended_download_btn"):
            self._recommended_download_btn.setEnabled(
                not self._downloading and self._selected_recommended() is not None
            )
        if hasattr(self, "_search_download_btn"):
            has_manual_target = bool(
                self._repo_edit.text().strip() and self._filename_combo.currentText().strip()
            )
            self._search_download_btn.setEnabled(
                not self._downloading and has_manual_target
            )

    def _selected_downloaded(self) -> DownloadedModel | None:
        rows = self._downloaded_table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        if row < 0 or row >= len(self._downloaded):
            return None
        return self._downloaded[row]

    def _selected_recommended(self) -> RecommendedModel | None:
        rows = self._recommended_table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        if row < 0 or row >= len(self._recommended):
            return None
        return self._recommended[row]

    def _use_selected_downloaded(self) -> None:
        model = self._selected_downloaded()
        if model is None:
            return
        self.useModelRequested.emit(str(Path(model.path)))
        self.accept()

    def _download_selected_recommended(self) -> None:
        model = self._selected_recommended()
        if model is None:
            self.set_download_status("Сначала выберите модель в таблице выше.")
            return
        self.downloadRequested.emit(model.repo_id, model.filename, model.description, "")

    def _download_manual(self) -> None:
        repo = self._repo_edit.text().strip()
        if not repo:
            self.set_download_status(
                "Сначала укажите репозиторий — найдите модель через поиск выше или введите вручную."
            )
            return
        display = self._filename_combo.currentText().strip()
        if not display:
            self.set_download_status("Выберите файл: нажмите «Искать файлы», затем выберите вариант.")
            return
        filename = self._filename_display_to_raw.get(display, display)
        token = self._hf_token_edit.text().strip()
        self.downloadRequested.emit(repo, filename, "", token)

    # ----- статус скачивания (вызывается из MainWindow) -----

    def set_download_status(self, text: str) -> None:
        self._download_status_label.setText(text)
        self._download_panel.setVisible(bool(text) or self._downloading)

    def set_download_progress(self, percent: int, done: int, total: int) -> None:
        self._download_progress.setValue(max(0, min(100, percent)))
        if total:
            self._download_status_label.setText(
                f"Скачивание: {_format_size(done)} из {_format_size(total)} ({percent}%)"
            )

    def set_downloading(self, active: bool) -> None:
        self._downloading = active
        if active:
            self._download_status_label.setText("Подготовка к скачиванию…")
        self._download_spinner.setVisible(active)
        self._download_progress.setVisible(active)
        self._download_panel.setVisible(active or bool(self._download_status_label.text()))
        self._sync_action_states()
        if active:
            self._download_progress.setValue(0)
            self._spinner_frame = 0
            self._download_spinner.setText(_SPINNER_FRAMES[0])
            self._spinner_timer.start()
        else:
            self._spinner_timer.stop()

    def _advance_spinner(self) -> None:
        self._spinner_frame = (self._spinner_frame + 1) % len(_SPINNER_FRAMES)
        self._download_spinner.setText(_SPINNER_FRAMES[self._spinner_frame])
