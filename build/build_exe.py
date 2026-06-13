#!/usr/bin/env python3
"""Build script for Windows EXE using PyInstaller.
Run this on a Windows machine with Python 3.9+ installed."""
import subprocess
import sys
import shutil
from pathlib import Path

# AES encryption key (16/24/32 bytes)
AES_KEY = "OfficeMeta2024KB"  # Change this for production

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build" / "pyinstaller"

def clean():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    print("OK 清理旧构建")

def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=OfficeMetaExtractor",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={BUILD_DIR}",
        f"--key={AES_KEY}",
        "--hidden-import=PyQt5.sip",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=docx",
        "--hidden-import=openpyxl",
        "--hidden-import=pptx",
        "--hidden-import=olefile",
        "--hidden-import=PyPDF2",
        "--hidden-import=win32com.client",
        "--hidden-import=win32com.gen_py",
        "--hidden-import=src.parsers.csv_parser",
        "--hidden-import=src.parsers.base_parser",
        "--hidden-import=src.parsers.docx_parser",
        "--hidden-import=src.parsers.xlsx_parser",
        "--hidden-import=src.parsers.pptx_parser",
        "--hidden-import=src.parsers.ole_parser",
        "--hidden-import=src.parsers.pdf_parser",
        "--hidden-import=src.utils.datamodel",
        "--hidden-import=src.utils.logger",
        "--hidden-import=src.utils.license",
        "--hidden-import=src.utils.config",
        "--hidden-import=src.audit",
        "--hidden-import=src.audit.company_extractor",
        "--hidden-import=src.audit.detector",
        "--hidden-import=src.audit.report_generator",
        str(PROJECT_ROOT / "main.py")
    ]
    
    print(f"执行命令:")
    print(" ".join(cmd))
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("打包失败:")
        print(result.stderr)
        sys.exit(1)
    
    print("OK PyInstaller 打包成功")
    
    exe_path = DIST_DIR / "OfficeMetaExtractor.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"OK 输出文件: {exe_path}")
        print(f"OK 文件大小: {size_mb:.1f} MB")

if __name__ == "__main__":
    clean()
    build()
    print("\n构建完成!")
