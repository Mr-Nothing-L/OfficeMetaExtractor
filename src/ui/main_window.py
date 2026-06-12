"""Main application window."""
import sys
import os
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QStatusBar,
    QFileDialog, QMessageBox,
    QMenuBar, QMenu, QAction, QComboBox, QLineEdit,
    QStackedWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from .drop_area import DropArea
from .result_table import ResultTable
from .audit_result_table import AuditResultTable
from .audit_detail_dialog import AuditDetailDialog, AuditAlertListDialog
from .styles import DARK_STYLE

from ..core.extractor_core import MetaExtractor
from ..parsers import SUPPORTED_EXT
from ..utils.logger import logger
from ..audit import export_to_excel as audit_export_to_excel


class ExtractionWorker(QThread):
    """Background worker for batch extraction with per-file timeout."""

    progress = pyqtSignal(int, int, str)
    result = pyqtSignal(list)
    finished_signal = pyqtSignal()

    FILE_TIMEOUT = 30

    def __init__(self, filepaths: List[str]):
        super().__init__()
        self.filepaths = filepaths
        self._stop = False

    def _extract_with_timeout(self, extractor, filepath: str) -> dict:
        import threading
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = extractor.extract(filepath)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.FILE_TIMEOUT)

        if thread.is_alive():
            raise TimeoutError(f"文件解析超过 {self.FILE_TIMEOUT} 秒")

        if exception[0] is not None:
            raise exception[0]

        return result[0]

    def run(self):
        extractor = MetaExtractor()
        results = []
        total = len(self.filepaths)

        for i, fp in enumerate(self.filepaths):
            if self._stop:
                break
            self.progress.emit(i + 1, total, Path(fp).name)
            try:
                result = self._extract_with_timeout(extractor, fp)
                results.append(result)
            except TimeoutError as e:
                logger.warning(f"Timeout parsing {fp}: {e}")
                results.append({
                    'filepath': fp,
                    'filename': Path(fp).name,
                    'format': Path(fp).suffix.upper()[1:] or 'UNKNOWN',
                    'status': f'失败: 解析超时（文件可能过大或格式异常）'
                })
            except Exception as e:
                logger.error(f"Failed to extract {fp}: {e}")
                results.append({
                    'filepath': fp,
                    'filename': Path(fp).name,
                    'format': Path(fp).suffix.upper()[1:] or 'UNKNOWN',
                    'status': f'失败: {str(e)}'
                })

        self.result.emit(results)
        self.finished_signal.emit()

    def stop(self):
        self._stop = True


class AuditWorker(QThread):
    """Background worker for audit mode extraction."""

    progress = pyqtSignal(int, int, str)
    result = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, project_name: str, folder_path: str):
        super().__init__()
        self.project_name = project_name
        self.folder_path = folder_path
        self._stop = False

    def run(self):
        extractor = MetaExtractor()
        files = extractor.scan_directory(self.folder_path, recursive=True)
        total = len(files)
        for i, fp in enumerate(files):
            if self._stop:
                break
            self.progress.emit(i + 1, total, Path(fp).name)

        audit_result = extractor.audit(self.project_name, self.folder_path)
        self.result.emit(audit_result)
        self.finished_signal.emit()

    def stop(self):
        self._stop = True


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OfficeMetaExtractor v1.0")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        self.worker = None
        self._current_mode = "audit"
        self._audit_summary = []
        self._audit_detail = []
        self._audit_alerts = []
        self._init_ui()
        self._apply_styles()
        self._init_menubar()

        logger.add_listener(self._on_log)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        top_layout = QHBoxLayout()
        title_label = QLabel("OfficeMetaExtractor")
        title_label.setObjectName("title")
        top_layout.addWidget(title_label)
        version_label = QLabel("v1.0")
        version_label.setObjectName("subtitle")
        top_layout.addWidget(version_label)
        top_layout.addStretch()

        mode_label = QLabel("模式:")
        top_layout.addWidget(mode_label)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("招标审计", "audit")
        self.mode_combo.addItem("单文件提取", "single")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        top_layout.addWidget(self.mode_combo)
        top_layout.addSpacing(20)

        self.file_count_label = QLabel("0 个文件")
        self.file_count_label.setObjectName("subtitle")
        top_layout.addWidget(self.file_count_label)
        layout.addLayout(top_layout)

        self.project_name_layout = QHBoxLayout()
        self.project_name_label = QLabel("项目名称:")
        self.project_name_layout.addWidget(self.project_name_label)
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("输入项目名称（用于模板复用检测）")
        self.project_name_layout.addWidget(self.project_name_input, 1)
        layout.addLayout(self.project_name_layout)

        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_area)

        btn_layout = QHBoxLayout()
        self.btn_select_files = QPushButton("选择文件")
        self.btn_select_files.setToolTip("选择单个或多个文件")
        self.btn_select_files.clicked.connect(self._on_select_files)
        btn_layout.addWidget(self.btn_select_files)

        self.btn_select_folder = QPushButton("选择文件夹")
        self.btn_select_folder.setToolTip("递归扫描文件夹")
        self.btn_select_folder.clicked.connect(self._on_select_folder)
        btn_layout.addWidget(self.btn_select_folder)
        btn_layout.addStretch()

        self.btn_export_csv = QPushButton("导出 CSV")
        self.btn_export_csv.setObjectName("secondary")
        self.btn_export_csv.clicked.connect(self._on_export_csv)
        self.btn_export_csv.setEnabled(False)
        btn_layout.addWidget(self.btn_export_csv)

        self.btn_export_json = QPushButton("导出 JSON")
        self.btn_export_json.setObjectName("secondary")
        self.btn_export_json.clicked.connect(self._on_export_json)
        self.btn_export_json.setEnabled(False)
        btn_layout.addWidget(self.btn_export_json)

        self.btn_export_excel = QPushButton("导出 Excel")
        self.btn_export_excel.setObjectName("secondary")
        self.btn_export_excel.clicked.connect(self._on_export_excel)
        self.btn_export_excel.setEnabled(False)
        btn_layout.addWidget(self.btn_export_excel)

        self.btn_export_audit = QPushButton("导出审计报告")
        self.btn_export_audit.setObjectName("secondary")
        self.btn_export_audit.clicked.connect(self._on_export_audit)
        self.btn_export_audit.setEnabled(False)
        btn_layout.addWidget(self.btn_export_audit)

        self.btn_view_alerts = QPushButton("查看发现详情")
        self.btn_view_alerts.setObjectName("secondary")
        self.btn_view_alerts.clicked.connect(self._on_view_alerts)
        self.btn_view_alerts.setEnabled(False)
        btn_layout.addWidget(self.btn_view_alerts)

        btn_layout.addSpacing(12)
        self.btn_clear = QPushButton("清空")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_clear.setEnabled(False)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

        self.table_stack = QStackedWidget()
        self.table_single = ResultTable()
        self.table_single.item_double_clicked.connect(self._on_item_double_clicked)
        self.table_audit = AuditResultTable()
        self.table_audit.item_double_clicked.connect(self._on_item_double_clicked)
        self.table_audit.show_audit_detail.connect(self._on_show_audit_detail)
        self.table_stack.addWidget(self.table_single)
        self.table_stack.addWidget(self.table_audit)
        layout.addWidget(self.table_stack, 1)

        self.status_bar = QStatusBar()
        self.status_bar.showMessage("就绪 | 支持格式: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.setStatusBar(self.status_bar)

        self.mode_combo.setCurrentIndex(0)
        self._apply_mode_ui()

    def _on_mode_changed(self, index):
        mode = self.mode_combo.itemData(index)
        self._current_mode = mode
        self._apply_mode_ui()
        self._on_clear()

    def _apply_mode_ui(self):
        if self._current_mode == "audit":
            self.project_name_label.setVisible(True)
            self.project_name_input.setVisible(True)
            self.drop_area.set_hint("拖拽项目文件夹（包含多家公司子文件夹）\n或点击选择文件夹")
            self.btn_select_files.setVisible(False)
            self.btn_select_folder.setVisible(True)
            self.btn_export_audit.setVisible(True)
            self.btn_view_alerts.setVisible(True)
            self.table_stack.setCurrentWidget(self.table_audit)
        else:
            self.project_name_label.setVisible(False)
            self.project_name_input.setVisible(False)
            self.drop_area.set_hint("拖拽文件到此处\n或点击选择文件 / 文件夹")
            self.btn_select_files.setVisible(True)
            self.btn_select_folder.setVisible(True)
            self.btn_export_audit.setVisible(False)
            self.btn_view_alerts.setVisible(False)
            self.table_stack.setCurrentWidget(self.table_single)

    def _init_menubar(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("文件")
        open_files_action = QAction("选择文件...", self)
        open_files_action.setShortcut("Ctrl+O")
        open_files_action.triggered.connect(self._on_select_files)
        file_menu.addAction(open_files_action)

        open_folder_action = QAction("选择文件夹...", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self._on_select_folder)
        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()

        export_menu = file_menu.addMenu("导出")
        export_csv_action = QAction("导出 CSV", self)
        export_csv_action.triggered.connect(self._on_export_csv)
        export_menu.addAction(export_csv_action)

        export_json_action = QAction("导出 JSON", self)
        export_json_action.triggered.connect(self._on_export_json)
        export_menu.addAction(export_json_action)

        export_excel_action = QAction("导出 Excel", self)
        export_excel_action.triggered.connect(self._on_export_excel)
        export_menu.addAction(export_excel_action)

        export_audit_action = QAction("导出审计报告", self)
        export_audit_action.triggered.connect(self._on_export_audit)
        export_menu.addAction(export_audit_action)
        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("编辑")
        clear_action = QAction("清空结果", self)
        clear_action.setShortcut("Ctrl+Shift+C")
        clear_action.triggered.connect(self._on_clear)
        edit_menu.addAction(clear_action)

        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _apply_styles(self):
        self.setStyleSheet(DARK_STYLE)

    def _on_files_dropped(self, paths: List[str]):
        if self._current_mode == "audit":
            dirs = [p for p in paths if os.path.isdir(p)]
            if dirs:
                self._run_audit(dirs[0])
            else:
                files = [p for p in paths if os.path.isfile(p)]
                if files:
                    self._run_audit(os.path.dirname(files[0]))
        else:
            files = self._collect_files(paths)
            if files:
                self._process_files(files)

    def _on_select_files(self):
        if self._current_mode == "audit":
            return
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "Office Documents (*.docx *.xlsx *.pptx *.doc *.xls *.ppt);;"
            "PDF Files (*.pdf);;All Files (*.*)"
        )
        if files:
            self._process_files(files)

    def _on_select_folder(self):
        if self._current_mode == "audit":
            folder = QFileDialog.getExistingDirectory(self, "选择项目文件夹", "")
            if folder:
                self._run_audit(folder)
        else:
            folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
            if folder:
                extractor = MetaExtractor()
                files = extractor.scan_directory(folder, recursive=True)
                if files:
                    self._process_files(files)
                else:
                    QMessageBox.information(self, "提示", "未找到支持的文件")

    def _run_audit(self, folder_path: str):
        project_name = self.project_name_input.text().strip()
        if not project_name:
            project_name = os.path.basename(folder_path)
            self.project_name_input.setText(project_name)

        extractor = MetaExtractor()
        files = extractor.scan_directory(folder_path, recursive=True)
        if not files:
            QMessageBox.information(self, "提示", "未找到支持的文件")
            return

        self.file_count_label.setText(f"{len(files)} 个文件")
        self.status_label.setText(f"准备审计 {len(files)} 个文件...")

        self.btn_export_csv.setEnabled(False)
        self.btn_export_json.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_audit.setEnabled(False)
        self.btn_view_alerts.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_select_files.setEnabled(False)
        self.btn_select_folder.setEnabled(False)

        self.progress_bar.setMaximum(len(files))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        self.worker = AuditWorker(project_name, folder_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_audit_results)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_audit_results(self, audit_result: dict):
        results = audit_result.get('results', [])
        alerts = audit_result.get('alerts', [])
        summary_table = audit_result.get('summary_table', [])
        detail_table = audit_result.get('detail_table', [])

        company_risk = {}
        for row in summary_table:
            company = row.get('公司名称', '')
            risk = row.get('风险等级', 'low')
            if company:
                company_risk[company] = risk

        table_data = []
        for meta in results:
            d = meta.to_dict()
            company = d.get('company', '')
            d['risk_level'] = company_risk.get(company, 'low')
            table_data.append(d)

        self.table_audit.set_data(table_data)
        self._audit_summary = summary_table
        self._audit_detail = detail_table

        self._audit_alerts = []
        for alert in alerts:
            if hasattr(alert, 'rule_name'):
                self._audit_alerts.append({
                    'rule_name': alert.rule_name,
                    'severity': alert.severity,
                    'description': alert.description,
                    'affected_companies': alert.affected_companies,
                    'affected_files': alert.affected_files,
                    'details': alert.details,
                })
            elif isinstance(alert, dict):
                self._audit_alerts.append(alert)

        success_count = sum(1 for r in results if r.parse_success)
        fail_count = len(results) - success_count
        alert_count = len(alerts)

        self.status_label.setText(f"审计完成: {len(results)} 个文件, {alert_count} 条发现")
        self.status_bar.showMessage(f"完成: {success_count} 成功, {fail_count} 失败, {alert_count} 条发现")

        self.btn_export_csv.setEnabled(True)
        self.btn_export_json.setEnabled(True)
        self.btn_export_excel.setEnabled(True)
        self.btn_export_audit.setEnabled(True)
        self.btn_view_alerts.setEnabled(True)

    def _collect_files(self, paths: List[str]) -> List[str]:
        files = []
        for p in paths:
            p_path = Path(p)
            if p_path.is_file():
                if p_path.suffix.lower() in SUPPORTED_EXT:
                    files.append(p)
            elif p_path.is_dir():
                extractor = MetaExtractor()
                files.extend(extractor.scan_directory(p, recursive=True))
        return files

    def _process_files(self, files: List[str]):
        if not files:
            return
        files = sorted(set(files))
        self.file_count_label.setText(f"{len(files)} 个文件")
        self.status_label.setText(f"准备解析 {len(files)} 个文件...")

        self.btn_export_csv.setEnabled(False)
        self.btn_export_json.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_audit.setEnabled(False)
        self.btn_view_alerts.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_select_files.setEnabled(False)
        self.btn_select_folder.setEnabled(False)

        self.progress_bar.setMaximum(len(files))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        self.worker = ExtractionWorker(files)
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_results)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, current: int, total: int, filename: str):
        self.progress_bar.setValue(current)
        self.status_label.setText(f"[{current}/{total}] 正在解析: {filename}")
        self.status_bar.showMessage(f"解析中... {current}/{total} | {filename}")

    def _on_results(self, results: List[dict]):
        self.table_single.set_data(results)
        self.status_label.setText(f"解析完成: {len(results)} 个文件")
        success_count = sum(1 for r in results if not str(r.get('status', '')).startswith('失败'))
        fail_count = len(results) - success_count
        self.status_bar.showMessage(f"完成: {success_count} 成功, {fail_count} 失败")
        self.btn_export_csv.setEnabled(True)
        self.btn_export_json.setEnabled(True)
        self.btn_export_excel.setEnabled(True)

    def _on_finished(self):
        self.progress_bar.setVisible(False)
        self.btn_clear.setEnabled(True)
        self.btn_select_files.setEnabled(True)
        self.btn_select_folder.setEnabled(True)
        self.worker = None

    def _on_clear(self):
        self.table_single.clear_data()
        self.table_audit.clear_data()
        self.file_count_label.setText("0 个文件")
        self.status_label.setText("就绪")
        self.status_bar.showMessage("就绪 | 支持格式: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_json.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_export_audit.setEnabled(False)
        self.btn_view_alerts.setEnabled(False)
        self._audit_summary = []
        self._audit_detail = []
        self._audit_alerts = []

    def _on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "metadata.csv", "CSV Files (*.csv)")
        if path:
            current_table = self.table_audit if self._current_mode == "audit" else self.table_single
            if current_table.export_csv(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")

    def _on_export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 JSON", "metadata.json", "JSON Files (*.json)")
        if path:
            current_table = self.table_audit if self._current_mode == "audit" else self.table_single
            if current_table.export_json(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")

    def _on_export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 Excel", "metadata.xlsx", "Excel Files (*.xlsx)")
        if path:
            current_table = self.table_audit if self._current_mode == "audit" else self.table_single
            if current_table.export_excel(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")

    def _on_export_audit(self):
        if not self._audit_summary and not self._audit_detail:
            QMessageBox.information(self, "提示", "没有审计结果可导出")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出审计报告", "audit_report.xlsx", "Excel Files (*.xlsx)")
        if path:
            if audit_export_to_excel(self._audit_summary, self._audit_detail, path):
                QMessageBox.information(self, "成功", f"审计报告已导出到:\n{path}")

    def _on_show_audit_detail(self, alert: dict):
        dialog = AuditDetailDialog(alert, parent=self)
        dialog.mark_handled.connect(lambda name: logger.info(f"Alert marked handled: {name}"))
        dialog.exec_()

    def _on_view_alerts(self):
        if not self._audit_alerts:
            QMessageBox.information(self, "提示", "当前没有审计发现")
            return
        dialog = AuditAlertListDialog(self._audit_alerts, parent=self)
        dialog.exec_()

    def _on_item_double_clicked(self, filepath: str):
        if os.path.exists(filepath):
            if sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.run(['open', filepath])
            else:
                import subprocess
                subprocess.run(['xdg-open', filepath])

    def _on_log(self, msg: str):
        self.status_bar.showMessage(msg, 3000)

    def _on_about(self):
        QMessageBox.about(
            self, "关于",
            "<b>OfficeMetaExtractor v1.0</b><br>"
            "提取 Office 文档和 PDF 的元信息<br><br>"
            "支持格式: DOCX, XLSX, PPTX, DOC, XLS, PPT, PDF<br><br>"
            "支持导出: CSV, JSON, Excel"
        )

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        event.accept()
