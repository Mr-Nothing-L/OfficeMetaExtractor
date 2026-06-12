"""Modernized drop area widget for drag and drop."""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


class DropArea(QWidget):
    """Widget that accepts drag and drop of files and folders."""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_over = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_icon = QLabel("◈")
        self.lbl_icon.setObjectName("dropIcon")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_icon)

        self.lbl_hint = QLabel("拖拽文件到此处\n或点击选择文件 / 文件夹")
        self.lbl_hint.setObjectName("dragHint")
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_hint)

        self.lbl_types = QLabel("支持: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.lbl_types.setObjectName("subtitle")
        self.lbl_types.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_types)

        self.setAcceptDrops(True)
        self.setMinimumHeight(150)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._drag_over = True
            self.setProperty("dragOver", "true")
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self._drag_over = False
        self.setProperty("dragOver", "")
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self._drag_over = False
        self.setProperty("dragOver", "")
        self.style().unpolish(self)
        self.style().polish(self)

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        """Click to open file dialog."""
        if event.button() == Qt.LeftButton:
            from PyQt5.QtWidgets import QFileDialog
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "选择文件",
                "",
                "Office Documents (*.docx *.xlsx *.pptx *.doc *.xls *.ppt);;"
                "PDF Files (*.pdf);;"
                "All Files (*.*)"
            )
            if files:
                self.files_dropped.emit(files)

    def set_hint(self, text: str):
        self.lbl_hint.setText(text)
