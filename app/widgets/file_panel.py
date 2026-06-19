"""
FilePanel — left-sidebar widget showing loaded data files with a rich
context menu exposing all visualisation options.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QMenu, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class FilePanel(QWidget):
    # Signals emitted to MainWindow
    file_selected       = pyqtSignal(int)
    context_zoom        = pyqtSignal()
    context_zoom_all    = pyqtSignal()
    context_plot_diff   = pyqtSignal()
    context_plot_filter = pyqtSignal()
    context_hovmoller   = pyqtSignal()
    context_stratification = pyqtSignal()
    context_annual_cycle   = pyqtSignal()
    context_thresholds     = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.setToolTip("Click to plot · Right-click for options")

        layout.addWidget(self.list_widget)

    # ------------------------------------------------------------------

    def add_file(self, filename: str, depth: str = "", site: str = ""):
        """Add a decorated file entry to the list."""
        display = filename
        item = QListWidgetItem()
        item.setText(f"  🌊  {display}")
        item.setToolTip(f"File: {filename}\nSite: {site}\nDepth: {depth}")
        item.setForeground(QColor("#B8D0E0"))
        self.list_widget.addItem(item)

    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QListWidgetItem):
        row = self.list_widget.row(item)
        self.file_selected.emit(row)

    def _show_context_menu(self, pos):
        if self.list_widget.count() == 0:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0E1F33;
                border: 1px solid #1E3050;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 7px 18px 7px 12px;
                border-radius: 4px;
                color: #B8D0E0;
            }
            QMenu::item:selected {
                background-color: #1E3050;
                color: #ECEFF4;
            }
            QMenu::separator {
                height: 1px;
                background-color: #1A2D45;
                margin: 3px 8px;
            }
        """)

        # --- Quick plots ---
        a_zoom     = menu.addAction("🔍  Zoom (beginning & end)")
        a_zoom_all = menu.addAction("🔍  Zoom all selected files")
        menu.addSeparator()

        # --- Difference plots ---
        a_diff    = menu.addAction("📊  Plot Difference")
        a_filter  = menu.addAction("📈  Plot Filtered Difference (10-day)")
        menu.addSeparator()

        # --- Advanced visualisations ---
        a_hov   = menu.addAction("🌡  Plot Hovmöller Diagram")
        a_strat = menu.addAction("🌊  Plot Stratification…")
        a_cycle = menu.addAction("🔄  Plot Annual T Cycles…")
        a_thr   = menu.addAction("🔥  Plot Heat Spike Thresholds…")

        # Connect
        a_zoom.triggered.connect(self.context_zoom)
        a_zoom_all.triggered.connect(self.context_zoom_all)
        a_diff.triggered.connect(self.context_plot_diff)
        a_filter.triggered.connect(self.context_plot_filter)
        a_hov.triggered.connect(self.context_hovmoller)
        a_strat.triggered.connect(self.context_stratification)
        a_cycle.triggered.connect(self.context_annual_cycle)
        a_thr.triggered.connect(self.context_thresholds)

        menu.exec(self.list_widget.viewport().mapToGlobal(pos))
