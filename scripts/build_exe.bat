@echo off
setlocal

cd /d %~dp0\..

echo [*] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [*] Creating virtual environment...
if exist .venv (
    echo     .venv already exists, skipping
) else (
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [*] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo [*] Installing requirements...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

echo [*] Installing PyInstaller...
pip install pyinstaller --quiet

echo [*] Copying config template...
if not exist config.yaml (
    copy config.example.yaml config.yaml >nul
    echo     → config.yaml created from config.example.yaml
) else (
    echo     → config.yaml already exists, skipping
)

echo [*] Creating data\log directories...
if not exist data mkdir data
if not exist logs  mkdir logs

echo [*] Building EXE (this may take a few minutes)...
python -m PyInstaller scripts\build_spec.spec --noconfirm --clean 2>&1

if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo [OK] Build complete!
echo.
echo Output directory: dist\WeChatGroupGuard\
echo.
echo To package as a ZIP distribution:
echo   powershell Compress-Archive -Path 'dist\WeChatGroupGuard' -DestinationPath 'WeChatGroupGuard.zip' -Force
echo.
echo To create an installer (optional, requires Inno Setup):
echo   https://jrsoftware.org/isdl.php
echo.
pause
