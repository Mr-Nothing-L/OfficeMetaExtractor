"""Company name extraction from file paths."""
import re
from pathlib import Path


def extract_company_name(filepath: str) -> str:
    """Extract company name from the immediate parent folder name.

    Strips leading digits followed by '-' or '_' (e.g. '001-ABC Corp' -> 'ABC Corp').
    Falls back to the raw parent folder name if no prefix pattern matches.
    """
    path = Path(filepath)
    parent_name = path.parent.name
    cleaned = re.sub(r'^\d+[-_]', '', parent_name)
    return cleaned.strip() or parent_name.strip()
