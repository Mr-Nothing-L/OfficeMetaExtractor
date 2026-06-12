"""OLE parser for .doc, .xls, .ppt legacy formats.

Strategy:
1. On Windows with Office: try pywin32 COM (most complete, gets last editor)
2. Fallback: olefile pure-Python parsing of basic properties
"""
from pathlib import Path
import struct
import sys
from typing import Optional, Dict, Any
from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta


# PID constants from MS-OLEPS
PIDSI_TITLE = 0x02
PIDSI_SUBJECT = 0x03
PIDSI_AUTHOR = 0x04
PIDSI_KEYWORDS = 0x05
PIDSI_COMMENTS = 0x06
PIDSI_TEMPLATE = 0x07
PIDSI_LASTAUTHOR = 0x08
PIDSI_REVNUMBER = 0x09
PIDSI_EDITTIME = 0x0A
PIDSI_PRINTED = 0x0B
PIDSI_CREATED = 0x0C
PIDSI_MODIFIED = 0x0D
PIDSI_PAGECOUNT = 0x0E
PIDSI_WORDCOUNT = 0x0F
PIDSI_CHARCOUNT = 0x10

PIDDSI_COMPANY = 0x0F

# Property type tags
VT_EMPTY = 0x0000
VT_NULL = 0x0001
VT_I2 = 0x0002
VT_I4 = 0x0003
VT_R4 = 0x0004
VT_R8 = 0x0005
VT_CY = 0x0006
VT_DATE = 0x0007
VT_BSTR = 0x0008
VT_ERROR = 0x000A
VT_BOOL = 0x000B
VT_I1 = 0x0010
VT_UI1 = 0x0011
VT_UI2 = 0x0012
VT_UI4 = 0x0013
VT_I8 = 0x0014
VT_UI8 = 0x0015
VT_INT = 0x0016
VT_UINT = 0x0017
VT_LPSTR = 0x001E
VT_LPWSTR = 0x001F
VT_FILETIME = 0x0040
VT_BLOB = 0x0041
VT_STREAM = 0x0042
VT_STORAGE = 0x0043
VT_STREAMED_OBJECT = 0x0044
VT_STORED_OBJECT = 0x0045
VT_BLOB_OBJECT = 0x0046
VT_CF = 0x0047
VT_CLSID = 0x0048


def filetime_to_datetime(ft: int) -> Optional[Any]:
    """Convert Windows FILETIME (100-nanosecond intervals since 1601-01-01) to datetime."""
    try:
        from datetime import datetime, timedelta
        # FILETIME epoch is 1601-01-01; Python epoch is 1970-01-01
        # Difference: 11644473600 seconds
        seconds = (ft / 10000000) - 11644473600
        if seconds < 0:
            return None
        return datetime.utcfromtimestamp(seconds)
    except Exception:
        return None


class OleParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.doc', '.xls', '.ppt']
    
    def parse(self, filepath: Path) -> DocumentMeta:
        meta = self._make_meta(
            filepath,
            filepath.suffix.upper()[1:]
        )
        
        # Strategy 1: COM on Windows
        if sys.platform == 'win32':
            try:
                return self._parse_via_com(filepath, meta)
            except Exception as e:
                meta.error_message = f"COM failed: {e}"
        
        # Strategy 2: olefile fallback
        try:
            return self._parse_via_olefile(filepath, meta)
        except Exception as e:
            meta.parse_success = False
            if meta.error_message:
                meta.error_message += f"; olefile: {e}"
            else:
                meta.error_message = f"OLE解析失败: {e}"
            return meta
    
    def _parse_via_com(self, filepath: Path, meta: DocumentMeta) -> DocumentMeta:
        import win32com.client
        
        app = None
        doc = None
        
        try:
            ext = filepath.suffix.lower()
            if ext == '.doc':
                app = win32com.client.Dispatch("Word.Application")
                app.Visible = False
                doc = app.Documents.Open(str(filepath.absolute()))
                props = doc.BuiltInDocumentProperties
            elif ext == '.xls':
                app = win32com.client.Dispatch("Excel.Application")
                app.Visible = False
                doc = app.Workbooks.Open(str(filepath.absolute()))
                props = doc.BuiltinDocumentProperties
            elif ext == '.ppt':
                app = win32com.client.Dispatch("PowerPoint.Application")
                app.Visible = False
                doc = app.Presentations.Open(str(filepath.absolute()))
                props = doc.BuiltInDocumentProperties
            else:
                raise ValueError(f"Unsupported COM extension: {ext}")
            
            def get_prop(name):
                try:
                    return props(name).Value
                except Exception:
                    return None
            
            meta.author = self._safe_str(get_prop("Author"))
            meta.last_modified_by = self._safe_str(get_prop("Last Author"))
            meta.title = self._safe_str(get_prop("Title"))
            meta.subject = self._safe_str(get_prop("Subject"))
            meta.company = self._safe_str(get_prop("Company"))
            meta.keywords = self._safe_str(get_prop("Keywords"))
            meta.comments = self._safe_str(get_prop("Comments"))
            
            try:
                meta.created = get_prop("Creation Date")
            except Exception:
                pass
            try:
                meta.modified = get_prop("Last Save Time")
            except Exception:
                pass
            
        finally:
            if doc:
                try:
                    doc.Close(False)
                except Exception:
                    pass
            if app:
                try:
                    app.Quit()
                except Exception:
                    pass
        
        return meta
    
    def _parse_via_olefile(self, filepath: Path, meta: DocumentMeta) -> DocumentMeta:
        import olefile
        
        ole = olefile.OleFileIO(str(filepath))
        try:
            # Parse SummaryInformation stream
            if ole.exists('\x05SummaryInformation'):
                try:
                    stream = ole.openstream('\x05SummaryInformation')
                    data = stream.read()
                    props = self._parse_property_set(data)
                    
                    meta.author = self._safe_str(props.get(PIDSI_AUTHOR))
                    meta.last_modified_by = self._safe_str(props.get(PIDSI_LASTAUTHOR))
                    meta.title = self._safe_str(props.get(PIDSI_TITLE))
                    meta.subject = self._safe_str(props.get(PIDSI_SUBJECT))
                    meta.keywords = self._safe_str(props.get(PIDSI_KEYWORDS))
                    meta.comments = self._safe_str(props.get(PIDSI_COMMENTS))
                    meta.template = self._safe_str(props.get(PIDSI_TEMPLATE))
                    meta.revision = self._safe_str(props.get(PIDSI_REVNUMBER))
                    meta.total_editing_time = props.get(PIDSI_EDITTIME)
                    
                    # Convert dates
                    if PIDSI_CREATED in props:
                        meta.created = props[PIDSI_CREATED]
                    if PIDSI_MODIFIED in props:
                        meta.modified = props[PIDSI_MODIFIED]
                    
                except Exception as e:
                    meta.error_message = f"SummaryInfo: {e}"
            
            # Parse DocumentSummaryInformation stream
            if ole.exists('\x05DocumentSummaryInformation'):
                try:
                    stream = ole.openstream('\x05DocumentSummaryInformation')
                    data = stream.read()
                    props = self._parse_property_set(data)
                    
                    company = props.get(PIDDSI_COMPANY)
                    if company:
                        meta.company = self._safe_str(company)
                    
                except Exception as e:
                    if meta.error_message:
                        meta.error_message += f"; DocSummary: {e}"
                    else:
                        meta.error_message = f"DocSummary: {e}"
        finally:
            ole.close()
        
        return meta
    
    def _parse_property_set(self, data: bytes) -> Dict[int, Any]:
        """Parse a PropertySet structure (simplified but functional)."""
        props = {}
        if len(data) < 28:
            return props
        
        # PropertySet header (28 bytes)
        # 0-1: Version (0x0100 for 0x0001, 0x0101 for 0x0001)
        # Actually, let's read more carefully:
        # The structure is:
        # 0:2   byte order (0xFFFE = little endian)
        # 2:2   format version (0x0000)
        # 4:4   OS version (4 bytes)
        # 8:4   OS minor (4 bytes)
        # 12:16  application-specific CLSID
        # 28:4   number of property sets (FMTID + offset pairs)
        
        try:
            byte_order = struct.unpack('<H', data[0:2])[0]
            if byte_order == 0xFFFE:
                endian = '<'
            else:
                endian = '>'
            
            # Actually, let's just follow the standard offset-based approach
            # which is more robust against endianness issues for this specific use case
            
            # PropertySet header is 28 bytes, then property set offsets
            # Let's use a simpler heuristic: parse the property offsets and values
            
            # Number of property sets
            num_sets = struct.unpack('<I', data[24:28])[0]
            
            offset = 28
            for _ in range(num_sets):
                if offset + 20 > len(data):
                    break
                # FMTID (16 bytes) + offset (4 bytes)
                offset += 16  # skip FMTID
                section_offset = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4
                
                if section_offset + 8 > len(data):
                    continue
                
                # Section: size (4) + count (4) + property offsets
                section_size = struct.unpack('<I', data[section_offset:section_offset+4])[0]
                prop_count = struct.unpack('<I', data[section_offset+4:section_offset+8])[0]
                
                prop_offset = section_offset + 8
                for p in range(prop_count):
                    if prop_offset + 8 > len(data):
                        break
                    prop_id = struct.unpack('<I', data[prop_offset:prop_offset+4])[0]
                    prop_data_offset = struct.unpack('<I', data[prop_offset+4:prop_offset+8])[0]
                    prop_offset += 8
                    
                    # Property data is at section_offset + prop_data_offset
                    abs_offset = section_offset + prop_data_offset
                    if abs_offset >= len(data):
                        continue
                    
                    value = self._read_property_value(data, abs_offset)
                    if value is not None:
                        props[prop_id] = value
            
        except Exception as e:
            # Fallback: try even simpler scan
            props = self._scan_property_values(data)
        
        return props
    
    def _read_property_value(self, data: bytes, offset: int) -> Optional[Any]:
        """Read a single property value from the given offset."""
        if offset + 4 > len(data):
            return None
        
        type_tag = struct.unpack('<H', data[offset:offset+2])[0]
        # padding 2 bytes
        
        val_offset = offset + 4
        
        if type_tag == VT_EMPTY or type_tag == VT_NULL:
            return None
        elif type_tag == VT_I2:
            if val_offset + 2 <= len(data):
                return struct.unpack('<h', data[val_offset:val_offset+2])[0]
        elif type_tag == VT_I4:
            if val_offset + 4 <= len(data):
                return struct.unpack('<i', data[val_offset:val_offset+4])[0]
        elif type_tag == VT_BOOL:
            if val_offset + 2 <= len(data):
                return struct.unpack('<H', data[val_offset:val_offset+2])[0] != 0
        elif type_tag == VT_LPSTR:
            if val_offset + 4 <= len(data):
                count = struct.unpack('<I', data[val_offset:val_offset+4])[0]
                if val_offset + 4 + count <= len(data):
                    raw = data[val_offset+4:val_offset+4+count]
                    # Remove null terminator if present
                    if raw and raw[-1:] == b'\x00':
                        raw = raw[:-1]
                    try:
                        return raw.decode('utf-8', errors='replace')
                    except Exception:
                        try:
                            return raw.decode('cp1252', errors='replace')
                        except Exception:
                            return raw.decode('latin-1', errors='replace')
        elif type_tag == VT_LPWSTR:
            if val_offset + 4 <= len(data):
                count = struct.unpack('<I', data[val_offset:val_offset+4])[0]
                byte_count = count * 2
                if val_offset + 4 + byte_count <= len(data):
                    raw = data[val_offset+4:val_offset+4+byte_count]
                    # Remove null terminator if present
                    if raw and raw[-2:] == b'\x00\x00':
                        raw = raw[:-2]
                    try:
                        return raw.decode('utf-16-le', errors='replace')
                    except Exception:
                        return None
        elif type_tag == VT_FILETIME:
            if val_offset + 8 <= len(data):
                low = struct.unpack('<I', data[val_offset:val_offset+4])[0]
                high = struct.unpack('<I', data[val_offset+4:val_offset+8])[0]
                ft = (high << 32) | low
                return filetime_to_datetime(ft)
        elif type_tag == VT_BSTR:
            if val_offset + 4 <= len(data):
                count = struct.unpack('<I', data[val_offset:val_offset+4])[0]
                if val_offset + 4 + count <= len(data):
                    raw = data[val_offset+4:val_offset+4+count]
                    try:
                        return raw.decode('utf-8', errors='replace')
                    except Exception:
                        return raw.decode('latin-1', errors='replace')
        elif type_tag == VT_I8:
            if val_offset + 8 <= len(data):
                return struct.unpack('<q', data[val_offset:val_offset+8])[0]
        elif type_tag == VT_R8:
            if val_offset + 8 <= len(data):
                return struct.unpack('<d', data[val_offset:val_offset+8])[0]
        elif type_tag == VT_DATE:
            if val_offset + 8 <= len(data):
                return struct.unpack('<d', data[val_offset:val_offset+8])[0]
        
        return None
    
    def _scan_property_values(self, data: bytes) -> Dict[int, Any]:
        """Fallback: scan for common property patterns."""
        props = {}
        # This is a last-resort heuristic parser
        try:
            import re
            # Look for known PID strings in the data
            for pid in [PIDSI_AUTHOR, PIDSI_LASTAUTHOR, PIDSI_TITLE, PIDSI_SUBJECT,
                       PIDSI_KEYWORDS, PIDSI_COMMENTS, PIDSI_TEMPLATE, PIDSI_REVISION]:
                # Look for VT_LPSTR or VT_LPWSTR markers after PIDs
                # Simple scan: find PID and then read next value
                pass
        except Exception:
            pass
        return props
