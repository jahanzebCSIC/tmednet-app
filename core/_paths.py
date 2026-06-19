"""
Central path resolver for the T-MEDNet backend.

Works correctly in both modes:
  - Source (python main.py): outputs go to data/output_files/ inside the project
  - Frozen (PyInstaller --onedir): seed data in _internal/, outputs next to tmednet.exe
"""

import os
import sys

if getattr(sys, 'frozen', False):
    # Bundled seed data lives in _internal/ (sys._MEIPASS)
    DATA_DIR   = os.path.join(sys._MEIPASS, 'data')
    # User-visible output folders sit next to tmednet.exe so they're easy to find
    _user_root = os.path.dirname(sys.executable)
    OUTPUT_DIR = os.path.join(_user_root, 'output_files')
    IMG_DIR    = os.path.join(_user_root, 'output_images')
else:
    _project   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR   = os.path.join(_project, 'data')
    OUTPUT_DIR = os.path.join(DATA_DIR, 'output_files')
    IMG_DIR    = os.path.join(DATA_DIR, 'output_images')

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMG_DIR,    exist_ok=True)
