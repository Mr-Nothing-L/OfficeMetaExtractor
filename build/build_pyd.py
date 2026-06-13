#!/usr/bin/env python3
"""Build Cython core module to .pyd (Windows) or .so (macOS/Linux).

This generates a real extractor_core.pyx that wraps the MetaExtractor class
from src.core.extractor_core. The .pyx imports from Python modules (parsers,
utils, audit) so the actual logic stays in Python source files, but the compiled
extension makes casual decompilation harder.

Run this before PyInstaller build."""
import subprocess
import sys
import shutil
from pathlib import Path

# Ensure stdout/stderr use UTF-8 so Chinese log messages do not crash on
# Windows runners whose console default code page is cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def build_pyd():
    # NOTE: src.utils.license is not Cythonized by this script. Ensure it is
    # collected/included by the final PyInstaller or embedded build.
    core_dir = Path(__file__).parent.parent / "src" / "core"
    build_dir = core_dir / "cython_build"

    # Clean old builds
    for pattern in ("*.pyd", "*.so", "*.c", "*.html", "*.pyx", "setup.py"):
        for p in core_dir.glob(pattern):
            p.unlink()
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Write setup.py in the core directory
    setup_py = core_dir / "setup.py"
    setup_py.write_text('''from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext

ext_modules = cythonize(
    "extractor_core.pyx",
    compiler_directives={
        'language_level': 3,
        'embedsignature': True,
    },
    annotate=True,
)

setup(
    name='extractor_core',
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext},
    zip_safe=False,
)
''', encoding='utf-8')

    # Write Cython source that wraps the real MetaExtractor class
    # The .pyx imports from Python modules so the actual logic stays in Python.
    pyx = core_dir / "extractor_core.pyx"
    pyx.write_text('''# cython: language_level=3
"""Compiled Cython wrapper around MetaExtractor.

The actual logic lives in Python modules (src.parsers, src.utils, src.audit).
This wrapper just cythonizes the class interface to make casual
disassembly/decompilation harder.
"""
from src.core._extractor_core import MetaExtractor as _PyMetaExtractor


cdef class MetaExtractor:
    """Compiled extractor coordinating parser calls.

    All behaviour is delegated to the Python implementation so that
    improvements in src.core.extractor_core are picked up automatically.
    """
    cdef object _impl

    def __init__(self, max_workers=None, bint detailed=False):
        self._impl = _PyMetaExtractor(max_workers=max_workers, detailed=detailed)

    cpdef dict extract(self, str filepath, object detailed=None):
        """Extract metadata from a single file."""
        if detailed is None:
            return self._impl.extract(filepath)
        return self._impl.extract(filepath, detailed=detailed)

    cpdef list batch_extract(self, list filepaths, object detailed=None):
        """Extract metadata from multiple files."""
        if detailed is None:
            return self._impl.batch_extract(filepaths)
        return self._impl.batch_extract(filepaths, detailed=detailed)

    def scan_directory(self, str directory, bint recursive=True):
        """Scan a directory for supported files."""
        return self._impl.scan_directory(directory, recursive=recursive)

    def audit(self, str project_name, str folder_path, str output_excel=None, bint detailed=False, list files=None):
        """Run full audit pipeline: scan -> parse -> detect -> generate report."""
        return self._impl.audit(project_name, folder_path, output_excel=output_excel, detailed=detailed, files=files)
''', encoding='utf-8')

    # Build
    result = subprocess.run(
        [sys.executable, str(setup_py), "build_ext", "--inplace"],
        cwd=str(core_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print("编译失败:")
        print(result.stderr)
        sys.exit(1)

    print("OK Cython 核心模块编译成功")

    # setuptools build_ext --inplace may place the .so/.pyd in a nested
    # directory (e.g. src/core/extractor_core.cpython-39-darwin.so).
    # Search recursively and move to core_dir.
    built = list(core_dir.rglob("*.pyd")) + list(core_dir.rglob("*.so"))
    if not built:
        print("WARN 未找到 .pyd/.so 输出文件")
        sys.exit(1)

    for b in built:
        if b.parent != core_dir:
            dest = core_dir / b.name
            shutil.move(str(b), str(dest))
            print(f"OK 移动 {b.name} -> {core_dir}")

    # Re-list after moving
    built = list(core_dir.glob("*.pyd")) + list(core_dir.glob("*.so"))
    print(f"OK 生成文件: {[b.name for b in built]}")

    # Clean up temporary build artifacts (keep .pyd/.so and annotation)
    for p in core_dir.rglob("setup.py"):
        p.unlink()
    for p in core_dir.rglob("extractor_core.pyx"):
        p.unlink()
    # Remove any nested build directories setuptools created
    for p in core_dir.glob("build"):
        if p.is_dir():
            shutil.rmtree(p)
    for p in core_dir.glob("src"):
        if p.is_dir():
            shutil.rmtree(p)

    print("OK 清理临时文件")


if __name__ == "__main__":
    build_pyd()
