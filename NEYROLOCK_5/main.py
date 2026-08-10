#!/usr/bin/env python3
"""NEYROLOCK v5 — точка входа."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import APP_QSS


def _application_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#6d8cff"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(2, 2, 60, 60, 17, 17)
    painter.setPen(QColor("#ffffff"))
    painter.setFont(QFont("Arial", 31, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "N")
    painter.end()
    return QIcon(pixmap)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("NEYROLOC NEW")
    app.setApplicationDisplayName("NEYROLOC NEW")
    app.setOrganizationName("NEYROLOCK")
    app.setWindowIcon(_application_icon())
    app_font = QFont("SF Pro Text", 10)
    app_font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(app_font)
    app.setStyleSheet(APP_QSS)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
