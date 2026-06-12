"""PDF parser using PyPDF2."""
from pathlib import Path
from datetime import datetime
from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta


class PdfParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.pdf']
    
    def parse(self, filepath: Path) -> DocumentMeta:
        meta = self._make_meta(filepath, 'PDF')
        
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(filepath))
            info = reader.metadata
            
            if info is not None:
                meta.author = self._safe_str(info.get('/Author'))
                meta.title = self._safe_str(info.get('/Title'))
                meta.subject = self._safe_str(info.get('/Subject'))
                meta.keywords = self._safe_str(info.get('/Keywords'))
                meta.company = self._safe_str(info.get('/Producer'))
                
                # Creator often maps to "last modified by" in some PDFs
                creator = self._safe_str(info.get('/Creator'))
                if creator:
                    meta.last_modified_by = creator
                
                # Parse dates
                try:
                    created_raw = info.get('/CreationDate')
                    if created_raw:
                        meta.created = self._parse_pdf_date(created_raw)
                except Exception:
                    pass
                
                try:
                    mod_raw = info.get('/ModDate')
                    if mod_raw:
                        meta.modified = self._parse_pdf_date(mod_raw)
                except Exception:
                    pass
                
                meta.raw_props = {
                    'producer': self._safe_str(info.get('/Producer')),
                    'creator': self._safe_str(info.get('/Creator')),
                    'trapped': self._safe_str(info.get('/Trapped')),
                }
            
        except Exception as e:
            meta.parse_success = False
            meta.error_message = str(e)
        
        return meta
    
    def _parse_pdf_date(self, date_str) -> datetime:
        """Parse PDF date string format: D:YYYYMMDDHHmmSS[+-]HH'mm'"""
        if isinstance(date_str, str) and date_str.startswith('D:'):
            date_str = date_str[2:]
        else:
            date_str = str(date_str)
        
        # Remove timezone offset for basic parsing
        if date_str and len(date_str) >= 14:
            try:
                return datetime(
                    int(date_str[0:4]), int(date_str[4:6]), int(date_str[6:8]),
                    int(date_str[8:10]), int(date_str[10:12]), int(date_str[12:14])
                )
            except ValueError:
                pass
        
        return None
