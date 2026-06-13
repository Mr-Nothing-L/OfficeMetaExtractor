"""CSV parser - extracts filesystem-level metadata for CSV files."""
import csv
from pathlib import Path
from datetime import datetime

from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta


class CsvParser(BaseParser):
    """Parser for CSV files using filesystem metadata."""
    
    SUPPORTED_EXTENSIONS = ['.csv']
    
    @classmethod
    def _validate_header(cls, filepath: Path) -> bool:
        """CSV has no magic header - accept any text file."""
        return True
    
    def parse(self, filepath: Path, detailed: bool = False) -> DocumentMeta:
        meta = self._make_meta(filepath, 'CSV')
        
        try:
            stat = filepath.stat()
            meta.file_size = stat.st_size
            meta.created = datetime.fromtimestamp(stat.st_ctime)
            meta.modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Try to read first row as title if file is valid CSV
            try:
                with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.reader(f)
                    first_row = next(reader, None)
                    if first_row:
                        meta.title = ', '.join(first_row[:5])[:200]
            except Exception:
                pass
            
            meta.parse_success = True
            
        except Exception as e:
            meta.parse_success = False
            meta.error_message = f"CSV解析失败: {str(e)}"
        
        return meta
