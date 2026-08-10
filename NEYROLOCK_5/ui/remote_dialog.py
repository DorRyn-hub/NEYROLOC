"""Диалог «Удалённый доступ с телефона»: включение сервера, код, QR."""

from __future__ import annotations

import errno
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.remote_server import DEFAULT_PORT


def _server_error_text(exc: OSError) -> str:
    """Понятное объяснение вместо системного кода ошибки."""
    if exc.errno == errno.EADDRINUSE:
        return (
            f"Порт {DEFAULT_PORT} занят другой программой — возможно, NEYROLOC "
            "уже запущен во втором окне. Закройте её и попробуйте снова."
        )
    if exc.errno in (errno.EACCES, errno.EPERM):
        return "Система не разрешила открыть порт. Проверьте настройки брандмауэра."
    return f"Не удалось запустить сервер: {exc}"


def _qr_pixmap(url: str) -> QPixmap | None:
    """QR-код адреса, если установлен segno (опционально)."""
    try:
        import io

        import segno

        buf = io.BytesIO()
        segno.make(url).save(buf, kind="png", scale=6, dark="#eef3fa", light="#171e2b")
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue(), "PNG")
        return pixmap
    except Exception:
        return None


class RemoteAccessDialog(QDialog):
    """Показывает состояние сервера удалённого доступа и управляет им.

    Сам сервер живёт в MainWindow — диалог только дёргает переданные
    колбэки start/stop и отображает адрес, код сопряжения и QR.
    """

    def __init__(
        self,
        is_running,
        start,
        stop,
        lan_url: str,
        pair_code: str,
        remote_url: Optional[str] = None,
        parent: Optional[QWidget] = None,
        tunnel=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("remoteAccessDialog")
        self.setWindowTitle("Удалённый доступ с телефона")
        self.setMinimumWidth(360)
        self._is_running = is_running
        self._start = start
        self._stop = stop
        self._tunnel = tunnel

        # Содержимое (адреса, QR, кнопки) выше, чем помещается на невысоких
        # экранах, поэтому кладём его в прокручиваемую область — иначе QR
        # обрезается и до него не домотать.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            self.setMaximumHeight(int(screen.availableGeometry().height() * 0.9))

        root = QVBoxLayout(content)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(12)

        title = QLabel("Управление с телефона")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        hint = QLabel(
            "Откройте адрес в браузере телефона (или отсканируйте QR) и введите код "
            "сопряжения. Затем в браузере: «Поделиться» → «На экран «Домой»» — "
            "NEYROLOC появится иконкой на телефоне и будет открываться как приложение."
        )
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        # Адрес №1 — в той же Wi-Fi.
        root.addWidget(self._addr_block("В этой Wi-Fi-сети:", lan_url))

        # Адрес №2 — откуда угодно, через Tailscale (если доступен).
        if remote_url:
            root.addWidget(self._addr_block(
                "Откуда угодно (через Tailscale):", remote_url,
                sub="Нужно, чтобы Tailscale был установлен и на телефоне (тот же аккаунт).",
            ))

        # Адрес №3 — публичный, через собственный туннель (работает в любой сети).
        self._tunnel_check = None
        self._tunnel_state = None
        self._tunnel_addr = None
        if tunnel is not None:
            box = QWidget()
            col = QVBoxLayout(box)
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(3)
            cap = QLabel("Откуда угодно (публичный адрес):")
            cap.setObjectName("fieldLabel")
            col.addWidget(cap)
            addr = QLabel(tunnel.public_url or "адрес будет выдан при первом включении")
            addr.setObjectName("remoteUrl")
            addr.setTextInteractionFlags(
                Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
            )
            addr.setAccessibleName("Публичный адрес")
            addr.setAlignment(Qt.AlignCenter)
            addr.setWordWrap(True)
            self._tunnel_addr = addr
            col.addWidget(addr)
            self._tunnel_check = QCheckBox("Включить доступ из интернета")
            self._tunnel_check.setAccessibleDescription(
                "Запускает публичный туннель и, при необходимости, локальный сервер."
            )
            self._tunnel_check.setChecked(tunnel.running)
            self._tunnel_check.toggled.connect(self._on_tunnel_toggled)
            col.addWidget(self._tunnel_check)
            self._tunnel_state = QLabel("")
            self._tunnel_state.setObjectName("hint")
            self._tunnel_state.setWordWrap(True)
            col.addWidget(self._tunnel_state)
            root.addWidget(box)
            tunnel.statusChanged.connect(self._on_tunnel_status)

        code_row = QHBoxLayout()
        code_caption = QLabel("Код сопряжения:")
        code_caption.setObjectName("fieldLabel")
        self._code_label = QLabel(pair_code)
        self._code_label.setObjectName("remotePairCode")
        self._code_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self._code_label.setAccessibleName(f"Код сопряжения: {pair_code}")
        code_row.addStretch(1)
        code_row.addWidget(code_caption)
        code_row.addWidget(self._code_label)
        code_row.addStretch(1)
        root.addLayout(code_row)

        # QR ведёт сразу на нужный адрес и содержит код сопряжения: телефон
        # (приложение или обычная камера) открывает его и подключается без
        # ручного ввода. Публичный адрес приоритетнее — он работает везде.
        self._lan_url = lan_url
        self._qr_label = QLabel()
        self._qr_label.setAlignment(Qt.AlignCenter)
        self._qr_label.setAccessibleName("QR-код для подключения телефона")
        root.addWidget(self._qr_label)
        self._qr_caption = QLabel("")
        self._qr_caption.setObjectName("hint")
        self._qr_caption.setAlignment(Qt.AlignCenter)
        self._qr_caption.setWordWrap(True)
        root.addWidget(self._qr_caption)
        self._refresh_qr()

        root.addStretch(1)

        # Кнопки — вне прокрутки, чтобы «Закрыть» всегда был под рукой.
        footer = QWidget()
        footer_col = QVBoxLayout(footer)
        footer_col.setContentsMargins(22, 10, 22, 18)
        footer_col.setSpacing(8)

        self._toggle_btn = QPushButton()
        self._toggle_btn.setObjectName("primary")
        self._toggle_btn.setAccessibleDescription(
            "Включает или выключает локальный сервер удалённого доступа."
        )
        self._toggle_btn.clicked.connect(self._on_toggle)
        footer_col.addWidget(self._toggle_btn)

        self._state_label = QLabel("")
        self._state_label.setObjectName("hint")
        self._state_label.setAlignment(Qt.AlignCenter)
        self._state_label.setWordWrap(True)
        footer_col.addWidget(self._state_label)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        footer_col.addWidget(close_btn)

        outer.addWidget(footer)

        self._sync()

    def _qr_target(self) -> tuple[str, str]:
        """(ссылка для QR, подпись) — публичный адрес, если туннель поднят."""
        code = self._code_label.text().strip()
        suffix = f"/?code={code}" if code else "/"
        if self._tunnel is not None and self._tunnel.running and self._tunnel.public_url:
            return self._tunnel.public_url + suffix, "Наведите камеру телефона — откроется ваш адрес, код подставится сам"
        return self._lan_url + suffix, "QR для этой Wi-Fi-сети. Включите доступ из интернета — QR станет рабочим из любой сети"

    def _refresh_qr(self) -> None:
        # Статус туннеля может прийти раньше, чем построен блок QR.
        if not hasattr(self, "_qr_label"):
            return
        url, caption = self._qr_target()
        pixmap = _qr_pixmap(url)
        if pixmap is None:
            self._qr_label.setVisible(False)
            self._qr_caption.setText("Установите пакет segno, чтобы видеть QR-код.")
            return
        self._qr_label.setVisible(True)
        # Ссылка с кодом длиннее обычной, поэтому QR крупный — приводим его к
        # предсказуемому размеру, чтобы окно оставалось компактным.
        if pixmap.width() > 250:
            pixmap = pixmap.scaled(
                250, 250, Qt.KeepAspectRatio, Qt.FastTransformation
            )
        self._qr_label.setPixmap(pixmap)
        self._qr_caption.setText(caption)

    def _addr_block(self, caption: str, url: str, sub: str = "") -> QWidget:
        box = QWidget()
        col = QVBoxLayout(box)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)
        cap = QLabel(caption)
        cap.setObjectName("fieldLabel")
        col.addWidget(cap)
        addr = QLabel(url)
        addr.setObjectName("remoteUrl")
        addr.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        addr.setAccessibleName(caption.rstrip(":"))
        addr.setAlignment(Qt.AlignCenter)
        addr.setWordWrap(True)
        col.addWidget(addr)
        if sub:
            sub_label = QLabel(sub)
            sub_label.setObjectName("hint")
            sub_label.setWordWrap(True)
            col.addWidget(sub_label)
        return box

    def _sync(self) -> None:
        running = self._is_running()
        self._toggle_btn.setText("Выключить доступ" if running else "Включить доступ")
        self._state_label.setText(
            "Сервер работает — телефон может подключаться." if running else "Сервер выключен."
        )

    def _on_tunnel_toggled(self, checked: bool) -> None:
        if self._tunnel is None:
            return
        if checked:
            # Туннель ведёт на локальный сервер — без него публиковать нечего.
            if not self._is_running():
                try:
                    self._start()
                except OSError as exc:
                    self._state_label.setText(_server_error_text(exc))
                    self._tunnel_check.setChecked(False)
                    return
                self._sync()
            if not self._tunnel.start():
                self._tunnel_check.setChecked(False)
            # Адрес мог только что появиться (первая регистрация).
            if self._tunnel_addr is not None and self._tunnel.public_url:
                self._tunnel_addr.setText(self._tunnel.public_url)
        else:
            self._tunnel.stop()

    def _on_tunnel_status(self, text: str) -> None:
        if self._tunnel_state is not None:
            self._tunnel_state.setText(text)
        if self._tunnel_addr is not None and self._tunnel.public_url:
            self._tunnel_addr.setText(self._tunnel.public_url)
        self._refresh_qr()   # адрес мог смениться на публичный

    def _on_toggle(self) -> None:
        try:
            if self._is_running():
                # Публиковать нечего, если сервер выключают.
                if self._tunnel is not None and self._tunnel.running:
                    self._tunnel.stop()
                    if self._tunnel_check is not None:
                        self._tunnel_check.setChecked(False)
                self._stop()
            else:
                self._start()
        except OSError as exc:
            self._state_label.setText(_server_error_text(exc))
            return
        self._sync()
        self._refresh_qr()
