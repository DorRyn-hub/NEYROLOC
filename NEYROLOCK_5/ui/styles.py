"""Unified dark visual language for NEYROLOC.

The stylesheet deliberately stays within QSS capabilities: contrast, spacing,
states and restrained borders do most of the work instead of relying on CSS
effects Qt does not implement.
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
    "text_muted": "#858581",
    "accent": "#368bff",
    "accent_hover": "#63a6ff",
    "accent_soft": "#34455f",
    "assistant": "#242424",
    "user": "#393d44",
    "success": "#63c796",
    "danger": "#ff7c8b",
}


APP_QSS = f"""
* {{
    font-family: "Onest", ".AppleSystemUIFont", "Helvetica Neue", Arial, sans-serif;
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


# Graphite workspace: neutral surfaces and native, restrained controls.
APP_QSS += """
QWidget { background: transparent; }
QMainWindow, QWidget#central { background: #242424; }
QFrame#workspaceNav { background: #2c2c2b; border-radius: 18px; }
QScrollArea#workspaceNavScroll, QScrollArea#parameterScroll, QScrollArea#settingsScroll,
QScrollArea#chatScroll { background: transparent; border: none; }
QLabel#workspaceTitle { font-size: 19px; font-weight: 700; }
QLabel#brandSubtitle { font-size: 9px; color: #858581; letter-spacing: 1px; }
QPushButton#navItem { background: transparent; border: none; border-radius: 9px;
    text-align: left; padding: 6px 10px; color: #b4b3b0; }
QPushButton#navItem:hover { background: #3a3a38; color: #f3f2f0; }
QPushButton#navItem:checked { background: #34455f; color: #f3f2f0; }
QPushButton#currentChat, QPushButton#sessionItem { text-align: left; border: none;
    background: #393938; border-radius: 8px; font-size: 11px; padding: 6px 10px; }
QPushButton#sessionItem { background: transparent; color: #b4b3b0; }
QPushButton#sessionItem:hover { background: #3a3a38; color: #f3f2f0; }
QLabel#sidebarSection { font-size: 9px; color: #858581; font-weight: 700;
    padding: 3px 2px; letter-spacing: 0.6px; }
QLineEdit#searchInput { background: #393938; border: none; border-radius: 10px;
    min-height: 24px; padding: 5px; }
QLabel#pageTitle { font-size: 23px; font-weight: 700; }
QLabel#pageSubtitle { font-size: 12px; color: #b4b3b0; }
QFrame#pageHeader { border-bottom: 1px solid #363635; }
QLabel#panelTitle { font-size: 14px; font-weight: 700; }
QFrame#settingsCard, QWidget#parameterPanel { background: #30302f; border: none;
    border-radius: 16px; }
QLabel#modelStatus { font-size: 11px; font-weight: 700; color: #b4b3b0; }
QLabel#modelStatus[ready="true"] { color: #63c796; }
QLabel#modelCaption { font-size: 10px; color: #858581; }
QPushButton { border: none; border-radius: 8px; background: #393938;
    min-height: 26px; padding: 6px 12px; }
QPushButton:hover { background: #454542; }
QPushButton:pressed { background: #4b4b48; }
QPushButton:disabled { background: #30302f; color: #858581; }
QPushButton#quietAction { border: 1px solid #414140; background: transparent; }
QPushButton#quietAction:hover { background: #3b3b38; }
QPushButton#primary { background: #368bff; border: none; color: white; }
QPushButton#primary:hover { background: #63a6ff; }
QPushButton#primary:disabled { background: #344158; color: #8495ad; }
QLineEdit, QComboBox, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background: #393938; border: 1px solid #454542; border-radius: 9px;
    padding: 8px 10px; selection-background-color: #34455f; }
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border-color: #368bff; }
QFrame#chatBubbleAssistant { background: transparent; border: none; border-radius: 0; }
QFrame#chatBubbleUser { background: #393d44; border-radius: 16px; }
QLabel#bubbleText { font-size: 14px; }
QLabel#bubbleRole { font-size: 11px; color: #9ca9ba; padding-bottom: 6px; }
QPushButton#bubbleAction { background: transparent; border: none; color: #858581;
    padding: 3px 6px; font-size: 10px; min-height: 20px; }
QPushButton#bubbleAction:hover { color: #f3f2f0; background: #30302f; }
QFrame#composer { background: #323231; border: 1px solid #52524e; border-radius: 18px; }
QPlainTextEdit#chatInput { background: transparent; border: none; padding: 2px; font-size: 14px; }
QLabel#composerModel { color: #b4b3b0; background: #3d3d3a; border-radius: 7px;
    padding: 5px 9px; font-size: 10px; }
QLabel#emptyTitle { font-size: 29px; font-weight: 700; }
QLabel#emptySubtitle { font-size: 13px; color: #b4b3b0; }
QPushButton#sendButton { background: #368bff; border-radius: 11px; padding: 0;
    min-height: 36px; min-width: 36px; max-width: 36px; }
QPushButton#sendButton:hover { background: #63a6ff; }
QPushButton#sendButton:disabled { background: #3e4651; }
QPushButton#stopButton { background: #594046; border-radius: 11px; }
QStatusBar { background: transparent; border: none; min-height: 23px; font-size: 10px; }
QStatusBar QLabel { font-size: 10px; }
QScrollBar:vertical { background: transparent; width: 7px; margin: 3px; }
QScrollBar::handle:vertical { background: #51514d; border-radius: 3px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: #6c6c66; }
QTabWidget#modelLibraryTabs::pane { background: transparent; border: none; }
QTabBar::tab { background: #30302f; border-radius: 8px; padding: 9px 15px; margin-right: 5px; }
QTabBar::tab:selected { background: #494946; color: #f3f2f0; border: none; }
QTableWidget { background: #30302f; alternate-background-color: #30302f; border-radius: 14px; }
QHeaderView::section { background: #30302f; color: #858581; font-size: 11px; padding: 12px; }
QTableWidget::item { padding: 12px; border-bottom: 1px solid #414140; }
QFrame#downloadPanel { background: #30302f; border: none; border-radius: 14px; }
QProgressBar#downloadProgress { background: #484843; border-radius: 5px; }
QProgressBar#downloadProgress::chunk { background: #368bff; border-radius: 5px; }
"""

APP_QSS += """
QFrame#modelCard { background: #30302f; border: 1px solid #3b3b38; border-radius: 15px; }
QFrame#modelCard:hover { border-color: #52524e; }
QLabel#modelCardTitle { font-size: 14px; font-weight: 700; }
QLabel#modelGlyph { background: #3b4149; border-radius: 10px; padding: 8px; }
"""
