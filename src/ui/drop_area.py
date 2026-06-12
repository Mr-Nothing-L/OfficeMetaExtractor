"""Modernized drop area widget for drag and drop."""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import (
    QDragEnterEvent, QDropEvent, QPainter, QPixmap,
    QPen, QColor, QFont
)

from .styles import Theme


class DropArea(QWidget):
    """Widget that accepts drag and drop of files and folders."""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_over = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        self.lbl_icon = QLabel()
        self.lbl_icon.setObjectName("dropIcon")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setPixmap(self._create_upload_icon(56))
        layout.addWidget(self.lbl_icon)

        self.lbl_hint = QLabel("拖拽文件到此处")
        self.lbl_hint.setObjectName("dragHint")
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_hint)

        self.lbl_sub_hint = QLabel("释放文件以开始解析")
        self.lbl_sub_hint.setObjectName("dragSubHint")
        self.lbl_sub_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_sub_hint)

        self.lbl_types = QLabel("支持: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.lbl_types.setObjectName("subtitle")
        self.lbl_types.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_types)

        self.setAcceptDrops(True)
        self.setMinimumHeight(160)

    @staticmethod
    def _create_upload_icon(size: int) -> QPixmap:
        """Draw a crisp cloud-upload icon as a QPixmap."""
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        color = QColor(Theme.GOLD_DIM)
        pen = QPen(color)
        pen.setWidthF(max(2.0, size / 28.0))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        w, h = size, size
        pad = size * 0.12
        cw = w - 2 * pad
        ch = h - 2 * pad

        cx = w / 2.0
        cy = h / 2.0 + pad * 0.3

        # Cloud outline (two arcs)
        r_small = cw * 0.22
        r_large = cw * 0.30
        cloud_bottom = cy + r_large * 0.55

        # Left small arc
        painter.drawArc(
            int(cx - r_large * 1.2), int(cy - r_large * 1.0),
            int(r_small * 2), int(r_small * 2),
            160 * 16, 180 * 16
        )
        # Top large arc
        painter.drawArc(
            int(cx - r_large * 0.85), int(cy - r_large * 1.45),
            int(r_large * 2), int(r_large * 2),
            40 * 16, 220 * 16
        )
        # Right medium arc
        painter.drawArc(
            int(cx + r_large * 0.35), int(cy - r_large * 0.9),
            int(r_large * 1.45), int(r_large * 1.45),
            300 * 16, 200 * 16
        )
        # Bottom flat line
        painter.drawLine(
            int(cx - r_large * 1.05), int(cloud_bottom),
            int(cx + r_large * 1.05), int(cloud_bottom)
        )

        # Upward arrow
        arrow_w = cw * 0.18
        arrow_head = ch * 0.22
        arrow_y_top = cy - ch * 0.15
        arrow_y_bottom = cloud_bottom - pad * 0.8

        # Arrow shaft
        painter.drawLine(int(cx), int(arrow_y_bottom), int(cx), int(arrow_y_top))
        # Arrow head
        painter.drawLine(int(cx - arrow_w), int(arrow_y_top + arrow_head), int(cx), int(arrow_y_top))
        painter.drawLine(int(cx + arrow_w), int(arrow_y_top + arrow_head), int(cx), int(arrow_y_top))

        painter.end()
        return pixmap

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._drag_over = True
            self.setProperty("dragOver", "true")
            self.style().unpolish(self)
            self.style().polish(self)
            self.lbl_sub_hint.setText("释放以开始解析")

    def dragLeaveEvent(self, event):
        self._drag_over = False
        self.setProperty("dragOver", "")
        self.style().unpolish(self)
        self.style().polish(self)
        self.lbl_sub_hint.setText("释放文件以开始解析")

    def dropEvent(self, event: QDropEvent):
        self._drag_over = False
        self.setProperty("dragOver", "")
        self.style().unpolish(self)
        self.style().polish(self)
        self.lbl_sub_hint.setText("释放文件以开始解析")

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
