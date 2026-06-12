"""XLSX parser implementation."""
from pathlib import Path
from datetime import datetime

from openpyxl import load_workbook

from .base_parser import BaseParser
from . import _ooxml_fast
from ..utils.datamodel import DocumentMeta


class XlsxParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.xlsx']

    # XLSX 文件头: PK (zip格式)
    HEADER = [b'PK\x03\x04', b'PK\x05\x06']

    @classmethod
    def _validate_header(cls, filepath: Path) -> bool:
        return cls._check_header(filepath, cls.HEADER)

    def parse(self, filepath: Path) -> DocumentMeta:
        meta = self._make_meta(filepath, 'XLSX')

        # Fast path: only read the OOXML package metadata. This avoids loading
        # the entire workbook, which is slow for large spreadsheets.
        try:
            props = _ooxml_fast.parse_ooxml_core(filepath)
            if props or _ooxml_fast.has_core_xml(filepath):
                self._apply_props(meta, props)
                meta.parse_success = True
                return meta
        except Exception:
            pass

        # Fallback: use openpyxl when the fast path yields nothing.
        try:
            wb = load_workbook(filepath)
            cp = wb.properties

            meta.author = self._safe_str(cp.creator)
            meta.last_modified_by = self._safe_str(cp.last_modified_by)
            meta.title = self._safe_str(cp.title)
            meta.subject = self._safe_str(cp.subject)
            meta.keywords = self._safe_str(cp.keywords)
            meta.comments = self._safe_str(cp.description)
            meta.revision = self._safe_str(cp.revision)

            if cp.created:
                meta.created = cp.created
            if cp.modified:
                meta.modified = cp.modified

            wb.close()
            meta.parse_success = True

        except BaseException as e:
            # If openpyxl fails too, try the zip fallback one more time.
            try:
                props = _ooxml_fast.parse_ooxml_core(filepath)
                self._apply_props(meta, props)
                meta.parse_success = True
                if meta.author or meta.last_modified_by or meta.title:
                    meta.error_message = (
                        f"openpyxl 解析失败({type(e).__name__}: {str(e)})，已使用备用方案提取部分信息"
                    )
                else:
                    meta.error_message = (
                        f"openpyxl 解析失败({type(e).__name__}: {str(e)})，文件core.xml中无元信息"
                    )
            except BaseException as fallback_error:
                meta.parse_success = False
                meta.error_message = (
                    f"XLSX解析失败: {type(e).__name__}: {str(e)}; "
                    f"备用方案也失败: {type(fallback_error).__name__}: {str(fallback_error)}"
                )

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
