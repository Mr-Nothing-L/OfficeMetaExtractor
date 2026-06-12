"""XLSX parser using openpyxl."""
from pathlib import Path
from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta


class XlsxParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.xlsx']
    
    def parse(self, filepath: Path) -> DocumentMeta:
        meta = self._make_meta(filepath, 'XLSX')
        
        try:
            from openpyxl import load_workbook
            wb = load_workbook(filepath, read_only=True, data_only=True)
            cp = wb.properties
            
            meta.author = self._safe_str(cp.creator)
            meta.last_modified_by = self._safe_str(cp.last_modified_by)
            meta.created = cp.created
            meta.modified = cp.modified
            meta.title = self._safe_str(cp.title)
            meta.subject = self._safe_str(cp.subject)
            meta.keywords = self._safe_str(cp.keywords)
            meta.comments = self._safe_str(cp.description)
            
            meta.raw_props = {
                'category': self._safe_str(cp.category),
                'language': self._safe_str(cp.language),
                'revision': self._safe_str(cp.revision),
                'version': self._safe_str(cp.version),
                'content_status': self._safe_str(cp.contentStatus),
                'identifier': self._safe_str(cp.identifier),
            }
            
            wb.close()
            
        except Exception as e:
            meta.parse_success = False
            meta.error_message = str(e)
        
        return meta
