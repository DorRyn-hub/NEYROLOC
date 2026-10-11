"""Unified dark visual language for NEYROLOC.

The stylesheet deliberately stays within QSS capabilities: contrast, spacing,
states and restrained borders do most of the work instead of relying on CSS
effects Qt does not implement.
"""

COLORS = {
    "window": "#0d111a",
    "sidebar": "#111723",
    "surface": "#171e2b",
    "surface_alt": "#141b27",
    "control": "#1b2433",
    "control_hover": "#222e40",
    "control_pressed": "#29384d",
    "separator": "#2b3749",
    "separator_soft": "#202b3a",
    "text": "#eef3fa",
    "text_secondary": "#a6b3c5",
    "text_muted": "#718097",
    "accent": "#6d8cff",
    "accent_hover": "#829dff",
    "accent_soft": "#263657",
    "assistant": "#171f2d",
    "user": "#526fd1",
    "success": "#4ed39a",
    "danger": "#ff7184",
}


APP_QSS = f"""
* {{
    font-family: ".AppleSystemUIFont", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: {COLORS["text"]};
}}

QMainWindow, QWidget#central {{
    background: {COLORS["window"]};
}}

QWidget#sidebar {{
    background: {COLORS["sidebar"]};
    border-right: 1px solid {COLORS["separator"]};
}}

QScrollArea#sidebarScroll {{
    background: {COLORS["sidebar"]};
    border: none;
}}

QLabel#sidebarTitle {{
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 1px;
    color: {COLORS["text"]};
}}

QLabel#sidebarSubtitle {{
    color: {COLORS["text_muted"]};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
}}

QLabel#brandMark {{
    color: #ffffff;
    background: {COLORS["accent"]};
    border-radius: 9px;
    font-size: 15px;
    font-weight: 800;
    padding: 4px 7px;
}}

QLabel#sidebarSection {{
    color: {COLORS["text_muted"]};
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 8px 3px 3px 3px;
}}

QLabel#backendGroupLabel {{
    color: {COLORS["text_muted"]};
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 4px 4px 2px 4px;
}}

QLabel#fieldLabel {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
}}

QLabel#temperatureValue {{
    color: {COLORS["text"]};
    background: {COLORS["accent_soft"]};
    border-radius: 6px;
    font-weight: 700;
    min-width: 42px;
    padding: 4px 6px;
}}

QLabel#hint {{
    color: {COLORS["text_muted"]};
    font-size: 11px;
}}

QFrame#sidebarPanel {{
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["separator_soft"]};
    border-radius: 11px;
}}

QPushButton {{
    min-height: 28px;
    background: {COLORS["control"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 7px;
    padding: 5px 11px;
    color: {COLORS["text"]};
}}

QPushButton:hover {{
    background: {COLORS["control_hover"]};
    border-color: #40506a;
}}

QPushButton:pressed {{
    background: {COLORS["control_pressed"]};
}}

QPushButton:disabled {{
    color: {COLORS["text_muted"]};
    background: #151c28;
    border-color: {COLORS["separator_soft"]};
}}

QPushButton#primary {{
    min-height: 32px;
    background: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
    color: #ffffff;
    font-weight: 700;
}}

QPushButton#primary:hover {{
    background: {COLORS["accent_hover"]};
    border-color: {COLORS["accent_hover"]};
}}

QPushButton#primary:disabled {{
    background: #273450;
    border-color: #273450;
    color: #7786a5;
}}

QPushButton#quietAction {{
    background: transparent;
    border-color: {COLORS["separator"]};
    color: {COLORS["text_secondary"]};
    padding-left: 8px;
    padding-right: 8px;
}}

QPushButton#quietAction:hover {{
    color: {COLORS["text"]};
    background: {COLORS["control_hover"]};
}}

QPushButton#backendItem {{
    text-align: left;
    min-height: 44px;
    padding: 0;
    background: transparent;
    border: none;
}}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background: {COLORS["control"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 7px;
    padding: 7px 9px;
    selection-background-color: {COLORS["accent"]};
    selection-color: #ffffff;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {COLORS["accent"]};
}}

QPlainTextEdit {{
    line-height: 18px;
}}

QFrame#composer {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 14px;
}}

QComboBox::drop-down {{
    border: none;
    width: 26px;
}}

QComboBox QAbstractItemView {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 7px;
    padding: 4px;
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: {COLORS["text"]};
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {COLORS["separator"]};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS["accent"]};
    border-radius: 2px;
}}

QSlider::add-page:horizontal {{
    background: {COLORS["separator"]};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    width: 14px;
    margin: -5px 0;
    background: #ffffff;
    border: 2px solid {COLORS["accent"]};
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS["accent_hover"]};
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 9px;
    margin: 4px 1px;
}}

QScrollBar::handle:vertical {{
    background: #344258;
    border-radius: 4px;
    min-height: 34px;
}}

QScrollBar::handle:vertical:hover {{
    background: #4b5c76;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
}}

QStatusBar {{
    background: {COLORS["surface_alt"]};
    border-top: 1px solid {COLORS["separator"]};
    color: {COLORS["text_secondary"]};
    min-height: 28px;
    padding-left: 10px;
}}

QStatusBar::item {{
    border: none;
}}

QStatusBar QLabel {{
    color: {COLORS["text_secondary"]};
}}

QSplitter::handle {{
    background: {COLORS["separator_soft"]};
    width: 1px;
}}

QFrame#chatBubbleUser {{
    background: {COLORS["user"]};
    border-radius: 13px;
}}

QFrame#chatBubbleUser QLabel#bubbleRole,
QFrame#chatBubbleUser QLabel#bubbleText {{
    color: #ffffff;
}}

QFrame#chatBubbleAssistant {{
    background: {COLORS["assistant"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 13px;
}}

QLabel#bubbleRole {{
    font-size: 11px;
    font-weight: 700;
    color: {COLORS["text_muted"]};
}}

QLabel#bubbleText {{
    font-size: 13px;
    color: {COLORS["text"]};
}}

QLabel#remoteUrl {{
    font-size: 17px;
    font-weight: 700;
    color: {COLORS["accent"]};
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 9px;
    padding: 10px 14px;
}}

QLabel#remotePairCode {{
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 6px;
    color: {COLORS["text"]};
}}

QFrame#codeBlock {{
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 9px;
}}

QFrame#codeBlockHeader {{
    background: {COLORS["control"]};
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    border-bottom: 1px solid {COLORS["separator"]};
}}

QLabel#codeBlockLang {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
    color: {COLORS["text_secondary"]};
}}

QPushButton#codeBlockCopy {{
    background: transparent;
    border: none;
    color: {COLORS["text_muted"]};
    font-size: 11px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 5px;
}}

QPushButton#codeBlockCopy:hover {{
    background: {COLORS["control_hover"]};
    color: {COLORS["text"]};
}}

QPushButton#codeBlockCopy:pressed {{
    background: {COLORS["control_pressed"]};
}}

QTextEdit#codeBlockBody {{
    background: transparent;
    border: none;
    padding: 8px 10px;
    selection-background-color: {COLORS["accent_soft"]};
}}

QTabWidget#modelLibraryTabs::pane {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 11px;
}}

QTabBar::tab {{
    background: transparent;
    border: none;
    padding: 9px 15px;
    color: {COLORS["text_muted"]};
}}

QTabBar::tab:hover {{
    color: {COLORS["text_secondary"]};
}}

QTabBar::tab:selected {{
    color: {COLORS["text"]};
    font-weight: 700;
    border-bottom: 2px solid {COLORS["accent"]};
}}

QFrame#downloadPanel {{
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["accent_soft"]};
    border-radius: 10px;
}}

QLabel#downloadSpinner {{
    color: {COLORS["accent"]};
    font-size: 15px;
    font-weight: 700;
}}

QLabel#downloadStatusText {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
}}

QProgressBar#downloadProgress {{
    background: {COLORS["control"]};
    border: none;
    border-radius: 8px;
    text-align: center;
    color: {COLORS["text"]};
    font-size: 10px;
    font-weight: 700;
}}

QProgressBar#downloadProgress::chunk {{
    background: {COLORS["accent"]};
    border-radius: 8px;
}}

QTableWidget {{
    background: {COLORS["surface"]};
    alternate-background-color: {COLORS["surface_alt"]};
    border: none;
    gridline-color: {COLORS["separator_soft"]};
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: {COLORS["text"]};
    outline: none;
}}

QTableWidget::item {{
    padding: 5px 7px;
    border-bottom: 1px solid {COLORS["separator_soft"]};
}}

QHeaderView::section {{
    background: {COLORS["surface_alt"]};
    border: none;
    border-bottom: 1px solid {COLORS["separator"]};
    padding: 8px;
    color: {COLORS["text_secondary"]};
    font-weight: 700;
}}

QDialog {{
    background: {COLORS["window"]};
}}

QDialogButtonBox QPushButton {{
    min-width: 80px;
}}
"""
