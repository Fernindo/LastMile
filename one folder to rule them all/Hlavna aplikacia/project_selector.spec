# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['project_selector.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\nikol\\AppData\\Local\\Programs\\Python\\Python313\\tcl\\tcl8.6', 'tcl8.6'), ('C:\\Users\\nikol\\AppData\\Local\\Programs\\Python\\Python313\\tcl\\tk8.6', 'tk8.6'), ('Vzorova_CP3.xlsx', '.'), ('gui.py', '.'), ('gui_functions.py', '.'), ('filter_panel.py', '.'), ('notes_panel.py', '.'), ('excel_processing.py', '.')],
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
    name='project_selector',
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
