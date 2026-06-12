"""Black & Gold theme QSS for OfficeMetaExtractor."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Centralized black & gold color palette."""

    # Backgrounds
    BLACK = "#000000"
    DEEP_BLACK = "#050508"
    PANEL_BG = "#0a0a0a"
    PANEL_BG_ALT = "#111000"
    INPUT_BG = "#151510"
    TABLE_BG = "#0d0d0d"
    TABLE_ALT = "#141412"

    # Golds
    GOLD = "#FFD700"
    GOLD_BRIGHT = "#FFEC8B"
    GOLD_DIM = "#B88C28"
    GOLD_DARK = "#785A14"
    AMBER = "#FFBE3C"
    AMBER_DIM = "#C48A18"

    # Text
    TEXT_PRIMARY = "#FFD700"
    TEXT_MUTED = "#A08030"
    TEXT_DISABLED = "#5a4a20"
    TEXT_WHITE = "#FFFFFF"

    # Accents / semantic
    BORDER = "#5a4a10"
    BORDER_FOCUS = "#FFD700"
    BUTTON_BG = "#1a1403"
    BUTTON_BG_HOVER = "#2a2005"
    PROGRESS_CHUNK = "#B88C28"
    SELECTION_BG = "#3a2e08"
    HEADER_FILL = "#B88C28"

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
    EXCEL_HEADER_FILL = "B88C28"
    EXCEL_HEADER_FONT = "FFFFFF"
    EXCEL_ERROR_FONT = "FF6B6B"
    EXCEL_RISK_CRITICAL = "FF0000"
    EXCEL_RISK_HIGH = "FF6600"
    EXCEL_RISK_MEDIUM = "FFCC00"
    EXCEL_RISK_LOW = "66CC66"


DARK_STYLE = f"""
/* Main Window */
QMainWindow {{
    background-color: {Theme.BLACK};
    color: {Theme.TEXT_PRIMARY};
}}

QWidget {{
    background-color: {Theme.BLACK};
    color: {Theme.TEXT_PRIMARY};
}}

/* Drop Area */
DropArea {{
    background-color: {Theme.PANEL_BG};
    border: 2px dashed {Theme.BORDER};
    border-radius: 8px;
    color: {Theme.TEXT_MUTED};
    font-size: 14px;
}}
DropArea:hover {{
    border-color: {Theme.GOLD_DIM};
    background-color: {Theme.PANEL_BG_ALT};
}}
DropArea[dragOver="true"] {{
    border-color: {Theme.GOLD};
    background-color: {Theme.SELECTION_BG};
}}

#dropIcon {{
    font-size: 48px;
    color: {Theme.GOLD_DIM};
    background-color: transparent;
}}

/* Table */
QTableWidget {{
    background-color: {Theme.TABLE_BG};
    border: 1px solid {Theme.BORDER};
    gridline-color: {Theme.BORDER};
    color: {Theme.TEXT_PRIMARY};
    selection-background-color: {Theme.SELECTION_BG};
    selection-color: {Theme.GOLD_BRIGHT};
    alternate-background-color: {Theme.TABLE_ALT};
}}
QTableWidget::item {{
    padding: 4px;
}}
QTableWidget::item:selected {{
    background-color: {Theme.SELECTION_BG};
    color: {Theme.GOLD_BRIGHT};
}}
QTableWidget::item:hover {{
    background-color: #1c1a10;
}}
QHeaderView::section {{
    background-color: {Theme.PANEL_BG};
    color: {Theme.GOLD};
    padding: 6px;
    border: 1px solid {Theme.BORDER};
    font-weight: bold;
}}
QHeaderView::section:hover {{
    background-color: {Theme.PANEL_BG_ALT};
}}

/* Scrollbar */
QScrollBar:vertical {{
    background-color: {Theme.BLACK};
    width: 12px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {Theme.GOLD_DARK};
    border-radius: 6px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {Theme.GOLD_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background-color: {Theme.BLACK};
    height: 12px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {Theme.GOLD_DARK};
    border-radius: 6px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {Theme.GOLD_DIM};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Buttons */
QPushButton {{
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a2e08,
        stop:1 {Theme.BUTTON_BG}
    );
    color: {Theme.GOLD};
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 13px;
    border: 1px solid {Theme.GOLD_DARK};
    min-height: 28px;
}}
QPushButton:hover {{
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #5a4a10,
        stop:1 {Theme.BUTTON_BG_HOVER}
    );
    border: 1px solid {Theme.GOLD};
}}
QPushButton:pressed {{
    background-color: {Theme.SELECTION_BG};
}}
QPushButton:disabled {{
    background-color: {Theme.PANEL_BG};
    color: {Theme.TEXT_DISABLED};
    border-color: {Theme.BORDER};
}}
QPushButton#secondary {{
    background-color: {Theme.PANEL_BG};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
}}
QPushButton#secondary:hover {{
    background-color: {Theme.PANEL_BG_ALT};
    border-color: {Theme.GOLD_DIM};
}}
QPushButton#danger {{
    background-color: #5a1a1a;
    color: {Theme.TEXT_WHITE};
    border-color: #8a2a2a;
}}
QPushButton#danger:hover {{
    background-color: #7a2a2a;
}}

/* Progress Bar */
QProgressBar {{
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    text-align: center;
    background-color: {Theme.TABLE_BG};
    color: {Theme.TEXT_PRIMARY};
    height: 20px;
}}
QProgressBar::chunk {{
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {Theme.GOLD_DARK},
        stop:1 {Theme.GOLD}
    );
    border-radius: 3px;
}}

/* Labels */
QLabel {{
    color: {Theme.TEXT_PRIMARY};
    font-size: 13px;
    background-color: transparent;
}}
QLabel#title {{
    font-size: 16px;
    font-weight: bold;
    color: {Theme.GOLD_BRIGHT};
}}
QLabel#subtitle {{
    font-size: 12px;
    color: {Theme.TEXT_MUTED};
}}
QLabel#status {{
    font-size: 12px;
    color: {Theme.TEXT_MUTED};
}}
QLabel#dragHint {{
    font-size: 14px;
    color: {Theme.TEXT_MUTED};
    background-color: transparent;
}}
QLabel#success {{
    color: {Theme.SUCCESS};
}}
QLabel#error {{
    color: {Theme.ERROR};
}}

/* Status Bar */
QStatusBar {{
    background-color: {Theme.PANEL_BG};
    color: {Theme.GOLD};
    font-size: 12px;
    border-top: 1px solid {Theme.BORDER};
}}
QStatusBar::item {{
    border: none;
}}

/* Menu */
QMenuBar {{
    background-color: {Theme.BLACK};
    color: {Theme.TEXT_PRIMARY};
}}
QMenuBar::item:selected {{
    background-color: {Theme.SELECTION_BG};
}}
QMenu {{
    background-color: {Theme.PANEL_BG};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
}}
QMenu::item:selected {{
    background-color: {Theme.SELECTION_BG};
}}
QMenu::separator {{
    height: 1px;
    background-color: {Theme.BORDER};
    margin: 4px 0px;
}}

#overlayContainer {{
    background-color: rgba(0, 0, 0, 220);
    border: none;
}}

/* Dialog / Inputs */
QDialog {{
    background-color: {Theme.BLACK};
}}
QLineEdit {{
    background-color: {Theme.INPUT_BG};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QLineEdit:focus {{
    border-color: {Theme.GOLD};
}}
QComboBox {{
    background-color: {Theme.INPUT_BG};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QComboBox:focus {{
    border-color: {Theme.GOLD};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {Theme.PANEL_BG};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    selection-background-color: {Theme.SELECTION_BG};
}}
QGroupBox {{
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}}
"""
