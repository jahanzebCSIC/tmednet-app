"""
build_app.py — Builds a standalone executable for T-MEDNet using PyInstaller.

Usage:
    python build_app.py

Output:
    dist/tmednet/tmednet.exe  (Windows)
    dist/tmednet/tmednet      (Linux / macOS)

Requirements:
    pip install pyinstaller

The resulting folder (dist/tmednet/) is self-contained — distribute the entire
folder to end users.  Double-clicking tmednet.exe opens the application.
"""

import os
import sys
import subprocess
import shutil

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY_POINT = os.path.join(PROJECT_DIR, "main.py")
APP_NAME    = "tmednet"
DATA_DIR    = os.path.join(PROJECT_DIR, "data")
CORE_DIR    = os.path.join(PROJECT_DIR, "core")
ICON_PATH   = os.path.join(PROJECT_DIR, "resources", "tmednet.ico")


def build():
    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",           # one folder (faster startup than --onefile)
        "--windowed",         # no console window
        "--clean",
        "--noconfirm",
        # Tell PyInstaller's static analyser to look inside core/
        f"--paths={CORE_DIR}",
        # Include the data/ folder
        f"--add-data={DATA_DIR}{os.pathsep}data",
        # Include core/ modules as collected data so they land in _MEIPASS root
        f"--add-data={CORE_DIR}{os.pathsep}.",
        # Hidden imports that PyInstaller often misses
        "--hidden-import=_paths",
        "--hidden-import=data_manager",
        "--hidden-import=gui_plots",
        "--hidden-import=file_manipulation",
        "--hidden-import=file_writer",
        "--hidden-import=excel_writer",
        "--hidden-import=surface_temperature",
        "--hidden-import=converter",
        "--hidden-import=mhw_calculations",
        "--hidden-import=matplotlib.backends.backend_qtagg",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=netCDF4",
        "--hidden-import=xarray",
        "--hidden-import=geojson",
        "--hidden-import=fpdf",
        "--hidden-import=scipy.ndimage.filters",
        "--hidden-import=scipy.ndimage._filters",
        "--hidden-import=openpyxl",
        "--hidden-import=openpyxl.styles",
        "--hidden-import=openpyxl.utils",
        "--hidden-import=openpyxl.writer.excel",
        "--hidden-import=openpyxl.reader.excel",
        "--hidden-import=et_xmlfile",
    ]

    # Add icon if it exists
    if os.path.isfile(ICON_PATH):
        cmd += ["--icon", ICON_PATH]

    cmd.append(ENTRY_POINT)

    print("=" * 60)
    print("Building T-MEDNet desktop application…")
    print("=" * 60)
    result = subprocess.run(cmd, cwd=PROJECT_DIR)

    if result.returncode == 0:
        exe_dir = os.path.join(PROJECT_DIR, "dist", APP_NAME)
        print("\nBuild successful!")
        print(f"  Executable folder: {exe_dir}")
        print("\nTo run:\n  Windows : double-click dist\\tmednet\\tmednet.exe")
        print("  macOS   : open dist/tmednet/tmednet")
        print("  Linux   : ./dist/tmednet/tmednet")
    else:
        print("\nBuild FAILED — check output above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    build()
