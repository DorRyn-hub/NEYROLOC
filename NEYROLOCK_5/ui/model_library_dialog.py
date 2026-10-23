"""Model library dialog: downloaded, recommended and manual HuggingFace GGUF."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFileDialog,
    QScrollArea,
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
from ui.workspace import PageHeader, action
from ui.icons import icon

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


class ModelLibraryDialog(QDialog):
    useModelRequested = Signal(str)
    downloadRequested = Signal(str, str, str, str)  # repo_id, filename, description, token

    def __init__(self, library: ModelLibrary, parent: Optional[QWidget] = None, *, embedded: bool = False) -> None:
        super().__init__(parent)
        self.setObjectName("modelLibraryDialog")
        self.setWindowTitle("Библиотека моделей")
        self.resize(920, 600)
        self._embedded = embedded
        if embedded:
            self.setWindowFlags(Qt.Widget)
        else:
            self.setMinimumSize(760, 480)
        self._downloading = False
        self._card_actions: list[QPushButton] = []
        self._library = library
        self._downloaded: list[DownloadedModel] = []
        self._recommended: list[RecommendedModel] = []
        self._filename_display_to_raw: dict[str, str] = {}

        root = QVBoxLayout(self)
        margin = 0 if embedded else 18
        root.setContentsMargins(margin, margin, margin, margin)
        root.setSpacing(12)

        header = PageHeader("Библиотека моделей", "Выберите модель для локальной работы или скачайте её с Hugging Face")
        self._add_file_btn = action("Добавить GGUF", "plus")
        self._add_file_btn.clicked.connect(self._pick_local_file)
        header.row.addWidget(self._add_file_btn)
        root.addWidget(header)

        tabs = QTabWidget()
        tabs.setObjectName("modelLibraryTabs")
        tabs.addTab(self._build_downloaded_tab(), "На этом компьютере")
        tabs.addTab(self._build_recommended_tab(), "Рекомендуемые")
        tabs.addTab(self._build_search_tab(), "Поиск Hugging Face")
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
        status_row.addWidget(self._download_spinner)
        self._download_status_label = QLabel("")
        self._download_status_label.setObjectName("downloadStatusText")
        self._download_status_label.setWordWrap(True)
        self._download_status_label.setTextFormat(Qt.PlainText)
        status_row.addWidget(self._download_status_label, 1)
        panel_layout.addLayout(status_row)

        self._download_progress = QProgressBar()
        self._download_progress.setObjectName("downloadProgress")
        self._download_progress.setRange(0, 100)
        self._download_progress.setValue(0)
        self._download_progress.setTextVisible(True)
        self._download_progress.setFormat("%p%")
        self._download_progress.setFixedHeight(16)
        panel_layout.addWidget(self._download_progress)

        root.addWidget(self._download_panel)

        self._spinner_frame = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(90)
        self._spinner_timer.timeout.connect(self._advance_spinner)

        if not embedded:
            buttons = QDialogButtonBox(QDialogButtonBox.Close)
            buttons.button(QDialogButtonBox.Close).setText("Закрыть")
            buttons.rejected.connect(self.reject)
            root.addWidget(buttons)
        self.refresh()

    def _card_list(self) -> tuple[QScrollArea, QVBoxLayout]:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(10)
        scroll.setWidget(content)
        return scroll, layout

    def _build_downloaded_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 18, 0, 0)
        row = QHBoxLayout()
        self._filter_edit = QLineEdit()
        self._filter_edit.setObjectName("searchInput")
        self._filter_edit.setPlaceholderText("Поиск на этом компьютере")
        self._filter_edit.addAction(icon("search"), QLineEdit.LeadingPosition)
        self._filter_edit.textChanged.connect(self._filter_downloaded)
        row.addWidget(self._filter_edit, 1)
        refresh_btn = action("Обновить", "refresh")
        refresh_btn.clicked.connect(self.refresh)
        row.addWidget(refresh_btn)
        layout.addLayout(row)
        scroll, self._downloaded_cards = self._card_list()
        layout.addWidget(scroll, 1)
        return tab

    def _build_recommended_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 18, 0, 0)
        hint = QLabel("Выберите размер под свой компьютер. Скачивание начнётся после нажатия кнопки.")
        hint.setObjectName("pageSubtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        scroll, self._recommended_cards = self._card_list()
        layout.addWidget(scroll, 1)
        return tab

    def _pick_local_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Выберите локальную модель", "", "GGUF (*.gguf)")
        if path:
            self._use_model(path)

    def _use_model(self, path: str) -> None:
        self.useModelRequested.emit(path)
        if not self._embedded:
            self.accept()

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
        self._query_edit.returnPressed.connect(self._search_hf_models)
        self._query_btn = QPushButton("Искать модели")
        self._query_btn.setObjectName("primary")
        self._query_btn.clicked.connect(self._search_hf_models)
        query_row.addWidget(self._query_edit, 1)
        query_row.addWidget(self._query_btn)
        layout.addLayout(query_row)

        self._models_table = QTableWidget(0, 3)
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
        form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._repo_edit = QLineEdit()
        self._repo_edit.setPlaceholderText("выберите модель выше или введите repo вручную")
        self._repo_edit.setMinimumWidth(280)
        self._repo_edit.returnPressed.connect(self._search_repo_files)
        self._hf_token_edit = QLineEdit()
        self._hf_token_edit.setEchoMode(QLineEdit.Password)
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
        self._filename_combo.setPlaceholderText("файл появится после выбора модели или поиска")
        self._filename_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._filename_combo.setMinimumWidth(280)

        form.addRow("Repo ID", repo_row_widget)
        form.addRow("HF token", self._hf_token_edit)
        form.addRow("Файл (.gguf)", self._filename_combo)
        layout.addWidget(form_widget)

        row = QHBoxLayout()
        hint = QLabel("После скачивания модель появится на вкладке «На этом компьютере».")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        self._search_download_btn = QPushButton("Скачать")
        self._search_download_btn.setObjectName("primary")
        self._search_download_btn.clicked.connect(self._download_manual)
        row.addWidget(hint, 1)
        row.addWidget(self._search_download_btn)
        layout.addLayout(row)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(tab)
        return scroll

    def _search_hf_models(self) -> None:
        query = self._query_edit.text().strip()
        if not query:
            self._search_status.setText("Введите, что ищете, например «llama 8b».")
            return

        self._query_btn.setEnabled(False)
        self._search_status.setText("Ищу модели на HuggingFace…")
        self._models_table.setRowCount(0)
        self.setCursor(QCursor(Qt.WaitCursor))
        try:
            from huggingface_hub import HfApi

            token = self._hf_token_edit.text().strip() or None
            api = HfApi(token=token)
            results = list(
                api.list_models(search=query, filter="gguf", sort="downloads", limit=30)
            )
            self._models_table.setRowCount(len(results))
            for row, model in enumerate(results):
                downloads = getattr(model, "downloads", None) or 0
                likes = getattr(model, "likes", None) or 0
                for col, value in enumerate([model.id, f"{downloads:,}", f"{likes:,}"]):
                    item = QTableWidgetItem(value)
                    item.setToolTip(model.id)
                    self._models_table.setItem(row, col, item)
            if results:
                self._search_status.setText(f"Найдено моделей: {len(results)}. Выберите одну ниже.")
            else:
                self._search_status.setText("Ничего не нашлось. Попробуйте другой запрос.")
        except ImportError:
            self._search_status.setText(
                "Не установлен huggingface-hub. Выполните: pip install huggingface-hub"
            )
        except Exception as exc:  # noqa: BLE001 — показываем ошибку пользователю как есть
            self._search_status.setText(f"Ошибка поиска: {exc}")
        finally:
            self.unsetCursor()
            self._query_btn.setEnabled(True)

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

        self._search_btn.setEnabled(False)
        self._search_status.setText("Ищу .gguf файлы…")
        self._filename_combo.clear()
        self._filename_display_to_raw.clear()
        self.setCursor(QCursor(Qt.WaitCursor))
        try:
            from huggingface_hub import HfApi
            from huggingface_hub.utils import GatedRepoError, RepositoryNotFoundError

            token = self._hf_token_edit.text().strip() or None
            api = HfApi(token=token)
            try:
                info = api.model_info(repo, files_metadata=True)
            except RepositoryNotFoundError:
                self._search_status.setText(f"Репозиторий не найден: {repo}")
                return
            except GatedRepoError:
                self._search_status.setText(
                    "Доступ к репозиторию требует токен (gated). Укажите HF token и повторите."
                )
                return

            files: list[tuple[str, int]] = []
            skipped_split = 0
            for sibling in info.siblings or []:
                name = sibling.rfilename
                if not name.endswith(".gguf"):
                    continue
                if _SPLIT_FILE_RE.search(name):
                    skipped_split += 1
                    continue
                files.append((name, sibling.size or 0))

            files.sort(key=lambda item: (_quant_rank(item[0]), item[1]))

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
        except ImportError:
            self._search_status.setText(
                "Не установлен huggingface-hub. Выполните: pip install huggingface-hub"
            )
        except Exception as exc:  # noqa: BLE001 — показываем ошибку пользователю как есть
            self._search_status.setText(f"Ошибка поиска: {exc}")
        finally:
            self.unsetCursor()
            self._search_btn.setEnabled(True)

    def refresh(self) -> None:
        self._card_actions = []
        self._downloaded = self._library.list_downloaded()
        self._recommended = self._library.recommended()
        self._fill_downloaded()
        self._fill_recommended()

    @staticmethod
    def _clear_cards(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def _model_card(self, model, recommended: bool) -> QFrame:
        card = QFrame()
        card.setObjectName("modelCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        row = QHBoxLayout(card)
        row.setContentsMargins(20, 18, 20, 18)
        row.setSpacing(16)
        glyph = QLabel()
        glyph.setPixmap(icon("cpu", "#8cb9ff", 24).pixmap(24, 24))
        glyph.setFixedSize(40, 40)
        glyph.setObjectName("modelGlyph")
        row.addWidget(glyph, 0, Qt.AlignTop)
        info = QVBoxLayout()
        title = QLabel(model.filename.removesuffix(".gguf"))
        title.setObjectName("modelCardTitle")
        title.setTextFormat(Qt.PlainText)
        title.setWordWrap(True)
        info.addWidget(title)
        subtitle = QLabel(f"{model.size_label} · {model.repo_id or 'Локальный файл'}")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setTextFormat(Qt.PlainText)
        subtitle.setWordWrap(True)
        info.addWidget(subtitle)
        if model.description:
            description = QLabel(model.description)
            description.setTextFormat(Qt.PlainText)
            description.setObjectName("modelCaption")
            description.setWordWrap(True)
            info.addWidget(description)
        row.addLayout(info, 1)
        button = action("Скачать" if recommended else "Использовать", "download" if recommended else "chat", primary=not recommended)
        button.setEnabled(not self._downloading)
        self._card_actions.append(button)
        if recommended:
            button.clicked.connect(lambda checked=False, m=model: self.downloadRequested.emit(m.repo_id, m.filename, m.description, ""))
        else:
            card.setToolTip(str(model.path))
            button.clicked.connect(lambda checked=False, m=model: self._use_model(str(m.path)))
        row.addWidget(button, 0, Qt.AlignVCenter)
        return card

    def _fill_downloaded(self) -> None:
        self._clear_cards(self._downloaded_cards)
        self._downloaded_card_rows = []
        for model in self._downloaded:
            card = self._model_card(model, False)
            self._downloaded_cards.addWidget(card)
            self._downloaded_card_rows.append((card, f"{model.filename} {model.repo_id}".lower()))
        self._empty_library = QLabel("Здесь появятся ваши модели\n\nДобавьте GGUF-файл или выберите модель в рекомендуемых.")
        self._empty_library.setObjectName("emptySubtitle")
        self._empty_library.setWordWrap(True)
        self._empty_library.setAlignment(Qt.AlignCenter)
        self._empty_library.setMinimumHeight(180)
        self._downloaded_cards.addWidget(self._empty_library)
        self._downloaded_cards.addStretch(1)
        self._filter_downloaded(self._filter_edit.text())

    def _filter_downloaded(self, query: str) -> None:
        found = 0
        for card, search_text in self._downloaded_card_rows:
            visible = query.strip().lower() in search_text
            card.setVisible(visible)
            found += visible
        self._empty_library.setVisible(not found)
        self._empty_library.setText("Ничего не найдено. Попробуйте другое название." if self._downloaded and not found else "Здесь появятся ваши модели\n\nДобавьте GGUF-файл или выберите модель в рекомендуемых.")

    def _fill_recommended(self) -> None:
        self._clear_cards(self._recommended_cards)
        category = None
        for model in self._recommended:
            if model.category != category:
                category = model.category
                label = QLabel(category.upper())
                label.setObjectName("sidebarSection")
                self._recommended_cards.addWidget(label)
            self._recommended_cards.addWidget(self._model_card(model, True))
        self._recommended_cards.addStretch(1)

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
        for button in self._card_actions:
            button.setEnabled(not active)
        self._add_file_btn.setEnabled(not active)
        self._search_download_btn.setEnabled(not active)
        self._download_panel.setVisible(active or bool(self._download_status_label.text()))
        self._download_spinner.setVisible(active)
        self._download_progress.setVisible(active)
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
