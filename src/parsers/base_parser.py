"""Base parser class."""
from abc import ABC, abstractmethod
from pathlib import Path
from ..utils.datamodel import DocumentMeta


class BaseParser(ABC):
    """Base class for all document parsers."""
    
    SUPPORTED_EXTENSIONS = []
    
    @classmethod
    def can_parse(cls, filepath: Path) -> bool:
        if filepath.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            return False
        # 验证文件头（magic number）
        return cls._validate_header(filepath)
    
    @classmethod
    def _validate_header(cls, filepath: Path) -> bool:
        """Validate file header (magic number). Override in subclasses."""
        return True  # 默认不验证，由子类实现
    
    @classmethod
    def _check_header(cls, filepath: Path, expected_headers: list) -> bool:
        """Check if file starts with expected header bytes."""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(8)
                for expected in expected_headers:
                    if header.startswith(expected):
                        return True
            return False
        except Exception:
            return False
    
    @abstractmethod
    def parse(self, filepath: Path) -> DocumentMeta:
        pass
    
    def _make_meta(self, filepath: Path, fmt: str) -> DocumentMeta:
        meta = DocumentMeta(
            filename=filepath.name,
            filepath=str(filepath),
            file_format=fmt
        )
        try:
            meta.file_size = filepath.stat().st_size
        except Exception:
            pass
        return meta
    
    def _safe_str(self, val) -> str:
        if val is None:
            return None
        if isinstance(val, str):
            return val
        return str(val)
