"""Main application window."""
import sys
import os
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QStatusBar,
    QFileDialog, QMessageBox, QSplitter, QFrame,
    QMenuBar, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from .drop_area import DropArea
from .result_table import ResultTable
from .styles import DARK_STYLE

from ..core.extractor_core import MetaExtractor
from ..parsers import SUPPORTED_EXT
from ..utils.logger import logger


class ExtractionWorker(QThread):
    """Background worker for batch extraction."""
    
    progress = pyqtSignal(int, int, str)
    result = pyqtSignal(list)
    finished_signal = pyqtSignal()
    
    def __init__(self, filepaths: List[str]):
        super().__init__()
        self.filepaths = filepaths
        self._stop = False
    
    def run(self):
        extractor = MetaExtractor()
        results = []
        total = len(self.filepaths)
        
        for i, fp in enumerate(self.filepaths):
            if self._stop:
                break
            
            self.progress.emit(i + 1, total, Path(fp).name)
            try:
                result = extractor.extract(fp)
                results.append(result)
            except Exception as e:
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


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OfficeMetaExtractor v1.0")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        self.worker = None
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
        
        # Top area
        top_layout = QHBoxLayout()
        
        title_label = QLabel("OfficeMetaExtractor")
        title_label.setObjectName("title")
        top_layout.addWidget(title_label)
        
        version_label = QLabel("v1.0")
        version_label.setObjectName("subtitle")
        top_layout.addWidget(version_label)
        
        top_layout.addStretch()
        
        self.file_count_label = QLabel("0 个文件")
        self.file_count_label.setObjectName("subtitle")
        top_layout.addWidget(self.file_count_label)
        
        layout.addLayout(top_layout)
        
        # Drop area
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_area)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_select_files = QPushButton("📁 选择文件")
        self.btn_select_files.setToolTip("选择单个或多个文件")
        self.btn_select_files.clicked.connect(self._on_select_files)
        btn_layout.addWidget(self.btn_select_files)
        
        self.btn_select_folder = QPushButton("📂 选择文件夹")
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
        
        btn_layout.addSpacing(12)
        
        self.btn_clear = QPushButton("🗑 清空")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_clear.setEnabled(False)
        btn_layout.addWidget(self.btn_clear)
        
        layout.addLayout(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)
        
        # Result table
        self.table = ResultTable()
        self.table.item_double_clicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.table, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("就绪 | 支持格式: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.setStatusBar(self.status_bar)
    
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
        files = self._collect_files(paths)
        if files:
            self._process_files(files)
    
    def _on_select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "Office Documents (*.docx *.xlsx *.pptx *.doc *.xls *.ppt);;"
            "PDF Files (*.pdf);;"
            "All Files (*.*)"
        )
        if files:
            self._process_files(files)
    
    def _on_select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if folder:
            extractor = MetaExtractor()
            files = extractor.scan_directory(folder, recursive=True)
            if files:
                self._process_files(files)
            else:
                QMessageBox.information(self, "提示", "未找到支持的文件")
    
    def _collect_files(self, paths: List[str]) -> List[str]:
        """Collect files from paths (files or directories)."""
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
        
        # Deduplicate and sort
        files = sorted(set(files))
        
        self.file_count_label.setText(f"{len(files)} 个文件")
        self.status_label.setText(f"准备解析 {len(files)} 个文件...")
        
        self.btn_export_csv.setEnabled(False)
        self.btn_export_json.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
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
        self.table.set_data(results)
        self.status_label.setText(f"解析完成: {len(results)} 个文件")
        
        success_count = sum(1 for r in results if not str(r.get('status', '')).startswith('失败'))
        fail_count = len(results) - success_count
        
        msg = f"完成: {success_count} 成功, {fail_count} 失败"
        self.status_bar.showMessage(msg)
        
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
        self.table.clear_data()
        self.file_count_label.setText("0 个文件")
        self.status_label.setText("就绪")
        self.status_bar.showMessage("就绪 | 支持格式: docx, xlsx, pptx, doc, xls, ppt, pdf")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_json.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.btn_clear.setEnabled(False)
    
    def _on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 CSV", "metadata.csv", "CSV Files (*.csv)"
        )
        if path:
            if self.table.export_csv(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")
    
    def _on_export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 JSON", "metadata.json", "JSON Files (*.json)"
        )
        if path:
            if self.table.export_json(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")
    
    def _on_export_excel(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 Excel", "metadata.xlsx", "Excel Files (*.xlsx)"
        )
        if path:
            if self.table.export_excel(path):
                QMessageBox.information(self, "成功", f"已导出到:\n{path}")
    
    def _on_item_double_clicked(self, filepath: str):
        """Open file with default application."""
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
