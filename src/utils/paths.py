"""Runtime path helpers."""
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Return the project root.

    In development this is the repository root. When packaged with
    PyInstaller onefile/onefolder, sys._MEIPASS points to the temporary
    extraction/bundle directory.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent.parent


def resource_path(relative_path: str) -> Path:
    """Resolve a path relative to the project/bundle root."""
    return get_project_root() / relative_path
