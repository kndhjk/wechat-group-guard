@echo off
cd /d %~dp0\..
rmdir /s /q .venv
echo Virtual environment removed.
echo To fully remove local runtime data, also delete data and logs folders.
