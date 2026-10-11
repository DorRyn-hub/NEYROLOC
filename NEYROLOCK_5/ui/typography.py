"""Единая типографика desktop-приложения NEYROLOC."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

FONT_FAMILY = "Onest"
FONT_WEIGHT_REGULAR = QFont.Weight.Normal
FONT_WEIGHT_BOLD = QFont.Weight.Bold

FONT_DIR = Path(__file__).resolve().parents[1] / "resources" / "fonts"
REGULAR_FONT_PATH = FONT_DIR / "Onest-Regular.ttf"
BOLD_FONT_PATH = FONT_DIR / "Onest-Bold.ttf"
_REQUIRED_FONT_PATHS = (REGULAR_FONT_PATH, BOLD_FONT_PATH)
_registered_font_ids: tuple[int, ...] = ()


def bundled_font_paths() -> tuple[Path, ...]:
    """Вернуть все поставляемые desktop-шрифты в стабильном порядке."""

    return tuple(path for path in _REQUIRED_FONT_PATHS if path.is_file())


def register_application_fonts() -> bool:
    """Зарегистрировать Onest Regular 400 и Bold 700 в Qt.

    Loader намеренно строгий: неполный или неверно размеченный комплект не
    должен незаметно заменяться системным шрифтом в собранном приложении.
    """

    global _registered_font_ids

    if not _registered_font_ids:
        missing = [path.name for path in _REQUIRED_FONT_PATHS if not path.is_file()]
        if missing:
            raise RuntimeError(
                "Не найдены обязательные файлы Onest: " + ", ".join(missing)
            )

        registered: list[int] = []
        for path in _REQUIRED_FONT_PATHS:
            font_id = QFontDatabase.addApplicationFont(str(path))
            families = (
                QFontDatabase.applicationFontFamilies(font_id)
                if font_id >= 0
                else []
            )
            if font_id < 0 or FONT_FAMILY not in families:
                if font_id >= 0:
                    QFontDatabase.removeApplicationFont(font_id)
                for registered_id in registered:
                    QFontDatabase.removeApplicationFont(registered_id)
                raise RuntimeError(
                    f"Qt не распознал {path.name} как семейство {FONT_FAMILY}."
                )
            registered.append(font_id)
        _registered_font_ids = tuple(registered)

    styles = set(QFontDatabase.styles(FONT_FAMILY))
    required_styles = {"Regular", "Bold"}
    missing_styles = required_styles - styles
    regular = QFontDatabase.font(FONT_FAMILY, "Regular", 13)
    bold = QFontDatabase.font(FONT_FAMILY, "Bold", 13)
    if missing_styles or int(regular.weight()) != 400 or int(bold.weight()) != 700:
        details = ", ".join(sorted(missing_styles)) or "неверные веса"
        raise RuntimeError(
            f"Комплект Onest не содержит корректные Regular 400/Bold 700: {details}."
        )
    return True


def app_font(
    point_size: int = 13,
    weight: QFont.Weight = FONT_WEIGHT_REGULAR,
) -> QFont:
    """Создать QFont из единственного разрешённого UI-семейства."""

    font = QFont(FONT_FAMILY, point_size)
    font.setWeight(weight)
    return font


def apply_application_typography(app: QApplication, point_size: int = 13) -> bool:
    """Загрузить bundled fonts и назначить Regular 400 всему приложению."""

    available = register_application_fonts()
    app.setFont(app_font(point_size, FONT_WEIGHT_REGULAR))
    return available
