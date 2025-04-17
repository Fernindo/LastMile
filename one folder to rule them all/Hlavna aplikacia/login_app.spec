# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['login_app.py'],
    pathex=[],
    binaries=[],
    datas=[('project_selector.py', '.'), ('gui.py', '.'), ('notes_panel.py', '.'), ('filter_panel.py', '.'), ('excel_processing.py', '.'), ('gui_functions.py', '.'), ('Vzorova_CP3.xlsx', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='login_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
