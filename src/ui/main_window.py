"""Main application window with clean, modern UI."""
import sys
import os
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QStatusBar,
    QFileDialog, QMessageBox,
    QMenuBar, QMenu, QAction, QComboBox, QLineEdit,
    QStackedWidget, QFrame, QToolButton, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from .drop_area import DropArea
from .result_table import ResultTable
from .audit_result_table import AuditResultTable
from .audit_detail_dialog import AuditDetailDialog, AuditAlertListDialog
from .ascii_starfield import AsciiStarfield
from .styles import DARK_STYLE

from ..core.extractor_core import MetaExtractor
from ..parsers import SUPPORTED_EXT
from ..utils.logger import logger
from ..utils.cache import get_default_cache
from ..audit import export_to_excel as audit_export_to_excel


class ExtractionWorker(QThread):
    """Background worker for batch extraction with per-file timeout."""

    progress = pyqtSignal(int, int, str)
    row_ready = pyqtSignal(dict)
    result = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    FILE_TIMEOUT = 30

    def __init__(self, filepaths: List[str], detailed: bool = False):
        super().__init__()
        self.filepaths = filepaths
        self.detailed = detailed
        self._stop = False

    def _extract_with_timeout(self, extractor, filepath: str) -> dict:
        import threading
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = extractor.extract(filepath, detailed=self.detailed)
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
        extractor = MetaExtractor(detailed=self.detailed)
        total = len(self.filepaths)
        success_count = 0
        fail_count = 0

        for i, fp in enumerate(self.filepaths):
            if self._stop:
                break
            self.progress.emit(i + 1, total, Path(fp).name)
            try:
                result = self._extract_with_timeout(extractor, fp)
                success_count += 1
            except TimeoutError as e:
                logger.warning(f"Timeout parsing {fp}: {e}")
                result = {
                    'filepath': fp,
                    'filename': Path(fp).name,
                    'format': Path(fp).suffix.upper()[1:] or 'UNKNOWN',
                    'status': f'失败: 解析超时（文件可能过大或格式异常）'
                }
                fail_count += 1
            except Exception as e:
                logger.error(f"Failed to extract {fp}: {e}")
                result = {
                    'filepath': fp,
                    'filename': Path(fp).name,
                    'format': Path(fp).suffix.upper()[1:] or 'UNKNOWN',
                    'status': f'失败: {str(e)}'
                }
                fail_count += 1

            self.row_ready.emit(result)

        self.result.emit({
            'total': total,
            'success_count': success_count,
            'fail_count': fail_count,
        })
        self.finished_signal.emit()

    def stop(self):
        self._stop = True


class AuditWorker(QThread):
    """Background worker for batch/audit mode extraction."""

    progress = pyqtSignal(int, int, str)
    row_ready = pyqtSignal(dict)
    result = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, project_name: str, folder_path: str,
                 files: List[str] = None, detailed: bool = False):
        super().__init__()
        self.project_name = project_name
        self.folder_path = folder_path
        self.files = files
        self.detailed = detailed
        self._stop = False

    def run(self):
        extractor = MetaExtractor(detailed=self.detailed)
        files = self.files or extractor.scan_directory(self.folder_path, recursive=True)
        total = len(files)

        for i, fp in enumerate(files):
            if self._stop:
                break
            self.progress.emit(i + 1, total, Path(fp).name)

        audit_result = extractor.audit(
            self.project_name,
            self.folder_path,
            detailed=self.detailed,
            files=files,
        )

        # Emit each parsed row for cache / UI incrementally.
        for meta in audit_result.get('results', []):
            if self._stop:
                break
            self.row_ready.emit(meta.to_dict())

        self.result.emit(audit_result)
        self.finished_signal.emit()

    def stop(self):
        self._stop = True


class MainWindow(QMainWindow):
    """Main application window with clean, modern UI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OfficeMetaExtractor v2.0.0")
        self.setMinimumSize(960, 640)
        self.resize(1080, 760)

        self.worker = None
        self._current_mode = "audit"
        self._audit_summary = []
        self._audit_detail = []
        self._audit_alerts = []
        self._cache = get_default_cache()
        self._init_ui()
        self._apply_styles()
        self._init_menubar()

        logger.add_listener(self._on_log)

    def _init_ui(self):
        # Root central widget and opaque dark surface panel.
        self._root = QWidget()
        self._root.setObjectName("centralRoot")
        self.setCentralWidget(self._root)

        self._container = QWidget(self._root)
        self._container.setObjectName("surfacePanel")

        # The starfield lives inside the container, behind the result tables,
        # so it shows through only the semi-transparent table area.
        self._starfield = AsciiStarfield(self._container)
        self._starfield.lower()

        main_layout = QVBoxLayout(self._container)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(28, 20, 28, 20)

        # ===== Header Row =====
        header_row = QHBoxLayout()
        header_row.setSpacing(16)
        header_row.setContentsMargins(0, 0, 0, 0)

        # Left: brand + file count
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(8)
        brand_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_title = QLabel("OfficeMetaExtractor")
        self.lbl_title.setObjectName("title")
        brand_layout.addWidget(self.lbl_title)

        self.lbl_version = QLabel("v2.0.0")
        self.lbl_version.setObjectName("subtitle")
        brand_layout.addWidget(self.lbl_version)

        brand_layout.addSpacing(12)

        self.lbl_file_count = QLabel("0 个文件")
        self.lbl_file_count.setObjectName("fileCount")
        brand_layout.addWidget(self.lbl_file_count)

        header_row.addLayout(brand_layout)
        header_row.addStretch()

        # Right: mode selector
        self.lbl_mode = QLabel("模式")
        self.lbl_mode.setObjectName("modeLabel")
        header_row.addWidget(self.lbl_mode)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItem("批量提取", "audit")
        self.cmb_mode.addItem("单文件提取", "single")
        self.cmb_mode.setEditable(True)
        self.cmb_mode.lineEdit().setReadOnly(True)
        self.cmb_mode.lineEdit().setAlignment(Qt.AlignCenter)
        self.cmb_mode.lineEdit().setFrame(False)
        self.cmb_mode.currentIndexChanged.connect(self._on_mode_changed)
        header_row.addWidget(self.cmb_mode)

        header_widget = QWidget()
        header_widget.setObjectName("panelRow")
        header_widget.setLayout(header_row)
        main_layout.addWidget(header_widget)

        # Separator
        sep1 = QFrame()
        sep1.setObjectName("sectionSeparator")
        main_layout.addSpacing(10)
        main_layout.addWidget(sep1)
        main_layout.addSpacing(10)

        # ===== Project Name Row (batch mode) =====
        project_row = QHBoxLayout()
        project_row.setSpacing(10)
        project_row.setContentsMargins(0, 0, 0, 0)

        self.lbl_project_name = QLabel("项目名称")
        self.lbl_project_name.setObjectName("modeLabel")
        project_row.addWidget(self.lbl_project_name)

        self.edt_project_name = QLineEdit()
        self.edt_project_name.setPlaceholderText("输入项目名称（用于模板关联检测）")
        project_row.addWidget(self.edt_project_name, 1)

        self._project_row_widget = QWidget()
        self._project_row_widget.setObjectName("panelRow")
        self._project_row_widget.setLayout(project_row)
        main_layout.addWidget(self._project_row_widget)

        # ===== Drop Area =====
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        main_layout.addWidget(self.drop_area)
        main_layout.addSpacing(10)

        # ===== Options Row =====
        options_row = QHBoxLayout()
        options_row.setSpacing(12)
        options_row.setContentsMargins(0, 0, 0, 0)

        self.chk_detailed = QCheckBox("深度解析（加载完整文档）")
        self.chk_detailed.setObjectName("checkBox")
        self.chk_detailed.setToolTip("默认仅读取 OOXML/OLE 核心属性；勾选后加载完整文档以获取更完整信息，但会占用更多内存和时间")
        options_row.addWidget(self.chk_detailed)

        options_row.addStretch()

        options_widget = QWidget()
        options_widget.setObjectName("panelRow")
        options_widget.setLayout(options_row)
        main_layout.addWidget(options_widget)
        main_layout.addSpacing(10)

        # ===== Action Buttons Row =====
        action_row = QHBoxLayout()
        action_row.setSpacing(14)
        action_row.setContentsMargins(0, 0, 0, 0)

        # Primary actions
        self.btn_select_files = QPushButton("选择文件")
        self.btn_select_files.setObjectName("primary")
        self.btn_select_files.setToolTip("选择单个或多个文件")
        self.btn_select_files.clicked.connect(self._on_select_files)
        action_row.addWidget(self.btn_select_files)

        self.btn_select_folder = QPushButton("选择文件夹")
        self.btn_select_folder.setObjectName("primary")
        self.btn_select_folder.setToolTip("递归扫描文件夹")
        self.btn_select_folder.clicked.connect(self._on_select_folder)
        action_row.addWidget(self.btn_select_folder)

        action_row.addStretch()

        # Export dropdown
        self.btn_export = QToolButton()
        self.btn_export.setObjectName("secondary")
        self.btn_export.setText("导出")
        self.btn_export.setToolTip("导出当前结果")
        self.btn_export.setPopupMode(QToolButton.InstantPopup)
        self._export_menu = QMenu(self.btn_export)
        self._export_menu.setObjectName("exportMenu")

        act_csv = QAction("导出 CSV", self)
        act_csv.triggered.connect(self._on_export_csv)
        self._export_menu.addAction(act_csv)

        act_json = QAction("导出 JSON", self)
        act_json.triggered.connect(self._on_export_json)
        self._export_menu.addAction(act_json)

        act_excel = QAction("导出 Excel", self)
        act_excel.triggered.connect(self._on_export_excel)
        self._export_menu.addAction(act_excel)

        self._export_menu.addSeparator()

        act_audit = QAction("导出审计报告", self)
        act_audit.triggered.connect(self._on_export_audit)
        self._export_menu.addAction(act_audit)

        self.btn_export.setMenu(self._export_menu)
        self.btn_export.setEnabled(False)
        action_row.addWidget(self.btn_export)

        self.btn_view_alerts = QPushButton("查看发现")
        self.btn_view_alerts.setObjectName("secondary")
        self.btn_view_alerts.setToolTip("查看批量检测发现")
        self.btn_view_alerts.clicked.connect(self._on_view_alerts)
        self.btn_view_alerts.setEnabled(False)
        action_row.addWidget(self.btn_view_alerts)

        self.btn_clear = QPushButton("清空")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.setToolTip("清空结果")
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_clear.setEnabled(False)
        action_row.addWidget(self.btn_clear)

        action_widget = QWidget()
        action_widget.setObjectName("panelRow")
        action_widget.setLayout(action_row)
        main_layout.addWidget(action_widget)

        # ===== Progress & Status =====
        status_row = QHBoxLayout()
        status_row.setSpacing(12)
        status_row.setContentsMargins(0, 0, 0, 0)

        self.prg_progress = QProgressBar()
        self.prg_progress.setVisible(False)
        self.prg_progress.setMaximumWidth(180)
        status_row.addWidget(self.prg_progress)

        self.lbl_status = QLabel("就绪")
        self.lbl_status.setObjectName("status")
        status_row.addWidget(self.lbl_status, 1)

        status_widget = QWidget()
        status_widget.setObjectName("panelRow")
        status_widget.setLayout(status_row)
        main_layout.addWidget(status_widget)
        main_layout.addSpacing(6)

        # ===== Table =====
        self.tbl_stack = QStackedWidget()
        self.tbl_stack.setObjectName("resultTableStack")

        self.tbl_single = ResultTable()
        self.tbl_single.setObjectName("resultTable")
        self.tbl_single.item_double_clicked.connect(self._on_item_double_clicked)

        self.tbl_audit = AuditResultTable()
        self.tbl_audit.setObjectName("resultTable")
        self.tbl_audit.item_double_clicked.connect(self._on_item_double_clicked)
        self.tbl_audit.show_audit_detail.connect(self._on_show_audit_detail)
        self.tbl_stack.addWidget(self.tbl_single)
        self.tbl_stack.addWidget(self.tbl_audit)
        main_layout.addWidget(self.tbl_stack, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("就绪 | 支持格式: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.setStatusBar(self.status_bar)

        self.cmb_mode.setCurrentIndex(0)
        self._apply_mode_ui()
        self._sync_layers()

    def _sync_layers(self):
        """Keep the container and starfield filling the central widget."""
        if not hasattr(self, "_root"):
            return
        rect = self._root.rect()
        self._starfield.setGeometry(rect)
        self._container.setGeometry(rect)
        self._container.raise_()
        if hasattr(self, "_starfield"):
            self._starfield.lower()
        if hasattr(self, "tbl_stack"):
            self.tbl_stack.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_layers()

    def _on_mode_changed(self, index):
        mode = self.cmb_mode.itemData(index)
        self._current_mode = mode
        self._apply_mode_ui()
        self._on_clear()

    def _apply_mode_ui(self):
        is_audit = self._current_mode == "audit"

        self._project_row_widget.setVisible(is_audit)
        self.btn_view_alerts.setVisible(is_audit)

        # Show/hide audit report export action in dropdown
        for action in self._export_menu.actions():
            if action.text() == "导出审计报告":
                action.setVisible(is_audit)

        if is_audit:
            self.drop_area.set_hint("拖拽项目文件夹（包含多家公司子文件夹）\n或点击选择文件夹")
            self.btn_select_files.setVisible(False)
            self.btn_select_folder.setVisible(True)
            self.tbl_stack.setCurrentWidget(self.tbl_audit)
        else:
            self.drop_area.set_hint("拖拽文件到此处\n或点击选择文件 / 文件夹")
            self.btn_select_files.setVisible(True)
            self.btn_select_folder.setVisible(True)
            self.tbl_stack.setCurrentWidget(self.tbl_single)

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
                extractor = MetaExtractor(detailed=self.chk_detailed.isChecked())
                files = extractor.scan_directory(folder, recursive=True)
                if files:
                    self._process_files(files)
                else:
                    QMessageBox.information(self, "提示", "未找到支持的文件")

    def _run_audit(self, folder_path: str):
        project_name = self.edt_project_name.text().strip()
        if not project_name:
            project_name = os.path.basename(folder_path)
            self.edt_project_name.setText(project_name)

        extractor = MetaExtractor(detailed=self.chk_detailed.isChecked())
        files = extractor.scan_directory(folder_path, recursive=True)
        if not files:
            QMessageBox.information(self, "提示", "未找到支持的文件")
            return

        self._cache.clear()
        self.tbl_audit.clear_data()
        self.lbl_file_count.setText(f"{len(files)} 个文件")
        self.lbl_status.setText(f"准备批量提取 {len(files)} 个文件...")

        self.btn_export.setEnabled(False)
        self.btn_view_alerts.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_select_files.setEnabled(False)
        self.btn_select_folder.setEnabled(False)
        self.chk_detailed.setEnabled(False)

        self.prg_progress.setMaximum(len(files))
        self.prg_progress.setValue(0)
        self.prg_progress.setVisible(True)

        self.worker = AuditWorker(
            project_name,
            folder_path,
            files=files,
            detailed=self.chk_detailed.isChecked(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.row_ready.connect(self._on_audit_row_ready)
        self.worker.result.connect(self._on_audit_results)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_audit_row_ready(self, row: dict):
        self._cache.append(row)
        self.tbl_audit.append_row(row)

    def _on_audit_results(self, audit_result: dict):
        results = audit_result.get('results', [])
        alerts = audit_result.get('alerts', [])
        summary_table = audit_result.get('summary_table', [])
        detail_table = audit_result.get('detail_table', [])

        table_data = []
        for meta in results:
            d = meta.to_dict()
            table_data.append(d)

        self.tbl_audit.set_data(table_data)
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

        self.lbl_status.setText(f"批量提取完成: {len(results)} 个文件, {alert_count} 条发现")
        self.status_bar.showMessage(f"完成: {success_count} 成功, {fail_count} 失败, {alert_count} 条发现")

        self.btn_export.setEnabled(True)
        self.btn_view_alerts.setEnabled(True)

    def _collect_files(self, paths: List[str]) -> List[str]:
        files = []
        for p in paths:
            p_path = Path(p)
            if p_path.is_file():
                if p_path.suffix.lower() in SUPPORTED_EXT:
                    files.append(p)
            elif p_path.is_dir():
                extractor = MetaExtractor(detailed=self.chk_detailed.isChecked())
                files.extend(extractor.scan_directory(p, recursive=True))
        return files

    def _process_files(self, files: List[str]):
        if not files:
            return
        files = sorted(set(files))
        self._cache.clear()
        self.tbl_single.clear_data()
        self.lbl_file_count.setText(f"{len(files)} 个文件")
        self.lbl_status.setText(f"准备解析 {len(files)} 个文件...")

        self.btn_export.setEnabled(False)
        self.btn_view_alerts.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_select_files.setEnabled(False)
        self.btn_select_folder.setEnabled(False)
        self.chk_detailed.setEnabled(False)

        self.prg_progress.setMaximum(len(files))
        self.prg_progress.setValue(0)
        self.prg_progress.setVisible(True)

        self.worker = ExtractionWorker(files, detailed=self.chk_detailed.isChecked())
        self.worker.progress.connect(self._on_progress)
        self.worker.row_ready.connect(self._on_single_row_ready)
        self.worker.result.connect(self._on_results)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_single_row_ready(self, row: dict):
        self._cache.append(row)
        self.tbl_single.append_row(row)

    def _on_progress(self, current: int, total: int, filename: str):
        self.prg_progress.setValue(current)
        self.lbl_status.setText(f"[{current}/{total}] 正在解析: {filename}")
        self.status_bar.showMessage(f"解析中... {current}/{total} | {filename}")

    def _on_results(self, summary: dict):
        total = summary.get('total', 0)
        success_count = summary.get('success_count', 0)
        fail_count = summary.get('fail_count', 0)
        self.lbl_status.setText(f"解析完成: {total} 个文件")
        self.status_bar.showMessage(f"完成: {success_count} 成功, {fail_count} 失败")
        self.btn_export.setEnabled(True)

    def _on_finished(self):
        self.prg_progress.setVisible(False)
        self.btn_clear.setEnabled(True)
        self.btn_select_files.setEnabled(True)
        self.btn_select_folder.setEnabled(True)
        self.chk_detailed.setEnabled(True)
        self.worker = None

    def _on_clear(self):
        self._cache.clear()
        self.tbl_single.clear_data()
        self.tbl_audit.clear_data()
        self.lbl_file_count.setText("0 个文件")
        self.lbl_status.setText("就绪")
        self.status_bar.showMessage("就绪 | 支持格式: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.btn_export.setEnabled(False)
        self.btn_view_alerts.setEnabled(False)
        self._audit_summary = []
        self._audit_detail = []
        self._audit_alerts = []

    def _on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "metadata.csv", "CSV Files (*.csv)")
        if path:
            current_table = self.tbl_audit if self._current_mode == "audit" else self.tbl_single
            if current_table.export_csv(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")

    def _on_export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 JSON", "metadata.json", "JSON Files (*.json)")
        if path:
            current_table = self.tbl_audit if self._current_mode == "audit" else self.tbl_single
            if current_table.export_json(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")

    def _on_export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出 Excel", "metadata.xlsx", "Excel Files (*.xlsx)")
        if path:
            current_table = self.tbl_audit if self._current_mode == "audit" else self.tbl_single
            if current_table.export_excel(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")

    def _on_export_audit(self):
        if not self._audit_summary and not self._audit_detail:
            QMessageBox.information(self, "提示", "没有批量结果可导出")
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
            QMessageBox.information(self, "提示", "当前没有检测发现")
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
            "<b>OfficeMetaExtractor v2.0.0</b><br>"
            "提取 Office 文档和 PDF 的元信息<br><br>"
            "支持格式: DOCX, XLSX, PPTX, DOC, XLS, PPT, PDF<br><br>"
            "支持导出: CSV, JSON, Excel"
        )

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        event.accept()
