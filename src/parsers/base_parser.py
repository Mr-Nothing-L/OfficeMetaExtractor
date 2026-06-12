"""Base parser class."""
from abc import ABC, abstractmethod
from pathlib import Path
from ..utils.datamodel import DocumentMeta


class BaseParser(ABC):
    """Base class for all document parsers."""
    
    SUPPORTED_EXTENSIONS = []
    
    @classmethod
    def can_parse(cls, filepath: Path) -> bool:
        return filepath.suffix.lower() in cls.SUPPORTED_EXTENSIONS
    
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
