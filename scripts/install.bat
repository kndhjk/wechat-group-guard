@echo off
setlocal enabledelayedexpansion

cd /d %~dp0\..

echo [*] Creating virtual environment…
python -m venv .venv
if errorlevel 1 (
    echo [ERROR] python -m venv failed. Is Python 3 installed?
    pause
    exit /b 1
)

echo [*] Activating virtual environment…
call .venv\Scripts\activate.bat

echo [*] Upgrading pip…
python -m pip install --upgrade pip --quiet

echo [*] Installing dependencies…
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

echo [*] Copying config…
if not exist config.yaml (
    copy config.example.yaml config.yaml >nul
    echo     → config.yaml created from config.example.yaml
    echo     → Edit config.yaml before first run
) else (
    echo     → config.yaml already exists, skipping
)

echo [*] Creating data\log directories…
if not exist data mkdir data
if not exist logs  mkdir logs

echo.
echo [OK] Install complete!
echo.
echo Next steps:
echo   1. Edit config.yaml  ^(especially dry_run setting^)
echo   2. Run GUI:      scripts\run_gui.bat
echo      Or console:  python main.py --mode console
echo.
pause
