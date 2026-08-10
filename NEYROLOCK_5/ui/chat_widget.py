"""Виджет чата: сообщения, поле ввода, потоковый вывод."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QGuiApplication, QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from backends.base import Message

# ----- разбиение markdown-текста на текстовые куски и блоки кода -----

_FENCE = "```"


def _parse_segments(text: str) -> list[tuple[str, str, str]]:
    """Разбить текст на сегменты (kind, language, content), kind ∈ {"text", "code"}.

    Незакрытый ``` в конце (стриминг ещё не дописал модель) тоже становится
    code-сегментом с тем, что уже пришло — блок появляется сразу, а не только
    после закрывающих кавычек.
    """
    segments: list[tuple[str, str, str]] = []
    pos = 0
    n = len(text)
    while pos < n:
        start = text.find(_FENCE, pos)
        if start == -1:
            if text[pos:]:
                segments.append(("text", "", text[pos:]))
            break
        if start > pos:
            segments.append(("text", "", text[pos:start]))
        newline = text.find("\n", start + len(_FENCE))
        if newline == -1:
            # Ещё не дописана даже строка с языком — рисуем пустой код-блок.
            segments.append(("code", text[start + len(_FENCE):].strip(), ""))
            break
        language = text[start + len(_FENCE):newline].strip()
        end = text.find(_FENCE, newline + 1)
        if end == -1:
            segments.append(("code", language, text[newline + 1:]))
            break
        segments.append(("code", language, text[newline + 1:end]))
        pos = end + len(_FENCE)
        if pos < n and text[pos] == "\n":
            pos += 1
    return segments


def _lexer_for(language: str, content: str):
    from pygments.lexers import TextLexer, get_lexer_by_name, guess_lexer
    from pygments.util import ClassNotFound

    if language:
        try:
            return get_lexer_by_name(language, stripnl=False)
        except ClassNotFound:
            pass
    if content.strip():
        try:
            return guess_lexer(content, stripnl=False)
        except Exception:
            pass
    return TextLexer(stripnl=False)


class CodeBlockWidget(QFrame):
    """Блок кода в ответе ассистента: язык + кнопка копирования + подсветка."""

    _MAX_HEIGHT = 420
    _MIN_HEIGHT = 34

    def __init__(self, language: str, content: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("codeBlock")
        self.setAccessibleName("Блок кода")
        self._language = language
        # None, а не content: set_content() ниже пропускает отрисовку, если
        # текст совпадает с уже показанным — с предзаполненным полем блок,
        # созданный сразу с готовым кодом (загрузка истории), оставался пустым.
        self._content: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("codeBlockHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 4, 6, 4)
        header_layout.setSpacing(6)
        self._lang_label = QLabel(language or "код")
        self._lang_label.setObjectName("codeBlockLang")
        header_layout.addWidget(self._lang_label)
        header_layout.addStretch(1)
        self._copy_btn = QPushButton("Копировать")
        self._copy_btn.setObjectName("codeBlockCopy")
        self._copy_btn.setAccessibleName("Копировать код")
        self._copy_btn.setCursor(Qt.PointingHandCursor)
        self._copy_btn.clicked.connect(self._on_copy)
        header_layout.addWidget(self._copy_btn)
        layout.addWidget(header)

        self._body = QTextEdit()
        self._body.setObjectName("codeBlockBody")
        self._body.setReadOnly(True)
        self._body.setLineWrapMode(QTextEdit.NoWrap)
        self._body.setFrameShape(QFrame.NoFrame)
        self._body.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._body.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._body.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self._body.setAccessibleName("Содержимое блока кода")
        mono = QFont("Menlo")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(11)
        self._body.setFont(mono)
        layout.addWidget(self._body)

        self.set_content(language, content)

    def set_content(self, language: str, content: str) -> None:
        if language and language != self._language:
            self._language = language
            self._lang_label.setText(language)
        self.setAccessibleDescription(f"Язык: {self._language or 'не указан'}")
        if content == self._content:
            return
        self._content = content
        self._body.setHtml(self._render_html(content))
        self._resize_to_content(content)

    def _render_html(self, content: str) -> str:
        try:
            from pygments import highlight
            from pygments.formatters import HtmlFormatter

            lexer = _lexer_for(self._language, content)
            fmt = HtmlFormatter(style="monokai", noclasses=True, nowrap=True)
            body = highlight(content, lexer, fmt)
        except Exception:
            # Подсветка — украшение, а не критичная функция; при любой ошибке
            # (незнакомый язык, битый импорт и т.п.) просто показываем текст.
            from html import escape

            body = escape(content)
        return f'<pre style="margin:0; white-space:pre; color:#f2f5fa;">{body}</pre>'

    def _resize_to_content(self, content: str) -> None:
        line_count = content.count("\n") + 1
        line_height = self._body.fontMetrics().height()
        # Перенос выключен, поэтому под длинными строками появляется
        # горизонтальный скроллбар — резервируем его высоту, иначе он
        # накрывает последнюю строку кода.
        scrollbar = self._body.horizontalScrollBar().sizeHint().height()
        height = line_count * line_height + 18 + scrollbar
        self._body.setFixedHeight(max(self._MIN_HEIGHT, min(height, self._MAX_HEIGHT)))

    def _on_copy(self) -> None:
        QGuiApplication.clipboard().setText(self._content)
        self._copy_btn.setText("Скопировано ✓")
        QTimer.singleShot(1400, self._reset_copy_label)

    def _reset_copy_label(self) -> None:
        try:
            self._copy_btn.setText("Копировать")
        except RuntimeError:
            # Виджет уже удалён (пользователь очистил чат пока таймер тикал).
            pass


class ChatBubble(QFrame):
    """Одно сообщение в чате.

    Пользовательский текст — один QLabel(PlainText), как раньше. Ответы
    ассистента разбиваются на сегменты: обычный текст (Markdown) и блоки
    кода (CodeBlockWidget с языком и кнопкой копирования), как в современных
    чат-интерфейсах.
    """

    regenerateRequested = Signal()

    def __init__(self, role: str, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._is_user = role == "user"
        self.setObjectName("chatBubbleUser" if self._is_user else "chatBubbleAssistant")
        self.setAccessibleName(
            "Сообщение пользователя" if self._is_user else "Ответ ассистента"
        )
        self.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        role_label = QLabel("Вы" if self._is_user else "Ассистент")
        role_label.setObjectName("bubbleRole")
        layout.addWidget(role_label)

        self._raw = ""
        self._body_layout = QVBoxLayout()
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(8)
        layout.addLayout(self._body_layout)

        if self._is_user:
            self._text_label = QLabel()
            self._text_label.setObjectName("bubbleText")
            self._text_label.setTextFormat(Qt.PlainText)
            self._text_label.setWordWrap(True)
            self._text_label.setTextInteractionFlags(
                Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
            )
            self._text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self._body_layout.addWidget(self._text_label)
        else:
            self._segments: list[tuple[str, str, str]] = []
            self._segment_widgets: list[QWidget] = []

        # Действия над сообщением: копировать — всегда, повторить — только у
        # последнего ответа ассистента (видимостью управляет ChatWidget).
        self._actions = QWidget()
        actions_row = QHBoxLayout(self._actions)
        actions_row.setContentsMargins(0, 2, 0, 0)
        actions_row.setSpacing(4)
        if self._is_user:
            actions_row.addStretch(1)
        self._copy_btn = self._make_action("Копировать", self._on_copy)
        actions_row.addWidget(self._copy_btn)
        self._regen_btn = self._make_action("Повторить", self.regenerateRequested.emit)
        self._regen_btn.setVisible(False)
        actions_row.addWidget(self._regen_btn)
        if not self._is_user:
            actions_row.addStretch(1)
        layout.addWidget(self._actions)

        if text:
            self.set_text(text)

    def _make_action(self, label: str, slot) -> QPushButton:
        btn = QPushButton(label)
        btn.setObjectName("bubbleAction")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFlat(True)
        btn.clicked.connect(slot)
        return btn

    def _on_copy(self) -> None:
        QGuiApplication.clipboard().setText(self._raw)
        self._copy_btn.setText("Скопировано ✓")
        QTimer.singleShot(1400, self._reset_copy_label)

    def _reset_copy_label(self) -> None:
        try:
            self._copy_btn.setText("Копировать")
        except RuntimeError:
            # Таймер мог сработать после очистки/переключения чата.
            pass

    @property
    def is_user(self) -> bool:
        return self._is_user

    def set_regenerate_visible(self, visible: bool) -> None:
        self._regen_btn.setVisible(visible)

    def set_actions_visible(self, visible: bool) -> None:
        self._actions.setVisible(visible)

    def _make_text_label(self, content: str) -> QLabel:
        label = QLabel()
        label.setObjectName("bubbleText")
        label.setTextFormat(Qt.MarkdownText)
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextSelectableByMouse
            | Qt.TextSelectableByKeyboard
            | Qt.LinksAccessibleByMouse
            | Qt.LinksAccessibleByKeyboard
        )
        # Ответ модели — недоверенный контент. Не отдаём Qt произвольные
        # file:/custom-scheme ссылки и не открываем браузер без подтверждения.
        label.setOpenExternalLinks(False)
        label.linkActivated.connect(self._open_external_link)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if content:
            label.setText(content)
        return label

    def _open_external_link(self, href: str) -> None:
        url = QUrl(href)
        if (
            not url.isValid()
            or url.scheme().lower() not in {"http", "https"}
            or not url.host()
            or url.userInfo()
        ):
            QMessageBox.warning(
                self.window(),
                "Ссылка заблокирована",
                "Разрешены только обычные HTTP/HTTPS-ссылки без встроенных учётных данных.",
            )
            return
        if (
            QMessageBox.question(
                self.window(),
                "Открыть внешнюю ссылку?",
                url.toDisplayString(),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            QDesktopServices.openUrl(url)

    def _rebuild_segments(self) -> None:
        """Инкрементально обновить виджеты-сегменты под текущий self._raw."""
        new_segments = _parse_segments(self._raw)

        common = min(len(new_segments), len(self._segments))
        diverge_at = common
        for i in range(common):
            if new_segments[i][0] != self._segments[i][0]:
                diverge_at = i
                break

        # Отличающийся "хвост" виджетов (по типу сегмента) пересоздаём.
        for widget in self._segment_widgets[diverge_at:]:
            widget.setParent(None)
            widget.deleteLater()
        self._segment_widgets = self._segment_widgets[:diverge_at]
        self._segments = self._segments[:diverge_at]

        for i in range(diverge_at):
            kind, lang, content = new_segments[i]
            if (kind, lang, content) == self._segments[i]:
                continue
            if kind == "text":
                self._segment_widgets[i].setText(content)
            else:
                self._segment_widgets[i].set_content(lang, content)
            self._segments[i] = (kind, lang, content)

        for i in range(diverge_at, len(new_segments)):
            kind, lang, content = new_segments[i]
            widget = CodeBlockWidget(lang, content) if kind == "code" else self._make_text_label(content)
            self._body_layout.addWidget(widget)
            self._segment_widgets.append(widget)
            self._segments.append((kind, lang, content))

    def append_text(self, chunk: str) -> None:
        # Текст копится в python-строке: полная перестройка на каждый токен
        # давала квадратичную склейку и перелэйаут; здесь сегменты, не
        # изменившиеся по составу, обновляются на месте, а не пересоздаются.
        self._raw += chunk
        if self._is_user:
            self._text_label.setText(self._raw)
        else:
            self._rebuild_segments()

    def text(self) -> str:
        return self._raw

    def set_text(self, text: str) -> None:
        self._raw = text
        if self._is_user:
            self._text_label.setText(text)
        else:
            self._rebuild_segments()


class ChatInput(QPlainTextEdit):
    """Поле ввода: Enter — отправить, Shift+Enter — перенос строки."""

    submit = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Сообщение")
        self.setAccessibleName("Сообщение")
        self.setAccessibleDescription(
            "Введите сообщение. Enter отправляет, Shift+Enter добавляет новую строку."
        )
        self.setMaximumHeight(140)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 (Qt API)
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (
            event.modifiers() & Qt.ShiftModifier
        ):
            self.submit.emit()
            return
        super().keyPressEvent(event)


class ChatWidget(QWidget):
    """Список сообщений + поле ввода + кнопки."""

    sendRequested = Signal(str)
    stopRequested = Signal()
    regenerateRequested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._busy = False
        self._input_enabled = True
        self._streaming_bubble: ChatBubble | None = None
        self._bubbles: list[ChatBubble] = []

        # Стриминговые chunks копятся в буфере и флашатся в bubble по таймеру:
        # рендерить markdown на каждый токен слишком дорого.
        self._pending_chunks: list[str] = []
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(70)
        self._flush_timer.timeout.connect(self._flush_pending)

        # Автоскролл «прилипает» к низу, пока пользователь сам не отмотал вверх.
        self._stick_to_bottom = True
        self._placeholder_spacer: QSpacerItem | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Прокручиваемая область с сообщениями.
        self._scroll = QScrollArea()
        self._scroll.setAccessibleName("История сообщений")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        # На минимальной ширине sizeHint пустого состояния мог включить
        # горизонтальный скроллбар на всю область чата. Текст и карточки
        # переносятся, а прокрутка остаётся доступна внутри code block.
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._messages_holder = QWidget()
        self._messages_layout = QVBoxLayout(self._messages_holder)
        self._messages_layout.setContentsMargins(8, 8, 8, 8)
        self._messages_layout.setSpacing(10)
        self._messages_layout.addStretch(1)
        self._scroll.setWidget(self._messages_holder)
        bar = self._scroll.verticalScrollBar()
        bar.valueChanged.connect(self._on_scroll_value_changed)
        bar.rangeChanged.connect(self._on_scroll_range_changed)
        root.addWidget(self._scroll, 1)

        # Поле ввода + кнопки.
        input_frame = QFrame()
        input_frame.setObjectName("composer")
        input_row = QHBoxLayout(input_frame)
        input_row.setContentsMargins(12, 10, 12, 10)
        input_row.setSpacing(8)
        self._input = ChatInput()
        self._input.submit.connect(self._on_submit)
        self._input.textChanged.connect(self._update_send_enabled)
        input_row.addWidget(self._input, 1)

        buttons_col = QVBoxLayout()
        buttons_col.setSpacing(6)
        self._send_btn = QPushButton("Отправить")
        self._send_btn.setObjectName("primary")
        self._send_btn.setToolTip("Отправить сообщение (Enter)")
        self._send_btn.clicked.connect(self._on_submit)
        self._stop_btn = QPushButton("Стоп")
        self._stop_btn.setObjectName("dangerAction")
        self._stop_btn.setToolTip("Остановить генерацию")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self.stopRequested)
        buttons_col.addWidget(self._send_btn)
        buttons_col.addWidget(self._stop_btn)
        input_row.addLayout(buttons_col)

        root.addWidget(input_frame)

        self._show_placeholder("Выберите backend, подключите модель и начните диалог.")
        self._update_send_enabled()

    # ----- сообщения -----

    def _add_bubble(self, role: str, text: str) -> ChatBubble:
        bubble = ChatBubble(role, text)
        bubble.setMaximumWidth(760)
        bubble.regenerateRequested.connect(self.regenerateRequested)
        self._bubbles.append(bubble)
        row = QWidget()
        row.setObjectName("bubbleRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        if role == "user":
            row_layout.addStretch(1)
            row_layout.addWidget(bubble)
        else:
            row_layout.addWidget(bubble)
            row_layout.addStretch(1)
        # вставляем перед stretch
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, row)
        self._refresh_actions()
        self._scroll_to_bottom()
        return bubble

    def _refresh_actions(self) -> None:
        """«Повторить» — только у последнего ответа ассистента и только когда
        генерация не идёт; у пузыря, который сейчас стримится, действий нет."""
        for i, bubble in enumerate(self._bubbles):
            is_last = i == len(self._bubbles) - 1
            streaming = bubble is self._streaming_bubble
            bubble.set_actions_visible(not streaming)
            bubble.set_regenerate_visible(
                is_last and not streaming and not self._busy and not bubble.is_user
            )

    def add_user_message(self, text: str) -> None:
        self._clear_placeholder()
        self._add_bubble("user", text)

    def add_assistant_message(self, text: str) -> None:
        self._clear_placeholder()
        self._add_bubble("assistant", text)

    def begin_streaming_assistant(self) -> None:
        self._clear_placeholder()
        self._pending_chunks = []
        self._streaming_bubble = self._add_bubble("assistant", "")
        self._flush_timer.start()

    def append_streaming_chunk(self, chunk: str) -> None:
        if self._streaming_bubble is None:
            self.begin_streaming_assistant()
        self._pending_chunks.append(chunk)

    def _flush_pending(self) -> None:
        if not self._pending_chunks or self._streaming_bubble is None:
            return
        text = "".join(self._pending_chunks)
        self._pending_chunks = []
        self._streaming_bubble.append_text(text)

    def end_streaming(self) -> str:
        self._flush_timer.stop()
        self._flush_pending()
        text = self._streaming_bubble.text() if self._streaming_bubble else ""
        self._streaming_bubble = None
        self._refresh_actions()
        return text

    def clear_messages(self) -> None:
        self._clear_placeholder()
        while self._messages_layout.count() > 1:
            item = self._messages_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._flush_timer.stop()
        self._pending_chunks = []
        self._streaming_bubble = None
        self._bubbles = []
        self._show_placeholder("История очищена. Можно начать новый диалог.")

    def set_messages(self, messages: list[Message]) -> None:
        self._clear_placeholder()
        while self._messages_layout.count() > 1:
            item = self._messages_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._flush_timer.stop()
        self._pending_chunks = []
        self._streaming_bubble = None
        self._bubbles = []
        visible = [m for m in messages if m.role != "system"]
        if not visible:
            self._show_placeholder("В этом чате пока нет сообщений.")
            return
        for message in visible:
            self._add_bubble(message.role, message.content)

    def _show_placeholder(self, text: str) -> None:
        self._clear_placeholder()
        card = QFrame()
        card.setObjectName("emptyState")
        card.setProperty("isPlaceholder", True)
        card.setAccessibleName("Пустой чат")
        card.setMaximumWidth(520)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(7)

        title = QLabel("Начните новый диалог")
        title.setObjectName("emptyStateTitle")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        hint = QLabel(text)
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        card_layout.addWidget(hint)

        shortcut = QLabel("Enter — отправить · Shift+Enter — новая строка")
        shortcut.setObjectName("emptyStateShortcut")
        shortcut.setAlignment(Qt.AlignCenter)
        shortcut.setWordWrap(True)
        card_layout.addWidget(shortcut)

        insert_at = self._messages_layout.count() - 1
        self._placeholder_spacer = QSpacerItem(
            0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self._messages_layout.insertItem(insert_at, self._placeholder_spacer)
        self._messages_layout.setStretch(insert_at, 1)
        self._messages_layout.insertWidget(
            insert_at + 1, card, 0, Qt.AlignHCenter
        )

    def _clear_placeholder(self) -> None:
        if self._placeholder_spacer is not None:
            self._messages_layout.removeItem(self._placeholder_spacer)
            self._placeholder_spacer = None
        for i in range(self._messages_layout.count() - 1, -1, -1):
            w = self._messages_layout.itemAt(i).widget()
            if w is not None and w.property("isPlaceholder"):
                self._messages_layout.takeAt(i)
                w.setParent(None)
                w.deleteLater()

    def _scroll_to_bottom(self) -> None:
        # Прямой setValue(maximum()) не доезжал: layout ещё не пересчитан
        # и maximum() устаревший. «Прилипаем» к низу — rangeChanged доскроллит.
        self._stick_to_bottom = True
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_scroll_value_changed(self, _value: int) -> None:
        # Пользователь отмотал вверх — перестаём дёргать его автоскроллом;
        # вернулся вниз — снова прилипаем.
        bar = self._scroll.verticalScrollBar()
        self._stick_to_bottom = bar.value() >= bar.maximum() - 40

    def _on_scroll_range_changed(self, _min: int, _max: int) -> None:
        if self._stick_to_bottom:
            bar = self._scroll.verticalScrollBar()
            bar.setValue(bar.maximum())

    # ----- управление состоянием ввода -----

    def _update_send_enabled(self) -> None:
        has_text = bool(self._input.toPlainText().strip())
        self._send_btn.setEnabled(self._input_enabled and not self._busy and has_text)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._stop_btn.setEnabled(busy)
        self._input.setReadOnly(busy)
        self._update_send_enabled()
        self._refresh_actions()

    def set_input_enabled(self, enabled: bool) -> None:
        self._input_enabled = enabled
        self._input.setEnabled(enabled)
        self._update_send_enabled()

    def _on_submit(self) -> None:
        if self._busy:
            return
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._input.clear()
        self.sendRequested.emit(text)
