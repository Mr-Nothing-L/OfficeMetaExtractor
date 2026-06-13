"""Audit engine for tender/bid document analysis."""
from .company_extractor import extract_company_name
from .detector import (
    check_author_consistency,
    check_creation_time_clustering,
    check_modified_time_clustering,
    check_template_reuse,
)
from .report_generator import (
    generate_summary_table,
    generate_detail_table,
    export_to_excel,
)

__all__ = [
    'extract_company_name',
    'check_author_consistency',
    'check_creation_time_clustering',
    'check_modified_time_clustering',
    'check_template_reuse',
    'generate_summary_table',
    'generate_detail_table',
    'export_to_excel',
]
