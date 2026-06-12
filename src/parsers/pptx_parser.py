"""PPTX parser using python-pptx."""
from pathlib import Path
from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta


class PptxParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.pptx']
    
    def parse(self, filepath: Path) -> DocumentMeta:
        meta = self._make_meta(filepath, 'PPTX')
        
        try:
            from pptx import Presentation
            prs = Presentation(filepath)
            cp = prs.core_properties
            
            meta.author = self._safe_str(cp.author)
            meta.last_modified_by = self._safe_str(cp.last_modified_by)
            meta.created = cp.created
            meta.modified = cp.modified
            meta.title = self._safe_str(cp.title)
            meta.subject = self._safe_str(cp.subject)
            meta.keywords = self._safe_str(cp.keywords)
            meta.comments = self._safe_str(cp.comments)
            meta.revision = self._safe_str(cp.revision)
            
            meta.raw_props = {
                'category': self._safe_str(cp.category),
                'content_status': self._safe_str(cp.content_status),
                'identifier': self._safe_str(cp.identifier),
                'language': self._safe_str(cp.language),
                'version': self._safe_str(cp.version),
            }
            
        except Exception as e:
            meta.parse_success = False
            meta.error_message = str(e)
        
        return meta
