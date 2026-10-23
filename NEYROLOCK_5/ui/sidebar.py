"""Compact navigation and configuration sidebar."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QRect, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from backends import ALL_BACKENDS, Backend
from ui.icons import icon


class BackendButton(QPushButton):
    """A small two-line backend item with a painted availability indicator."""

    def __init__(
        self,
        display_name: str,
        description: str,
        available: bool,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._display_name = display_name
        self._description = description
        self._available = available
        self.setObjectName("backendItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setToolTip(description)

    def set_available(self, available: bool) -> None:
        self._available = available
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 — Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        if self.isChecked():
            background = QColor("#34455f")
            border = QColor("#536b8b")
        elif self.underMouse():
            background = QColor("#3d3d3b")
            border = QColor("#555551")
        else:
            background = QColor("#30302f")
            border = QColor("#414140")

        painter.setBrush(background)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(rect, 9, 9)

        dot_color = QColor("#63c796" if self._available else "#858581")
        painter.setPen(Qt.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(QRect(14, 19, 8, 8))

        painter.setPen(QColor("#f3f2f0"))
        painter.drawText(QRect(34, 7, self.width() - 46, 18), Qt.AlignVCenter, self._display_name)

        status = "доступен" if self._available else "не установлено"
        painter.setPen(QColor("#b4b3b0" if self._available else "#858581"))
        painter.drawText(QRect(34, 25, self.width() - 46, 16), Qt.AlignVCenter, status)


class Sidebar(QWidget):
    """Backend selection, model controls and chat actions."""

    backendActivated = Signal(str)
    applyClicked = Signal()
    modelChanged = Signal(str)
    temperatureChanged = Signal(float)
    systemPromptChanged = Signal(str)
    modelLibraryClicked = Signal()
    newChatClicked = Signal()
    saveChatClicked = Signal()
    loadChatClicked = Signal()

    settingsRequested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("parameterPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumWidth(246)
        self.setMaximumWidth(300)
        self._backend_buttons: dict[str, BackendButton] = {}
        self._config_inputs: dict[str, QLineEdit] = {}
        self._current_backend_id: str | None = None
        self._locked = False
        self._apply_requested_enabled = False

        # Connection controls live on the settings page; this widget is the
        # conversation inspector. There is only one instance of each control.
        self.connection_page = QWidget()
        self.connection_page.setObjectName("settingsPage")
        connection = QVBoxLayout(self.connection_page)
        connection.setContentsMargins(24, 24, 24, 24)
        connection.setSpacing(18)
        title = QLabel("Подключение и модель")
        title.setObjectName("pageTitle")
        connection.addWidget(title)
        hint = QLabel("Выберите источник, укажите параметры и подключите модель.")
        hint.setObjectName("pageSubtitle")
        hint.setWordWrap(True)
        connection.addWidget(hint)
        connection.addWidget(self._section("ИСТОЧНИК"))
        providers = QHBoxLayout()
        providers.setSpacing(10)
        self._backend_group = QButtonGroup(self)
        self._backend_group.setExclusive(True)
        for cls in ALL_BACKENDS:
            btn = BackendButton(cls.display_name, cls.description, cls.is_available())
            btn.setMinimumWidth(140)
            btn.setMinimumHeight(64)
            btn.clicked.connect(lambda _=False, c=cls: self._on_backend_clicked(c))
            self._backend_group.addButton(btn)
            self._backend_buttons[cls.id] = btn
            providers.addWidget(btn)
        connection.addLayout(providers)
        self._config_section_label = self._section("ПАРАМЕТРЫ ПОДКЛЮЧЕНИЯ")
        connection.addWidget(self._config_section_label)
        self._config_panel = QFrame()
        self._config_panel.setObjectName("settingsCard")
        config_layout = QVBoxLayout(self._config_panel)
        config_layout.setContentsMargins(20, 18, 20, 18)
        self._config_form_widget = QWidget()
        self._config_form = QFormLayout(self._config_form_widget)
        self._config_form.setContentsMargins(0, 0, 0, 0)
        self._config_form.setSpacing(14)
        self._config_form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self._config_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        config_layout.addWidget(self._config_form_widget)
        connection.addWidget(self._config_panel)
        self._apply_btn = QPushButton("Подключить и загрузить модели")
        self._apply_btn.setObjectName("primary")
        self._apply_btn.setIcon(icon("bolt", "#FFFFFF"))
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self.applyClicked)
        connection.addWidget(self._apply_btn, 0, Qt.AlignRight)
        self._provider_hint = QLabel()
        self._provider_hint.setObjectName("hint")
        self._provider_hint.setWordWrap(True)
        connection.addWidget(self._provider_hint)
        connection.addStretch(1)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 20, 18, 20)
        root.setSpacing(12)
        title = QLabel("Параметры диалога")
        title.setObjectName("panelTitle")
        root.addWidget(title)
        root.addSpacing(6)
        root.addWidget(self._section("ИСТОЧНИК"))
        self._source_label = QLabel("Не выбран")
        self._source_label.setObjectName("fieldLabel")
        root.addWidget(self._source_label)
        configure = QPushButton("Настроить подключение")
        configure.setObjectName("quietAction")
        configure.setIcon(icon("settings"))
        configure.clicked.connect(self.settingsRequested)
        root.addWidget(configure)
        root.addSpacing(12)
        root.addWidget(self._section("МОДЕЛЬ"))
        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        self._model_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self._model_combo.setMinimumContentsLength(12)
        self._model_combo.setPlaceholderText("Выберите модель")
        self._model_combo.lineEdit().setPlaceholderText("Выберите модель")
        self._model_combo.activated.connect(lambda _idx: self._emit_model_changed())
        self._model_combo.lineEdit().editingFinished.connect(self._emit_model_changed)
        root.addWidget(self._model_combo)
        library = QPushButton("Библиотека моделей")
        library.setObjectName("quietAction")
        library.setIcon(icon("models"))
        library.clicked.connect(self.modelLibraryClicked)
        root.addWidget(library)
        root.addSpacing(12)
        temperature_row = QHBoxLayout()
        temperature_row.addWidget(QLabel("Температура"), 1)
        self._temp_value = QLabel("0.70")
        self._temp_value.setObjectName("temperatureValue")
        temperature_row.addWidget(self._temp_value)
        root.addLayout(temperature_row)
        self._temp_slider = QSlider(Qt.Horizontal)
        self._temp_slider.setRange(0, 200)
        self._temp_slider.setValue(70)
        self._temp_slider.setToolTip("От 0 — точнее, до 2 — свободнее")
        self._temp_slider.valueChanged.connect(self._on_temperature_slider)
        root.addWidget(self._temp_slider)
        ends = QHBoxLayout()
        for label in ("Точнее", "Свободнее"):
            widget = QLabel(label)
            widget.setObjectName("hint")
            ends.addWidget(widget)
        ends.itemAt(1).widget().setAlignment(Qt.AlignRight)
        root.addLayout(ends)
        root.addSpacing(12)
        root.addWidget(self._section("СИСТЕМНАЯ ИНСТРУКЦИЯ"))
        self._system_edit = QPlainTextEdit()
        self._system_edit.setPlaceholderText("Как отвечать ассистенту…")
        self._system_edit.setMinimumHeight(96)
        self._system_edit.setMaximumHeight(160)
        self._system_edit.textChanged.connect(
            lambda: self.systemPromptChanged.emit(self._system_edit.toPlainText())
        )
        root.addWidget(self._system_edit)
        root.addStretch(1)
        self._privacy = QLabel("Выберите источник для диалога")
        self._privacy.setObjectName("hint")
        self._privacy.setWordWrap(True)
        root.addWidget(self._privacy)
        self._set_config_form_visible(False)
        self._availability_timer = QTimer(self)
        self._availability_timer.setInterval(5000)
        self._availability_timer.timeout.connect(self.refresh_backend_availability)
        self._availability_timer.start()

    def set_busy(self, busy: bool) -> None:
        self._locked = busy
        self.connection_page.setEnabled(not busy)
        self._model_combo.setEnabled(not busy)
        self._apply_btn.setEnabled(not busy and self._apply_requested_enabled)

    def _update_source(self, cls: type[Backend]) -> None:
        self._source_label.setText(cls.display_name)
        self._privacy.setText(
            "Запросы обрабатываются на этом компьютере."
            if cls.category == "local" else
            "Сообщения отправляются выбранному облачному провайдеру."
        )
        self._provider_hint.setText(
            "После загрузки локальной модели интернет для ответов не нужен."
            if cls.category == "local" else
            "Для подключения используйте API-ключ выбранного провайдера."
        )

    @staticmethod
    def _section(title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("sidebarSection")
        return label

    def refresh_backend_availability(self) -> None:
        for cls in ALL_BACKENDS:
            button = self._backend_buttons.get(cls.id)
            if button is not None:
                button.set_available(cls.is_available())

        if self._current_backend_id:
            cls = next((item for item in ALL_BACKENDS if item.id == self._current_backend_id), None)
            if cls is not None and not cls.is_available():
                self._apply_btn.setEnabled(False)

    def _on_backend_clicked(self, cls: type[Backend]) -> None:
        self.refresh_backend_availability()
        self._current_backend_id = cls.id
        self._rebuild_config_form(cls)
        self._update_source(cls)
        available = cls.is_available()
        self.set_apply_enabled(available)
        self._apply_btn.setToolTip(
            "Запросить список моделей" if available else "Установите зависимость этого backend'а"
        )
        self.backendActivated.emit(cls.id)

    def _rebuild_config_form(self, cls: type[Backend]) -> None:
        while self._config_form.rowCount():
            self._config_form.removeRow(0)
        self._config_inputs.clear()

        if not cls.config_fields:
            self._set_config_form_visible(False)
            return

        for key, label, kind in cls.config_fields:
            compact_labels = {
                "base_url": "Адрес сервера / Base URL",
                "hf_repo": "Repo ID",
                "hf_token": "HF token",
                "n_ctx": "Контекст",
                "n_gpu_layers": "Слоёв на GPU",
                "model_path": "Файл модели",
                "api_key": "API-ключ",
            }
            field_label = QLabel(compact_labels.get(key, label))
            field_label.setObjectName("fieldLabel")
            field_label.setToolTip(label)
            if kind == "file":
                row = QHBoxLayout()
                row.setSpacing(5)
                edit = QLineEdit()
                browse = QPushButton("Обзор")
                browse.setObjectName("quietAction")
                browse.setFixedWidth(66)
                browse.clicked.connect(lambda _=False, e=edit: self._pick_file(e))
                row.addWidget(edit)
                row.addWidget(browse)
                container = QWidget()
                container.setLayout(row)
                self._config_form.addRow(field_label, container)
            else:
                edit = QLineEdit()
                if kind == "password":
                    edit.setEchoMode(QLineEdit.Password)
                self._config_form.addRow(field_label, edit)
            self._config_inputs[key] = edit

        self._set_config_form_visible(True)

    def _set_config_form_visible(self, visible: bool) -> None:
        self._config_panel.setVisible(visible)
        self._config_section_label.setVisible(visible)

    def _pick_file(self, edit: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл модели", "", "GGUF (*.gguf);;Все файлы (*)"
        )
        if path:
            edit.setText(path)

    def _on_temperature_slider(self, raw_value: int) -> None:
        value = raw_value / 100.0
        self._temp_value.setText(f"{value:.2f}")
        self.temperatureChanged.emit(value)

    def _emit_model_changed(self) -> None:
        text = self._model_combo.currentText().strip()
        if text and not self._locked:
            self.modelChanged.emit(text)

    @property
    def current_backend_id(self) -> str | None:
        return self._current_backend_id

    def set_active_backend(self, backend_id: str) -> None:
        button = self._backend_buttons.get(backend_id)
        if button is None:
            return
        cls = next((item for item in ALL_BACKENDS if item.id == backend_id), None)
        if cls is None:
            return
        button.setChecked(True)
        self._current_backend_id = backend_id
        self._rebuild_config_form(cls)
        self._update_source(cls)
        self.set_apply_enabled(cls.is_available())

    def get_config_values(self) -> dict[str, str]:
        return {key: edit.text().strip() for key, edit in self._config_inputs.items()}

    def set_config_values(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            edit = self._config_inputs.get(key)
            if edit is not None:
                edit.setText(str(value) if value is not None else "")

    def set_models(
        self,
        models: list[str],
        selected: str | None = None,
        auto_emit: bool = True,
    ) -> None:
        self._model_combo.blockSignals(True)
        self._model_combo.clear()
        self._model_combo.addItems(models)
        if selected:
            self._model_combo.setCurrentText(selected)
        self._model_combo.blockSignals(False)
        if auto_emit and self._model_combo.currentText():
            self.modelChanged.emit(self._model_combo.currentText())

    def current_model(self) -> str:
        return self._model_combo.currentText().strip()

    def set_temperature(self, value: float) -> None:
        self._temp_slider.setValue(max(0, min(200, round(value * 100))))

    def set_system_prompt(self, text: str) -> None:
        self._system_edit.setPlainText(text)

    def set_apply_enabled(self, enabled: bool) -> None:
        self._apply_requested_enabled = enabled and self._current_backend_id is not None
        self._apply_btn.setEnabled(self._apply_requested_enabled and not self._locked)
