"""Drop area widget for drag and drop."""
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        self.icon_label = QLabel("◈")
        self.icon_label.setObjectName("dropIcon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        self.hint_label = QLabel("拖拽文件到此处\n或点击选择文件 / 文件夹")
        self.hint_label.setObjectName("dragHint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint_label)
        
        self.types_label = QLabel("支持: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.types_label.setObjectName("subtitle")
        self.types_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.types_label)
        
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
    
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
        self.hint_label.setText(text)
