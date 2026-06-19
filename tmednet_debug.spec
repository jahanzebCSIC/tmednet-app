# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\tmednet-app\\main.py'],
    pathex=['C:\\tmednet-app\\core'],
    binaries=[],
    datas=[('C:\\tmednet-app\\data', 'data'), ('C:\\tmednet-app\\core', '.')],
    hiddenimports=['_paths', 'data_manager', 'gui_plots', 'file_manipulation', 'file_writer', 'excel_writer', 'surface_temperature', 'converter', 'mhw_calculations', 'marineHeatWaves', 'matplotlib.backends.backend_qtagg', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'netCDF4', 'xarray', 'geojson', 'fpdf', 'xlsxwriter', 'openpyxl', 'openpyxl.styles', 'openpyxl.utils', 'openpyxl.writer.excel', 'openpyxl.reader.excel', 'et_xmlfile', 'scipy.ndimage.filters', 'scipy.ndimage._filters'],
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
    [],
    exclude_binaries=True,
    name='tmednet_debug',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tmednet_debug',
)
