# Windows EXE build

## Prerequisite
Use Windows for the final EXE build.

## Build steps

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
scripts\build_exe.sh
```

If running from Git Bash / WSL-style shell on Windows:

```bash
./scripts/build_exe.sh
```

## Output
PyInstaller should produce one of:
- `dist/WeChatGroupGuard/`
- `dist/WeChatGroupGuard.exe`

## Notes
The current GUI is a local review GUI. Real desktop WeChat integration still needs to be completed.
