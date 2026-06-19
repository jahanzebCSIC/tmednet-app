"""
PlotWidget — embeds the matplotlib figure inside a PyQt6 widget.
Provides the toolbar (home/pan/zoom/save) and dynamic threshold-temperature
tab buttons that gui_plots requests via callbacks.
"""

import matplotlib
matplotlib.use("QtAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)


class ThemedNavigationToolbar(NavigationToolbar):
    """NavigationToolbar that opens our custom FigureOptionsDialog instead of
    matplotlib's built-in one, so it's properly themed and has the extra
    grid-toggle and reset-defaults controls."""

    def edit_parameters(self):
        from app.widgets.dialogs import FigureOptionsDialog
        dlg = FigureOptionsDialog(self.canvas, parent=self.parent())
        dlg.exec()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QSizePolicy, QTextEdit, QTabWidget,
)
from PyQt6.QtCore import Qt


class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._threshold_buttons: list = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Tab widget: Plot + Report ----
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # --- Plot tab ---
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(0)

        # Matplotlib figure
        self.fig = Figure(figsize=(8, 5), dpi=100, constrained_layout=True)

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        plot_layout.addWidget(self.canvas, 1)

        # ---- Toolbar area ----
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("plotToolbar")
        toolbar_frame.setFixedHeight(44)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(8, 0, 8, 0)
        toolbar_layout.setSpacing(4)

        # Matplotlib navigation toolbar
        self.nav_toolbar = ThemedNavigationToolbar(self.canvas, toolbar_frame)
        toolbar_layout.addWidget(self.nav_toolbar)

        # "Clear Plot" button
        self._clear_btn = QPushButton("✕  Clear Plot")
        self._clear_btn.setObjectName("toolBtn")
        self._clear_btn.setFixedHeight(30)
        self._clear_btn.clicked.connect(self._on_clear_plot)
        toolbar_layout.addWidget(self._clear_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        toolbar_layout.addWidget(sep)

        # Container for dynamic threshold-temperature buttons
        self._temp_btn_container = QWidget()
        self._temp_btn_layout = QHBoxLayout(self._temp_btn_container)
        self._temp_btn_layout.setContentsMargins(0, 0, 0, 0)
        self._temp_btn_layout.setSpacing(3)
        toolbar_layout.addWidget(self._temp_btn_container)

        toolbar_layout.addStretch()

        plot_layout.addWidget(toolbar_frame)
        self.tabs.addTab(plot_container, "  📈  Plot  ")

        # --- Report tab ---
        self.report_text = QTextEdit()
        self.report_text.setObjectName("reportBox")
        self.report_text.setReadOnly(True)
        self.tabs.addTab(self.report_text, "  📄  Report  ")

    # ------------------------------------------------------------------ Clear

    def _on_clear_plot(self):
        """Delegate to gui_plot.clear_plots if available."""
        parent = self.parent()
        if parent and hasattr(parent, "gui_plot"):
            parent.gui_plot.clear_plots()

    # -------------------------------------------------------- Tab helpers

    def show_report_tab(self):
        self.tabs.setCurrentIndex(1)

    def show_plot_tab(self):
        self.tabs.setCurrentIndex(0)

    # ---------------------------------------- Threshold-button callbacks
    # These are set by MainWindow onto gui_plot._add_threshold_btn and
    # gui_plot._clear_threshold_btns so the backend can create/destroy buttons
    # without importing PyQt6.

    def add_threshold_button(self, label: str, callback) -> QPushButton:
        """Create a temperature-tab button and add it to the toolbar."""
        btn = QPushButton(f"{label}°C")
        btn.setObjectName("tempTabBtn")
        btn.setCheckable(True)
        btn.setFixedHeight(30)
        btn.clicked.connect(lambda checked, b=btn: self._on_temp_btn_clicked(b, callback))
        self._temp_btn_layout.addWidget(btn)
        self._threshold_buttons.append(btn)
        return btn

    def _on_temp_btn_clicked(self, clicked_btn: QPushButton, callback):
        # Uncheck all others
        for btn in self._threshold_buttons:
            btn.setChecked(btn is clicked_btn)
        callback()

    def clear_threshold_buttons(self):
        """Remove all threshold buttons (called by gui_plot.clear_plots)."""
        for btn in self._threshold_buttons:
            self._temp_btn_layout.removeWidget(btn)
            btn.deleteLater()
        self._threshold_buttons.clear()
