"""License activation dialog for OfficeMetaExtractor."""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

from ..utils.license import get_machine_code, save_license_key
from ..utils.config import PURCHASE_URL


class ActivationDialog(QDialog):
    """Dialog for entering and validating a license key."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入激活码")
        self.setMinimumSize(480, 220)
        self.resize(520, 240)
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel("请输入授权激活码。激活码与当前机器绑定，不可共享使用。")
        info.setWordWrap(True)
        info.setObjectName("activationInfo")
        layout.addWidget(info)

        machine_code = get_machine_code()
        machine_layout = QHBoxLayout()
        machine_layout.setSpacing(8)
        self.machine_label = QLabel(f"机器码: {machine_code}")
        self.machine_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.machine_label.setWordWrap(True)
        self.machine_label.setObjectName("machineCode")
        machine_layout.addWidget(self.machine_label, 1)

        self.btn_copy = QPushButton("复制")
        self.btn_copy.setToolTip("复制机器码，发给客服获取激活码")
        self.btn_copy.clicked.connect(self._on_copy_machine_code)
        machine_layout.addWidget(self.btn_copy)
        layout.addLayout(machine_layout)

        self.edt_key = QLineEdit()
        self.edt_key.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX-XXXX")
        self.edt_key.setObjectName("activationInput")
        layout.addWidget(self.edt_key)

        purchase_link = QLabel('<a href="#" style="color: #E6B800;">还没有激活码？点击购买授权</a>')
        purchase_link.setOpenExternalLinks(False)
        purchase_link.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        purchase_link.linkActivated.connect(self._on_buy)
        layout.addWidget(purchase_link)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_activate = QPushButton("激活")
        self.btn_activate.setObjectName("primary")
        self.btn_activate.setDefault(True)
        self.btn_activate.clicked.connect(self._on_activate)
        btn_layout.addWidget(self.btn_activate)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _apply_styles(self):
        from .styles import Theme
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PRIMARY};
            }}
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
                background-color: transparent;
            }}
            QLabel#activationInfo {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 13px;
            }}
            QLabel#machineCode {{
                color: {Theme.GOLD_BRIGHT};
                font-family: "SF Mono", "Menlo", "Consolas", monospace;
                font-size: 12px;
            }}
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.GOLD};
            }}
            QPushButton {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 13px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
                border-color: {Theme.GOLD_DIM};
                color: {Theme.GOLD_BRIGHT};
            }}
            QPushButton#primary {{
                background-color: {Theme.GOLD};
                color: {Theme.BUTTON_PRIMARY_TEXT};
                border: 1px solid {Theme.GOLD};
                font-weight: bold;
            }}
            QPushButton#primary:hover {{
                background-color: {Theme.GOLD_BRIGHT};
                border-color: {Theme.GOLD_BRIGHT};
            }}
        """)

    def _on_copy_machine_code(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(get_machine_code())
        self.btn_copy.setText("已复制")
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.btn_copy.setText("复制"))

    def _on_buy(self):
        QDesktopServices.openUrl(QUrl(PURCHASE_URL))

    def _on_activate(self):
        key = self.edt_key.text().strip()
        if not key:
            QMessageBox.warning(self, "提示", "请输入激活码")
            return

        if save_license_key(key):
            QMessageBox.information(self, "激活成功", "授权激活成功，感谢使用！")
            self.accept()
        else:
            QMessageBox.warning(
                self, "激活失败",
                "激活码无效或与当前机器不匹配，请检查后重试。"
            )
