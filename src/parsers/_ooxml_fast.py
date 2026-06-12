"""Fast metadata extraction for OOXML packages via zip/core.xml/app.xml.

Avoids loading the whole document into memory. Useful for large DOCX/XLSX/PPTX
files where only core/extended properties are needed.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import zipfile
from xml.etree import ElementTree as ET


_CORE_NS = {
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
}

_APP_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'


def _parse_w3c_datetime(text: Optional[str]) -> Optional[datetime]:
    """Parse W3CDTF datetime as stored in OOXML core.xml.

    Returns a naive UTC datetime to stay compatible with the existing
    python-docx/openpyxl/python-pptx output.
    """
    if not text:
        return None
    text = text.strip()
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _get_text(root: ET.Element, tag: str, ns: Dict[str, str]) -> Optional[str]:
    """Return stripped text of a namespaced child element, or None."""
    elem = root.find(tag, ns)
    if elem is None or elem.text is None:
        return None
    return elem.text.strip() or None


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except Exception:
        return None


def has_core_xml(filepath: Path) -> bool:
    """Return True if the file looks like an OOXML package with docProps/core.xml."""
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            return 'docProps/core.xml' in zf.namelist()
    except Exception:
        return False


def parse_ooxml_core(filepath: Path) -> Dict[str, Any]:
    """Extract metadata directly from an OOXML package.

    Returns a dict with keys: author, last_modified_by, title, subject,
    keywords, comments, revision, created, modified, template, company,
    total_editing_time. Missing values are omitted.
    """
    props: Dict[str, Any] = {}

    with zipfile.ZipFile(filepath, 'r') as zf:
        # ---- core.xml ----
        if 'docProps/core.xml' in zf.namelist():
            root = ET.fromstring(zf.read('docProps/core.xml'))

            text = _get_text(root, 'dc:creator', _CORE_NS)
            if text:
                props['author'] = text

            text = _get_text(root, 'cp:lastModifiedBy', _CORE_NS)
            if text:
                props['last_modified_by'] = text

            text = _get_text(root, 'dc:title', _CORE_NS)
            if text:
                props['title'] = text

            text = _get_text(root, 'dc:subject', _CORE_NS)
            if text:
                props['subject'] = text

            text = _get_text(root, 'cp:keywords', _CORE_NS)
            if text:
                props['keywords'] = text

            text = _get_text(root, 'dc:description', _CORE_NS)
            if text:
                props['comments'] = text

            text = _get_text(root, 'cp:revision', _CORE_NS)
            if text:
                props['revision'] = text

            created = _get_text(root, 'dcterms:created', _CORE_NS)
            if created:
                props['created'] = _parse_w3c_datetime(created)

            modified = _get_text(root, 'dcterms:modified', _CORE_NS)
            if modified:
                props['modified'] = _parse_w3c_datetime(modified)

        # ---- app.xml ----
        if 'docProps/app.xml' in zf.namelist():
            root = ET.fromstring(zf.read('docProps/app.xml'))

            template = root.find('{%s}Template' % _APP_NS)
            if template is not None and template.text:
                props['template'] = template.text.strip() or None

            company = root.find('{%s}Company' % _APP_NS)
            if company is not None and company.text:
                props['company'] = company.text.strip() or None

            total_time = root.find('{%s}TotalTime' % _APP_NS)
            if total_time is not None and total_time.text:
                props['total_editing_time'] = _safe_int(total_time.text)

    return props
