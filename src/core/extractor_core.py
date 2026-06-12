"""Core metadata extractor."""
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
    
    def __init__(self):
        self.results: List[DocumentMeta] = []
        self.errors: List[str] = []
    
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
    
    def batch_extract(self, filepaths: List[str]) -> List[Dict[str, Any]]:
        """Extract metadata from multiple files."""
        results = []
        for fp in filepaths:
            try:
                results.append(self.extract(fp))
            except Exception as e:
                logger.error(f"Failed to extract {fp}: {e}")
                results.append({
                    'filepath': fp,
                    'status': f'失败: {str(e)}'
                })
        return results
    
    def scan_directory(self, directory: str, recursive: bool = True) -> List[str]:
        """Scan a directory for supported files."""
        root = Path(directory)
        if not root.exists() or not root.is_dir():
            logger.error(f"Directory not found: {directory}")
            return []
        
        files = []
        if recursive:
            for ext in SUPPORTED_EXT:
                files.extend(root.rglob(f'*{ext}'))
        else:
            for ext in SUPPORTED_EXT:
                files.extend(root.glob(f'*{ext}'))
        
        # Sort and deduplicate
        files = sorted(set(files))
        logger.info(f"Found {len(files)} supported files in {directory}")
        return [str(f) for f in files]

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
        results: List[DocumentMeta] = []

        for filepath in files:
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

            results.append(meta)

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
