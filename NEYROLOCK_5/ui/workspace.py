"""Graphite workspace navigation and page headers."""
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.icons import icon


def caption(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sidebarSection")
    return label


def action(text: str, name: str, primary: bool = False) -> QPushButton:
    button = QPushButton(text)
    button.setIcon(icon(name, "#FFFFFF" if primary else "#B4B3B0"))
    button.setCursor(Qt.PointingHandCursor)
    button.setObjectName("primary" if primary else "quietAction")
    return button


class PageHeader(QFrame):
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setObjectName("pageHeader")
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(12, 14, 12, 18)
        self.row.setSpacing(10)
        labels = QVBoxLayout()
        labels.setSpacing(5)
        self.title = QLabel(title)
        self.title.setObjectName("pageTitle")
        self.title.setTextFormat(Qt.PlainText)
        self.title.setWordWrap(True)
        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("pageSubtitle")
        self.subtitle.setTextFormat(Qt.PlainText)
        self.subtitle.setWordWrap(True)
        labels.addWidget(self.title)
        labels.addWidget(self.subtitle)
        self.row.addLayout(labels, 1)


class WorkspaceNav(QFrame):
    pageRequested = Signal(str)
    backendRequested = Signal(str)
    sessionRequested = Signal(str)
    newChatRequested = Signal()
    openChatRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspaceNav")
        self.setFixedWidth(234)
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 16, 14, 12)
        root.setSpacing(2)
        brand = QHBoxLayout()
        mark = QLabel()
        mark.setPixmap(QIcon(str(Path(__file__).resolve().parents[1] / "resources" / "mark.svg")).pixmap(38, 38))
        brand.addWidget(mark)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        title = QLabel("NEYROLOC")
        title.setObjectName("workspaceTitle")
        brand_text.addWidget(title)
        subtitle = QLabel("LOCAL + CLOUD")
        subtitle.setObjectName("brandSubtitle")
        brand_text.addWidget(subtitle)
        brand.addLayout(brand_text, 1)
        root.addLayout(brand)
        root.addSpacing(6)
        self.search = QLineEdit()
        self.search.setObjectName("searchInput")
        self.search.setPlaceholderText("Поиск диалогов")
        self.search.addAction(icon("search"), QLineEdit.LeadingPosition)
        self.search.textChanged.connect(self._filter_sessions)
        root.addWidget(self.search)
        root.addSpacing(6)
        # Scroll the middle section while keeping brand, search and footer visible.
        navigation = QWidget()
        navigation_layout = QVBoxLayout(navigation)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setSpacing(2)
        middle_scroll = QScrollArea()
        middle_scroll.setWidgetResizable(True)
        middle_scroll.setFrameShape(QFrame.NoFrame)
        middle_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        middle_scroll.setWidget(navigation)
        root.addWidget(middle_scroll, 1)
        footer = root
        root = navigation_layout
        root.addWidget(caption("РАБОЧЕЕ ПРОСТРАНСТВО"))
        self._pages = {}
        self._page_group = QButtonGroup(self)
        for key, title, symbol in [
            ("chat", "Диалог", "chat"), ("models", "Модели", "models"),
            ("phone", "Доступ с телефона", "phone"),
        ]:
            button = self._nav_button(title, symbol)
            self._page_group.addButton(button)
            self._pages[key] = button
            button.clicked.connect(lambda checked=False, page=key: self.pageRequested.emit(page))
            root.addWidget(button)
        root.addSpacing(6)
        root.addWidget(caption("ИСТОЧНИКИ"))
        self._providers = {}
        for key, title, symbol in [
            ("local_gguf", "Локальная модель", "cpu"),
            ("openai", "OpenAI", "cloud"), ("groq", "Groq", "bolt"),
        ]:
            button = self._nav_button(title, symbol)
            button.setCheckable(False)
            button.clicked.connect(lambda checked=False, backend=key: self.backendRequested.emit(backend))
            self._providers[key] = button
            root.addWidget(button)
        root.addSpacing(6)
        chats_row = QHBoxLayout()
        chats_row.addWidget(caption("ДИАЛОГИ"), 1)
        new = action("", "plus")
        new.setFixedSize(28, 28)
        new.setToolTip("Новый диалог")
        new.setAccessibleName("Новый диалог")
        new.clicked.connect(self.newChatRequested)
        chats_row.addWidget(new)
        root.addLayout(chats_row)
        self.current_chat = self._nav_button("Новый диалог", "chat")
        self.current_chat.setCheckable(False)
        self.current_chat.setObjectName("currentChat")
        self.current_chat.clicked.connect(lambda: self.pageRequested.emit("chat"))
        root.addWidget(self.current_chat)
        sessions_scroll = QScrollArea()
        sessions_scroll.setWidgetResizable(True)
        sessions_scroll.setMinimumHeight(0)
        sessions_scroll.setFrameShape(QFrame.NoFrame)
        sessions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        holder = QWidget()
        self._sessions_layout = QVBoxLayout(holder)
        self._sessions_layout.setContentsMargins(0, 0, 0, 0)
        self._sessions_layout.setSpacing(3)
        self._sessions_layout.addStretch(1)
        sessions_scroll.setWidget(holder)
        root.addWidget(sessions_scroll, 1)
        self._session_buttons = []
        root = footer
        open_button = action("Открыть диалог…", "folder")
        open_button.clicked.connect(self.openChatRequested)
        root.addWidget(open_button)
        settings = self._nav_button("Настройки", "settings")
        self._page_group.addButton(settings)
        self._pages["settings"] = settings
        settings.clicked.connect(lambda: self.pageRequested.emit("settings"))
        root.addWidget(settings)
        status_card = QFrame()
        status_card.setObjectName("settingsCard")
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(12, 12, 12, 12)
        self.status = QLabel("Модель не подключена")
        self.status.setObjectName("modelStatus")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.PlainText)
        self.model = QLabel("Выберите источник")
        self.model.setObjectName("modelCaption")
        self.model.setWordWrap(True)
        self.model.setTextFormat(Qt.PlainText)
        status_layout.addWidget(self.status)
        status_layout.addWidget(self.model)
        root.addWidget(status_card)
        self.set_page("chat")

    def _nav_button(self, title, symbol):
        button = QPushButton(title)
        button.setObjectName("navItem")
        button.setCheckable(True)
        button.setIcon(icon(symbol, "#76AAEE"))
        button.setIconSize(QSize(19, 19))
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(30)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return button

    def set_page(self, key):
        button = self._pages.get(key)
        if button:
            button.setChecked(True)

    def set_current_chat(self, title):
        metrics = self.current_chat.fontMetrics()
        self.current_chat.setText(metrics.elidedText(title, Qt.ElideRight, 166))
        self.current_chat.setToolTip(title)

    def set_sessions(self, paths):
        for button in self._session_buttons:
            self._sessions_layout.removeWidget(button)
            button.deleteLater()
        self._session_buttons = []
        for path in paths:
            button = QPushButton(self.fontMetrics().elidedText(path.stem, Qt.ElideRight, 175))
            button.setObjectName("sessionItem")
            button.setToolTip(path.name)
            button.setProperty("sessionTitle", path.stem)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, p=str(path): self.sessionRequested.emit(p))
            self._sessions_layout.insertWidget(self._sessions_layout.count() - 1, button)
            self._session_buttons.append(button)
        self._filter_sessions(self.search.text())

    def _filter_sessions(self, query):
        for button in self._session_buttons:
            button.setVisible(query.casefold() in button.property("sessionTitle").casefold())

    def set_busy(self, busy):
        for button in self._providers.values():
            button.setEnabled(not busy)

    def set_model_state(self, title, detail, ready=False):
        self.status.setText(title)
        self.model.setText(detail)
        self.status.setProperty("ready", ready)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
