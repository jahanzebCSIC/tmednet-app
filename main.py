import sys
import os

# Frozen (PyInstaller) vs source — resolve the core/ module path correctly.
if getattr(sys, 'frozen', False):
    # In a --onedir bundle, core modules are extracted to sys._MEIPASS root
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

import matplotlib
matplotlib.use("QtAgg")

from app.theme import DARK_MPL
matplotlib.rcParams.update(DARK_MPL)

from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QTimer, QRect

from app.main_window import MainWindow


def create_splash_pixmap():
    w, h = 640, 360
    pixmap = QPixmap(w, h)
    pixmap.fill(QColor("#0B1829"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Ocean gradient background
    gradient = QLinearGradient(0, 0, 0, h)
    gradient.setColorAt(0.0, QColor("#0B1829"))
    gradient.setColorAt(1.0, QColor("#0A2540"))
    painter.fillRect(0, 0, w, h, QBrush(gradient))

    # Accent line at top
    painter.setPen(QColor("#0DB4D8"))
    painter.setBrush(QColor("#0DB4D8"))
    painter.drawRect(0, 0, w, 4)

    # Main title
    font = QFont("Segoe UI", 42, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#ECEFF4"))
    painter.drawText(QRect(0, 80, w, 80), Qt.AlignmentFlag.AlignCenter, "T-MEDNet")

    # Subtitle
    font2 = QFont("Segoe UI", 14)
    painter.setFont(font2)
    painter.setPen(QColor("#0DB4D8"))
    painter.drawText(QRect(0, 165, w, 40), Qt.AlignmentFlag.AlignCenter,
                     "Temperature Mediterranean Network")

    # Version
    font3 = QFont("Segoe UI", 10)
    painter.setFont(font3)
    painter.setPen(QColor("#4A6580"))
    painter.drawText(QRect(0, 270, w, 30), Qt.AlignmentFlag.AlignCenter,
                     "Version 1.0  ·  Marine Data Analysis Platform")

    # Loading indicator
    painter.setPen(QColor("#243650"))
    painter.setBrush(QColor("#243650"))
    painter.drawRoundedRect(120, 320, 400, 6, 3, 3)
    painter.setPen(QColor("#0DB4D8"))
    painter.setBrush(QColor("#0DB4D8"))
    painter.drawRoundedRect(120, 320, 180, 6, 3, 3)

    painter.end()
    return pixmap


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("T-MEDNet")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("TMEDNET Research")
    app.setOrganizationDomain("tmednet.org")

    # Splash screen
    splash_pix = create_splash_pixmap()
    splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    # Create main window (this triggers all imports and setup)
    window = MainWindow()

    # --auto-load file1 file2 ... : load and plot all files after splash
    # Optional --light flag before --auto-load switches to light theme first
    args = sys.argv[1:]
    if "--light" in args:
        args = [a for a in args if a != "--light"]
        QTimer.singleShot(2100, window.on_toggle_theme)

    if args and args[0] == "--auto-load":
        file_paths = args[1:]
        if file_paths:
            QTimer.singleShot(2800, lambda: window.load_and_plot_all(file_paths))

    QTimer.singleShot(2000, splash.close)
    QTimer.singleShot(2000, window.show)

    sys.exit(app.exec())


def run_excel_headless(filepath):
    """CLI test mode: run Excel generation without the GUI and print result."""
    import time, traceback
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))
    import excel_writer as ew
    print(f"[headless] file: {filepath}")
    t0 = time.time()
    try:
        er = ew.ExcelReport(filepath)
        er.excel_writer()
        print(f"[headless] SUCCESS in {time.time()-t0:.2f}s")
    except BaseException:
        print(f"[headless] FAILED after {time.time()-t0:.2f}s")
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--run-excel":
        run_excel_headless(sys.argv[2])
    else:
        main()
