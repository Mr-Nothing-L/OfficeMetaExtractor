"""Core metadata extractor."""
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Optional

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

    # Chunk size for parallel batch processing.
    BATCH_CHUNK_SIZE = 50

    # Per-file timeout for audit parsing (seconds).
    AUDIT_FILE_TIMEOUT = 30

    def __init__(self, max_workers: int = None, detailed: bool = False):
        self.results: List[DocumentMeta] = []
        self.errors: List[str] = []
        self.max_workers = max_workers
        self.detailed = detailed

    def extract(self, filepath: str, detailed: bool = None) -> Dict[str, Any]:
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

        use_detailed = detailed if detailed is not None else self.detailed
        result = parser.parse(path, detailed=use_detailed)
        return result.to_dict()

    def _extract_one(self, filepath: str, detailed: bool = None) -> Dict[str, Any]:
        """Helper for batch_extract; exceptions are returned as failed statuses."""
        try:
            return self.extract(filepath, detailed=detailed)
        except Exception as e:
            logger.error(f"Failed to extract {filepath}: {e}")
            return {
                'filepath': filepath,
                'status': f'失败: {str(e)}'
            }

    def batch_extract(self, filepaths: List[str], detailed: bool = None) -> List[Dict[str, Any]]:
        """Extract metadata from multiple files (parallel when batch is large)."""
        use_detailed = detailed if detailed is not None else self.detailed

        if len(filepaths) < self.PARALLEL_THRESHOLD:
            return [self._extract_one(fp, detailed=use_detailed) for fp in filepaths]

        max_workers = min(4, os.cpu_count() or 4)
        results = []
        for i in range(0, len(filepaths), self.BATCH_CHUNK_SIZE):
            chunk = filepaths[i:i + self.BATCH_CHUNK_SIZE]
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results.extend(
                    list(executor.map(self._extract_one, chunk, [use_detailed] * len(chunk)))
                )
        return results
    
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

    def _parse_audit_one(self, filepath: str, detailed: bool = False) -> DocumentMeta:
        """Parse a single file and fill in company name from path."""
        try:
            meta = parse_file(Path(filepath), detailed=detailed)
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

    def _parse_audit_one_with_timeout(
        self,
        filepath: str,
        detailed: bool = False,
        timeout: int = None,
    ) -> DocumentMeta:
        """Parse a single audit file with a per-file timeout."""
        timeout = timeout or self.AUDIT_FILE_TIMEOUT
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = self._parse_audit_one(filepath, detailed=detailed)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            logger.warning(f"Timeout parsing {filepath}: 超过 {timeout} 秒")
            return DocumentMeta(
                filename=Path(filepath).name,
                filepath=filepath,
                file_format=Path(filepath).suffix.upper()[1:] or 'UNKNOWN',
                parse_success=False,
                error_message=f"解析超时（文件可能过大或格式异常）",
            )

        if exception[0] is not None:
            logger.error(f"Failed to parse {filepath}: {exception[0]}")
            return DocumentMeta(
                filename=Path(filepath).name,
                filepath=filepath,
                file_format=Path(filepath).suffix.upper()[1:] or 'UNKNOWN',
                parse_success=False,
                error_message=str(exception[0]),
            )

        return result[0]

    def audit(
        self,
        project_name: str,
        folder_path: str,
        output_excel: str = None,
        detailed: bool = False,
        files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run full audit pipeline: scan -> parse -> detect -> generate report.

        Args:
            project_name: Name of the current project (for template reuse context).
            folder_path: Root directory containing company subfolders.
            output_excel: Optional path to write the Excel audit report.
            detailed: Whether to use deep full-document parsing.
            files: Optional pre-scanned file list to avoid scanning twice.

        Returns:
            dict with keys: 'results', 'alerts', 'summary_table',
            'detail_table', 'output_excel'.
        """
        if files is None:
            files = self.scan_directory(folder_path, recursive=True)

        # Parse files in parallel when the batch is large enough to amortize overhead.
        if len(files) < self.PARALLEL_THRESHOLD:
            results: List[DocumentMeta] = [
                self._parse_audit_one_with_timeout(fp, detailed=detailed)
                for fp in files
            ]
        else:
            max_workers = min(4, os.cpu_count() or 4)
            results = []
            for i in range(0, len(files), self.BATCH_CHUNK_SIZE):
                chunk = files[i:i + self.BATCH_CHUNK_SIZE]
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    results.extend(
                        list(
                            executor.map(
                                self._parse_audit_one_with_timeout,
                                chunk,
                                [detailed] * len(chunk),
                            )
                        )
                    )

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
