#!/usr/bin/env python3
"""Vendor tool for generating OfficeMetaExtractor license keys (PyQt5 GUI)."""
import sys
import os

# Ensure src/ is importable when running from project root
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QDesktopWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard

from src.ui.styles import DARK_STYLE, Theme
from src.utils.license import generate_license_key


class LicenseKeyGenerator(QWidget):
    """Vendor-facing license key generator."""

    MACHINE_CODE_LENGTH = 32

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OfficeMetaExtractor 激活码生成工具")
        self.setMinimumSize(520, 420)
        self._build_ui()
        self._center()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("OfficeMetaExtractor 激活码生成工具")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("输入客户机器码、授权天数和 HMAC 密钥以生成激活码。")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)

        # Machine code
        layout.addWidget(QLabel("客户机器码"))
        self.machine_input = QLineEdit()
        self.machine_input.setPlaceholderText("请输入 32 位机器码")
        self.machine_input.setMaxLength(self.MACHINE_CODE_LENGTH)
        layout.addWidget(self.machine_input)

        # Days
        layout.addWidget(QLabel("有效期（天，0 表示永久授权）"))
        self.days_input = QLineEdit()
        self.days_input.setPlaceholderText("365")
        self.days_input.setText("365")
        layout.addWidget(self.days_input)

        # Secret
        layout.addWidget(QLabel("HMAC 密钥（可选，默认 OfficeMeta2024KB）"))
        self.secret_input = QLineEdit()
        self.secret_input.setPlaceholderText("OfficeMeta2024KB")
        self.secret_input.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        layout.addWidget(self.secret_input)

        # Generate button
        self.generate_btn = QPushButton("生成激活码")
        self.generate_btn.setObjectName("primary")
        self.generate_btn.clicked.connect(self.generate_key)
        layout.addWidget(self.generate_btn)

        # Output
        layout.addWidget(QLabel("生成的激活码"))
        self.key_output = QTextEdit()
        self.key_output.setReadOnly(True)
        self.key_output.setPlaceholderText("点击“生成激活码”后此处显示结果")
        layout.addWidget(self.key_output)

        # Copy button
        self.copy_btn = QPushButton("复制")
        self.copy_btn.setObjectName("secondary")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_btn)

        # Status
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

    def _center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def generate_key(self):
        machine_code = self.machine_input.text().strip()
        days_text = self.days_input.text().strip()
        secret = self.secret_input.text().strip() or None

        # Validate machine code
        if not machine_code:
            self._show_error("机器码不能为空")
            return
        if len(machine_code) != self.MACHINE_CODE_LENGTH:
            self._show_error(f"机器码长度错误：需要 {self.MACHINE_CODE_LENGTH} 位，当前 {len(machine_code)} 位")
            return

        # Validate days
        try:
            days = int(days_text) if days_text else 0
            if days < 0:
                self._show_error("有效期不能为负数")
                return
        except ValueError:
            self._show_error("有效期必须为正整数或 0")
            return

        try:
            key = generate_license_key(machine_code, days=days, secret=secret)
        except Exception as exc:  # pragma: no cover
            self._show_error(f"生成失败：{exc}")
            return

        self.key_output.setPlainText(key)
        self.copy_btn.setEnabled(True)
        mode = "永久授权" if days == 0 else f"{days} 天"
        self.status_label.setObjectName("statusSuccess")
        self.status_label.setText(f"生成成功（{mode}）")
        self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")

    def copy_to_clipboard(self):
        key = self.key_output.toPlainText().strip()
        if key:
            clipboard = QApplication.clipboard()
            clipboard.setText(key, QClipboard.Clipboard)
            self.status_label.setObjectName("statusSuccess")
            self.status_label.setText("已复制到剪贴板")
            self.status_label.setStyleSheet(f"color: {Theme.SUCCESS};")

    def _show_error(self, message: str):
        self.key_output.clear()
        self.copy_btn.setEnabled(False)
        self.status_label.setObjectName("statusError")
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {Theme.ERROR};")
        QMessageBox.warning(self, "输入错误", message)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("OfficeMetaExtractorKeyGen")
    app.setApplicationVersion("2.0.0")
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    window = LicenseKeyGenerator()
    window.setStyleSheet(DARK_STYLE + f"""
        QWidget {{
            background-color: {Theme.BG_PRIMARY};
            color: {Theme.TEXT_PRIMARY};
            font-family: "SF Pro Text", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
        }}
        QLabel#title {{
            font-size: 18px;
            font-weight: bold;
            color: {Theme.GOLD};
            padding-bottom: 4px;
        }}
    """)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
