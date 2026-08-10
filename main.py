#!/usr/bin/env python3
"""Stable project launcher for the active NEYROLOC desktop application.

The Qt/UI imports intentionally stay inside :func:`main`.  This keeps simple
operations such as importing the launcher, running diagnostics, or discovering
tests independent from a display server and from optional model dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "NEYROLOC NEW"
APP_DIR = Path(__file__).resolve().parent / "NEYROLOCK_5"


def _activate_app_path() -> Path:
    """Make the active application package importable from any working directory."""
    # Nuitka embeds the active modules in the executable; a standalone bundle
    # deliberately has no source checkout beside it.
    if "__compiled__" in globals():
        return APP_DIR
    if not (APP_DIR / "ui").is_dir():
        raise RuntimeError(f"Каталог активного приложения не найден: {APP_DIR}")
    app_path = str(APP_DIR)
    if app_path not in sys.path:
        sys.path.insert(0, app_path)
    return APP_DIR


def _application_icon():
    """Create a small crisp app mark without requiring an external asset."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

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
    _activate_app_path()

    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    from ui.macos_appname import set_app_name
    from ui.main_window import MainWindow
    from ui.styles import APP_QSS

    # Должно быть до создания QApplication: AppKit читает CFBundleName при
    # инициализации NSApplication, чтобы назвать меню приложения.
    set_app_name(APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
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
