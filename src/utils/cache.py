"""CSV cache utility for parsed Office document metadata.

Writes parsed results to a CSV file on disk as they are produced, so memory does
not grow with batch size. The cache lives in ``{app_dir}/cache/`` and is cleared
at the start of each new batch.
"""

import csv
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union


class ResultCache:
    """Append-only CSV cache for parsed metadata rows.

    The cache stores results in a single UTF-8-SIG encoded CSV file inside
    ``cache_dir``. It is designed for a single writer (e.g. a background worker
    calling :meth:`append` or :meth:`append_many`) and a single reader (e.g. the
    UI iterating via :meth:`iter_rows` after the worker signals completion).
    Public methods are protected by an instance lock for basic thread safety,
    but callers are responsible for higher-level write/read coordination.
    """

    CACHE_FILENAME = "results.csv"

    def __init__(self, cache_dir: Optional[Union[Path, str]] = None):
        """Initialize cache.

        If ``cache_dir`` is None, use ``{application_directory}/cache``.
        On Windows (PyInstaller bundle), ``application_directory`` is the
        directory containing the executable. Otherwise it is the project root.

        Args:
            cache_dir: Optional explicit directory for the cache. When omitted,
                a default directory is derived from the runtime environment.
        """
        if cache_dir is None:
            if getattr(sys, "frozen", False):
                app_dir = Path(sys.executable).parent
            else:
                app_dir = Path(__file__).parent.parent.parent
            cache_dir = app_dir / "cache"
        else:
            cache_dir = Path(cache_dir)

        self._cache_dir = cache_dir.resolve()
        self._path = self._cache_dir / self.CACHE_FILENAME
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        """Path to the current cache CSV file."""
        return self._path

    def clear(self) -> None:
        """Remove all files in the cache directory and recreate it.

        Safe to call multiple times. Creates the cache directory if it does not
        already exist.
        """
        with self._lock:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            for item in self._cache_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    item.rmdir()

    def _ensure_dir(self) -> None:
        """Ensure the cache directory exists."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _file_exists_and_has_content(self) -> bool:
        """Return True if the cache file exists and has at least one byte."""
        return self._path.exists() and self._path.stat().st_size > 0

    def append(self, row: Dict[str, Any]) -> None:
        """Append a single result dict as one CSV row.

        Writes the header when the file is new or empty.

        Args:
            row: Mapping of column name to value.
        """
        self.append_many([row])

    def append_many(self, rows: List[Dict[str, Any]]) -> None:
        """Append multiple rows efficiently.

        Writes the header when the file is new or empty. The header is derived
        from the keys of the first row in ``rows``.

        Args:
            rows: List of mappings to append.
        """
        if not rows:
            return

        with self._lock:
            self._ensure_dir()
            file_exists_with_content = self._file_exists_and_has_content()
            mode = "a" if file_exists_with_content else "w"

            with self._path.open(mode=mode, newline="", encoding="utf-8-sig") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                if not file_exists_with_content:
                    writer.writeheader()
                writer.writerows(rows)

    def iter_rows(self) -> Iterator[Dict[str, Any]]:
        """Iterate over cached rows as dicts.

        Yields nothing if the cache file does not exist or is empty.
        """
        with self._lock:
            if not self._path.exists():
                return iter([])

            fh = self._path.open(mode="r", newline="", encoding="utf-8-sig")

        try:
            reader = csv.DictReader(fh)
            for row in reader:
                yield row
        finally:
            fh.close()

    def __len__(self) -> int:
        """Return number of cached rows (excluding header)."""
        with self._lock:
            if not self._file_exists_and_has_content():
                return 0

            with self._path.open(mode="r", newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                return sum(1 for _ in reader)

    def is_empty(self) -> bool:
        """Return True if cache file does not exist or only has header."""
        with self._lock:
            if not self._path.exists():
                return True

            size = self._path.stat().st_size
            if size == 0:
                return True

            with self._path.open(mode="r", newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                try:
                    next(reader)
                except StopIteration:
                    return True
                return False


_DEFAULT_CACHE: Optional[ResultCache] = None
_DEFAULT_CACHE_LOCK = threading.Lock()


def get_default_cache() -> ResultCache:
    """Return the default/singleton :class:`ResultCache` instance."""
    global _DEFAULT_CACHE
    if _DEFAULT_CACHE is None:
        with _DEFAULT_CACHE_LOCK:
            if _DEFAULT_CACHE is None:
                _DEFAULT_CACHE = ResultCache()
    return _DEFAULT_CACHE
