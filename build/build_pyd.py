#!/usr/bin/env python3
"""Build Cython core module to .pyd (Windows) or .so (Linux).
Run this before PyInstaller build."""
import subprocess
import sys
import shutil
from pathlib import Path

def build_pyd():
    core_dir = Path(__file__).parent.parent / "src" / "core"
    
    # Clean old builds
    for p in core_dir.glob("*.pyd"):
        p.unlink()
    for p in core_dir.glob("*.so"):
        p.unlink()
    for p in core_dir.glob("*.c"):
        p.unlink()
    
    # Write setup.py
    setup_py = core_dir / "setup.py"
    setup_py.write_text(f'''from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext

ext_modules = cythonize(
    "extractor_core.pyx",
    compiler_directives={{
        'language_level': 3,
        'embedsignature': True,
    }},
    annotate=True,
)

setup(
    name='extractor_core',
    ext_modules=ext_modules,
    cmdclass={{'build_ext': build_ext}},
    zip_safe=False,
)
''')
    
    # Write Cython source
    pyx = core_dir / "extractor_core.pyx"
    pyx.write_text('''# cython: language_level=3
from pathlib import Path
import cython

cdef class MetaExtractor:
    cdef public list parsers
    
    def __init__(self):
        self.parsers = []
    
    cpdef dict extract(self, str filepath):
        from src.parsers import parse_file
        result = parse_file(Path(filepath))
        return result.to_dict()
    
    cpdef list batch_extract(self, list filepaths):
        cdef list results = []
        cdef str fp
        for fp in filepaths:
            try:
                results.append(self.extract(fp))
            except Exception as e:
                results.append({{
                    'filepath': fp,
                    'status': f'失败: {{str(e)}}'
                }})
        return results
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
    
    built = list(core_dir.glob("*.pyd")) + list(core_dir.glob("*.so"))
    if not built:
        print("WARN 未找到 .pyd/.so 输出文件")
    else:
        print(f"OK 生成文件: {[b.name for b in built]}")

if __name__ == "__main__":
    build_pyd()
