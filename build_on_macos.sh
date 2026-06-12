#!/bin/bash
# Build OfficeMetaExtractor on macOS
# Usage: chmod +x build_on_macos.sh && ./build_on_macos.sh

set -e

echo "🍎 OfficeMetaExtractor macOS Builder"
echo "===================================="

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found. Install it first: https://python.org/downloads"
    exit 1
fi

# Create venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📦 Installing PyInstaller..."
pip install PyInstaller

echo "🔨 Building macOS .app bundle..."

pyinstaller \
    --name="OfficeMetaExtractor" \
    --windowed \
    --noconfirm \
    --clean \
    --distpath=dist \
    --workpath=build/pyinstaller \
    --specpath=build/pyinstaller \
    --paths=src \
    --collect-all src \
    --collect-all docx \
    --collect-all openpyxl \
    --collect-all pptx \
    --collect-all olefile \
    --collect-all PyPDF2 \
    --hidden-import=PyQt5.sip \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    main.py

echo "✅ Done!"
echo "📦 App bundle: dist/OfficeMetaExtractor.app"
echo "📦 Single binary: dist/OfficeMetaExtractor (if --onefile was used)"

# Optionally sign for distribution (requires Apple Developer cert)
# codesign --force --deep --sign - dist/OfficeMetaExtractor.app

echo ""
echo "🚀 To run:"
echo "   open dist/OfficeMetaExtractor.app"
