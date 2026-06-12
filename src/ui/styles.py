"""Dark theme QSS for OfficeMetaExtractor."""

DARK_STYLE = """
/* Main Window */
QMainWindow {
    background-color: #1e1e1e;
    color: #d4d4d4;
}

QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
}

/* Drop Area */
DropArea {
    background-color: #2d2d2d;
    border: 2px dashed #5a5a5a;
    border-radius: 8px;
    color: #808080;
    font-size: 14px;
}
DropArea:hover {
    border-color: #007acc;
    background-color: #252526;
}
DropArea[dragOver="true"] {
    border-color: #007acc;
    background-color: #1e3a5f;
}

/* Table */
QTableWidget {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    gridline-color: #3c3c3c;
    color: #d4d4d4;
    selection-background-color: #094771;
    selection-color: #ffffff;
    alternate-background-color: #2a2a2a;
}
QTableWidget::item {
    padding: 4px;
}
QTableWidget::item:selected {
    background-color: #094771;
    color: #ffffff;
}
QTableWidget::item:hover {
    background-color: #2a2d2e;
}
QHeaderView::section {
    background-color: #333333;
    color: #d4d4d4;
    padding: 6px;
    border: 1px solid #3c3c3c;
    font-weight: bold;
}
QHeaderView::section:hover {
    background-color: #3a3a3a;
}

/* Scrollbar */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #424242;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #4f4f4f;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #424242;
    border-radius: 6px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #4f4f4f;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Buttons */
QPushButton {
    background-color: #0e639c;
    color: white;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 13px;
    border: none;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #1177bb;
}
QPushButton:pressed {
    background-color: #094771;
}
QPushButton:disabled {
    background-color: #3a3a3a;
    color: #808080;
}
QPushButton#secondary {
    background-color: #3c3c3c;
    color: #d4d4d4;
}
QPushButton#secondary:hover {
    background-color: #4a4a4a;
}
QPushButton#danger {
    background-color: #c75450;
}
QPushButton#danger:hover {
    background-color: #d16966;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    text-align: center;
    background-color: #252526;
    color: #d4d4d4;
    height: 20px;
}
QProgressBar::chunk {
    background-color: #0e639c;
    border-radius: 3px;
}

/* Labels */
QLabel {
    color: #d4d4d4;
    font-size: 13px;
}
QLabel#title {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
}
QLabel#subtitle {
    font-size: 12px;
    color: #808080;
}
QLabel#status {
    font-size: 12px;
    color: #808080;
}
QLabel#dragHint {
    font-size: 14px;
    color: #808080;
}
QLabel#success {
    color: #4ec9b0;
}
QLabel#error {
    color: #f48771;
}

/* Status Bar */
QStatusBar {
    background-color: #007acc;
    color: white;
    font-size: 12px;
}
QStatusBar::item {
    border: none;
}

/* Menu */
QMenuBar {
    background-color: #1e1e1e;
    color: #d4d4d4;
}
QMenuBar::item:selected {
    background-color: #094771;
}
QMenu {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
}
QMenu::item:selected {
    background-color: #094771;
}
QMenu::separator {
    height: 1px;
    background-color: #3c3c3c;
    margin: 4px 0px;
}

/* Dialog */
QDialog {
    background-color: #1e1e1e;
}
QLineEdit {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px 8px;
}
QLineEdit:focus {
    border-color: #007acc;
}
QComboBox {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px 8px;
}
QComboBox:focus {
    border-color: #007acc;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    selection-background-color: #094771;
}
QGroupBox {
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
"""
