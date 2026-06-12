"""Parser factory and registration."""
from pathlib import Path
from typing import List, Type, Optional

from .base_parser import BaseParser
from .docx_parser import DocxParser
from .xlsx_parser import XlsxParser
from .pptx_parser import PptxParser
from .ole_parser import OleParser
from .pdf_parser import PdfParser

from ..utils.datamodel import DocumentMeta

# Registered parsers (priority order)
PARSERS: List[Type[BaseParser]] = [
    DocxParser,
    XlsxParser,
    PptxParser,
    OleParser,    # covers .doc/.xls/.ppt
    PdfParser,
]

# Supported extensions mapping
SUPPORTED_EXT = set()
for p in PARSERS:
    SUPPORTED_EXT.update(p.SUPPORTED_EXTENSIONS)


def get_parser(filepath: Path) -> Optional[BaseParser]:
    """Get the appropriate parser for a file."""
    for parser_cls in PARSERS:
        if parser_cls.can_parse(filepath):
            return parser_cls()
    return None


def parse_file(filepath: Path) -> DocumentMeta:
    """Parse a single file and return metadata."""
    parser = get_parser(filepath)
    if parser is None:
        meta = DocumentMeta(
            filename=filepath.name,
            filepath=str(filepath),
            file_format=filepath.suffix.upper()[1:],
            parse_success=False,
            error_message=f"不支持的文件格式: {filepath.suffix}"
        )
        return meta
    return parser.parse(filepath)


def parse_files(filepaths: List[Path]) -> List[DocumentMeta]:
    """Parse multiple files."""
    results = []
    for fp in filepaths:
        results.append(parse_file(fp))
    return results
