"""DOCX parser implementation."""
from pathlib import Path
from datetime import datetime

from docx import Document

from .base_parser import BaseParser
from . import _ooxml_fast
from ..utils.datamodel import DocumentMeta


class DocxParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.docx']

    # DOCX 文件头: PK (zip格式)
    HEADER = [b'PK\x03\x04', b'PK\x05\x06']

    @classmethod
    def _validate_header(cls, filepath: Path) -> bool:
        return cls._check_header(filepath, cls.HEADER)

    def parse(self, filepath: Path, detailed: bool = False) -> DocumentMeta:
        meta = self._make_meta(filepath, 'DOCX')

        # Fast path: read only the OOXML package metadata.
        try:
            props = _ooxml_fast.parse_ooxml_core(filepath)
            if detailed:
                if props or _ooxml_fast.has_core_xml(filepath):
                    self._apply_props(meta, props)
                    meta.parse_success = True
                    return meta
            elif props:
                self._apply_props(meta, props)
                meta.parse_success = True
                return meta
        except Exception:
            pass

        if not detailed:
            meta.parse_success = False
            meta.error_message = (
                "快速模式仅读取 OOXML 核心属性，文件缺少 core.xml 或内容为空"
            )
            return meta

        # Fallback: load the whole document via python-docx.
        try:
            doc = Document(filepath)
            cp = doc.core_properties

            meta.author = self._safe_str(cp.author)
            meta.last_modified_by = self._safe_str(cp.last_modified_by)
            meta.title = self._safe_str(cp.title)
            meta.subject = self._safe_str(cp.subject)
            meta.keywords = self._safe_str(cp.keywords)
            meta.comments = self._safe_str(cp.comments)
            meta.revision = self._safe_str(cp.revision)
            try:
                meta.total_editing_time = cp.total_editing_time
            except Exception:
                pass

            if cp.created:
                meta.created = cp.created
            if cp.modified:
                meta.modified = cp.modified

            # Extended properties
            try:
                meta.template = self._safe_str(cp.template)
            except Exception:
                pass

            meta.parse_success = True

        except Exception as e:
            meta.parse_success = False
            meta.error_message = f"DOCX解析失败: {str(e)}"

        return meta

    def _apply_props(self, meta: DocumentMeta, props: dict) -> None:
        meta.author = self._safe_str(props.get('author'))
        meta.last_modified_by = self._safe_str(props.get('last_modified_by'))
        meta.title = self._safe_str(props.get('title'))
        meta.subject = self._safe_str(props.get('subject'))
        meta.keywords = self._safe_str(props.get('keywords'))
        meta.comments = self._safe_str(props.get('comments'))
        meta.revision = self._safe_str(props.get('revision'))
        meta.created = props.get('created')
        meta.modified = props.get('modified')
        meta.template = self._safe_str(props.get('template'))
        meta.company = self._safe_str(props.get('company'))
        meta.total_editing_time = props.get('total_editing_time')
