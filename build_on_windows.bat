@echo off
chcp 65001 >nul
setlocal

echo ===========================================
echo OfficeMetaExtractor - Windows Build Script
echo ===========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add to PATH.
    pause
    exit /b 1
)

echo [OK] Python found.

REM Create virtual environment if not exists
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing dependencies...
pip install -r requirements.txt

echo.
echo [INFO] Building EXE with PyInstaller...
python build\build_exe.py

echo.
if exist dist\OfficeMetaExtractor.exe (
    echo [SUCCESS] Build complete!
    echo [INFO] EXE location: dist\OfficeMetaExtractor.exe
    echo.
    pause
) else (
    echo [ERROR] Build failed. Check error messages above.
    pause
    exit /b 1
)
endlocal
