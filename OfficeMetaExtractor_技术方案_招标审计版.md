# Office文档元信息提取工具 — 技术方案文档

## 一、项目概述

| 项目 | 说明 |
|------|------|
| 名称 | OfficeMetaExtractor |
| 功能 | 提取 Word/Excel/PPT/PDF 等文档的元信息(作者, 最后编辑者, 创建时间, 修改时间等) |
| 输出 | 单文件 EXE, Windows 7/8/10/11 兼容 |
| 防护级别 | 防普通解包(Cython 编译核心 + PyInstaller AES 加密) |
| UI | PyQt5 桌面应用, 支持拖拽, 批量处理, 结果导出 |

---

## 二、技术栈

### 2.1 文档读取层

| 格式 | 库 | 说明 |
|------|-----|------|
| .docx | python-docx 0.8.11 | OpenXML 标准读取 |
| .xlsx | openpyxl 3.0.10 | OpenXML 标准读取 |
| .pptx | python-pptx 0.6.21 | OpenXML 标准读取 |
| .doc/.xls/.ppt | pywin32 306(COM) + olefile 0.47(兜底) | 优先 COM(需 Office), 无 Office 时用 olefile 解析基础元信息 |
| .pdf | PyPDF2 3.0.1 | 读取 /Info 字典 |
| 其他 | textract 1.6.5 | 兜底方案 |

### 2.2 UI 层

| 组件 | 库 | 版本 |
|------|-----|------|
| GUI 框架 | PyQt5 | 5.15.10 |
| 样式 | QSS(Qt StyleSheet) | 自定义暗色主题 |
| 图标 | 内置 SVG / 字体图标 | 无外部依赖 |

### 2.3 打包与防护层

| 环节 | 工具 | 配置 |
|------|------|------|
| 核心逻辑编译 | Cython 0.29.37 | 将 extractor_core.py 编译为 .pyd |
| 打包 | PyInstaller 5.13.2 | --onefile --windowed --key=AES_KEY |
| 压缩 | UPX 4.2 | 减小体积 |
| 运行环境 | Python 3.9.13 | 兼容 Win7+, 长期支持 |

---

## 三、项目目录结构

```
OfficeMetaExtractor/
├── src/
│   ├── main.py                 # 程序入口, PyQt5 主窗口
│   ├── ui/
│   │   ├── main_window.py      # 主界面布局
│   │   ├── drop_area.py        # 拖拽区域组件
│   │   ├── result_table.py     # 结果表格组件
│   │   └── styles.py           # QSS 样式定义
│   ├── core/                   # 核心逻辑(将被 Cython 编译)
│   │   ├── extractor_core.pyx  # Cython 源文件
│   │   ├── setup.py            # Cython 编译配置
│   │   └── __init__.py
│   ├── parsers/                # 各格式解析器
│   │   ├── __init__.py
│   │   ├── docx_parser.py
│   │   ├── xlsx_parser.py
│   │   ├── pptx_parser.py
│   │   ├── ole_parser.py       # .doc/.xls 通用 OLE 解析
│   │   └── pdf_parser.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── config.py
├── build/
│   ├── build_pyd.py            # 一键编译 .pyd 脚本
│   └── build_exe.py            # 一键打包 EXE 脚本
├── dist/                       # 输出目录
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 四、UI 设计规格

### 4.1 界面布局(主窗口 900x600)

```
+-------------------------------------------------------------+
|  OfficeMetaExtractor v1.0                    [-] [ ] [x]   |
+-------------------------------------------------------------+
|                                                             |
|  +-----------------------------------------------------+   |
|  |                                                     |   |
|  |              拖拽文件到此处                         |   |
|  |         或点击选择文件 / 文件夹                      |   |
|  |                                                     |   |
|  |         支持: docx, xlsx, pptx, doc, xls, pdf       |   |
|  |                                                     |   |
|  +-----------------------------------------------------+   |
|                                                             |
|  +-----------------------------------------------------+   |
|  | 文件名      | 格式 | 作者      | 最后编辑者 | 修改时间 |   |
|  +-------------+------+-----------+------------+----------+   |
|  | 合同.docx   | DOCX | 张三      | 李四       | 2024-... |   |
|  | 报表.xls    | XLS  | Admin     | test       | 2023-... |   |
|  | ...         | ...  | ...       | ...        | ...      |   |
|  +-----------------------------------------------------+   |
|                                                             |
|  [进度: 3/5] 正在解析: 合同.docx...                         |
|                                                             |
|  [导出 CSV]  [导出 JSON]  [导出 Excel]  [清空]              |
|                                                             |
+-------------------------------------------------------------+
```

### 4.2 交互设计

| 功能 | 交互方式 |
|------|---------|
| 添加文件 | 拖拽到中央区域 / 点击选择文件按钮 |
| 添加文件夹 | 点击选择文件夹按钮, 递归扫描 |
| 解析 | 自动开始, 显示进度条 |
| 结果展示 | 表格形式, 列可排序 |
| 导出 | 支持 CSV / JSON / Excel 三种格式 |
| 错误提示 | 底部状态栏显示, 错误文件标红 |
| 右键菜单 | 复制单元格 / 打开文件位置 / 重新解析 |

### 4.3 QSS 暗色主题(核心样式)

```qss
/* 主窗口 */
QMainWindow {
    background-color: #1e1e1e;
    color: #d4d4d4;
}

/* 拖拽区域 */
DropArea {
    background-color: #2d2d2d;
    border: 2px dashed #5a5a5a;
    border-radius: 8px;
    color: #808080;
}
DropArea:hover {
    border-color: #007acc;
    background-color: #252526;
}

/* 表格 */
QTableWidget {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    gridline-color: #3c3c3c;
    color: #d4d4d4;
}
QTableWidget::item:selected {
    background-color: #094771;
}
QHeaderView::section {
    background-color: #333333;
    color: #d4d4d4;
    padding: 6px;
    border: 1px solid #3c3c3c;
}

/* 按钮 */
QPushButton {
    background-color: #0e639c;
    color: white;
    border-radius: 4px;
    padding: 6px 16px;
}
QPushButton:hover {
    background-color: #1177bb;
}
QPushButton:pressed {
    background-color: #094771;
}
```

---

## 五、核心代码框架

### 5.1 元信息数据结构

```python
# src/utils/datamodel.py
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime

@dataclass
class DocumentMeta:
    filename: str                    # 文件名
    filepath: str                    # 完整路径
    file_format: str                 # 格式标识
    
    # 核心元信息
    author: Optional[str] = None           # 作者
    last_modified_by: Optional[str] = None # 最后编辑者
    created: Optional[datetime] = None   # 创建时间
    modified: Optional[datetime] = None    # 最后修改时间
    title: Optional[str] = None            # 标题
    subject: Optional[str] = None          # 主题
    company: Optional[str] = None        # 公司
    
    # 解析状态
    parse_success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'filename': self.filename,
            'format': self.file_format,
            'author': self.author or '',
            'last_modified_by': self.last_modified_by or '',
            'created': self.created.isoformat() if self.created else '',
            'modified': self.modified.isoformat() if self.modified else '',
            'title': self.title or '',
            'subject': self.subject or '',
            'company': self.company or '',
            'status': '成功' if self.parse_success else f'失败: {self.error_message}'
        }
```

### 5.2 解析器接口

```python
# src/parsers/base_parser.py
from abc import ABC, abstractmethod
from pathlib import Path
from ..utils.datamodel import DocumentMeta

class BaseParser(ABC):
    # 所有解析器的基类
    
    SUPPORTED_EXTENSIONS = []
    
    @classmethod
    def can_parse(cls, filepath: Path) -> bool:
        return filepath.suffix.lower() in cls.SUPPORTED_EXTENSIONS
    
    @abstractmethod
    def parse(self, filepath: Path) -> DocumentMeta:
        # 解析文件并返回元信息
        pass
```

### 5.3 新格式解析器示例(.docx)

```python
# src/parsers/docx_parser.py
from pathlib import Path
from docx import Document
from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta

class DocxParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.docx']
    
    def parse(self, filepath: Path) -> DocumentMeta:
        meta = DocumentMeta(
            filename=filepath.name,
            filepath=str(filepath),
            file_format='DOCX'
        )
        
        try:
            doc = Document(filepath)
            core_props = doc.core_properties
            
            meta.author = core_props.author
            meta.last_modified_by = core_props.last_modified_by
            meta.created = core_props.created
            meta.modified = core_props.modified
            meta.title = core_props.title
            meta.subject = core_props.subject
            
        except Exception as e:
            meta.parse_success = False
            meta.error_message = str(e)
        
        return meta
```

### 5.4 老格式解析器(.doc/.xls OLE 解析)

```python
# src/parsers/ole_parser.py
# .doc / .xls 元信息解析
# 策略:
# 1. 优先尝试 pywin32 COM 接口(最完整, 可读取最后编辑者)
# 2. 无 Office 环境时, fallback 到 olefile 解析基础属性

import struct
from pathlib import Path
from typing import Optional
from .base_parser import BaseParser
from ..utils.datamodel import DocumentMeta

class OleParser(BaseParser):
    SUPPORTED_EXTENSIONS = ['.doc', '.xls', '.ppt']
    
    def parse(self, filepath: Path) -> DocumentMeta:
        meta = DocumentMeta(
            filename=filepath.name,
            filepath=str(filepath),
            file_format=filepath.suffix.upper()[1:]
        )
        
        # 策略1: 尝试 COM 接口(Windows + Office 环境)
        try:
            return self._parse_via_com(filepath, meta)
        except Exception:
            pass  # COM 失败, 继续 fallback
        
        # 策略2: olefile 纯 Python 解析
        try:
            return self._parse_via_olefile(filepath, meta)
        except Exception as e:
            meta.parse_success = False
            meta.error_message = f"OLE解析失败: {str(e)}"
            return meta
    
    def _parse_via_com(self, filepath: Path, meta: DocumentMeta) -> DocumentMeta:
        # 通过 pywin32 COM 读取完整属性
        import win32com.client
        
        app = None
        doc = None
        
        try:
            # 根据扩展名选择应用
            if filepath.suffix.lower() == '.doc':
                app = win32com.client.Dispatch("Word.Application")
                app.Visible = False
                doc = app.Documents.Open(str(filepath.absolute()))
                props = doc.BuiltInDocumentProperties
            elif filepath.suffix.lower() == '.xls':
                app = win32com.client.Dispatch("Excel.Application")
                app.Visible = False
                doc = app.Workbooks.Open(str(filepath.absolute()))
                props = doc.BuiltinDocumentProperties
            elif filepath.suffix.lower() == '.ppt':
                app = win32com.client.Dispatch("PowerPoint.Application")
                app.Visible = False
                doc = app.Presentations.Open(str(filepath.absolute()))
                props = doc.BuiltInDocumentProperties
            
            # 读取属性(通过索引或名称)
            def get_prop(name):
                try:
                    return props(name).Value
                except:
                    return None
            
            meta.author = get_prop("Author")
            meta.last_modified_by = get_prop("Last Author")
            meta.title = get_prop("Title")
            meta.subject = get_prop("Subject")
            meta.company = get_prop("Company")
            
            # 时间属性需要转换
            try:
                meta.created = get_prop("Creation Date")
                meta.modified = get_prop("Last Save Time")
            except:
                pass
            
        finally:
            if doc:
                doc.Close(False)
            if app:
                app.Quit()
        
        return meta
    
    def _parse_via_olefile(self, filepath: Path, meta: DocumentMeta) -> DocumentMeta:
        # 通过 olefile 纯 Python 读取基础属性(无 Office 环境)
        import olefile
        
        ole = olefile.OleFileIO(str(filepath))
        
        # 读取 DocumentSummaryInformation 和 SummaryInformation 流
        # 这些是 OLE 文档的标准属性集
        
        # 尝试读取 SummaryInformation
        try:
            if ole.exists('\x05SummaryInformation'):
                stream = ole.openstream('\x05SummaryInformation')
                data = stream.read()
                # 解析 PropertySet 结构(简化版)
                # 实际实现需要完整解析 PropertySet 格式
                # 这里给出框架, 具体实现需补充字节解析逻辑
                meta.author = self._extract_property(data, PIDSI_AUTHOR)
                meta.title = self._extract_property(data, PIDSI_TITLE)
                meta.subject = self._extract_property(data, PIDSI_SUBJECT)
        except Exception as e:
            meta.error_message = f"olefile解析: {str(e)}"
        
        # 尝试读取 DocumentSummaryInformation 获取最后编辑者
        try:
            if ole.exists('\x05DocumentSummaryInformation'):
                stream = ole.openstream('\x05DocumentSummaryInformation')
                data = stream.read()
                meta.company = self._extract_property(data, PIDDSI_COMPANY)
        except:
            pass
        
        ole.close()
        return meta
    
    def _extract_property(self, data: bytes, prop_id: int) -> Optional[str]:
        # 从 PropertySet 数据中提取指定属性(简化实现)
        # 完整实现需要解析 PropertySet 结构:
        # 1. 读取 header (28 bytes)
        # 2. 读取 property count
        # 3. 遍历 property offsets
        # 4. 根据类型读取 string/int/date 等
        # 这里需要参考 MS-OLEPS 规范实现
        # 实际代码约 200 行, 此处省略完整实现
        return None

# OLE Property IDs (SummaryInformation)
PIDSI_TITLE = 0x02
PIDSI_SUBJECT = 0x03
PIDSI_AUTHOR = 0x04
PIDSI_LASTAUTHOR = 0x08  # 最后编辑者
PIDSI_CREATED = 0x0C
PIDSI_MODIFIED = 0x0D
PIDSI_COMPANY = 0x0F

# OLE Property IDs (DocumentSummaryInformation)
PIDDSI_COMPANY = 0x0F
```

### 5.5 解析器工厂与调度

```python
# src/parsers/__init__.py
from pathlib import Path
from typing import List, Type
from .base_parser import BaseParser
from .docx_parser import DocxParser
from .xlsx_parser import XlsxParser
from .pptx_parser import PptxParser
from .ole_parser import OleParser
from .pdf_parser import PdfParser

# 注册所有解析器(按优先级排序)
PARSERS: List[Type[BaseParser]] = [
    DocxParser,
    XlsxParser,
    PptxParser,
    OleParser,    # 覆盖 .doc/.xls/.ppt
    PdfParser,
]

def get_parser(filepath: Path) -> BaseParser:
    # 根据文件扩展名获取对应解析器
    for parser_cls in PARSERS:
        if parser_cls.can_parse(filepath):
            return parser_cls()
    raise ValueError(f"不支持的文件格式: {filepath.suffix}")

def parse_file(filepath: Path):
    # 解析单个文件
    parser = get_parser(filepath)
    return parser.parse(filepath)
```

---

## 六、Cython 编译配置

### 6.1 Cython 源文件(extractor_core.pyx)

```cython
# src/core/extractor_core.pyx
# 将核心解析逻辑编译为 C 扩展, 防止直接反编译

from pathlib import Path
import cython

cdef class MetaExtractor:
    # Cython 编译的元信息提取器
    
    cdef public list parsers
    
    def __init__(self):
        self.parsers = []
        self._register_parsers()
    
    cdef void _register_parsers(self):
        # 注册解析器(此处硬编码, 防止被外部修改)
        # 实际导入在运行时通过 Python 层完成
        pass
    
    cpdef dict extract(self, str filepath):
        # 提取元信息并返回字典
        # 调用 Python 层解析器
        from ..parsers import parse_file
        result = parse_file(Path(filepath))
        return result.to_dict()
    
    cpdef list batch_extract(self, list filepaths):
        # 批量提取
        cdef list results = []
        cdef str fp
        for fp in filepaths:
            try:
                results.append(self.extract(fp))
            except Exception as e:
                results.append({
                    'filepath': fp,
                    'status': f'失败: {str(e)}'
                })
        return results
```

### 6.2 编译脚本(setup.py)

```python
# src/core/setup.py
from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
import numpy as np

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
    include_dirs=[np.get_include()],
    cmdclass={'build_ext': build_ext},
    zip_safe=False,
)
```

### 6.3 一键编译脚本

```python
# build/build_pyd.py
# 编译 Cython 核心模块为 .pyd
import subprocess
import sys
import shutil
from pathlib import Path

def build_pyd():
    core_dir = Path(__file__).parent.parent / "src" / "core"
    
    # 清理旧构建
    for p in core_dir.glob("*.pyd"):
        p.unlink()
    for p in core_dir.glob("*.c"):
        p.unlink()
    
    # 执行编译
    result = subprocess.run(
        [sys.executable, "setup.py", "build_ext", "--inplace"],
        cwd=core_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("编译失败:")
        print(result.stderr)
        sys.exit(1)
    
    print("OK Cython 核心模块编译成功")
    
    # 验证输出
    pyd_files = list(core_dir.glob("*.pyd"))
    if not pyd_files:
        print("错误: 未找到 .pyd 输出文件")
        sys.exit(1)
    
    print(f"OK 生成文件: {pyd_files[0].name}")

if __name__ == "__main__":
    build_pyd()
```

---

## 七、PyInstaller 打包配置

### 7.1 打包脚本(build/build_exe.py)

```python
# build/build_exe.py
# PyInstaller 打包脚本, 生成单文件 EXE
import subprocess
import sys
import shutil
from pathlib import Path
import os

# 配置
AES_KEY = "YourSecretKey16B"  # 16/24/32 字节 AES 密钥, 修改此值
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build" / "pyinstaller"

def clean():
    # 清理旧构建
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    print("OK 清理旧构建")

def check_upx():
    # 检查 UPX 可用性
    upx_path = shutil.which("upx")
    if upx_path:
        print(f"OK UPX 可用: {upx_path}")
        return upx_path
    print("WARN UPX 未找到, 将不进行压缩")
    return None

def build():
    # 执行 PyInstaller 打包
    
    # 确保 .pyd 已编译
    pyd_files = list(SRC_DIR.glob("core/*.pyd"))
    if not pyd_files:
        print("错误: 未找到 .pyd 文件, 请先运行 build_pyd.py")
        sys.exit(1)
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=OfficeMetaExtractor",
        "--onefile",                    # 单文件
        "--windowed",                   # 无控制台窗口(GUI 模式)
        "--noconfirm",                  # 覆盖输出
        "--clean",                      # 清理临时文件
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={BUILD_DIR}",
        f"--key={AES_KEY}",             # AES 加密
        "--hidden-import=PyQt5.sip",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=docx",
        "--hidden-import=openpyxl",
        "--hidden-import=pptx",
        "--hidden-import=olefile",
        "--hidden-import=PyPDF2",
        "--hidden-import=win32com.client",  # pywin32
        "--hidden-import=win32com.gen_py",
        # 收集数据文件
        f"--add-data={SRC_DIR / 'ui' / 'styles.py'};ui",
    ]
    
    # UPX 配置
    upx_path = check_upx()
    if upx_path:
        cmd.extend(["--upx-dir", os.path.dirname(upx_path)])
    
    # 主入口文件
    cmd.append(str(SRC_DIR / "main.py"))
    
    print(f"执行命令:
{' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("打包失败:")
        print(result.stderr)
        sys.exit(1)
    
    print("OK PyInstaller 打包成功")
    
    # 输出信息
    exe_path = DIST_DIR / "OfficeMetaExtractor.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"OK 输出文件: {exe_path}")
        print(f"OK 文件大小: {size_mb:.1f} MB")

def verify():
    # 验证输出
    exe_path = DIST_DIR / "OfficeMetaExtractor.exe"
    if not exe_path.exists():
        print("错误: 未找到输出 EXE")
        sys.exit(1)
    print("OK 验证通过")

if __name__ == "__main__":
    clean()
    build()
    verify()
    print("\n构建完成!")
```

---

## 八、依赖清单(requirements.txt)

```
# Python 3.9.13 推荐
# 打包前请锁定版本

# UI
PyQt5==5.15.10

# 文档解析
python-docx==0.8.11
openpyxl==3.0.10
python-pptx==0.6.21
olefile==0.47
PyPDF2==3.0.1

# Windows 老格式 COM 解析(仅 Windows)
pywin32==306

# 编译
Cython==0.29.37

# 打包
PyInstaller==5.13.2

# 工具
pathlib2==2.3.7  # 兼容旧版
```

---

## 九、Windows 兼容性检查清单

| 检查项 | 要求 | 验证方法 |
|--------|------|---------|
| Python 版本 | 3.8 - 3.9 | 避免 3.10+ 的 Win7 不兼容问题 |
| PyQt5 版本 | 5.15.x | 5.15 是最后一个支持 Win7 的 LTS |
| VC++ 运行库 | 2015-2022 Redistributable | 目标机器需安装 |
| .NET Framework | 4.5+(pywin32 依赖) | 检查 Win7 默认安装 |
| 32/64 位 | 统一为 x64 | 现代系统均为 x64 |
| 测试环境 | Win7 SP1 / Win10 / Win11 | 虚拟机测试 |

---

## 十、防解包效果说明

| 攻击手段 | 防护效果 |
|---------|---------|
| pyinstxtractor 直接解包 | X 失败(AES 加密) |
| 提取 pyc 后反编译 | X 核心逻辑为 .pyd 机器码 |
| 字符串搜索密钥 | WARN 需配合代码混淆 |
| 动态调试(x64dbg) | WARN 可运行分析, 但无法直接还原源码 |
| 专业逆向(IDA Pro) | WARN 可分析, 但成本极高 |

**建议增强措施**:
1. 核心算法加入反调试检测(检查 IsDebuggerPresent)
2. 敏感字符串(AES 密钥)运行时动态解密
3. 使用 VMProtect 或 Themida 对最终 EXE 加壳(商业级)

---

## 十一、执行计划

1. Phase 1: 搭建项目结构, 实现基础解析器(docx/xlsx/pptx/pdf)
2. Phase 2: 实现 OLE 解析器(doc/xls), 含 COM 和 olefile 双策略
3. Phase 3: PyQt5 UI 开发, 实现拖拽, 表格, 导出功能
4. Phase 4: Cython 编译核心逻辑, 测试 .pyd 导入
5. Phase 5: PyInstaller 打包, AES 加密, UPX 压缩
6. Phase 6: 多版本 Windows 兼容性测试

---

文档版本: v1.0
生成时间: 2026-06-11
适用: 移交 Agent 执行

---

## 十二、招标审计场景专项需求

### 12.1 业务背景

本工具核心面向**招投标审计与围标串标排查**场景。根据《招标投标法实施条例》第四十条, 不同投标人的投标文件由同一单位或个人编制, 可直接视为串标。文档元数据(作者、最后保存者、创建时间、修改时间等)是识别此类违规的关键电子证据。

参考审计实践:
- 某市工程招标中, 系统扫描发现A、B、C三家投标文件作者栏均为"张某某", 三家全废标并罚款
- 政府采购项目中, 三家PDF创建时间前后差不到3分钟, 最后修改者为同一人, 评标委员会直接启动调查
- 海南省住建厅要求开标后自动比对所有投标文件的IP地址、MAC地址、计价软件加密锁号等信息, 涉嫌串通投标的自动截留并推送监管部门

### 12.2 核心审计指标

| 指标 | 字段名 | 审计意义 | 风险等级 |
|------|--------|---------|---------|
| 作者 | Author | 标书是否由同一人编写 | 高 |
| 最后保存者 | Last Modified By | 最终编辑者是否一致 | 高 |
| 创建时间 | Created | 是否在同一时间段批量生成 | 中 |
| 修改时间 | Modified | 最后修改时间是否集中 | 中 |
| 公司 | Company | 文档属性中的公司信息是否一致 | 中 |
| 标题 | Title | 是否包含其他项目名称(模板复用痕迹) | 低 |
| 主题 | Subject | 是否包含其他项目信息 | 低 |

### 12.3 围标串标检测规则

#### 规则1: 作者/保存者一致性检测

核心逻辑: 跨公司比对作者和最后保存者。若多家不同公司的投标文件出现相同的作者或保存者, 标记为串标嫌疑。

```python
def check_author_consistency(results):
    # 检测不同公司间作者/保存者一致性
    # 输入: 多家公司的文档元信息列表
    # 输出: 嫌疑公司配对列表
    from collections import defaultdict

    author_groups = defaultdict(list)
    for r in results:
        if r.author:
            author_groups[r.author].append(r)
        if r.last_modified_by:
            author_groups[r.last_modified_by].append(r)

    alerts = []
    for author, docs in author_groups.items():
        companies = set()
        for d in docs:
            company = extract_company_name(d.filepath)
            companies.add(company)

        if len(companies) > 1:
            alerts.append({
                'type': '作者/保存者跨公司一致',
                'value': author,
                'companies': list(companies),
                'file_count': len(docs),
                'risk_level': '高',
                'files': [d.filename for d in docs]
            })

    return alerts
```

#### 规则2: 创建时间集中性检测

检测多家公司投标文件是否在极短时间内创建, 默认阈值30分钟。

```python
from datetime import timedelta

def check_creation_time_clustering(results, threshold_minutes=30):
    timed_results = [r for r in results if r.created]
    if len(timed_results) < 2:
        return []

    timed_results.sort(key=lambda x: x.created)

    alerts = []
    window = []
    for r in timed_results:
        window.append(r)
        while window and (r.created - window[0].created) > timedelta(minutes=threshold_minutes):
            window.pop(0)

        companies = set(extract_company_name(d.filepath) for d in window)
        if len(companies) > 1 and len(window) >= 2:
            alerts.append({
                'type': '创建时间集中',
                'time_window': f'{window[0].created} ~ {r.created}',
                'companies': list(companies),
                'file_count': len(window),
                'risk_level': '中',
                'files': [d.filename for d in window]
            })

    return alerts
```

#### 规则3: 模板复用检测

检测文档标题/主题中是否包含非当前项目名称, 提示使用了其他项目的模板未清理干净。

```python
def check_template_reuse(results, current_project_name):
    alerts = []
    for r in results:
        suspicious = []
        for field in [r.title, r.subject]:
            if field and current_project_name not in field:
                suspicious.append(field)

        if suspicious:
            alerts.append({
                'type': '模板复用嫌疑',
                'company': extract_company_name(r.filepath),
                'suspicious_content': suspicious,
                'risk_level': '低',
                'file': r.filename
            })

    return alerts
```

### 12.4 输出报表格式

#### 审计汇总表(Excel)

| 公司 | 文件数 | 作者一致 | 保存者一致 | 创建时间集中 | 模板复用 | 综合风险 |
|------|--------|---------|-----------|-------------|---------|---------|
| 1-天津富通 | 5 | 是 | 是 | 否 | 否 | **高** |
| 2-江苏南方 | 5 | 是 | 是 | 是 | 否 | **高** |
| 3-杭州金龙 | 5 | 否 | 否 | 否 | 否 | 低 |

#### 详细比对表(Excel)

| 文件名 | 公司 | 格式 | 作者 | 最后保存者 | 创建时间 | 修改时间 | 风险标记 |
|--------|------|------|------|-----------|---------|---------|---------|
| 技术方案.docx | 天津富通 | DOCX | 张三 | 李四 | 2026-06-08 10:00 | 2026-06-08 17:30 | 作者与江苏南方一致 |
| 商务文件.xlsx | 江苏南方 | XLSX | 张三 | 李四 | 2026-06-08 10:05 | 2026-06-08 17:35 | 作者与天津富通一致 |

#### 审计报告(PDF/Word)

```
============================================
     投标文件元数据审计报告
============================================

项目名称: 资格预审申请文件-01标包室外光缆
审计日期: 2026-06-12
投标公司数: 7家
审计文件数: 35份

【高风险发现】

1. 作者/保存者跨公司一致(高风险)
   ----------------------------------------
   发现3家公司的投标文件作者均为"Administrator",
   最后保存者均为"test":

   - 1-天津富通信息科技股份有限公司
     文件: 技术方案.docx, 资质证明.docx
   - 2-江苏南方通信科技有限公司
     文件: 技术方案.docx, 商务报价.xlsx
   - 4-浙江富春江光电科技有限公司
     文件: 施工方案.docx

   判定依据: 《招标投标法实施条例》第四十条第(一)项
   "不同投标人的投标文件由同一单位或者个人编制"

2. 创建时间集中(中风险)
   ----------------------------------------
   5家公司的投标文件在2026-06-08 17:00-17:30
   30分钟内集中创建, 疑似批量生成:

   - 2-江苏南方通信科技有限公司: 17:29
   - 3-杭州金龙光电股份有限公司: 17:29
   - 4-浙江富春江光电科技有限公司: 17:29
   - 5-深圳市特发信息股份有限公司: 17:29
   - 6-江苏俊知技术有限公司: 17:29

【建议措施】
1. 对高风险公司启动串标调查程序
2. 要求涉事公司书面说明文档编制过程
3. 核查是否存在同一编制人员或同一设备

============================================
```

### 12.5 文件夹结构解析

工具需支持从文件夹名自动提取公司名称:

```python
def extract_company_name(filepath):
    # 从文件夹路径提取公司名称
    # 示例路径:
    # E:/删/26-6-8/资格预审申请文件-01标包室外光缆/1-天津富通信息科技股份有限公司/技术方案.docx

    # 提取规则:
    # 1. 取父文件夹名
    # 2. 去除前缀数字和横线(如 "1-")
    # 3. 返回纯公司名称

    from pathlib import Path
    import re

    p = Path(filepath)
    parent_name = p.parent.name
    cleaned = re.sub(r'^\d+[-_]', '', parent_name)

    return cleaned
```

### 12.6 UI 适配招标审计场景

#### 主界面调整

```
+-------------------------------------------------------------+
|  投标文件元数据审计工具 v1.0                 [-] [ ] [x]   |
+-------------------------------------------------------------+
|  项目名称: [资格预审申请文件-01标包室外光缆______]         |
|  [选择项目文件夹]                                           |
|                                                             |
|  +-----------------------------------------------------+   |
|  |              拖拽项目文件夹到此处                    |   |
|  |         或点击选择包含多家公司投标文件的文件夹        |   |
|  |                                                     |   |
|  |    预期结构: 项目文件夹/公司名-1/投标文件.*          |   |
|  |              项目文件夹/公司名-2/投标文件.*          |   |
|  |                                                     |   |
|  +-----------------------------------------------------+   |
|                                                             |
|  [开始审计]  [进度: 0/7家公司]                              |
|                                                             |
|  +-----------------------------------------------------+   |
|  | 公司名 | 文件数 | 作者一致 | 保存者一致 | 风险等级 |   |
|  +--------+--------+----------+------------+----------+   |
|  | 天津富通 | 5      | 是       | 是         | 高       |   |
|  | 江苏南方 | 5      | 是       | 是         | 高       |   |
|  | ...      | ...    | ...      | ...        | ...      |   |
|  +-----------------------------------------------------+   |
|                                                             |
|  [导出审计报告(PDF)]  [导出比对表(Excel)]  [导出原始数据]   |
|                                                             |
+-------------------------------------------------------------+
```

#### 审计结果详情弹窗

```
+--------------------------------------------------+
|  高风险发现 - 作者跨公司一致                      |
+--------------------------------------------------+
|                                                   |
|  作者: "Administrator"                            |
|                                                   |
|  涉及公司:                                        |
|  [x] 1-天津富通信息科技股份有限公司              |
|  [x] 2-江苏南方通信科技有限公司                  |
|  [x] 4-浙江富春江光电科技有限公司                |
|                                                   |
|  涉及文件:                                        |
|  - 天津富通/技术方案.docx                         |
|  - 江苏南方/商务报价.xlsx                         |
|  - 富春江光电/施工方案.docx                      |
|                                                   |
|  [查看详细]  [标记为已处理]  [加入审计报告]       |
|                                                   |
+--------------------------------------------------+
```

### 12.7 合规与法律依据

| 法规 | 条款 | 内容 |
|------|------|------|
| 《招标投标法实施条例》 | 第四十条 | 不同投标人的投标文件由同一单位或个人编制, 视为串标 |
| 《反不正当竞争法》 | 第二十七条 | 串通投标可处1-20万元罚款 |
| 《刑法》 | 第二百二十三条 | 情节严重处三年以下有期徒刑或拘役 |

### 12.8 竞品对标

| 功能 | 筑龙标事通 | 本工具定位 |
|------|-----------|-----------|
| 文档属性检查 | 支持 | 核心功能, 深度优化 |
| 文字查重 | 支持 | 暂不实现, 专注元数据 |
| 图片查重 | 支持 | 暂不实现 |
| 价格分析 | 支持 | 暂不实现 |
| 导出报告 | 支持 | 审计专用报告模板 |
| 离线使用 | 网络版+单机版 | **纯离线, 保护敏感数据** |
| 价格 | 年费制 | 买断制, 一次性付费 |

### 12.9 产品定位声明

> **投标文件元数据审计工具**
> 
> 专为招标代理机构、审计部门、评标委员会设计。
> 一键批量提取多家投标公司的文档元数据,
> 自动比对作者、保存者、创建时间等关键指标,
> 快速识别围标串标嫌疑, 生成合规审计报告。
> 
> 纯离线运行, 投标数据不上传云端,
> 保障敏感信息安全。

