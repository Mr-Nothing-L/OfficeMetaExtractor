"""OLE parser for legacy Office documents (.doc, .xls, .ppt)."""
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta


def filetime_to_datetime(ft: int) -> Optional[Any]:
    """Convert Windows FILETIME to datetime."""
    if not ft:
        return None
    # FILETIME is 100-nanosecond intervals since 1601-01-01
    from datetime import timedelta, timezone
    try:
        return datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ft / 10)
    except Exception:
        return None


class OleParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.doc', '.xls', '.ppt']
    
    # OLE 文件头: D0CF11E0 (复合文档格式)
    HEADER = [b'\xd0\xcf\x11\xe0']
    
    @classmethod
    def _validate_header(cls, filepath: Path) -> bool:
        return cls._check_header(filepath, cls.HEADER)
    
    def parse(self, filepath: Path) -> DocumentMeta:
        meta = self._make_meta(
            filepath,
            filepath.suffix.upper()[1:]
        )
        
        # Try Windows COM first (most complete)
        try:
            import win32com.client
            return self._parse_com(filepath, meta)
        except ImportError:
            pass
        except Exception as e:
            # COM failed, fall through to olefile
            pass
        
        # Fallback to olefile
        try:
            return self._parse_olefile(filepath, meta)
        except Exception as e:
            meta.parse_success = False
            meta.error_message = f"OLE解析失败: {str(e)}"
            return meta
    
    def _parse_com(self, filepath: Path, meta: DocumentMeta) -> DocumentMeta:
        """Parse using Windows COM."""
        import win32com.client
        
        app_name = self._get_com_app(filepath.suffix)
        app = win32com.client.Dispatch(app_name)
        app.Visible = False
        
        try:
            doc = app.Documents.Open(str(filepath))
            try:
                props = doc.BuiltInDocumentProperties
                meta.author = self._safe_str(props("Author").Value)
                meta.last_modified_by = self._safe_str(props("Last Author").Value)
                meta.title = self._safe_str(props("Title").Value)
                meta.subject = self._safe_str(props("Subject").Value)
                meta.keywords = self._safe_str(props("Keywords").Value)
                meta.comments = self._safe_str(props("Comments").Value)
                meta.template = self._safe_str(props("Template").Value)
                meta.revision = self._safe_str(props("Revision Number").Value)
                
                try:
                    meta.created = props("Creation Date").Value
                except Exception:
                    pass
                try:
                    meta.modified = props("Last Save Time").Value
                except Exception:
                    pass
                try:
                    meta.total_editing_time = props("Total Editing Time").Value
                except Exception:
                    pass
                try:
                    meta.company = self._safe_str(props("Company").Value)
                except Exception:
                    pass
                
                meta.parse_success = True
            finally:
                doc.Close(SaveChanges=False)
        finally:
            app.Quit()
        
        return meta
    
    def _parse_olefile(self, filepath: Path, meta: DocumentMeta) -> DocumentMeta:
        """Parse using olefile fallback."""
        import olefile
        
        ole = olefile.OleFileIO(str(filepath))
        try:
            # SummaryInformation stream
            if ole.exists('\x05SummaryInformation'):
                si = ole.getproperties('\x05SummaryInformation')
                meta.author = self._safe_str(si.get(0x00000004))
                meta.title = self._safe_str(si.get(0x00000002))
                meta.subject = self._safe_str(si.get(0x00000003))
                meta.keywords = self._safe_str(si.get(0x00000005))
                meta.comments = self._safe_str(si.get(0x00000006))
                meta.last_modified_by = self._safe_str(si.get(0x00000008))
                meta.revision = self._safe_str(si.get(0x00000009))
                meta.template = self._safe_str(si.get(0x00000007))
                
                created = si.get(0x0000000C)
                if created:
                    meta.created = filetime_to_datetime(created)
                modified = si.get(0x0000000D)
                if modified:
                    meta.modified = filetime_to_datetime(modified)
            
            # DocumentSummaryInformation stream
            if ole.exists('\x05DocumentSummaryInformation'):
                dsi = ole.getproperties('\x05DocumentSummaryInformation')
                meta.company = self._safe_str(dsi.get(0x0000000F))
                meta.total_editing_time = dsi.get(0x0000000A)
            
            meta.parse_success = True
        finally:
            ole.close()
        
        return meta
    
    def _get_com_app(self, suffix: str) -> str:
        """Get COM application name for file extension."""
        suffix = suffix.lower()
        if suffix == '.doc':
            return 'Word.Application'
        elif suffix == '.xls':
            return 'Excel.Application'
        elif suffix == '.ppt':
            return 'PowerPoint.Application'
        return 'Word.Application'
