"""Graphite UI tokens and a single QSS cascade for the desktop workspace.

Polish follows Unslop by Damir Sokolovsky (CC BY 4.0).
See docs/INTERFACE_POLISH.md for attribution and design decisions.
"""

COLORS = {
    "window": "#242424",
    "sidebar": "#2c2c2b",
    "surface": "#30302f",
    "surface_alt": "#292928",
    "control": "#393938",
    "control_hover": "#444441",
    "control_pressed": "#4b4b48",
    "separator": "#414140",
    "separator_soft": "#363635",
    "text": "#f3f2f0",
    "text_secondary": "#b4b3b0",
    "text_muted": "#a3a39e",
    "accent": "#368bff",
    "accent_hover": "#63a6ff",
    "accent_soft": "#34455f",
    "assistant": "#242424",
    "user": "#393d44",
    "success": "#63c796",
    "danger": "#ff7c8b",
    "primary_ink": "#151515",
    "composer": "#323231",
    "composer_border": "#52524e",
}


APP_QSS = f"""
* {{
    font-family: "Onest", ".AppleSystemUIFont", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: {COLORS["text"]};
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
    font-weight: 600;
    color: {COLORS["text"]};
}}

QLabel#sidebarSubtitle {{
    color: {COLORS["text_muted"]};
    font-size: 11px;
    font-weight: 600;
}}

QLabel#brandMark {{
    color: #ffffff;
    background: {COLORS["accent"]};
    border-radius: 9px;
    font-size: 15px;
    font-weight: 600;
    padding: 4px 7px;
}}

QLabel#backendGroupLabel {{
    color: {COLORS["text_muted"]};
    font-size: 12px;
    font-weight: 600;
    padding: 4px 4px 2px 4px;
}}

QLabel#fieldLabel {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
}}

QLabel#temperatureValue {{
    color: {COLORS["text"]};
    background: {COLORS["control"]};
    border-radius: 6px;
    font-weight: 400;
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

QPushButton#backendItem {{
    text-align: left;
    min-height: 44px;
    padding: 0;
    background: transparent;
    border: none;
}}

QTextEdit {{
    background: {COLORS["control"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 7px;
    padding: 7px 9px;
    selection-background-color: {COLORS["accent"]};
    selection-color: #ffffff;
}}

QTextEdit:focus {{
    border: 1px solid {COLORS["accent"]};
}}

QDoubleSpinBox:focus {{
    border: 1px solid {COLORS["accent"]};
}}

QSpinBox:focus {{
    border: 1px solid {COLORS["accent"]};
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

QScrollBar::add-line:vertical {{
    height: 0;
    background: transparent;
}}

QScrollBar::sub-line:vertical {{
    height: 0;
    background: transparent;
}}

QScrollBar::add-page:vertical {{
    height: 0;
    background: transparent;
}}

QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
}}

QStatusBar::item {{
    border: none;
}}

QSplitter::handle {{
    background: {COLORS["separator_soft"]};
    width: 1px;
}}

QFrame#chatBubbleUser QLabel#bubbleRole {{
    color: #ffffff;
}}

QFrame#chatBubbleUser QLabel#bubbleText {{
    color: #ffffff;
}}

QLabel#remoteUrl {{
    font-size: 17px;
    font-weight: 600;
    color: {COLORS["accent"]};
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["separator"]};
    border-radius: 9px;
    padding: 10px 14px;
}}

QLabel#remotePairCode {{
    font-size: 21px;
    font-weight: 600;
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
    font-weight: 600;
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

QTabBar::tab:hover {{
    color: {COLORS["text_secondary"]};
}}

QLabel#downloadSpinner {{
    color: {COLORS["accent"]};
    font-size: 15px;
    font-weight: 600;
}}

QLabel#downloadStatusText {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
}}

QDialog {{
    background: {COLORS["window"]};
}}

QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

QWidget {{
    background: transparent;
}}

QMainWindow {{
    background: {COLORS["window"]};
}}

QWidget#central {{
    background: {COLORS["window"]};
}}

QFrame#workspaceNav {{
    background: {COLORS["sidebar"]};
    border-radius: 18px;
}}

QScrollArea#workspaceNavScroll {{
    background: transparent;
    border: none;
}}

QScrollArea#parameterScroll {{
    background: transparent;
    border: none;
}}

QScrollArea#settingsScroll {{
    background: transparent;
    border: none;
}}

QScrollArea#chatScroll {{
    background: transparent;
    border: none;
}}

QLabel#workspaceTitle {{
    font-size: 19px;
    font-weight: 600;
}}

QLabel#brandSubtitle {{
    font-size: 11px;
    color: {COLORS["text_muted"]};
}}

QPushButton#navItem {{
    background: transparent;
    border: none;
    border-radius: 9px;
    text-align: left;
    padding: 6px 10px;
    color: {COLORS["text_secondary"]};
    min-height: 24px;
}}

QPushButton#navItem:hover {{
    background: #3a3a38;
    color: {COLORS["text"]};
}}

QPushButton#navItem:checked {{
    background: {COLORS["control"]};
    color: {COLORS["text"]};
}}

QPushButton#currentChat {{
    text-align: left;
    border: none;
    background: {COLORS["control"]};
    border-radius: 8px;
    font-size: 12px;
    padding: 6px 10px;
}}

QPushButton#sessionItem {{
    text-align: left;
    border: none;
    background: transparent;
    border-radius: 8px;
    font-size: 12px;
    padding: 6px 10px;
    color: {COLORS["text_secondary"]};
}}

QPushButton#sessionItem:hover {{
    background: #3a3a38;
    color: {COLORS["text"]};
}}

QLabel#sidebarSection {{
    color: {COLORS["text_secondary"]};
    font-size: 12px;
    font-weight: 400;
    padding: 4px 0;
}}

QLineEdit#searchInput {{
    background: {COLORS["control"]};
    border: none;
    border-radius: 8px;
    min-height: 24px;
    padding: 5px;
}}

QLabel#pageTitle {{
    font-size: 23px;
    font-weight: 600;
}}

QLabel#pageSubtitle {{
    font-size: 12px;
    color: {COLORS["text_secondary"]};
}}

QFrame#pageHeader {{
    border-bottom: 1px solid {COLORS["separator_soft"]};
}}

QLabel#panelTitle {{
    font-size: 14px;
    font-weight: 600;
}}

QFrame#settingsCard {{
    background: {COLORS["surface"]};
    border: none;
    border-radius: 16px;
}}

QWidget#parameterPanel {{
    background: {COLORS["surface"]};
    border: none;
    border-radius: 16px;
}}

QLabel#modelStatus {{
    font-size: 11px;
    font-weight: 600;
    color: {COLORS["text_secondary"]};
}}

QLabel#modelStatus[ready="true"] {{
    color: {COLORS["success"]};
}}

QLabel#modelCaption {{
    font-size: 11px;
    color: {COLORS["text_muted"]};
}}

QPushButton {{
    min-height: 26px;
    background: {COLORS["control"]};
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
    color: {COLORS["text"]};
}}

QPushButton:hover {{
    background: #454542;
    border-color: {COLORS["separator"]};
}}

QPushButton:pressed {{
    background: {COLORS["control_pressed"]};
}}

QPushButton:disabled {{
    color: {COLORS["text_muted"]};
    background: {COLORS["surface"]};
    border-color: {COLORS["separator_soft"]};
}}

QPushButton#quietAction {{
    background: transparent;
    border-color: {COLORS["separator"]};
    color: {COLORS["text_secondary"]};
    padding-left: 8px;
    padding-right: 8px;
    border: 1px solid {COLORS["separator"]};
}}

QPushButton#quietAction:hover {{
    color: {COLORS["text"]};
    background: #3b3b38;
}}

QPushButton#primary {{
    min-height: 32px;
    background: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
    color: {COLORS["primary_ink"]};
    font-weight: 600;
    border: none;
}}

QPushButton#primary:hover {{
    background: {COLORS["accent_hover"]};
    border-color: {COLORS["accent_hover"]};
    color: {COLORS["primary_ink"]};
}}

QPushButton#primary:disabled {{
    background: {COLORS["surface"]};
    border-color: {COLORS["separator_soft"]};
    color: {COLORS["text_muted"]};
}}

QLineEdit {{
    background: {COLORS["control"]};
    border: 1px solid #454542;
    border-radius: 9px;
    padding: 8px 10px;
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: #ffffff;
}}

QPlainTextEdit {{
    background: {COLORS["control"]};
    border: 1px solid #454542;
    border-radius: 9px;
    padding: 8px 10px;
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: #ffffff;
    line-height: 18px;
}}

QComboBox {{
    background: {COLORS["control"]};
    border: 1px solid #454542;
    border-radius: 9px;
    padding: 8px 10px;
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: #ffffff;
}}

QDoubleSpinBox {{
    background: {COLORS["control"]};
    border: 1px solid #454542;
    border-radius: 9px;
    padding: 8px 10px;
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: #ffffff;
}}

QSpinBox {{
    background: {COLORS["control"]};
    border: 1px solid #454542;
    border-radius: 9px;
    padding: 8px 10px;
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: #ffffff;
}}

QLineEdit:focus {{
    border: 1px solid {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

QPlainTextEdit:focus {{
    border: 1px solid {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

QComboBox:focus {{
    border: 1px solid {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

QFrame#chatBubbleAssistant {{
    background: transparent;
    border: none;
    border-radius: 0;
}}

QFrame#chatBubbleUser {{
    background: {COLORS["user"]};
    border-radius: 16px;
}}

QLabel#bubbleText {{
    font-size: 14px;
    color: {COLORS["text"]};
}}

QLabel#bubbleRole {{
    font-size: 11px;
    font-weight: 600;
    color: {COLORS["text_secondary"]};
    padding-bottom: 6px;
}}

QPushButton#bubbleAction {{
    background: transparent;
    border: none;
    color: {COLORS["text_muted"]};
    padding: 3px 6px;
    font-size: 11px;
    min-height: 20px;
}}

QPushButton#bubbleAction:hover {{
    color: {COLORS["text"]};
    background: {COLORS["surface"]};
}}

QFrame#composer {{
    background: {COLORS["composer"]};
    border: 1px solid {COLORS["composer_border"]};
    border-radius: 16px;
}}

QPlainTextEdit#chatInput {{
    background: transparent;
    border: none;
    padding: 2px;
    font-size: 14px;
}}

QLabel#composerModel {{
    color: {COLORS["text_secondary"]};
    background: transparent;
    border-radius: 7px;
    padding: 4px 0;
    font-size: 11px;
}}

QLabel#emptyTitle {{
    font-size: 28px;
    font-weight: 600;
}}

QLabel#emptySubtitle {{
    font-size: 13px;
    color: {COLORS["text_secondary"]};
}}

QPushButton#sendButton {{
    background: {COLORS["accent"]};
    border-radius: 11px;
    padding: 0;
    min-height: 36px;
    min-width: 36px;
    max-width: 36px;
    color: {COLORS["primary_ink"]};
}}

QPushButton#sendButton:hover {{
    background: {COLORS["accent_hover"]};
    color: {COLORS["primary_ink"]};
}}

QPushButton#sendButton:disabled {{
    background: {COLORS["control"]};
}}

QPushButton#stopButton {{
    background: #594046;
    border-radius: 11px;
}}

QStatusBar {{
    background: transparent;
    border-top: 1px solid {COLORS["separator"]};
    color: {COLORS["text_secondary"]};
    min-height: 23px;
    padding-left: 10px;
    border: none;
    font-size: 11px;
}}

QStatusBar QLabel {{
    color: {COLORS["text_secondary"]};
    font-size: 11px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 7px;
    margin: 3px;
}}

QScrollBar::handle:vertical {{
    background: #51514d;
    border-radius: 3px;
    min-height: 32px;
}}

QScrollBar::handle:vertical:hover {{
    background: #6c6c66;
}}

QTabWidget#modelLibraryTabs::pane {{
    background: transparent;
    border: none;
    border-radius: 11px;
}}

QTabBar::tab {{
    background: {COLORS["surface"]};
    border: none;
    padding: 9px 15px;
    color: {COLORS["text_muted"]};
    border-radius: 8px;
    margin-right: 5px;
}}

QTabBar::tab:selected {{
    color: {COLORS["text"]};
    font-weight: 600;
    border-bottom: 2px solid {COLORS["accent"]};
    background: #494946;
    border: none;
}}

QTableWidget {{
    background: {COLORS["surface"]};
    alternate-background-color: {COLORS["surface"]};
    border: none;
    gridline-color: {COLORS["separator_soft"]};
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: {COLORS["text"]};
    outline: none;
    border-radius: 14px;
}}

QHeaderView::section {{
    background: {COLORS["surface"]};
    border: none;
    border-bottom: 1px solid {COLORS["separator"]};
    padding: 12px;
    color: {COLORS["text_muted"]};
    font-weight: 600;
    font-size: 11px;
}}

QTableWidget::item {{
    padding: 12px;
    border-bottom: 1px solid {COLORS["separator"]};
}}

QFrame#downloadPanel {{
    background: {COLORS["surface"]};
    border: none;
    border-radius: 14px;
}}

QProgressBar#downloadProgress {{
    background: #484843;
    border: none;
    border-radius: 5px;
    text-align: center;
    color: {COLORS["text"]};
    font-size: 11px;
    font-weight: 600;
}}

QProgressBar#downloadProgress::chunk {{
    background: {COLORS["accent"]};
    border-radius: 5px;
}}

QFrame#modelCard {{
    background: {COLORS["surface"]};
    border: 1px solid #3b3b38;
    border-radius: 16px;
}}

QFrame#modelCard:hover {{
    border-color: {COLORS["composer_border"]};
}}

QLabel#modelCardTitle {{
    font-size: 14px;
    font-weight: 600;
}}

QLabel#modelGlyph {{
    background: {COLORS["control"]};
    border-radius: 10px;
    padding: 8px;
}}

QPushButton:focus {{
    border: 1px solid {COLORS["accent"]};
}}

QTabBar::tab:focus {{
    border: 1px solid {COLORS["accent"]};
}}

"""
