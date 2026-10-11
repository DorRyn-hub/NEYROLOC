#!/usr/bin/env python3
"""NEYROLOC NEW launcher: v2 engine functions inside the v5 PySide interface."""
#launcher vers: 12:20 12.07.26
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap


APP_DIR = Path(__file__).resolve().parent / "NEYROLOCK_5"
sys.path.insert(0, str(APP_DIR))

from PySide6.QtWidgets import QApplication  # noqa: E402

from ui.macos_appname import set_app_name  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402
from ui.styles import APP_QSS  # noqa: E402


def _application_icon() -> QIcon:
    """Create a small crisp app mark without requiring an external asset."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#6d8cff"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(2, 2, 60, 60, 17, 17)
    painter.setPen(QColor("#ffffff"))
    font = QFont("Arial", 31, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "N")
    painter.end()
    return QIcon(pixmap)


def main() -> int:
    # Должно быть до создания QApplication: AppKit читает CFBundleName при
    # инициализации NSApplication, чтобы назвать меню приложения.
    set_app_name("NEYROLOC NEW")

    app = QApplication(sys.argv)
    app.setApplicationName("NEYROLOC NEW")
    app.setApplicationDisplayName("NEYROLOC NEW")
    app.setOrganizationName("NEYROLOC")
    app.setWindowIcon(_application_icon())
    # ".AppleSystemUIFont" — системный шрифт macOS (San Francisco). Прежнее
    # "SF Pro Text" не резолвится по имени и сыпало варнингом на каждом старте.
    app_font = QFont(".AppleSystemUIFont", 13)
    app_font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(app_font)
    app.setStyleSheet(APP_QSS)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
