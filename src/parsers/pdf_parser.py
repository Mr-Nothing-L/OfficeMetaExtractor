"""PDF parser implementation."""
from pathlib import Path

from PyPDF2 import PdfReader

from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta


class PdfParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.pdf']
    
    # PDF 文件头: %PDF
    HEADER = [b'%PDF']
    
    @classmethod
    def _validate_header(cls, filepath: Path) -> bool:
        return cls._check_header(filepath, cls.HEADER)
    
    def parse(self, filepath: Path, detailed: bool = False) -> DocumentMeta:
        meta = self._make_meta(filepath, 'PDF')
        
        try:
            reader = PdfReader(filepath)
            info = reader.metadata
            
            if info:
                meta.author = self._safe_str(info.author)
                meta.title = self._safe_str(info.title)
                meta.subject = self._safe_str(info.subject)
                meta.keywords = self._safe_str(getattr(info, 'keywords', None))
                meta.comments = self._safe_str(getattr(info, 'comments', None))
                meta.company = self._safe_str(getattr(info, 'producer', None))
                meta.last_modified_by = self._safe_str(info.creator)
                
                try:
                    if info.creation_date_raw:
                        meta.created = info.creation_date
                except Exception:
                    pass
                try:
                    if info.modification_date_raw:
                        meta.modified = info.modification_date
                except Exception:
                    pass
            
            meta.parse_success = True
            
        except Exception as e:
            meta.parse_success = False
            meta.error_message = f"PDF解析失败: {str(e)}"
        
        return meta
