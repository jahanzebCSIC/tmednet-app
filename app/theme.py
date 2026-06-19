# ── Matplotlib colour dictionaries ──────────────────────────────────────────

DARK_MPL = {
    'figure.facecolor':      '#0D1E30',
    'figure.edgecolor':      '#0D1E30',
    'axes.facecolor':        '#0D1E30',
    'axes.edgecolor':        '#2A4A6A',
    'axes.spines.top':       False,
    'axes.spines.right':     False,
    'text.color':            '#C8DDE8',
    'axes.labelcolor':       '#C8DDE8',
    'axes.titlecolor':       '#ECEFF4',
    'axes.labelsize':        11,
    'axes.titlesize':        12,
    'xtick.color':           '#8AB8D0',
    'ytick.color':           '#8AB8D0',
    'xtick.labelcolor':      '#8AB8D0',
    'ytick.labelcolor':      '#8AB8D0',
    'xtick.labelsize':       10,
    'ytick.labelsize':       10,
    'axes.grid':             True,
    'grid.color':            '#1E3050',
    'grid.linewidth':        0.5,
    'grid.alpha':            0.6,
    'legend.facecolor':      '#0E1F33',
    'legend.edgecolor':      '#1E3050',
    'legend.labelcolor':     '#C8DDE8',
    'legend.fontsize':       9,
    'legend.title_fontsize': 9,
    'savefig.facecolor':     '#0D1E30',
    'savefig.edgecolor':     '#0D1E30',
    'lines.linewidth':       1.2,
}

LIGHT_MPL = {
    'figure.facecolor':      '#FFFFFF',
    'figure.edgecolor':      '#FFFFFF',
    'axes.facecolor':        '#FFFFFF',
    'axes.edgecolor':        '#A0B4C8',
    'axes.spines.top':       False,
    'axes.spines.right':     False,
    'text.color':            '#1A2838',
    'axes.labelcolor':       '#1A2838',
    'axes.titlecolor':       '#0D1828',
    'axes.labelsize':        11,
    'axes.titlesize':        12,
    'xtick.color':           '#3A5060',
    'ytick.color':           '#3A5060',
    'xtick.labelcolor':      '#3A5060',
    'ytick.labelcolor':      '#3A5060',
    'xtick.labelsize':       10,
    'ytick.labelsize':       10,
    'axes.grid':             True,
    'grid.color':            '#DDE6EE',
    'grid.linewidth':        0.5,
    'grid.alpha':            0.8,
    'legend.facecolor':      '#FFFFFF',
    'legend.edgecolor':      '#C0CEDC',
    'legend.labelcolor':     '#1A2838',
    'legend.fontsize':       9,
    'legend.title_fontsize': 9,
    'savefig.facecolor':     '#FFFFFF',
    'savefig.edgecolor':     '#FFFFFF',
    'lines.linewidth':       1.2,
}


# ── Qt Stylesheets ────────────────────────────────────────────────────────────

OCEAN_DARK = """
/* ============================================================
   T-MEDNet — Ocean Dark Theme
   ============================================================ */

QMainWindow, QDialog {
    background-color: #0B1829;
    color: #ECEFF4;
}

QWidget {
    background-color: #0B1829;
    color: #ECEFF4;
    font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
    font-size: 12px;
}

/* ---- Header ---- */
QFrame#appHeader {
    background-color: #0A1520;
    border-bottom: 1px solid #1A2D45;
}

/* ---- Panels & frames ---- */
QFrame#sidebar {
    background-color: #0A1520;
    border-right: 1px solid #1A2D45;
}

QFrame#sectionCard {
    background-color: #162239;
    border: 1px solid #1E3050;
    border-radius: 6px;
}

QFrame#plotPanel {
    background-color: #0D1E30;
    border: 1px solid #1A2D45;
    border-radius: 6px;
}

/* ---- Section headers ---- */
QLabel#sectionHeader {
    color: #7BB8D4;
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 1.5px;
    padding: 8px 12px 4px 12px;
    background-color: transparent;
}

QLabel#appTitle {
    color: #0DB4D8;
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 1px;
}

QLabel#appSubtitle {
    color: #4A8FA8;
    font-size: 10px;
}

/* ---- Info panel ---- */
QFrame#infoPanel {
    background-color: transparent;
    margin: 4px 8px;
}

QLabel#infoKey {
    color: #7A9AB5;
    font-size: 11px;
    padding: 1px 12px;
}

QLabel#infoValue {
    color: #ECEFF4;
    font-size: 11px;
    font-weight: 500;
    padding: 1px 0;
}

/* ---- Status bar ---- */
QStatusBar {
    background-color: #071018;
    border-top: 1px solid #1A2D45;
    color: #8AB8D0;
    font-size: 11px;
    padding: 2px 8px;
}

QStatusBar::item { border: none; }

QStatusBar QLabel {
    background-color: transparent;
    color: #8AB8D0;
    font-size: 11px;
    padding: 0 8px;
}

QStatusBar QLabel#statusReady   { color: #00C9A7; }
QStatusBar QLabel#statusWorking { color: #F5A623; }
QStatusBar QLabel#statusError   { color: #E94560; }
QStatusBar QLabel#statusInfo    { color: #8AB8D0; }
QStatusBar QLabel#statusVer     { color: #5A8AA0; }

/* ---- Buttons ---- */
QPushButton {
    background-color: #1E2E47;
    color: #C8D8E8;
    border: 1px solid #243650;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #243C5C;
    border: 1px solid #0DB4D8;
    color: #ECEFF4;
}

QPushButton:pressed {
    background-color: #0A9BB8;
    color: #ECEFF4;
}

QPushButton:disabled {
    background-color: #141E2D;
    color: #2A3E55;
    border: 1px solid #1A2535;
}

QPushButton#accentBtn {
    background-color: #0DB4D8;
    color: #071220;
    border: none;
    font-weight: bold;
}

QPushButton#accentBtn:hover {
    background-color: #16C8EE;
    color: #0B1829;
}

QPushButton#accentBtn:pressed { background-color: #0A96B5; }

QPushButton#dangerBtn {
    background-color: #1E2E47;
    color: #E94560;
    border: 1px solid #E94560;
}

QPushButton#dangerBtn:hover {
    background-color: #E94560;
    color: #ECEFF4;
}

QPushButton#themeBtn {
    background-color: #1E2E47;
    color: #A8C8DC;
    border: 1px solid #243650;
    font-size: 13px;
    padding: 4px 10px;
    border-radius: 5px;
    min-width: 32px;
}

QPushButton#themeBtn:hover {
    background-color: #243C5C;
    border-color: #0DB4D8;
    color: #ECEFF4;
}

QPushButton#toolBtn {
    background-color: transparent;
    color: #8FA8C0;
    border: none;
    border-radius: 4px;
    padding: 5px 8px;
    text-align: left;
}

QPushButton#toolBtn:hover {
    background-color: #1A2D45;
    color: #ECEFF4;
}

QPushButton#tempTabBtn {
    background-color: #1A2B40;
    color: #8FA8C0;
    border: 1px solid #243650;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: bold;
    min-width: 44px;
}

QPushButton#tempTabBtn:hover {
    background-color: #243C5C;
    color: #ECEFF4;
    border-color: #0DB4D8;
}

QPushButton#tempTabBtn:checked {
    background-color: #0DB4D8;
    color: #071220;
    border-color: #0DB4D8;
}

/* ---- File list ---- */
QListWidget {
    background-color: #0E1F33;
    border: 1px solid #1E3050;
    border-radius: 5px;
    outline: none;
    padding: 2px;
}

QListWidget::item {
    border-radius: 4px;
    padding: 6px 8px;
    color: #B8D0E0;
    border-bottom: 1px solid #162035;
}

QListWidget::item:selected {
    background-color: #0D3D5C;
    color: #ECEFF4;
    border: 1px solid #0DB4D8;
}

QListWidget::item:hover:!selected {
    background-color: #162239;
    color: #ECEFF4;
}

/* ---- Text areas ---- */
QTextEdit, QPlainTextEdit {
    background-color: #0A1520;
    color: #A8C4D8;
    border: 1px solid #1A2D45;
    border-radius: 5px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    selection-background-color: #0D4060;
    selection-color: #ECEFF4;
}

QTextEdit#reportBox {
    background-color: #0A1520;
    color: #C8DDE8;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}

/* ---- Scroll bars ---- */
QScrollBar:vertical {
    width: 7px;
    background: #0A1520;
    border: none;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #1E3050;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover { background: #2A4468; }

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal {
    height: 7px;
    background: #0A1520;
    border: none;
}

QScrollBar::handle:horizontal {
    background: #1E3050;
    border-radius: 3px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover { background: #2A4468; }

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

/* ---- Tab widget ---- */
QTabWidget::pane {
    background-color: #0A1520;
    border: 1px solid #1A2D45;
    border-radius: 0 0 5px 5px;
}

QTabBar::tab {
    background-color: #0E1F33;
    color: #8AAEC8;
    padding: 6px 16px;
    border: 1px solid #1A2D45;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0A1520;
    color: #ECEFF4;
    border-bottom: 2px solid #0DB4D8;
}

QTabBar::tab:hover:!selected {
    background-color: #162239;
    color: #C8D8E8;
}

/* ---- Splitter ---- */
QSplitter::handle            { background-color: #1A2D45; }
QSplitter::handle:horizontal { width: 3px; }
QSplitter::handle:vertical   { height: 3px; }
QSplitter::handle:hover      { background-color: #0DB4D8; }

/* ---- Menu bar ---- */
QMenuBar {
    background-color: #0A1520;
    color: #C4D8E8;
    border-bottom: 1px solid #1A2D45;
    padding: 2px;
    spacing: 2px;
}

QMenuBar::item { padding: 4px 12px; border-radius: 4px; }
QMenuBar::item:selected { background-color: #162239; color: #ECEFF4; }
QMenuBar::item:pressed  { background-color: #1E3050; }

QMenu {
    background-color: #0E1F33;
    border: 1px solid #1E3050;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    color: #B8D0E0;
}

QMenu::item:selected { background-color: #1E3050; color: #ECEFF4; }

QMenu::separator {
    height: 1px;
    background-color: #1A2D45;
    margin: 4px 8px;
}

/* ---- Input fields ---- */
QLineEdit {
    background-color: #0E1F33;
    color: #ECEFF4;
    border: 1px solid #243650;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #0DB4D8;
}

QLineEdit:focus { border-color: #0DB4D8; }

/* ---- Toolbar ---- */
QToolBar {
    background-color: #0A1520;
    border: none;
    border-top: 1px solid #1A2D45;
    padding: 4px 6px;
    spacing: 3px;
}

QToolButton {
    background-color: transparent;
    color: #B0C8DC;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 6px;
}

QToolButton:hover {
    background-color: #1A2D45;
    color: #ECEFF4;
    border-color: #243650;
}

QToolButton:pressed { background-color: #243650; color: #0DB4D8; }

/* ---- Progress dialog ---- */
QProgressBar {
    background-color: #0E1F33;
    border: 1px solid #1E3050;
    border-radius: 4px;
    text-align: center;
    color: #ECEFF4;
    height: 16px;
}

QProgressBar::chunk { background-color: #0DB4D8; border-radius: 3px; }

/* ---- Message box ---- */
QMessageBox { background-color: #0B1829; }
QMessageBox QLabel { color: #ECEFF4; }

/* ---- Separators ---- */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #1A2D45;
    border: none;
    border-top: 1px solid #1A2D45;
}

/* ---- Plot toolbar frame ---- */
QFrame#plotToolbar {
    background-color: #162A42;
    border-top: 1px solid #2A4468;
}

/* ---- Dialog header label ---- */
QLabel#header {
    color: #0DB4D8;
    font-size: 14px;
    font-weight: bold;
    padding-bottom: 6px;
}

/* ---- Group box ---- */
QGroupBox {
    border: 1px solid #1E3050;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    color: #7BB8D4;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.5px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 12px;
}

/* ---- Checkboxes ---- */
QCheckBox {
    color: #C8D8E8;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #2A4468;
    border-radius: 3px;
    background: #0E1F33;
}
QCheckBox::indicator:checked {
    background: #0DB4D8;
    border-color: #0DB4D8;
}
QCheckBox::indicator:hover { border-color: #0DB4D8; }

/* ---- Combo box ---- */
QComboBox {
    background: #0E1F33;
    color: #ECEFF4;
    border: 1px solid #243650;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 80px;
}
QComboBox:focus { border-color: #0DB4D8; }
QComboBox::drop-down {
    border: none;
    background: #162A42;
    width: 20px;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}
QComboBox QAbstractItemView {
    background: #0E1F33;
    color: #ECEFF4;
    border: 1px solid #1E3050;
    selection-background-color: #1E3050;
    outline: none;
}

/* ---- Spin boxes ---- */
QSpinBox, QDoubleSpinBox {
    background: #0E1F33;
    color: #ECEFF4;
    border: 1px solid #243650;
    border-radius: 4px;
    padding: 4px 8px;
}
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #0DB4D8; }
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: #162A42;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #1E3A58;
}

/* ---- Tooltips ---- */
QToolTip {
    background-color: #0E1F33;
    color: #ECEFF4;
    border: 1px solid #0DB4D8;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
"""


OCEAN_LIGHT = """
/* ============================================================
   T-MEDNet — Ocean Light Theme
   ============================================================ */

QMainWindow, QDialog {
    background-color: #F4F7FB;
    color: #1A2838;
}

QWidget {
    background-color: #F4F7FB;
    color: #1A2838;
    font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
    font-size: 12px;
}

/* ---- Header ---- */
QFrame#appHeader {
    background-color: #E8EEF6;
    border-bottom: 1px solid #C0CEDC;
}

/* ---- Panels & frames ---- */
QFrame#sidebar {
    background-color: #ECF1F8;
    border-right: 1px solid #C8D4E0;
}

QFrame#sectionCard {
    background-color: #DDE5F0;
    border: 1px solid #BDC9D8;
    border-radius: 6px;
}

QFrame#plotPanel {
    background-color: #FFFFFF;
    border: 1px solid #C8D4E0;
    border-radius: 6px;
}

/* ---- Section headers ---- */
QLabel#sectionHeader {
    color: #3A6880;
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 1.5px;
    padding: 8px 12px 4px 12px;
    background-color: transparent;
}

QLabel#appTitle {
    color: #0090B0;
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 1px;
}

QLabel#appSubtitle {
    color: #3A7090;
    font-size: 10px;
}

/* ---- Info panel ---- */
QFrame#infoPanel {
    background-color: transparent;
    margin: 4px 8px;
}

QLabel#infoKey {
    color: #4A6880;
    font-size: 11px;
    padding: 1px 12px;
}

QLabel#infoValue {
    color: #1A2838;
    font-size: 11px;
    font-weight: 600;
    padding: 1px 0;
}

/* ---- Status bar ---- */
QStatusBar {
    background-color: #E0E8F2;
    border-top: 1px solid #C0CEDC;
    color: #3A6070;
    font-size: 11px;
    padding: 2px 8px;
}

QStatusBar::item { border: none; }

QStatusBar QLabel {
    background-color: transparent;
    color: #3A6070;
    font-size: 11px;
    padding: 0 8px;
}

QStatusBar QLabel#statusReady   { color: #007A60; }
QStatusBar QLabel#statusWorking { color: #B06010; }
QStatusBar QLabel#statusError   { color: #C02840; }
QStatusBar QLabel#statusInfo    { color: #3A6070; }
QStatusBar QLabel#statusVer     { color: #5878A0; }

/* ---- Buttons ---- */
QPushButton {
    background-color: #DDEAF5;
    color: #1A3050;
    border: 1px solid #B0C4D8;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #C8DCF0;
    border: 1px solid #0090B0;
    color: #0D2040;
}

QPushButton:pressed {
    background-color: #0090B0;
    color: #FFFFFF;
}

QPushButton:disabled {
    background-color: #E8EEF5;
    color: #9AAABB;
    border: 1px solid #C8D4E0;
}

QPushButton#accentBtn {
    background-color: #0090B0;
    color: #FFFFFF;
    border: none;
    font-weight: bold;
}

QPushButton#accentBtn:hover {
    background-color: #00A8CE;
    color: #FFFFFF;
}

QPushButton#accentBtn:pressed { background-color: #0078A0; }

QPushButton#dangerBtn {
    background-color: #FDEEF0;
    color: #C02840;
    border: 1px solid #C02840;
}

QPushButton#dangerBtn:hover {
    background-color: #C02840;
    color: #FFFFFF;
}

QPushButton#themeBtn {
    background-color: #DDEAF5;
    color: #1A3050;
    border: 1px solid #B0C4D8;
    font-size: 13px;
    padding: 4px 10px;
    border-radius: 5px;
    min-width: 32px;
}

QPushButton#themeBtn:hover {
    background-color: #C8DCF0;
    border-color: #0090B0;
}

QPushButton#toolBtn {
    background-color: transparent;
    color: #2A4860;
    border: none;
    border-radius: 4px;
    padding: 5px 8px;
    text-align: left;
}

QPushButton#toolBtn:hover {
    background-color: #C8DCF0;
    color: #0D2040;
}

QPushButton#tempTabBtn {
    background-color: #DDEAF5;
    color: #1A3050;
    border: 1px solid #B0C4D8;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: bold;
    min-width: 44px;
}

QPushButton#tempTabBtn:hover {
    background-color: #C8DCF0;
    color: #0D2040;
    border-color: #0090B0;
}

QPushButton#tempTabBtn:checked {
    background-color: #0090B0;
    color: #FFFFFF;
    border-color: #0090B0;
}

/* ---- File list ---- */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #C0CEDC;
    border-radius: 5px;
    outline: none;
    padding: 2px;
}

QListWidget::item {
    border-radius: 4px;
    padding: 6px 8px;
    color: #1A3050;
    border-bottom: 1px solid #DDE6EE;
}

QListWidget::item:selected {
    background-color: #B8DCEE;
    color: #0D2040;
    border: 1px solid #0090B0;
}

QListWidget::item:hover:!selected {
    background-color: #DCE8F4;
    color: #0D2040;
}

/* ---- Text areas ---- */
QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    color: #1A2838;
    border: 1px solid #C0CEDC;
    border-radius: 5px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    selection-background-color: #A0CEE8;
    selection-color: #0D2040;
}

QTextEdit#reportBox {
    background-color: #FFFFFF;
    color: #1A2838;
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
}

/* ---- Scroll bars ---- */
QScrollBar:vertical {
    width: 7px;
    background: #E8EEF6;
    border: none;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #AABCCC;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover { background: #7A9AB8; }

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal {
    height: 7px;
    background: #E8EEF6;
    border: none;
}

QScrollBar::handle:horizontal {
    background: #AABCCC;
    border-radius: 3px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover { background: #7A9AB8; }

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

/* ---- Tab widget ---- */
QTabWidget::pane {
    background-color: #FFFFFF;
    border: 1px solid #C0CEDC;
    border-radius: 0 0 5px 5px;
}

QTabBar::tab {
    background-color: #DCE8F4;
    color: #3A5878;
    padding: 6px 16px;
    border: 1px solid #C0CEDC;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #1A2838;
    border-bottom: 2px solid #0090B0;
}

QTabBar::tab:hover:!selected {
    background-color: #C8DCF0;
    color: #0D2040;
}

/* ---- Splitter ---- */
QSplitter::handle            { background-color: #C0CEDC; }
QSplitter::handle:horizontal { width: 3px; }
QSplitter::handle:vertical   { height: 3px; }
QSplitter::handle:hover      { background-color: #0090B0; }

/* ---- Menu bar ---- */
QMenuBar {
    background-color: #E8EEF6;
    color: #1A2838;
    border-bottom: 1px solid #C0CEDC;
    padding: 2px;
    spacing: 2px;
}

QMenuBar::item { padding: 4px 12px; border-radius: 4px; }
QMenuBar::item:selected { background-color: #C8DCF0; color: #0D2040; }
QMenuBar::item:pressed  { background-color: #B0CCE4; }

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #C0CEDC;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    color: #1A2838;
}

QMenu::item:selected { background-color: #DCE8F4; color: #0D2040; }

QMenu::separator {
    height: 1px;
    background-color: #C8D4E0;
    margin: 4px 8px;
}

/* ---- Input fields ---- */
QLineEdit {
    background-color: #FFFFFF;
    color: #1A2838;
    border: 1px solid #B0C4D8;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #0090B0;
    selection-color: #FFFFFF;
}

QLineEdit:focus { border-color: #0090B0; }

/* ---- Toolbar ---- */
QToolBar {
    background-color: #E8EEF6;
    border: none;
    border-top: 1px solid #C0CEDC;
    padding: 4px 6px;
    spacing: 3px;
}

QToolButton {
    background-color: transparent;
    color: #2A4060;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 6px;
}

QToolButton:hover {
    background-color: #C8DCF0;
    color: #0D2040;
    border-color: #B0C4D8;
}

QToolButton:pressed { background-color: #B0CCE4; color: #0090B0; }

/* ---- Progress dialog ---- */
QProgressBar {
    background-color: #E0E8F2;
    border: 1px solid #C0CEDC;
    border-radius: 4px;
    text-align: center;
    color: #1A2838;
    height: 16px;
}

QProgressBar::chunk { background-color: #0090B0; border-radius: 3px; }

/* ---- Message box ---- */
QMessageBox { background-color: #F4F7FB; }
QMessageBox QLabel { color: #1A2838; }

/* ---- Separators ---- */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #C8D4E0;
    border: none;
    border-top: 1px solid #C8D4E0;
}

/* ---- Plot toolbar frame ---- */
QFrame#plotToolbar {
    background-color: #DCE8F4;
    border-top: 1px solid #B0C4D8;
}

/* ---- Dialog header label ---- */
QLabel#header {
    color: #0090B0;
    font-size: 14px;
    font-weight: bold;
    padding-bottom: 6px;
}

/* ---- Group box ---- */
QGroupBox {
    border: 1px solid #B0C4D8;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    color: #3A6880;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.5px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 12px;
}

/* ---- Checkboxes ---- */
QCheckBox {
    color: #1A2838;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #A0B8CC;
    border-radius: 3px;
    background: #FFFFFF;
}
QCheckBox::indicator:checked {
    background: #0090B0;
    border-color: #0090B0;
}
QCheckBox::indicator:hover { border-color: #0090B0; }

/* ---- Combo box ---- */
QComboBox {
    background: #FFFFFF;
    color: #1A2838;
    border: 1px solid #B0C4D8;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 80px;
}
QComboBox:focus { border-color: #0090B0; }
QComboBox::drop-down {
    border: none;
    background: #DCE8F4;
    width: 20px;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    color: #1A2838;
    border: 1px solid #C0CEDC;
    selection-background-color: #DCE8F4;
    outline: none;
}

/* ---- Spin boxes ---- */
QSpinBox, QDoubleSpinBox {
    background: #FFFFFF;
    color: #1A2838;
    border: 1px solid #B0C4D8;
    border-radius: 4px;
    padding: 4px 8px;
}
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #0090B0; }
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: #DCE8F4;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #C8DCF0;
}

/* ---- Tooltips ---- */
QToolTip {
    background-color: #FFFFFF;
    color: #1A2838;
    border: 1px solid #0090B0;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
"""
