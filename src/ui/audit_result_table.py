"""Result table widget for displaying audit-mode metadata."""
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QMenu, QAction, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
import os
import subprocess
from typing import List, Dict, Any

from .styles import Theme
from .audit_detail_dialog import AuditDetailDialog


class AuditResultTable(QTableWidget):
    """Table displaying audit-mode document metadata extraction results."""

    item_double_clicked = pyqtSignal(str)
    show_audit_detail = pyqtSignal(dict)  # Emits alert dict for detail view

    COLUMN_HEADERS = [
        "文件名", "格式", "公司", "作者", "最后编辑者",
        "创建时间", "修改时间", "标题", "风险等级", "状态"
    ]
    COLUMN_KEYS = [
        'filename', 'format', 'company', 'author', 'last_modified_by',
        'created', 'modified', 'title', 'risk_level', 'status'
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
        self._init_ui()

    def _init_ui(self):
        self.setColumnCount(len(self.COLUMN_HEADERS))
        self.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        # Column sizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.setColumnWidth(1, 50)
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 公司
        header.setSectionResizeMode(8, QHeaderView.Fixed)        # 风险等级
        self.setColumnWidth(8, 70)
        for i in range(3, 8):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        header.setSectionResizeMode(9, QHeaderView.Interactive)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.cellDoubleClicked.connect(self._on_double_click)

    def set_data(self, data: List[Dict[str, Any]]):
        """Populate table with data."""
        self._data = data
        self.setSortingEnabled(False)
        self.setRowCount(len(data))

        for row_idx, item in enumerate(data):
            success = not str(item.get('status', '')).startswith('失败')

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val = item.get(key, '')
                if val is None:
                    val = ''
                cell = QTableWidgetItem(str(val))
                cell.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                cell.setData(Qt.UserRole, item.get('filepath', ''))

                if not success:
                    cell.setForeground(QColor(Theme.ERROR))

                # Color risk level column
                if key == 'risk_level':
                    risk = str(val).lower()
                    if risk == 'critical':
                        cell.setForeground(QColor(Theme.RISK_CRITICAL))
                        cell.setFont(QFont("", -1, QFont.Bold))
                    elif risk == 'high':
                        cell.setForeground(QColor(Theme.RISK_HIGH))
                    elif risk == 'medium':
                        cell.setForeground(QColor(Theme.RISK_MEDIUM))
                    elif risk == 'low':
                        cell.setForeground(QColor(Theme.RISK_LOW))

                self.setItem(row_idx, col_idx, cell)

            # Set row height
            self.setRowHeight(row_idx, 24)

        self.setSortingEnabled(True)
        self.resizeColumnsToContents()
        # Reset first column to stretch after resize
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def get_data(self) -> List[Dict[str, Any]]:
        """Return current data."""
        return self._data

    def clear_data(self):
        """Clear all data."""
        self._data = []
        self.setRowCount(0)

    def selected_rows_data(self) -> List[Dict[str, Any]]:
        """Get data for selected rows."""
        selected = []
        for idx in self.selectionModel().selectedRows():
            row = idx.row()
            if 0 <= row < len(self._data):
                selected.append(self._data[row])
        return selected

    def _show_context_menu(self, position):
        menu = QMenu(self)

        copy_action = QAction("复制单元格", self)
        copy_action.triggered.connect(self._copy_cell)
        menu.addAction(copy_action)

        copy_row_action = QAction("复制整行", self)
        copy_row_action.triggered.connect(self._copy_row)
        menu.addAction(copy_row_action)

        menu.addSeparator()

        open_loc_action = QAction("打开文件位置", self)
        open_loc_action.triggered.connect(self._open_file_location)
        menu.addAction(open_loc_action)

        menu.addSeparator()

        view_detail_action = QAction("查看审计详情", self)
        view_detail_action.triggered.connect(self._on_view_detail)
        menu.addAction(view_detail_action)

        menu.exec_(self.viewport().mapToGlobal(position))

    def _on_view_detail(self):
        """Emit signal to show audit detail for selected row(s)."""
        selected = self.selected_rows_data()
        if not selected:
            return
        # Emit the first selected row's data as a simple alert dict
        # The main window will map this to actual alerts
        row_data = selected[0]
        alert = {
            'rule_name': 'file_audit_summary',
            'severity': row_data.get('risk_level', 'low'),
            'description': f"文件: {row_data.get('filename', '')}\n公司: {row_data.get('company', '')}\n作者: {row_data.get('author', '')}\n最后编辑者: {row_data.get('last_modified_by', '')}",
            'affected_companies': [row_data.get('company', '')] if row_data.get('company') else [],
            'affected_files': [row_data.get('filepath', '')] if row_data.get('filepath') else [],
            'details': row_data,
        }
        self.show_audit_detail.emit(alert)

    def _copy_cell(self):
        item = self.currentItem()
        if item:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(item.text())

    def _copy_row(self):
        row = self.currentRow()
        if row < 0 or row >= len(self._data):
            return

        values = []
        for col in range(self.columnCount()):
            item = self.item(row, col)
            values.append(item.text() if item else '')

        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText('\t'.join(values))

    def _open_file_location(self):
        row = self.currentRow()
        if row < 0 or row >= len(self._data):
            return

        filepath = self._data[row].get('filepath', '')
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "错误", "文件不存在")
            return

        directory = os.path.dirname(filepath)
        if sys.platform == 'win32':
            subprocess.run(['explorer', '/select,', filepath])
        elif sys.platform == 'darwin':
            subprocess.run(['open', directory])
        else:
            subprocess.run(['xdg-open', directory])

    def _on_double_click(self, row, col):
        if row < 0 or row >= len(self._data):
            return
        filepath = self._data[row].get('filepath', '')
        if filepath:
            self.item_double_clicked.emit(filepath)

    def export_csv(self, filepath: str) -> bool:
        """Export data to CSV."""
        import csv
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(self.COLUMN_HEADERS)
                for item in self._data:
                    writer.writerow([item.get(k, '') for k in self.COLUMN_KEYS])
            return True
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出 CSV 失败:\n{str(e)}")
            return False

    def export_json(self, filepath: str) -> bool:
        """Export data to JSON."""
        import json
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出 JSON 失败:\n{str(e)}")
            return False

    def export_excel(self, filepath: str) -> bool:
        """Export data to Excel."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill

            wb = Workbook()
            ws = wb.active
            ws.title = "Metadata"

            # Header
            header_font = Font(bold=True, color=Theme.EXCEL_HEADER_FONT)
            header_fill = PatternFill(start_color=Theme.EXCEL_HEADER_FILL, end_color=Theme.EXCEL_HEADER_FILL, fill_type="solid")
            header_align = Alignment(horizontal="center", vertical="center")

            for col_idx, header in enumerate(self.COLUMN_HEADERS, 1):
                cell = ws.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_align

            # Data
            for row_idx, item in enumerate(self._data, 2):
                for col_idx, key in enumerate(self.COLUMN_KEYS, 1):
                    val = item.get(key, '')
                    if val is None:
                        val = ''
                    cell = ws.cell(row=row_idx, column=col_idx, value=str(val))
                    if str(item.get('status', '')).startswith('失败'):
                        cell.font = Font(color="F48771")

            # Auto column widths
            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        if cell.value:
                            max_len = max(max_len, len(str(cell.value)))
                    except Exception:
                        pass
                adjusted = min(max_len + 2, 50)
                ws.column_dimensions[col_letter].width = adjusted

            wb.save(filepath)
            return True

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出 Excel 失败:\n{str(e)}")
            return False


import sys
