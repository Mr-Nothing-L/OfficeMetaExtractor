"""Modern dark theme QSS for OfficeMetaExtractor."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Modern dark color palette with gold accents."""

    # Backgrounds
    BG_PRIMARY = "#1e1e1e"
    BG_SECONDARY = "#252526"
    BG_CARD = "#2d2d30"
    BG_CARD_HOVER = "#333337"
    BG_INPUT = "#3c3c3c"
    BG_TABLE = "#1e1e1e"
    BG_TABLE_ALT = "#252526"

    # Gold accents
    GOLD = "#c9a227"
    GOLD_BRIGHT = "#ffd700"
    GOLD_DIM = "#a08030"
    GOLD_DARK = "#8a6d1f"
    GOLD_GLOW = "rgba(201, 162, 39, 0.25)"

    # Text
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_MUTED = "#808080"
    TEXT_DISABLED = "#555555"
    TEXT_WHITE = "#ffffff"

    # Accents / semantic
    BORDER = "#3c3c3c"
    BORDER_FOCUS = "#c9a227"
    BUTTON_BG = "#2d2d30"
    BUTTON_BG_HOVER = "#3c3c3c"
    PROGRESS_CHUNK = "#c9a227"
    SELECTION_BG = "rgba(201, 162, 39, 0.20)"
    HEADER_FILL = "#c9a227"

    # Status
    SUCCESS = "#66CC66"
    ERROR = "#FF6B6B"
    WARNING = "#FFCC00"

    # Risk levels
    RISK_CRITICAL = "#FF0000"
    RISK_HIGH = "#FF6600"
    RISK_MEDIUM = "#FFCC00"
    RISK_LOW = "#66CC66"

    # Excel export colors (openpyxl expects hex without #)
    EXCEL_HEADER_FILL = "c9a227"
    EXCEL_HEADER_FONT = "ffffff"
    EXCEL_ERROR_FONT = "FF6B6B"
    EXCEL_RISK_CRITICAL = "FF0000"
    EXCEL_RISK_HIGH = "FF6600"
    EXCEL_RISK_MEDIUM = "FFCC00"
    EXCEL_RISK_LOW = "66CC66"


DARK_STYLE = f"""
/* Main Window */
QMainWindow {{
    background-color: {Theme.BG_PRIMARY};
    color: {Theme.TEXT_PRIMARY};
}}

QWidget {{
    background-color: {Theme.BG_PRIMARY};
    color: {Theme.TEXT_PRIMARY};
}}

/* Card-style containers */
#cardContainer {{
    background-color: {Theme.BG_CARD};
    border: 1px solid {Theme.BORDER};
    border-radius: 8px;
    padding: 12px;
}}

#cardContainer:hover {{
    border-color: {Theme.GOLD_DIM};
}}

/* Drop Area */
DropArea {{
    background-color: {Theme.BG_CARD};
    border: 2px dashed {Theme.BORDER};
    border-radius: 10px;
    color: {Theme.TEXT_MUTED};
    font-size: 14px;
    padding: 16px;
}}
DropArea:hover {{
    border-color: {Theme.GOLD_DIM};
    background-color: {Theme.BG_CARD_HOVER};
}}
DropArea[dragOver="true"] {{
    border-color: {Theme.GOLD_BRIGHT};
    background-color: {Theme.SELECTION_BG};
}}

#dropIcon {{
    font-size: 48px;
    color: {Theme.GOLD_DIM};
    background-color: transparent;
}}

/* Table */
QTableWidget {{
    background-color: {Theme.BG_TABLE};
    border: 1px solid {Theme.BORDER};
    border-radius: 8px;
    gridline-color: {Theme.BORDER};
    color: {Theme.TEXT_PRIMARY};
    selection-background-color: {Theme.SELECTION_BG};
    selection-color: {Theme.GOLD_BRIGHT};
    alternate-background-color: {Theme.BG_TABLE_ALT};
    padding: 4px;
}}
QTableWidget::item {{
    padding: 6px 8px;
    border-radius: 3px;
}}
QTableWidget::item:selected {{
    background-color: {Theme.SELECTION_BG};
    color: {Theme.GOLD_BRIGHT};
}}
QTableWidget::item:hover {{
    background-color: {Theme.BG_CARD_HOVER};
}}
QHeaderView::section {{
    background-color: {Theme.BG_CARD};
    color: {Theme.GOLD};
    padding: 8px 10px;
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    font-weight: bold;
    font-size: 13px;
}}
QHeaderView::section:hover {{
    background-color: {Theme.BG_CARD_HOVER};
    color: {Theme.GOLD_BRIGHT};
}}

/* Scrollbar */
QScrollBar:vertical {{
    background-color: {Theme.BG_PRIMARY};
    width: 10px;
    border-radius: 5px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {Theme.GOLD_DARK};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {Theme.GOLD};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background-color: {Theme.BG_PRIMARY};
    height: 10px;
    border-radius: 5px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {Theme.GOLD_DARK};
    border-radius: 5px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {Theme.GOLD};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Buttons */
QPushButton {{
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {Theme.BG_CARD_HOVER},
        stop:1 {Theme.BUTTON_BG}
    );
    color: {Theme.GOLD};
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 13px;
    border: 1px solid {Theme.GOLD_DARK};
    min-height: 30px;
}}
QPushButton:hover {{
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {Theme.BG_INPUT},
        stop:1 {Theme.BUTTON_BG_HOVER}
    );
    border: 1px solid {Theme.GOLD};
    color: {Theme.GOLD_BRIGHT};
}}
QPushButton:pressed {{
    background-color: {Theme.SELECTION_BG};
    border: 1px solid {Theme.GOLD_BRIGHT};
    padding-top: 8px;
    padding-bottom: 6px;
}}
QPushButton:disabled {{
    background-color: {Theme.BG_SECONDARY};
    color: {Theme.TEXT_DISABLED};
    border-color: {Theme.BORDER};
}}
QPushButton#secondary {{
    background-color: {Theme.BG_CARD};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
}}
QPushButton#secondary:hover {{
    background-color: {Theme.BG_CARD_HOVER};
    border-color: {Theme.GOLD_DIM};
    color: {Theme.GOLD_BRIGHT};
}}
QPushButton#secondary:pressed {{
    background-color: {Theme.SELECTION_BG};
}}
QPushButton#danger {{
    background-color: #5a1a1a;
    color: {Theme.TEXT_WHITE};
    border-color: #8a2a2a;
}}
QPushButton#danger:hover {{
    background-color: #7a2a2a;
    border-color: #aa3a3a;
}}

/* Progress Bar */
QProgressBar {{
    border: 1px solid {Theme.BORDER};
    border-radius: 6px;
    text-align: center;
    background-color: {Theme.BG_TABLE};
    color: {Theme.TEXT_PRIMARY};
    height: 22px;
    font-size: 12px;
}}
QProgressBar::chunk {{
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {Theme.GOLD_DARK},
        stop:0.5 {Theme.GOLD},
        stop:1 {Theme.GOLD_BRIGHT}
    );
    border-radius: 5px;
    margin: 1px;
}}

/* Labels */
QLabel {{
    color: {Theme.TEXT_PRIMARY};
    font-size: 13px;
    background-color: transparent;
}}
QLabel#title {{
    font-size: 18px;
    font-weight: bold;
    color: {Theme.GOLD_BRIGHT};
    letter-spacing: 1px;
}}
QLabel#subtitle {{
    font-size: 12px;
    color: {Theme.TEXT_MUTED};
}}
QLabel#status {{
    font-size: 12px;
    color: {Theme.TEXT_SECONDARY};
    padding: 4px 8px;
    background-color: {Theme.BG_CARD};
    border-radius: 4px;
}}
QLabel#dragHint {{
    font-size: 14px;
    color: {Theme.TEXT_SECONDARY};
    background-color: transparent;
}}
QLabel#success {{
    color: {Theme.SUCCESS};
}}
QLabel#error {{
    color: {Theme.ERROR};
}}
QLabel#modeLabel {{
    font-size: 13px;
    color: {Theme.TEXT_SECONDARY};
    font-weight: bold;
}}
QLabel#fileCount {{
    font-size: 13px;
    color: {Theme.GOLD};
    font-weight: bold;
    padding: 4px 10px;
    background-color: {Theme.BG_CARD};
    border-radius: 4px;
    border: 1px solid {Theme.GOLD_DARK};
}}

/* Status Bar */
QStatusBar {{
    background-color: {Theme.BG_CARD};
    color: {Theme.GOLD};
    font-size: 12px;
    border-top: 1px solid {Theme.BORDER};
    padding: 4px 8px;
}}
QStatusBar::item {{
    border: none;
}}

/* Menu */
QMenuBar {{
    background-color: {Theme.BG_PRIMARY};
    color: {Theme.TEXT_PRIMARY};
    border-bottom: 1px solid {Theme.BORDER};
    padding: 2px 4px;
}}
QMenuBar::item {{
    background-color: transparent;
    padding: 4px 12px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: {Theme.SELECTION_BG};
    color: {Theme.GOLD_BRIGHT};
}}
QMenu {{
    background-color: {Theme.BG_CARD};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {Theme.SELECTION_BG};
    color: {Theme.GOLD_BRIGHT};
}}
QMenu::separator {{
    height: 1px;
    background-color: {Theme.BORDER};
    margin: 4px 8px;
}}

#overlayContainer {{
    background-color: rgba(30, 30, 30, 235);
    border: none;
}}

/* Dialog / Inputs */
QDialog {{
    background-color: {Theme.BG_PRIMARY};
}}
QLineEdit {{
    background-color: {Theme.BG_INPUT};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {Theme.GOLD};
    background-color: {Theme.BG_CARD};
}}
QComboBox {{
    background-color: {Theme.BG_INPUT};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    min-height: 18px;
}}
QComboBox:focus {{
    border-color: {Theme.GOLD};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {Theme.BG_CARD};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: 6px;
    selection-background-color: {Theme.SELECTION_BG};
    padding: 4px;
}}
QGroupBox {{
    color: {Theme.GOLD};
    border: 1px solid {Theme.BORDER};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
}}
QSplitter::handle {{
    background-color: {Theme.BORDER};
    border-radius: 2px;
}}
QSplitter::handle:horizontal {{
    width: 4px;
    margin: 2px 0;
}}
QSplitter::handle:vertical {{
    height: 4px;
    margin: 0 2px;
}}
"""
