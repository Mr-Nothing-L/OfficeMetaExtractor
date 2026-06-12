"""Core metadata extractor."""
from pathlib import Path
from typing import List, Dict, Any

from ..parsers import parse_file, get_parser, SUPPORTED_EXT
from ..utils.datamodel import DocumentMeta
from ..utils.logger import logger


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
