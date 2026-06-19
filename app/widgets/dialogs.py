"""
Application dialogs:
  - AboutDialog
  - BrowserDialog (generic "select file + optional year" dialog)
  - HistoricalMergeDialog
  - ProgressDialog (threaded long-operation feedback)
  - FigureOptionsDialog (matplotlib figure options — themed, with grid toggle + reset)
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QProgressBar, QFrame, QGroupBox,
    QCheckBox, QComboBox, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


# ---------------------------------------------------------------------------
# About dialog
# ---------------------------------------------------------------------------

class AboutDialog(QDialog):
    def __init__(self, parent=None, version="1.0.0", build="2024"):
        super().__init__(parent)
        self.setWindowTitle("About T-MEDNet")
        self.setFixedSize(420, 280)
        self._build(version, build)

    def _build(self, version, build):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(10)

        title = QLabel("🌊  T-MEDNet")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Temperature Mediterranean Network")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        for key, val in [
            ("Version",  version),
            ("Build",    build),
            ("Author",   "Marc Jou"),
            ("Platform", "Python · PyQt6 · Matplotlib"),
            ("License",  "Creative Commons Attribution 4.0"),
        ]:
            row = QHBoxLayout()
            lbl_k = QLabel(key + ":")
            lbl_k.setObjectName("infoKey")
            lbl_k.setFixedWidth(80)
            lbl_v = QLabel(val)
            lbl_v.setObjectName("infoValue")
            row.addWidget(lbl_k)
            row.addWidget(lbl_v, 1)
            layout.addLayout(row)

        layout.addStretch()

        ok_btn = QPushButton("Close")
        ok_btn.setObjectName("accentBtn")
        ok_btn.setFixedWidth(100)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, 0, Qt.AlignmentFlag.AlignCenter)


# ---------------------------------------------------------------------------
# Generic browser dialog — select file + optional second input
# ---------------------------------------------------------------------------

class BrowserDialog(QDialog):
    """Emits dialog_accepted(file_path, second_value_or_None) when user confirms."""
    dialog_accepted = pyqtSignal(str, str)

    def __init__(self, parent=None, title="Select", label1="File:", label2=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(460)
        self._label2 = label2
        self._build(title, label1, label2)

    def _build(self, title, label1, label2):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        hdr = QLabel(title)
        hdr.setObjectName("header")
        layout.addWidget(hdr)

        # File row
        row1 = QHBoxLayout()
        lbl1 = QLabel(label1)
        lbl1.setFixedWidth(120)
        self._file_input = QLineEdit()
        self._file_input.setPlaceholderText("Click Browse to select a file…")
        browse = QPushButton("Browse")
        browse.setFixedWidth(76)
        browse.clicked.connect(lambda: self._browse(self._file_input))
        row1.addWidget(lbl1)
        row1.addWidget(self._file_input, 1)
        row1.addWidget(browse)
        layout.addLayout(row1)

        self._second_input = None
        if label2:
            row2 = QHBoxLayout()
            lbl2 = QLabel(label2)
            lbl2.setFixedWidth(120)
            self._second_input = QLineEdit()
            self._second_input.setPlaceholderText("e.g. 2010")
            row2.addWidget(lbl2)
            row2.addWidget(self._second_input, 1)
            layout.addLayout(row2)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Confirm")
        ok.setObjectName("accentBtn")
        ok.clicked.connect(self._on_confirm)
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

    def _browse(self, target: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(self, "Select file", "", "All files (*.*)")
        if path:
            target.setText(path)

    def _on_confirm(self):
        f = self._file_input.text().strip()
        s = self._second_input.text().strip() if self._second_input else ""
        if not f:
            self._file_input.setStyleSheet("border: 1px solid #E94560;")
            return
        self.dialog_accepted.emit(f, s)
        self.accept()


# ---------------------------------------------------------------------------
# Historical merge dialog
# ---------------------------------------------------------------------------

class HistoricalMergeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historical Merge")
        self.setFixedWidth(480)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        hdr = QLabel("Historical Merge")
        hdr.setObjectName("header")
        layout.addWidget(hdr)

        self._f1 = self._file_row(layout, "Historical file:")
        self._f2 = self._file_row(layout, "New file:")

        out_row = QHBoxLayout()
        out_lbl = QLabel("Output filename:")
        out_lbl.setFixedWidth(130)
        self._out = QLineEdit()
        self._out.setPlaceholderText("e.g. merged_output.txt")
        out_row.addWidget(out_lbl)
        out_row.addWidget(self._out, 1)
        layout.addLayout(out_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Merge")
        ok.setObjectName("accentBtn")
        ok.clicked.connect(self._on_ok)
        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

    def _file_row(self, layout, label):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(130)
        inp = QLineEdit()
        inp.setPlaceholderText("Click Browse…")
        browse = QPushButton("Browse")
        browse.setFixedWidth(76)
        browse.clicked.connect(lambda checked, i=inp: self._browse(i))
        row.addWidget(lbl)
        row.addWidget(inp, 1)
        row.addWidget(browse)
        layout.addLayout(row)
        return inp

    def _browse(self, target: QLineEdit):
        path, _ = QFileDialog.getOpenFileName(self, "Select file", "", "All files (*.*)")
        if path:
            target.setText(path)

    def _on_ok(self):
        if self._f1.text() and self._f2.text() and self._out.text():
            self.accept()

    def values(self):
        return self._f1.text(), self._f2.text(), self._out.text()


# ---------------------------------------------------------------------------
# Progress dialog for long operations
# ---------------------------------------------------------------------------

class ProgressDialog(QDialog):
    def __init__(self, parent=None, message="Working…"):
        super().__init__(parent)
        self.setWindowTitle("Processing")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)
        self.setFixedSize(340, 120)
        self._build(message)

    def _build(self, message):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self._msg = QLabel(message)
        self._msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._msg)

        self._bar = QProgressBar()
        self._bar.setRange(0, 0)  # indeterminate
        self._bar.setFixedHeight(8)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

    def set_message(self, msg: str):
        self._msg.setText(msg)

    def finish(self):
        self._bar.setRange(0, 100)
        self._bar.setValue(100)
        QTimer.singleShot(400, self.accept)


# ---------------------------------------------------------------------------
# Figure options dialog — replaces matplotlib's built-in ⚙ dialog
# ---------------------------------------------------------------------------

_LS_LABELS = ["Solid", "Dashed", "Dash-dot", "Dotted"]
_LS_VALUES = ["-",     "--",     "-.",       ":"]


class FigureOptionsDialog(QDialog):
    """Themed figure-options dialog: adapts to dark/light theme, has grid
    toggle and 'Reset Defaults' button."""

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.setWindowTitle("Figure Options")
        self.setMinimumWidth(440)
        self._build()
        self._load_state()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hdr = QLabel("Figure Options")
        hdr.setObjectName("header")
        layout.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # ---- Axes ----
        axes_grp = QGroupBox("Axes")
        ag = QFormLayout(axes_grp)
        ag.setSpacing(8)
        ag.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._title_edit  = QLineEdit()
        self._xlabel_edit = QLineEdit()
        self._ylabel_edit = QLineEdit()
        self._grid_check  = QCheckBox("Show grid")
        self._xscale = QComboBox()
        self._xscale.addItems(["linear", "log"])
        self._yscale = QComboBox()
        self._yscale.addItems(["linear", "log"])

        ag.addRow("Title:",   self._title_edit)
        ag.addRow("X Label:", self._xlabel_edit)
        ag.addRow("Y Label:", self._ylabel_edit)
        ag.addRow("",         self._grid_check)
        ag.addRow("X Scale:", self._xscale)
        ag.addRow("Y Scale:", self._yscale)
        layout.addWidget(axes_grp)

        # ---- Lines ----
        lines_grp = QGroupBox("Lines")
        lg = QFormLayout(lines_grp)
        lg.setSpacing(8)
        lg.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._line_combo = QComboBox()
        self._line_combo.currentIndexChanged.connect(self._on_line_changed)
        self._linewidth = QDoubleSpinBox()
        self._linewidth.setRange(0.1, 10.0)
        self._linewidth.setSingleStep(0.1)
        self._linewidth.setDecimals(1)
        self._linestyle = QComboBox()
        self._linestyle.addItems(_LS_LABELS)

        lg.addRow("Line:",  self._line_combo)
        lg.addRow("Width:", self._linewidth)
        lg.addRow("Style:", self._linestyle)
        layout.addWidget(lines_grp)

        layout.addStretch()

        # ---- Buttons ----
        btn_row = QHBoxLayout()

        reset_btn = QPushButton("↺  Reset Defaults")
        reset_btn.setObjectName("dangerBtn")
        reset_btn.setToolTip("Reset figure appearance to current theme defaults")
        reset_btn.clicked.connect(self._on_reset)

        apply_btn = QPushButton("✓  Apply")
        apply_btn.setObjectName("accentBtn")
        apply_btn.clicked.connect(self._on_apply)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    # ---------------------------------------------------------------- helpers

    def _get_axes(self):
        return self.canvas.figure.get_axes()

    def _get_lines(self):
        axes = self._get_axes()
        if not axes:
            return []
        return [l for l in axes[0].get_lines()
                if l.get_label() and not l.get_label().startswith('_')]

    # ---------------------------------------------------------------- state

    def _load_state(self):
        axes = self._get_axes()
        if not axes:
            return
        ax = axes[0]

        self._title_edit.setText(ax.get_title())
        self._xlabel_edit.setText(ax.get_xlabel())
        self._ylabel_edit.setText(ax.get_ylabel())

        grid_lines = ax.get_xgridlines()
        self._grid_check.setChecked(bool(grid_lines and grid_lines[0].get_visible()))

        xs = ax.get_xscale()
        self._xscale.setCurrentText(xs if xs in ("linear", "log") else "linear")
        ys = ax.get_yscale()
        self._yscale.setCurrentText(ys if ys in ("linear", "log") else "linear")

        self._line_combo.blockSignals(True)
        self._line_combo.clear()
        for line in self._get_lines():
            self._line_combo.addItem(line.get_label())
        self._line_combo.blockSignals(False)
        self._on_line_changed(0)

    def _on_line_changed(self, idx: int):
        lines = self._get_lines()
        if not lines or idx < 0 or idx >= len(lines):
            return
        line = lines[idx]
        self._linewidth.blockSignals(True)
        self._linewidth.setValue(line.get_linewidth())
        self._linewidth.blockSignals(False)
        try:
            ls_idx = _LS_VALUES.index(line.get_linestyle())
        except ValueError:
            ls_idx = 0
        self._linestyle.setCurrentIndex(ls_idx)

    # ---------------------------------------------------------------- actions

    def _on_apply(self):
        axes = self._get_axes()
        if not axes:
            return
        for ax in axes:
            ax.set_title(self._title_edit.text())
            ax.set_xlabel(self._xlabel_edit.text())
            ax.set_ylabel(self._ylabel_edit.text())
            ax.grid(self._grid_check.isChecked())
            try:
                ax.set_xscale(self._xscale.currentText())
                ax.set_yscale(self._yscale.currentText())
            except Exception:
                pass

        idx   = self._line_combo.currentIndex()
        lines = self._get_lines()
        if lines and 0 <= idx < len(lines):
            line = lines[idx]
            line.set_linewidth(self._linewidth.value())
            line.set_linestyle(_LS_VALUES[self._linestyle.currentIndex()])

        self.canvas.draw_idle()

    def _on_reset(self):
        """Reset figure appearance to current theme defaults via MainWindow."""
        win = self.window()
        if hasattr(win, '_apply_mpl_theme_to_figure'):
            win._apply_mpl_theme_to_figure()
        self._load_state()
