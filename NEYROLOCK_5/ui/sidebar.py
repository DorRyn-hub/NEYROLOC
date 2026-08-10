"""Compact navigation and configuration sidebar."""

from __future__ import annotations

from typing import Optional

from backends import ALL_BACKENDS, Backend
from PySide6.QtCore import QRect, Qt, QTimer, Signal
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

from ui.styles import COLORS


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
        self.setAccessibleName(display_name)
        self.setAccessibleDescription(self._accessible_description())
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setToolTip(description)

    def set_available(self, available: bool) -> None:
        self._available = available
        self.setAccessibleDescription(self._accessible_description())
        self.update()

    def _accessible_description(self) -> str:
        status = "доступен" if self._available else "не установлен"
        return f"{self._description}. Статус: {status}."

    def paintEvent(self, _event) -> None:  # noqa: N802 — Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        if self.isChecked():
            background = QColor("#202c43")
            border = QColor("#3e5686")
        elif self.underMouse():
            background = QColor("#192536")
            border = QColor("#2b3d58")
        else:
            background = QColor("#141d2a")
            border = QColor("#202b3a")

        focused = self.hasFocus()
        if focused:
            border = QColor("#829dff")

        painter.setBrush(background)
        painter.setPen(QPen(border, 2 if focused else 1))
        painter.drawRoundedRect(rect, 9, 9)

        dot_color = QColor("#4ed39a" if self._available else "#65748a")
        painter.setPen(Qt.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(QRect(14, 19, 8, 8))

        painter.setPen(QColor("#eef3fa"))
        painter.drawText(QRect(34, 7, self.width() - 46, 18), Qt.AlignVCenter, self._display_name)

        status = "доступен" if self._available else "не установлено"
        painter.setPen(
            QColor(COLORS["text_secondary"] if self._available else COLORS["text_muted"])
        )
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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(280)
        self.setMaximumWidth(420)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._backend_buttons: dict[str, BackendButton] = {}
        self._config_inputs: dict[str, QLineEdit] = {}
        self._current_backend_id: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(5)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 2)
        brand_row.setSpacing(9)
        mark = QLabel("N")
        mark.setObjectName("brandMark")
        mark.setAlignment(Qt.AlignCenter)
        mark.setFixedSize(30, 30)
        brand_row.addWidget(mark)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel("NEYROLOC")
        title.setObjectName("sidebarTitle")
        subtitle = QLabel("LOCAL + CLOUD WORKSPACE")
        subtitle.setObjectName("sidebarSubtitle")
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        brand_row.addLayout(brand_text)
        brand_row.addStretch(1)
        root.addLayout(brand_row)

        root.addWidget(self._section("ПОДКЛЮЧЕНИЕ"))
        backend_panel = QFrame()
        backend_panel.setObjectName("sidebarPanel")
        backend_layout = QVBoxLayout(backend_panel)
        backend_layout.setContentsMargins(7, 7, 7, 7)
        backend_layout.setSpacing(4)
        self._backend_group = QButtonGroup(self)
        self._backend_group.setExclusive(True)
        group_titles = {"local": "ЛОКАЛЬНО", "online": "ОНЛАЙН"}
        seen_categories: set[str] = set()
        for cls in ALL_BACKENDS:
            if cls.category not in seen_categories:
                seen_categories.add(cls.category)
                group_label = QLabel(group_titles.get(cls.category, cls.category.upper()))
                group_label.setObjectName("backendGroupLabel")
                if seen_categories - {cls.category}:
                    backend_layout.addSpacing(4)
                backend_layout.addWidget(group_label)
            btn = BackendButton(
                cls.display_name,
                cls.description,
                cls.is_available(),
            )
            btn.clicked.connect(lambda _=False, c=cls: self._on_backend_clicked(c))
            self._backend_group.addButton(btn)
            self._backend_buttons[cls.id] = btn
            backend_layout.addWidget(btn)
        root.addWidget(backend_panel)

        self._config_section_label = self._section("ПАРАМЕТРЫ BACKEND'А")
        root.addWidget(self._config_section_label)
        self._config_panel = QFrame()
        self._config_panel.setObjectName("sidebarPanel")
        config_panel_layout = QVBoxLayout(self._config_panel)
        config_panel_layout.setContentsMargins(9, 8, 9, 8)
        self._config_form_widget = QWidget()
        self._config_form = QFormLayout(self._config_form_widget)
        self._config_form.setContentsMargins(0, 0, 0, 0)
        self._config_form.setSpacing(6)
        self._config_form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        config_panel_layout.addWidget(self._config_form_widget)
        root.addWidget(self._config_panel)

        self._apply_btn = QPushButton("Подключить")
        self._apply_btn.setObjectName("primary")
        self._apply_btn.setToolTip("Выберите доступный backend")
        self._apply_btn.setAccessibleDescription(
            "Подключает выбранный backend и запрашивает список моделей."
        )
        self._apply_btn.setEnabled(False)
        self._apply_btn.clicked.connect(self.applyClicked)
        root.addWidget(self._apply_btn)

        root.addWidget(self._section("МОДЕЛЬ"))
        model_panel = QFrame()
        model_panel.setObjectName("sidebarPanel")
        model_layout = QVBoxLayout(model_panel)
        model_layout.setContentsMargins(9, 8, 9, 8)
        model_layout.setSpacing(7)
        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        self._model_combo.setAccessibleName("Модель")
        self._model_combo.setAccessibleDescription(
            "Выберите модель из списка или введите её название."
        )
        self._model_combo.setPlaceholderText("Выберите модель")
        self._model_combo.lineEdit().setPlaceholderText("Выберите модель")
        self._model_combo.activated.connect(lambda _idx: self._emit_model_changed())
        self._model_combo.lineEdit().editingFinished.connect(self._emit_model_changed)
        model_layout.addWidget(self._model_combo)
        library_btn = QPushButton("Открыть библиотеку моделей")
        library_btn.setObjectName("quietAction")
        library_btn.setToolTip("Найти, скачать или выбрать локальную GGUF-модель")
        library_btn.clicked.connect(self.modelLibraryClicked)
        model_layout.addWidget(library_btn)
        root.addWidget(model_panel)

        root.addWidget(self._section("ГЕНЕРАЦИЯ"))
        temperature_row = QHBoxLayout()
        temperature_row.setContentsMargins(3, 0, 3, 0)
        temperature_row.setSpacing(10)
        temp_caption = QLabel("Температура")
        temp_caption.setObjectName("fieldLabel")
        self._temp_slider = QSlider(Qt.Horizontal)
        self._temp_slider.setRange(0, 200)
        self._temp_slider.setSingleStep(5)
        self._temp_slider.setPageStep(10)
        self._temp_slider.setValue(70)
        self._temp_slider.setToolTip("От 0.00 — точные ответы, до 2.00 — более свободные")
        self._temp_slider.setAccessibleName("Температура генерации")
        self._temp_slider.setAccessibleDescription(
            "От 0.00 для более точных ответов до 2.00 для более свободных."
        )
        self._temp_value = QLabel("0.70")
        self._temp_value.setObjectName("temperatureValue")
        self._temp_value.setAccessibleName("Значение температуры: 0.70")
        self._temp_value.setAlignment(Qt.AlignCenter)
        temperature_row.addWidget(temp_caption)
        temperature_row.addWidget(self._temp_slider, 1)
        temperature_row.addWidget(self._temp_value)
        root.addLayout(temperature_row)
        self._temp_slider.valueChanged.connect(self._on_temperature_slider)

        root.addWidget(self._section("СИСТЕМНЫЙ ПРОМПТ"))
        self._system_edit = QPlainTextEdit()
        self._system_edit.setPlaceholderText("Например: Ты — полезный ассистент…")
        self._system_edit.setAccessibleName("Системный промпт")
        self._system_edit.setAccessibleDescription(
            "Инструкция, задающая роль и стиль ответов модели."
        )
        self._system_edit.setMinimumHeight(66)
        self._system_edit.setMaximumHeight(82)
        self._system_edit.textChanged.connect(
            lambda: self.systemPromptChanged.emit(self._system_edit.toPlainText())
        )
        root.addWidget(self._system_edit)

        root.addWidget(self._section("ЧАТ"))
        actions = QHBoxLayout()
        actions.setSpacing(6)
        for label, signal in (
            ("Новый", self.newChatClicked),
            ("Открыть", self.loadChatClicked),
            ("Сохранить", self.saveChatClicked),
        ):
            button = QPushButton(label)
            button.setObjectName("quietAction")
            button.setToolTip(f"{label} чат")
            button.clicked.connect(signal)
            actions.addWidget(button)
        root.addLayout(actions)

        root.addStretch(1)
        hint = QLabel("Зависимости устанавливаются только для выбранных backend'ов.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self._set_config_form_visible(False)
        self._availability_timer = QTimer(self)
        self._availability_timer.setInterval(5000)
        self._availability_timer.timeout.connect(self.refresh_backend_availability)
        self._availability_timer.start()

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
        available = cls.is_available()
        self._apply_btn.setEnabled(available)
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
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(5)
                edit = QLineEdit()
                edit.setAccessibleName(compact_labels.get(key, label))
                edit.setPlaceholderText("Выберите GGUF-файл")
                edit.textChanged.connect(
                    lambda text, e=edit: e.setToolTip(text or "Выберите GGUF-файл")
                )
                browse = QPushButton("Обзор")
                browse.setObjectName("quietAction")
                browse.setFixedWidth(66)
                browse.setAccessibleDescription(
                    f"Выбрать файл для поля «{compact_labels.get(key, label)}»."
                )
                browse.clicked.connect(lambda _=False, e=edit: self._pick_file(e))
                row.addWidget(edit, 1)
                row.addWidget(browse)
                container = QWidget()
                container.setLayout(row)
                self._config_form.addRow(field_label, container)
            else:
                edit = QLineEdit()
                edit.setAccessibleName(compact_labels.get(key, label))
                if kind == "password":
                    edit.setEchoMode(QLineEdit.Password)
                self._config_form.addRow(field_label, edit)
            field_label.setBuddy(edit)
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
            edit.setCursorPosition(len(path))
            edit.deselect()

    def _on_temperature_slider(self, raw_value: int) -> None:
        value = raw_value / 100.0
        self._temp_value.setText(f"{value:.2f}")
        self._temp_value.setAccessibleName(f"Значение температуры: {value:.2f}")
        self.temperatureChanged.emit(value)

    def _emit_model_changed(self) -> None:
        text = self._model_combo.currentText().strip()
        if text:
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
        available = cls.is_available()
        self._apply_btn.setEnabled(available)
        self._apply_btn.setToolTip(
            "Запросить список моделей"
            if available
            else "Установите зависимость этого backend'а"
        )

    def get_config_values(self) -> dict[str, str]:
        return {key: edit.text().strip() for key, edit in self._config_inputs.items()}

    def set_config_values(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            edit = self._config_inputs.get(key)
            if edit is not None:
                text = str(value) if value is not None else ""
                edit.setText(text)
                if key == "model_path":
                    edit.setToolTip(text or "Выберите GGUF-файл")
                    edit.setCursorPosition(len(text))
                    edit.deselect()

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
        self._apply_btn.setEnabled(enabled and self._current_backend_id is not None)
