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


def build_pyd():
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
''')

    # Write Cython source that wraps the real MetaExtractor class
    # The .pyx imports from Python modules so the actual logic stays in Python.
    pyx = core_dir / "extractor_core.pyx"
    pyx.write_text('''# cython: language_level=3
"""Compiled Cython wrapper around MetaExtractor.

The actual logic lives in Python modules (src.parsers, src.utils, src.audit).
This wrapper just cythonizes the class interface to make casual
disassembly/decompilation harder.
"""
from pathlib import Path
import cython

# Import real implementations from Python modules at runtime
from src.parsers import parse_file, get_parser, SUPPORTED_EXT
from src.utils.datamodel import DocumentMeta
from src.utils.logger import logger
from src.audit import (
    extract_company_name,
    check_author_consistency,
    check_creation_time_clustering,
    check_modified_time_clustering,
    check_template_reuse,
    generate_summary_table,
    generate_detail_table,
    export_to_excel,
)


cdef class MetaExtractor:
    """Compiled extractor coordinating parser calls."""
    cdef public list results
    cdef public list errors

    def __init__(self):
        self.results = []
        self.errors = []

    cpdef dict extract(self, str filepath):
        """Extract metadata from a single file."""
        cdef object path = Path(filepath)
        cdef object parser
        cdef object result

        if not path.exists():
            return {
                'filepath': filepath,
                'status': '失败: 文件不存在'
            }

        parser = get_parser(path)
        if parser is None:
            return {
                'filepath': filepath,
                'status': '失败: 不支持的格式 ' + path.suffix
            }

        result = parser.parse(path)
        return result.to_dict()

    cpdef list batch_extract(self, list filepaths):
        """Extract metadata from multiple files."""
        cdef list results = []
        cdef str fp
        cdef dict res
        for fp in filepaths:
            try:
                res = self.extract(fp)
                results.append(res)
            except Exception as e:
                logger.error(f"Failed to extract {fp}: {e}")
                results.append({
                    'filepath': fp,
                    'status': '失败: ' + str(e)
                })
        return results

    def scan_directory(self, str directory, bint recursive=True):
        """Scan a directory for supported files."""
        cdef object root = Path(directory)
        cdef list files = []
        cdef str ext

        if not root.exists() or not root.is_dir():
            logger.error(f"Directory not found: {directory}")
            return []

        if recursive:
            for ext in SUPPORTED_EXT:
                files.extend(root.rglob('*' + ext))
        else:
            for ext in SUPPORTED_EXT:
                files.extend(root.glob('*' + ext))

        # Sort and deduplicate
        files = sorted(set(files))
        logger.info(f"Found {len(files)} supported files in {directory}")
        return [str(f) for f in files]

    def audit(self, str project_name, str folder_path, str output_excel=None):
        """Run full audit pipeline: scan -> parse -> detect -> generate report."""
        cdef list files = self.scan_directory(folder_path, recursive=True)
        cdef list results = []
        cdef str filepath
        cdef object meta
        cdef list alerts
        cdef object summary_table
        cdef object detail_table
        cdef str saved_path

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
''')

    # Build
    result = subprocess.run(
        [sys.executable, str(setup_py), "build_ext", "--inplace"],
        cwd=str(core_dir),
        capture_output=True,
        text=True
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
