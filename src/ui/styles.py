"""Modern dark theme QSS for OfficeMetaExtractor."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Unified dark color palette with controlled gold accents."""

    # --- Backgrounds ---
    BG_PRIMARY = "#0f0f10"          # Deepest background (window, menu bar)
    BG_SURFACE = "#141415"          # Main container / status bar
    BG_PANEL = "#1a1a1c"            # Cards, panels, drop area
    BG_INPUT = "#222225"            # Inputs, combo boxes
    BG_HOVER = "#252528"            # Hover states
    BG_TABLE = "#161618"            # Table background
    BG_TABLE_ALT = "#1c1c1e"        # Alternating row
    BG_RAISED = "#202023"           # Elevated surfaces

    # --- Accents (single gold family) ---
    GOLD = "#c9a227"
    GOLD_BRIGHT = "#e6bc3a"
    GOLD_DIM = "#8f7325"
    GOLD_DARK = "#53431a"
    GOLD_GLOW = "rgba(201, 162, 39, 0.12)"

    # --- Text ---
    TEXT_PRIMARY = "#ededed"
    TEXT_SECONDARY = "#a6a6a6"
    TEXT_MUTED = "#75757a"
    TEXT_DISABLED = "#4d4d52"
    TEXT_WHITE = "#ffffff"
    TEXT_ON_ACCENT = "#121212"

    # --- Borders ---
    BORDER = "#2c2c2f"
    BORDER_SUBTLE = "#232326"
    BORDER_FOCUS = "#c9a227"

    # --- Buttons ---
    BUTTON_BG = "#1e1e21"
    BUTTON_BG_HOVER = "#262629"
    BUTTON_PRIMARY_BG = "#c9a227"
    BUTTON_PRIMARY_TEXT = "#121212"

    # --- Progress / Selection ---
    PROGRESS_CHUNK = "#c9a227"
    PROGRESS_BG = "#1a1a1c"
    SELECTION_BG = "rgba(201, 162, 39, 0.15)"

    # --- Status ---
    SUCCESS = "#5ecf5e"
    ERROR = "#ff6b6b"
    WARNING = "#ffcc00"
    INFO = "#5ab3f0"

    # --- Risk levels ---
    RISK_CRITICAL = "#ff4444"
    RISK_HIGH = "#ff8800"
    RISK_MEDIUM = "#ffcc00"
    RISK_LOW = "#5ecf5e"

    # --- Excel export colors (openpyxl expects hex without #) ---
    EXCEL_HEADER_FILL = "c9a227"
    EXCEL_HEADER_FONT = "ffffff"
    EXCEL_ERROR_FONT = "ff6b6b"
    EXCEL_RISK_CRITICAL = "ff4444"
    EXCEL_RISK_HIGH = "ff8800"
    EXCEL_RISK_MEDIUM = "ffcc00"
    EXCEL_RISK_LOW = "5ecf5e"

    # --- Aliases for backward compatibility / dialog fixes ---
    BLACK = BG_PRIMARY
    TABLE_BG = BG_TABLE
    PANEL_BG = BG_PANEL
    PANEL_BG_ALT = BG_RAISED


# Common dimensions
RADIUS_CARD = 8
RADIUS_BUTTON = 6
RADIUS_BADGE = 4
RADIUS_INPUT = 6
RADIUS_TABLE = 6

DARK_STYLE = f"""
/* ------------------------------------------------------------------
   Global reset
   ------------------------------------------------------------------ */
QMainWindow {{
    background-color: {Theme.BG_PRIMARY};
    color: {Theme.TEXT_PRIMARY};
}}

QWidget {{
    background-color: transparent;
    color: {Theme.TEXT_PRIMARY};
}}

/* ------------------------------------------------------------------
   Root / surface layering
   ------------------------------------------------------------------ */
#centralRoot {{
    background-color: {Theme.BG_SURFACE};
    border: none;
}}

#surfacePanel {{
    background-color: {Theme.BG_SURFACE};
    border: none;
}}

#panelRow {{
    background-color: {Theme.BG_SURFACE};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: {RADIUS_CARD}px;
    padding: 12px 20px;
}}

#resultTableStack {{
    background-color: transparent;
    border: none;
}}

/* ------------------------------------------------------------------
   Section separator
   ------------------------------------------------------------------ */
#sectionSeparator {{
    background-color: {Theme.BORDER_SUBTLE};
    max-height: 1px;
    min-height: 1px;
}}

/* ------------------------------------------------------------------
   Drop Area
   ------------------------------------------------------------------ */
DropArea {{
    background-color: {Theme.BG_PANEL};
    border: 1.5px dashed {Theme.BORDER};
    border-radius: {RADIUS_CARD}px;
    color: {Theme.TEXT_MUTED};
    font-size: 14px;
    padding: 16px;
}}

DropArea:hover {{
    border-color: {Theme.GOLD_DIM};
    background-color: {Theme.BG_HOVER};
}}

DropArea[dragOver="true"] {{
    border-color: {Theme.GOLD};
    background-color: {Theme.GOLD_GLOW};
}}

#dropIcon {{
    font-size: 42px;
    color: {Theme.GOLD_DIM};
    background-color: transparent;
}}

#dragHint {{
    font-size: 14px;
    font-weight: bold;
    color: {Theme.TEXT_SECONDARY};
    background-color: transparent;
}}

#dragSubHint {{
    font-size: 12px;
    color: {Theme.TEXT_MUTED};
    background-color: transparent;
}}

/* ------------------------------------------------------------------
   Table
   ------------------------------------------------------------------ */
QTableWidget {{
    background-color: {Theme.BG_TABLE};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_TABLE}px;
    gridline-color: {Theme.BORDER_SUBTLE};
    color: {Theme.TEXT_PRIMARY};
    selection-background-color: {Theme.SELECTION_BG};
    selection-color: {Theme.GOLD_BRIGHT};
    alternate-background-color: {Theme.BG_TABLE_ALT};
    padding: 2px;
}}

QTableWidget::item {{
    padding: 5px 10px;
    border-bottom: 1px solid {Theme.BORDER_SUBTLE};
}}

QTableWidget::item:selected {{
    background-color: {Theme.SELECTION_BG};
    color: {Theme.GOLD_BRIGHT};
}}

QTableWidget::item:hover {{
    background-color: {Theme.BG_HOVER};
}}

QHeaderView::section {{
    background-color: {Theme.BG_PANEL};
    color: {Theme.GOLD};
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {Theme.BORDER};
    border-radius: 0px;
    font-weight: bold;
    font-size: 12px;
}}

QHeaderView::section:first {{
    border-top-left-radius: {RADIUS_TABLE}px;
}}

QHeaderView::section:last {{
    border-top-right-radius: {RADIUS_TABLE}px;
}}

QHeaderView::section:hover {{
    background-color: {Theme.BG_HOVER};
    color: {Theme.GOLD_BRIGHT};
}}

/* ------------------------------------------------------------------
   Scrollbar
   ------------------------------------------------------------------ */
QScrollBar:vertical {{
    background-color: {Theme.BG_SURFACE};
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {Theme.BORDER};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Theme.GOLD_DIM};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {Theme.BG_SURFACE};
    height: 8px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {Theme.BORDER};
    border-radius: 4px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {Theme.GOLD_DIM};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ------------------------------------------------------------------
   Buttons
   ------------------------------------------------------------------ */
QPushButton {{
    background-color: {Theme.BUTTON_BG};
    color: {Theme.TEXT_PRIMARY};
    border-radius: {RADIUS_BUTTON}px;
    padding: 6px 16px;
    font-size: 13px;
    border: 1px solid {Theme.BORDER};
    min-height: 30px;
}}

QPushButton:hover {{
    background-color: {Theme.BUTTON_BG_HOVER};
    border-color: {Theme.GOLD_DIM};
    color: {Theme.GOLD_BRIGHT};
}}

QPushButton:pressed {{
    background-color: {Theme.SELECTION_BG};
    border-color: {Theme.GOLD};
}}

QPushButton:disabled {{
    background-color: {Theme.BG_SURFACE};
    color: {Theme.TEXT_DISABLED};
    border-color: {Theme.BORDER_SUBTLE};
}}

/* Primary action button (gold) */
QPushButton#primary {{
    background-color: {Theme.GOLD};
    color: {Theme.BUTTON_PRIMARY_TEXT};
    border: 1px solid {Theme.GOLD};
    font-weight: bold;
}}

QPushButton#primary:hover {{
    background-color: {Theme.GOLD_BRIGHT};
    border-color: {Theme.GOLD_BRIGHT};
    color: {Theme.BG_PRIMARY};
}}

QPushButton#primary:pressed {{
    background-color: {Theme.GOLD_DIM};
    border-color: {Theme.GOLD_DIM};
}}

QPushButton#primary:disabled {{
    background-color: {Theme.GOLD_DARK};
    color: {Theme.TEXT_DISABLED};
    border-color: {Theme.GOLD_DARK};
}}

/* Secondary action button */
QPushButton#secondary {{
    background-color: {Theme.BG_PANEL};
    color: {Theme.TEXT_SECONDARY};
    border: 1px solid {Theme.BORDER};
}}

QPushButton#secondary:hover {{
    background-color: {Theme.BG_HOVER};
    border-color: {Theme.GOLD_DIM};
    color: {Theme.GOLD_BRIGHT};
}}

QPushButton#secondary:pressed {{
    background-color: {Theme.SELECTION_BG};
}}

/* Danger / clear button */
QPushButton#danger {{
    background-color: {Theme.BG_PANEL};
    color: {Theme.ERROR};
    border: 1px solid {Theme.BORDER};
}}

QPushButton#danger:hover {{
    background-color: {Theme.BG_HOVER};
    border-color: {Theme.ERROR};
    color: #ff8888;
}}

/* Tool / icon button */
QPushButton#toolButton {{
    background-color: transparent;
    color: {Theme.TEXT_SECONDARY};
    border: 1px solid transparent;
    border-radius: {RADIUS_BUTTON}px;
    padding: 4px 10px;
    min-height: 28px;
}}

QPushButton#toolButton:hover {{
    background-color: {Theme.BG_HOVER};
    color: {Theme.TEXT_PRIMARY};
}}

QPushButton#toolButton:pressed {{
    background-color: {Theme.SELECTION_BG};
    color: {Theme.GOLD_BRIGHT};
}}

/* QToolButton (export dropdown) */
QToolButton {{
    background-color: {Theme.BG_PANEL};
    color: {Theme.TEXT_SECONDARY};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_BUTTON}px;
    padding: 6px 14px;
    font-size: 13px;
    min-height: 30px;
}}

QToolButton:hover {{
    background-color: {Theme.BG_HOVER};
    border-color: {Theme.GOLD_DIM};
    color: {Theme.GOLD_BRIGHT};
}}

QToolButton:pressed {{
    background-color: {Theme.SELECTION_BG};
    border-color: {Theme.GOLD};
}}

QToolButton:disabled {{
    background-color: {Theme.BG_SURFACE};
    color: {Theme.TEXT_DISABLED};
    border-color: {Theme.BORDER_SUBTLE};
}}

QToolButton::menu-indicator {{
    image: none;
}}

QToolButton::menu-arrow {{
    border: none;
    width: 0px;
    height: 0px;
}}

/* ------------------------------------------------------------------
   Progress Bar
   ------------------------------------------------------------------ */
QProgressBar {{
    border: none;
    border-radius: 2px;
    text-align: center;
    background-color: {Theme.PROGRESS_BG};
    color: transparent;
    height: 4px;
    font-size: 1px;
}}

QProgressBar::chunk {{
    background-color: {Theme.GOLD};
    border-radius: 2px;
}}

/* ------------------------------------------------------------------
   Labels
   ------------------------------------------------------------------ */
QLabel {{
    color: {Theme.TEXT_PRIMARY};
    font-size: 13px;
    background-color: transparent;
}}

QLabel#title {{
    font-size: 17px;
    font-weight: bold;
    color: {Theme.TEXT_WHITE};
    letter-spacing: 0.3px;
}}

QLabel#subtitle {{
    font-size: 11px;
    color: {Theme.TEXT_MUTED};
}}

QLabel#status {{
    font-size: 12px;
    color: {Theme.TEXT_SECONDARY};
    padding: 2px 0px;
    background-color: transparent;
}}

QLabel#statusSuccess {{
    font-size: 12px;
    color: {Theme.SUCCESS};
}}

QLabel#statusError {{
    font-size: 12px;
    color: {Theme.ERROR};
}}

QLabel#statusWarning {{
    font-size: 12px;
    color: {Theme.WARNING};
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
    font-size: 12px;
    color: {Theme.TEXT_MUTED};
}}

QLabel#fileCount {{
    font-size: 12px;
    color: {Theme.GOLD};
    font-weight: bold;
    padding: 3px 10px;
    background-color: {Theme.BG_PANEL};
    border-radius: 999px;
    border: 1px solid {Theme.BORDER};
}}

QLabel#badge {{
    font-size: 11px;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: {RADIUS_BADGE}px;
}}

QLabel#sectionTitle {{
    font-size: 13px;
    font-weight: bold;
    color: {Theme.TEXT_SECONDARY};
}}

/* ------------------------------------------------------------------
   Status Bar
   ------------------------------------------------------------------ */
QStatusBar {{
    background-color: {Theme.BG_PRIMARY};
    color: {Theme.TEXT_MUTED};
    font-size: 11px;
    border-top: 1px solid {Theme.BORDER_SUBTLE};
    padding: 2px 12px;
}}

QStatusBar::item {{
    border: none;
}}

/* ------------------------------------------------------------------
   Menu
   ------------------------------------------------------------------ */
QMenuBar {{
    background-color: {Theme.BG_PRIMARY};
    color: {Theme.TEXT_PRIMARY};
    border-bottom: 1px solid {Theme.BORDER_SUBTLE};
    padding: 2px 8px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 4px 12px;
    border-radius: {RADIUS_BADGE}px;
}}

QMenuBar::item:selected {{
    background-color: {Theme.SELECTION_BG};
    color: {Theme.GOLD_BRIGHT};
}}

QMenu {{
    background-color: {Theme.BG_PANEL};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_CARD}px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 20px;
    border-radius: {RADIUS_BADGE}px;
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

/* ------------------------------------------------------------------
   Dialog / Inputs
   ------------------------------------------------------------------ */
QDialog {{
    background-color: {Theme.BG_PRIMARY};
}}

QLineEdit {{
    background-color: {Theme.BG_INPUT};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_INPUT}px;
    padding: 6px 10px;
    font-size: 13px;
}}

QLineEdit:focus {{
    border-color: {Theme.GOLD};
    background-color: {Theme.BG_PANEL};
}}

QComboBox {{
    background-color: {Theme.BG_INPUT};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_INPUT}px;
    padding: 5px 10px;
    font-size: 13px;
    min-height: 18px;
}}

QComboBox:focus {{
    border-color: {Theme.GOLD};
}}

QComboBox::drop-down {{
    border: none;
    width: 22px;
}}

QComboBox QAbstractItemView {{
    background-color: {Theme.BG_PANEL};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_CARD}px;
    selection-background-color: {Theme.SELECTION_BG};
    padding: 4px;
}}

QGroupBox {{
    color: {Theme.GOLD};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_CARD}px;
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

QListWidget {{
    background-color: {Theme.BG_TABLE};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_CARD}px;
    padding: 4px;
}}

QListWidget::item {{
    padding: 5px 8px;
    border-radius: {RADIUS_BADGE}px;
}}

QListWidget::item:selected {{
    background-color: {Theme.SELECTION_BG};
    color: {Theme.GOLD_BRIGHT};
}}

QTextEdit {{
    background-color: {Theme.BG_TABLE};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER};
    border-radius: {RADIUS_CARD}px;
    padding: 6px;
    font-family: "SF Mono", "Menlo", "Consolas", monospace;
    font-size: 12px;
}}

/* ------------------------------------------------------------------
   Result tables (semi-transparent so the background planets show through)
   ------------------------------------------------------------------ */
#resultTable {{
    background-color: rgba(22, 22, 24, 165);
    alternate-background-color: rgba(28, 28, 30, 140);
    border: 1px solid rgba(44, 44, 47, 180);
    gridline-color: rgba(35, 35, 38, 120);
    selection-background-color: rgba(201, 162, 39, 0.14);
}}

#resultTable::item:selected {{
    background-color: rgba(201, 162, 39, 0.14);
}}

#resultTable::item:hover {{
    background-color: rgba(37, 37, 40, 170);
}}

#resultTable QHeaderView::section {{
    background-color: {Theme.BG_PANEL};
    border-bottom: 1px solid {Theme.BORDER};
}}
"""
