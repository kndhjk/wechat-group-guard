@echo off
setlocal

cd /d %~dp0\..

echo [*] Removing virtual environment...
if exist .venv (
    rmdir /s /q .venv
    echo     .venv removed.
) else (
    echo     No .venv found, skipping.
)

echo.
echo [*] Optional: remove runtime data (kept by default to preserve your settings)...
echo.
echo   To remove ALL local data including decisions, config, and logs:
echo     rmdir /s /q data
echo     rmdir /s /q logs
echo     del config.yaml
echo.
echo   To KEEP your data, do nothing — data^, logs^, and config.yaml are preserved.
echo.
echo Uninstall complete.
pause
