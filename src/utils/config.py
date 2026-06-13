"""Config module."""
import sys
from pathlib import Path

APP_NAME = "OfficeMetaExtractor"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Extract metadata from Office documents and PDFs"

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.docx', '.doc',
    '.xlsx', '.xls',
    '.pptx', '.ppt',
    '.pdf'
}

# Supported extensions for display
EXTENSION_LABELS = {
    '.docx': 'DOCX',
    '.doc': 'DOC',
    '.xlsx': 'XLSX',
    '.xls': 'XLS',
    '.pptx': 'PPTX',
    '.ppt': 'PPT',
    '.pdf': 'PDF'
}

# Column headers for result table
COLUMN_HEADERS = [
    "文件名", "格式", "作者", "最后编辑者",
    "创建时间", "修改时间", "标题", "主题", "状态"
]

COLUMN_KEYS = [
    'filename', 'format', 'author', 'last_modified_by',
    'created', 'modified', 'title', 'subject', 'status'
]

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"

# Licensing / purchase configuration
DOCS_DIR = PROJECT_ROOT / "docs"
ACTIVATION_GUIDE_PATH = DOCS_DIR / "activation_guide.html"
PURCHASE_URL = ACTIVATION_GUIDE_PATH.as_uri()
TRIAL_DAYS = 12
