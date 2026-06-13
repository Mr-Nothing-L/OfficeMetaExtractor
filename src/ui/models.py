"""Virtual table models for metadata and audit result tables."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex

from ..utils.cache import ResultCache


class MetadataTableModel(QAbstractTableModel):
    """Base table model backed by an in-memory list of row dicts.

    The model is designed to be fed incrementally by a background worker:
    call ``append_row`` as each file is parsed.  For very large batches the
    worker writes to a CSV cache on disk; the model keeps only the rows it
    needs for display, but in the current implementation it stores all rows
    as lightweight dicts.  This avoids creating one ``QTableWidgetItem`` per
    cell, which is the main UI memory sink for large result sets.
    """

    COLUMN_HEADERS: List[str] = []
    COLUMN_KEYS: List[str] = []

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[Dict[str, Any]] = []
        self._cache: Optional[ResultCache] = None

    # ------------------------------------------------------------------
    # Data source management
    # ------------------------------------------------------------------
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """Replace the entire in-memory dataset."""
        self.beginResetModel()
        self._data = list(data)
        self.endResetModel()

    def clear(self) -> None:
        """Clear all rows."""
        self.beginResetModel()
        self._data = []
        self._cache = None
        self.endResetModel()

    def append_row(self, row: Dict[str, Any]) -> None:
        """Append a single row and notify the view."""
        row_idx = len(self._data)
        self.beginInsertRows(QModelIndex(), row_idx, row_idx)
        self._data.append(row)
        self.endInsertRows()

    def append_rows(self, rows: List[Dict[str, Any]]) -> None:
        """Append multiple rows efficiently."""
        if not rows:
            return
        start = len(self._data)
        end = start + len(rows) - 1
        self.beginInsertRows(QModelIndex(), start, end)
        self._data.extend(rows)
        self.endInsertRows()

    def set_cache(self, cache: ResultCache) -> None:
        """Attach a CSV cache for export / reload."""
        self._cache = cache

    def load_from_cache(self, cache: Optional[ResultCache] = None) -> None:
        """Load all rows from the given or attached cache into memory."""
        cache = cache or self._cache
        if cache is None:
            self.clear()
            return
        self.set_data(list(cache.iter_rows()))

    def get_data(self) -> List[Dict[str, Any]]:
        """Return the full in-memory dataset."""
        return self._data

    def row_count(self) -> int:
        """Return number of rows."""
        return len(self._data)

    def row_for_index(self, index: QModelIndex) -> Optional[Dict[str, Any]]:
        """Return the row dict for the given model index."""
        row = index.row()
        if 0 <= row < len(self._data):
            return self._data[row]
        return None

    # ------------------------------------------------------------------
    # QAbstractTableModel implementation
    # ------------------------------------------------------------------
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.COLUMN_HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.COLUMN_HEADERS):
                return self.COLUMN_HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._data) or col < 0 or col >= len(self.COLUMN_KEYS):
            return None

        item = self._data[row]
        key = self.COLUMN_KEYS[col]

        if role in (Qt.DisplayRole, Qt.EditRole):
            val = item.get(key, '')
            if val is None:
                return ''
            return str(val)

        if role == Qt.UserRole:
            return item.get('filepath', '')

        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.ToolTipRole:
            val = item.get(key, '')
            if val:
                return str(val)

        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class ResultTableModel(MetadataTableModel):
    """Model for single-file extraction results."""

    COLUMN_HEADERS = [
        "文件名", "格式", "作者", "最后编辑者",
        "创建时间", "修改时间", "标题", "主题", "状态"
    ]
    COLUMN_KEYS = [
        'filename', 'format', 'author', 'last_modified_by',
        'created', 'modified', 'title', 'subject', 'status'
    ]


class AuditTableModel(MetadataTableModel):
    """Model for batch/audit extraction results."""

    COLUMN_HEADERS = [
        "文件名", "格式", "公司", "作者", "最后编辑者",
        "创建时间", "修改时间", "标题", "状态"
    ]
    COLUMN_KEYS = [
        'filename', 'format', 'company', 'author', 'last_modified_by',
        'created', 'modified', 'title', 'status'
    ]
