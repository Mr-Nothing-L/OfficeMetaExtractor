"""Core metadata extractor."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any

from ..parsers import parse_file, get_parser, SUPPORTED_EXT
from ..utils.datamodel import DocumentMeta
from ..utils.logger import logger
from ..audit import (
    extract_company_name,
    check_author_consistency,
    check_creation_time_clustering,
    check_modified_time_clustering,
    check_template_reuse,
    generate_summary_table,
    generate_detail_table,
    export_to_excel,
)


class MetaExtractor:
    """Main extractor coordinating parser calls."""

    # Use sequential parsing for very small batches to avoid thread-pool overhead.
    PARALLEL_THRESHOLD = 4

    def __init__(self, max_workers: int = None):
        self.results: List[DocumentMeta] = []
        self.errors: List[str] = []
        self.max_workers = max_workers
    
    def extract(self, filepath: str) -> Dict[str, Any]:
        """Extract metadata from a single file."""
        path = Path(filepath)
        if not path.exists():
            return {
                'filepath': filepath,
                'status': f'失败: 文件不存在'
            }
        
        parser = get_parser(path)
        if parser is None:
            return {
                'filepath': filepath,
                'status': f'失败: 不支持的格式 {path.suffix}'
            }
        
        result = parser.parse(path)
        return result.to_dict()
    
    def _extract_one(self, filepath: str) -> Dict[str, Any]:
        """Helper for batch_extract; exceptions are returned as failed statuses."""
        try:
            return self.extract(filepath)
        except Exception as e:
            logger.error(f"Failed to extract {filepath}: {e}")
            return {
                'filepath': filepath,
                'status': f'失败: {str(e)}'
            }

    def batch_extract(self, filepaths: List[str]) -> List[Dict[str, Any]]:
        """Extract metadata from multiple files (parallel when batch is large)."""
        if len(filepaths) < self.PARALLEL_THRESHOLD:
            return [self._extract_one(fp) for fp in filepaths]
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(self._extract_one, filepaths))
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[str]:
        """Scan a directory for supported files."""
        root = Path(directory)
        if not root.exists() or not root.is_dir():
            logger.error(f"Directory not found: {directory}")
            return []

        # Single traversal is faster than one rglob per extension.
        pattern = root.rglob('*') if recursive else root.glob('*')
        files = [f for f in pattern if f.is_file() and f.suffix.lower() in SUPPORTED_EXT]

        # Sort and deduplicate
        files = sorted(set(files))
        logger.info(f"Found {len(files)} supported files in {directory}")
        return [str(f) for f in files]

    def _parse_audit_one(self, filepath: str) -> DocumentMeta:
        """Parse a single file and fill in company name from path."""
        try:
            meta = parse_file(Path(filepath))
        except Exception as e:
            logger.error(f"Failed to parse {filepath}: {e}")
            meta = DocumentMeta(
                filename=Path(filepath).name,
                filepath=filepath,
                file_format=Path(filepath).suffix.upper()[1:] or 'UNKNOWN',
                parse_success=False,
                error_message=str(e),
            )

        # Fill company from path if parser did not provide one
        if not meta.company:
            meta.company = extract_company_name(filepath)
        return meta

    def audit(self, project_name: str, folder_path: str, output_excel: str = None) -> Dict[str, Any]:
        """Run full audit pipeline: scan -> parse -> detect -> generate report.

        Args:
            project_name: Name of the current project (for template reuse context).
            folder_path: Root directory containing company subfolders.
            output_excel: Optional path to write the Excel audit report.

        Returns:
            dict with keys: 'results', 'alerts', 'summary_table',
            'detail_table', 'output_excel'.
        """
        files = self.scan_directory(folder_path, recursive=True)

        # Parse files in parallel when the batch is large enough to amortize overhead.
        if len(files) < self.PARALLEL_THRESHOLD:
            results: List[DocumentMeta] = [self._parse_audit_one(fp) for fp in files]
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = list(executor.map(self._parse_audit_one, files))

        alerts = []
        alerts.extend(check_author_consistency(results))
        alerts.extend(check_creation_time_clustering(results, threshold_minutes=30))
        alerts.extend(check_modified_time_clustering(results, threshold_minutes=30))
        alerts.extend(check_template_reuse(results, project_name))

        summary_table = generate_summary_table(results, alerts)
        detail_table = generate_detail_table(results, alerts)

        saved_path = None
        if output_excel:
            if export_to_excel(summary_table, detail_table, output_excel):
                saved_path = output_excel

        return {
            'results': results,
            'alerts': alerts,
            'summary_table': summary_table,
            'detail_table': detail_table,
            'output_excel': saved_path,
        }
