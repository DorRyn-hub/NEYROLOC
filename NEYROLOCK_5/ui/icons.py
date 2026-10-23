"""Small, themeable SVG icons rendered by Qt (no extra packages)."""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_PATHS = {
    "chat": "M4 4h16v12H9l-5 4V4Z",
    "models": "M4 4h6v6H4ZM14 4h6v6h-6ZM4 14h6v6H4ZM14 14h6v6h-6Z",
    "settings": "M4 6h16M4 12h16M4 18h16M8 3v6M16 9v6M10 15v6",
    "cpu": "M6 6h12v12H6ZM9 9h6v6H9ZM9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4",
    "cloud": "M7 18h11a4 4 0 0 0 0-8 6 6 0 0 0-11-2 5 5 0 0 0 0 10Z",
    "phone": "M8 3h8a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2ZM10 17h4",
    "plus": "M12 5v14M5 12h14",
    "search": "M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13ZM16 16l5 5",
    "send": "M12 19V5M6 11l6-6 6 6",
    "stop": "M6 6h12v12H6Z",
    "download": "M12 3v12M7 10l5 5 5-5M4 17v4h16v-4",
    "folder": "M3 6h7l2 3h9v12H3V6Z",
    "bolt": "M14 2 4 14h7l-1 8 10-12h-7l1-8Z",
    "lock": "M5 11h14v10H5ZM8 11V7a4 4 0 0 1 8 0v4",
    "copy": "M8 8h12v12H8ZM4 15V4h11",
    "refresh": "M20 7v5h-5M20 12a8 8 0 1 0-2 6",
}


def icon(name: str, color: str = "#B4B3B0", size: int = 20) -> QIcon:
    path = _PATHS[name]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
           f'<path d="{path}" fill="none" stroke="{QColor(color).name()}" '
           'stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)
