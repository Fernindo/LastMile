# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['project_selector.py'],
    pathex=[],
    binaries=[('C:/Windows/System32/vcruntime140.dll', '.'), ('C:/Windows/System32/vcruntime140_1.dll', '.'), ('C:/Windows/System32/msvcp140.dll', '.'), ('C:/Users/nikol/AppData/Local/Programs/Python/Python313/tcl/tcl8.6', 'tcl/tcl8.6'), ('C:/Users/nikol/AppData/Local/Programs/Python/Python313/tcl/tk8.6', 'tcl/tk8.6')],
    datas=[('gui.exe', '.'), ('launcher.exe', '.'), ('gui.py', '.'), ('launcher.py', '.'), ('filter_panel.py', '.'), ('gui_functions.py', '.'), ('notes_panel.py', '.'), ('excel_processing.py', '.'), ('Vzorova_CP3.xlsx', '.')],
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
