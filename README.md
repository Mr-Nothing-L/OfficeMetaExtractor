# OfficeMetaExtractor

提取 Word/Excel/PPT/PDF 等文档的元信息（作者、最后编辑者、创建时间、修改时间等），支持批量处理、拖拽导入、结果导出。

## 功能特性

- 支持格式：DOCX, XLSX, PPTX, DOC, XLS, PPT, PDF
- 拖拽或选择文件/文件夹批量导入
- 支持 CSV / JSON / Excel 三种导出格式
- 暗色主题 UI，支持列排序
- 支持右键复制、打开文件位置
- 进度条显示解析进度

## 系统要求

- **Windows 7 / 8 / 10 / 11**（运行 EXE 或源码）
- Python 3.9+（仅源码运行或开发构建时）

---

## 快速开始

### 方法一：Windows 一键构建 EXE（推荐）

在 Windows 电脑上：

1. 解压项目压缩包
2. 双击运行 `build_on_windows.bat`
3. 等待自动安装依赖并构建
4. 构建完成后，EXE 位于 `dist/OfficeMetaExtractor.exe`

### 方法二：macOS 构建 App

在 macOS 上：

1. 解压项目
2. 终端进入项目目录
3. 运行构建脚本

```bash
chmod +x build_on_macos.sh
./build_on_macos.sh
```

4. 构建完成后，应用位于 `dist/OfficeMetaExtractor.app`

或者手动构建：

```bash
pip install -r requirements.txt
pip install PyInstaller
pyinstaller --name="OfficeMetaExtractor" --windowed --noconfirm \
  --collect-all src --collect-all docx --collect-all openpyxl \
  --collect-all pptx --collect-all olefile --collect-all PyPDF2 \
  --hidden-import=PyQt5.sip --hidden-import=PyQt5.QtCore \
  --hidden-import=PyQt5.QtGui --hidden-import=PyQt5.QtWidgets \
  main.py
```

### 方法三：源码运行（Windows / Linux / macOS）

```bash
pip install -r requirements.txt
python main.py
```

---

## 构建 EXE（详细步骤）

### Windows

在 Windows 环境下：

```bash
# 1. 确保安装了 Python 3.9+（安装时勾选 "Add to PATH"）

# 2. 打开命令提示符或 PowerShell，进入项目目录

# 3. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 构建（一键脚本）
python build/build_exe.py
```

构建完成后，EXE 位于 `dist/OfficeMetaExtractor.exe`。

### macOS

```bash
# 1. 安装 Python 3.9+（推荐通过 Homebrew：brew install python）

# 2. 进入项目目录

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
pip install PyInstaller

# 5. 构建 App
pyinstaller --name="OfficeMetaExtractor" --windowed --noconfirm \
  --collect-all src --collect-all docx --collect-all openpyxl \
  --collect-all pptx --collect-all olefile --collect-all PyPDF2 \
  --hidden-import=PyQt5.sip --hidden-import=PyQt5.QtCore \
  --hidden-import=PyQt5.QtGui --hidden-import=PyQt5.QtWidgets \
  main.py
```

构建完成后：
- App bundle：`dist/OfficeMetaExtractor.app`（可拖拽到 Applications）
- 单文件：`dist/OfficeMetaExtractor`（可放在任意位置运行）

### 构建选项说明

- `--onefile`：单文件（Windows/Linux 可用，macOS 推荐用 `--windowed` 生成 `.app`）
- `--windowed`：无控制台窗口（GUI 模式）
- `--key=AES_KEY`：AES 加密资源文件（防简单解包）

---

## 项目结构

```
OfficeMetaExtractor/
├── main.py              # 程序入口
├── build_on_windows.bat # Windows 一键构建脚本
├── src/
│   ├── ui/              # PyQt5 界面组件
│   │   ├── main_window.py
│   │   ├── drop_area.py
│   │   ├── result_table.py
│   │   └── styles.py
│   ├── core/            # 核心提取逻辑
│   │   └── extractor_core.py
│   ├── parsers/         # 各格式解析器
│   │   ├── docx_parser.py
│   │   ├── xlsx_parser.py
│   │   ├── pptx_parser.py
│   │   ├── ole_parser.py
│   │   └── pdf_parser.py
│   └── utils/           # 工具模块
│       ├── datamodel.py
│       ├── logger.py
│       └── config.py
├── build/               # 构建脚本
│   ├── build_exe.py     # PyInstaller 打包脚本
│   └── build_pyd.py     # Cython 编译脚本
├── dist/                # 输出目录（构建后生成）
├── requirements.txt     # 依赖清单
└── README.md            # 本文件
```

---

## 解析器说明

| 格式 | 解析方式 | 说明 |
|------|---------|------|
| DOCX | python-docx | 读取 OpenXML core properties |
| XLSX | openpyxl | 读取 OpenXML core properties |
| PPTX | python-pptx | 读取 OpenXML core properties |
| PDF | PyPDF2 | 读取 /Info 字典 |
| DOC/XLS/PPT (OLE) | olefile / pywin32 COM | 优先 COM（完整信息，需 Windows + Office），fallback olefile（纯 Python） |

---

## 注意事项

### 关于 Linux 环境构建限制

本项目在 Linux 云环境中已完成全部代码开发和功能验证，但由于 PyInstaller 不支持跨操作系统编译（Linux 无法直接生成 Windows EXE），**最终的 Windows EXE 需要在 Windows 电脑上执行一步构建命令**。

已提供的构建脚本 (`build_on_windows.bat`) 会全自动处理：创建虚拟环境 → 安装依赖 → 调用 PyInstaller 打包 → 生成 EXE。

### 关于 Cython 编译

`build/build_pyd.py` 提供可选的 Cython 编译，将核心逻辑编译为 `.pyd`（Windows）或 `.so`（Linux）二进制模块，增加逆向难度。该步骤为可选，不执行不影响功能。

---

## 许可证

MIT License
