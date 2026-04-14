# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build specification for WeChat Group Guard
# Run:  pyinstaller scripts/build_spec.spec

import sys
from pathlib import Path

block_cipher = None

# Collect all needed Python packages
hiddenimports = [
    'yaml',
    'uiautomation',
    'tkinter',
]

a = Analysis(
    ['main.py'],
    pathex=[str(Path(__file__).parent.parent)],
    binaries=[],
    datas=[
        ('config.example.yaml', '.'),
        ('samples', 'samples'),
        ('data', 'data'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WeChatGroupGuard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,        # GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='WeChatGroupGuard',
)
