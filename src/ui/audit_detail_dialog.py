"""Audit detail dialog for displaying high-risk findings."""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QGroupBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

import json
from typing import Dict, Any

from .styles import Theme


class AuditDetailDialog(QDialog):
    """Dialog displaying detailed information for a single audit alert."""

    mark_handled = pyqtSignal(str)  # Emits rule_name when marked handled

    # Severity color mapping
    SEVERITY_COLORS = {
        'critical': Theme.RISK_CRITICAL,
        'high': Theme.RISK_HIGH,
        'medium': Theme.RISK_MEDIUM,
        'low': Theme.RISK_LOW,
    }

    SEVERITY_LABELS = {
        'critical': '严重',
        'high': '高',
        'medium': '中',
        'low': '低',
    }

    def __init__(self, alert: Dict[str, Any], parent=None):
        super().__init__(parent)
        self._alert = alert
        self._rule_name = alert.get('rule_name', '')
        self._severity = alert.get('severity', 'low')
        self._handled = False
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        self.setWindowTitle("审计发现详情")
        self.setMinimumSize(560, 480)
        self.resize(620, 520)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header: Rule name + Severity badge
        header_layout = QHBoxLayout()

        rule_label = QLabel(f"规则: {self._rule_name}")
        rule_label.setObjectName("ruleName")
        header_layout.addWidget(rule_label)

        header_layout.addStretch()

        severity_text = self.SEVERITY_LABELS.get(self._severity, self._severity)
        self.severity_badge = QLabel(f"  {severity_text}  ")
        self.severity_badge.setObjectName("severityBadge")
        self.severity_badge.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.severity_badge)

        layout.addLayout(header_layout)

        # Description
        desc = self._alert.get('description', '')
        self.desc_label = QLabel(desc)
        self.desc_label.setWordWrap(True)
        self.desc_label.setObjectName("description")
        layout.addWidget(self.desc_label)

        # Splitter for affected companies and files
        splitter = QSplitter(Qt.Vertical)

        # Affected companies
        companies_group = QGroupBox("涉及公司")
        companies_layout = QVBoxLayout(companies_group)
        companies_layout.setContentsMargins(8, 12, 8, 8)
        self.companies_list = QListWidget()
        for company in self._alert.get('affected_companies', []):
            item = QListWidgetItem(company)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.companies_list.addItem(item)
        companies_layout.addWidget(self.companies_list)
        splitter.addWidget(companies_group)

        # Affected files
        files_group = QGroupBox("涉及文件")
        files_layout = QVBoxLayout(files_group)
        files_layout.setContentsMargins(8, 12, 8, 8)
        self.files_edit = QTextEdit()
        self.files_edit.setReadOnly(True)
        files_text = "\n".join(self._alert.get('affected_files', []))
        self.files_edit.setPlainText(files_text)
        files_layout.addWidget(self.files_edit)
        splitter.addWidget(files_group)

        # Details (pretty JSON / key-value)
        details_group = QGroupBox("判定依据")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(8, 12, 8, 8)
        self.details_edit = QTextEdit()
        self.details_edit.setReadOnly(True)
        details = self._alert.get('details', {})
        self.details_edit.setPlainText(self._format_details(details))
        details_layout.addWidget(self.details_edit)
        splitter.addWidget(details_group)

        # Set splitter proportions
        splitter.setSizes([80, 140, 140])
        layout.addWidget(splitter, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_mark_handled = QPushButton("标记已处理")
        self.btn_mark_handled.setObjectName("secondary")
        self.btn_mark_handled.clicked.connect(self._on_mark_handled)
        btn_layout.addWidget(self.btn_mark_handled)

        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format details dict into readable key-value text."""
        lines = []
        for key, value in details.items():
            label = self._detail_key_label(key)
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)
            lines.append(f"{label}: {value_str}")
        return "\n".join(lines)

    def _detail_key_label(self, key: str) -> str:
        """Map detail keys to human-readable labels."""
        mapping = {
            'author': '作者',
            'modifier': '修改者',
            'company_count': '涉及公司数',
            'file_count': '涉及文件数',
            'field': '检测字段',
            'time_bucket': '时间段',
            'threshold_minutes': '时间阈值（分钟）',
            'template': '模板名称',
        }
        return mapping.get(key, key)

    def _apply_styles(self):
        """Apply dark theme styling to the dialog."""
        severity_color = self.SEVERITY_COLORS.get(self._severity, Theme.TEXT_PRIMARY)
        badge_bg = {
            'critical': 'rgba(255, 68, 68, 0.18)',
            'high':     'rgba(255, 136, 0, 0.18)',
            'medium':   'rgba(255, 204, 0, 0.18)',
            'low':      'rgba(94, 207, 94, 0.18)',
        }.get(self._severity.lower(), 'rgba(117, 117, 122, 0.18)')

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PRIMARY};
            }}
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
                background-color: transparent;
            }}
            QLabel#ruleName {{
                font-size: 15px;
                font-weight: bold;
                color: {Theme.GOLD_BRIGHT};
            }}
            QLabel#description {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 13px;
                padding: 4px 0px;
            }}
            QLabel#severityBadge {{
                background-color: {badge_bg};
                color: {severity_color};
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 3px 10px;
            }}
            QGroupBox {{
                color: {Theme.GOLD};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
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
            QListWidget {{
                background-color: {Theme.BG_TABLE};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 5px 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {Theme.SELECTION_BG};
                color: {Theme.GOLD_BRIGHT};
            }}
            QTextEdit {{
                background-color: {Theme.BG_TABLE};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 6px;
                font-family: "SF Mono", "Menlo", "Consolas", monospace;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 13px;
                border: 1px solid {Theme.BORDER};
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
                border-color: {Theme.GOLD_DIM};
                color: {Theme.GOLD_BRIGHT};
            }}
            QPushButton:pressed {{
                background-color: {Theme.SELECTION_BG};
                border-color: {Theme.GOLD};
            }}
            QPushButton#secondary {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
            }}
            QPushButton#secondary:hover {{
                background-color: {Theme.BG_HOVER};
                border-color: {Theme.GOLD_DIM};
            }}
            QSplitter::handle {{
                background-color: {Theme.BORDER};
            }}
        """)

    def _on_mark_handled(self):
        """Mark this alert as handled and emit signal."""
        self._handled = True
        self.btn_mark_handled.setEnabled(False)
        self.btn_mark_handled.setText("已处理")
        self.mark_handled.emit(self._rule_name)

    def is_handled(self) -> bool:
        """Return whether the alert was marked as handled."""
        return self._handled


class AuditAlertListDialog(QDialog):
    """Dialog listing all audit alerts; selecting one opens a detail dialog."""

    def __init__(self, alerts: list, parent=None):
        super().__init__(parent)
        self._alerts = alerts
        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        self.setWindowTitle("审计发现列表")
        self.setMinimumSize(500, 400)
        self.resize(560, 460)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("审计发现")
        header.setObjectName("dialogHeader")
        layout.addWidget(header)

        self.alert_list = QListWidget()
        self.alert_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        for alert in self._alerts:
            severity = alert.get('severity', 'low')
            rule = alert.get('rule_name', '')
            desc = alert.get('description', '')
            text = f"[{severity.upper()}] {rule}: {desc[:60]}{'...' if len(desc) > 60 else ''}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, alert)
            # Color-code by severity
            color = AuditDetailDialog.SEVERITY_COLORS.get(severity, Theme.TEXT_PRIMARY)
            item.setForeground(QColor(color))
            self.alert_list.addItem(item)

        layout.addWidget(self.alert_list, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_detail = QPushButton("查看详情")
        btn_detail.clicked.connect(self._on_view_detail)
        btn_layout.addWidget(btn_detail)

        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PRIMARY};
            }}
            QLabel#dialogHeader {{
                font-size: 16px;
                font-weight: bold;
                color: {Theme.GOLD_BRIGHT};
                padding-bottom: 4px;
            }}
            QListWidget {{
                background-color: {Theme.BG_TABLE};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {Theme.SELECTION_BG};
                color: {Theme.GOLD_BRIGHT};
            }}
            QPushButton {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 13px;
                border: 1px solid {Theme.BORDER};
                min-height: 30px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_HOVER};
                border-color: {Theme.GOLD_DIM};
                color: {Theme.GOLD_BRIGHT};
            }}
            QPushButton:pressed {{
                background-color: {Theme.SELECTION_BG};
                border-color: {Theme.GOLD};
            }}
        """)

    def _on_item_double_clicked(self, item):
        alert = item.data(Qt.UserRole)
        if alert:
            self._open_detail(alert)

    def _on_view_detail(self):
        item = self.alert_list.currentItem()
        if item:
            alert = item.data(Qt.UserRole)
            self._open_detail(alert)

    def _open_detail(self, alert: Dict[str, Any]):
        dialog = AuditDetailDialog(alert, parent=self)
        dialog.exec_()
