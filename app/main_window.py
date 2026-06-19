"""
MainWindow — central PyQt6 window for T-MEDNet.
Coordinates the sidebar, plot area, console, and all menu actions.
"""

import os
import sys
import time
import threading
import traceback as _traceback
import datetime as _datetime
import pandas as pd

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QPushButton, QFrame, QStatusBar, QMessageBox,
    QFileDialog, QMenuBar, QMenu, QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QFont, QColor

from app.theme import OCEAN_DARK, OCEAN_LIGHT, DARK_MPL, LIGHT_MPL
from app.adapters import ConsoleAdapter, TextBoxAdapter, ListboxAdapter
from app.widgets.file_panel import FilePanel
from app.widgets.plot_widget import PlotWidget
from app.widgets.console_widget import ConsoleWidget
from app.widgets.dialogs import (
    AboutDialog, BrowserDialog, HistoricalMergeDialog, ProgressDialog
)

# Backend (core/) imports — core/ is on sys.path via main.py
import data_manager as dm_module
import gui_plots as gp_module
import file_writer as fw_module
import excel_writer as ew_module
import surface_temperature as st_module
from _paths import OUTPUT_DIR as _OUTPUT_DIR, IMG_DIR as _IMG_DIR

VERSION = "1.0.0"
BUILD   = "2024"


# ---------------------------------------------------------------------------
# Worker thread for long-running operations
# Uses Python's threading.Thread (more reliable in frozen/windowed exes than
# QThread + moveToThread) with a QTimer that polls for completion on the
# main thread so all UI callbacks run safely on the main thread.
# ---------------------------------------------------------------------------

def _log_error(tb: str):
    """Write traceback to a log file next to the exe (visible even with --windowed)."""
    try:
        log_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) \
                  else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        log_path = os.path.join(log_dir, 'tmednet_error.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f'\n--- {_datetime.datetime.now()} ---\n{tb}\n')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# MainWindow
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("T-MEDNet  —  Temperature Mediterranean Network")
        self.resize(1400, 860)
        self.setMinimumSize(900, 600)

        # Internal state
        self._recoverindex = None
        self._reportlogger: list = []
        self._current_value = ""
        self._dark_mode = True

        # Apply stylesheet at QApplication level so ALL windows/dialogs inherit it
        QApplication.instance().setStyleSheet(OCEAN_DARK)

        self._build_ui()
        self._build_menus()
        self._init_backend()
        self._connect_signals()

        self.status_label.setText("Ready")
        self.status_label.setObjectName("statusReady")

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- Header bar ----
        header = self._make_header()
        root_layout.addWidget(header)

        # ---- Main splitter ----
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        root_layout.addWidget(splitter, 1)

        # Left sidebar
        self.sidebar = self._make_sidebar()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(260)
        self.sidebar.setMaximumWidth(400)
        splitter.addWidget(self.sidebar)

        # Right — plot area
        self.plot_widget = PlotWidget(self)
        splitter.addWidget(self.plot_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 1100])

        # ---- Status bar ----
        self._build_status_bar()

    def _make_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("appHeader")
        header.setFixedHeight(52)
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(10)

        # Logo / title
        logo_label = QLabel("🌊  T-MEDNet")
        logo_label.setObjectName("appTitle")
        h.addWidget(logo_label)

        subtitle = QLabel("Temperature Mediterranean Network")
        subtitle.setObjectName("appSubtitle")
        h.addWidget(subtitle)

        h.addStretch()

        # Quick-action buttons
        for text, tip, slot, obj_name in [
            ("  Open",   "Load temperature data files",       self.on_open,   "accentBtn"),
            ("  Save",   "Save current plot as image",        self.on_save,   ""),
            ("  Report", "Generate TXT + PDF report",         self.on_report, ""),
            ("  Reset",  "Clear all data and plots",          self.on_reset,  "dangerBtn"),
        ]:
            btn = QPushButton(text)
            btn.setToolTip(tip)
            btn.setObjectName(obj_name)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            h.addWidget(btn)
            setattr(self, f"_btn_{text.strip().lower()}", btn)

        # Theme toggle button (☀ = switch to light, 🌙 = switch to dark)
        self._theme_btn = QPushButton("☀")
        self._theme_btn.setObjectName("themeBtn")
        self._theme_btn.setToolTip("Switch to light theme")
        self._theme_btn.setFixedHeight(34)
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.clicked.connect(self.on_toggle_theme)
        h.addWidget(self._theme_btn)

        return header

    def _make_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Files section ---
        files_header = self._section_header("LOADED FILES")
        layout.addWidget(files_header)

        self.file_panel = FilePanel(self)
        layout.addWidget(self.file_panel, 3)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep1)

        # --- Station info ---
        info_header = self._section_header("STATION INFO")
        layout.addWidget(info_header)

        self.info_panel = self._make_info_panel()
        layout.addWidget(self.info_panel)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)

        # --- Console ---
        console_header = self._section_header("CONSOLE LOG")
        layout.addWidget(console_header)

        self.console_widget = ConsoleWidget(self)
        layout.addWidget(self.console_widget, 2)

        return sidebar

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionHeader")
        return lbl

    def _make_info_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("infoPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 4, 4, 8)
        layout.setSpacing(0)

        self._info_site  = self._info_row(layout, "Site")
        self._info_depth = self._info_row(layout, "Depth")
        self._info_from  = self._info_row(layout, "From")
        self._info_to    = self._info_row(layout, "To")
        self._info_sn    = self._info_row(layout, "S/N")

        return panel

    def _info_row(self, layout: QVBoxLayout, label: str) -> QLabel:
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(8, 2, 8, 2)
        hl.setSpacing(6)

        lbl = QLabel(label + ":")
        lbl.setObjectName("infoKey")
        lbl.setFixedWidth(46)
        val = QLabel("—")
        val.setObjectName("infoValue")
        hl.addWidget(lbl)
        hl.addWidget(val, 1)
        layout.addWidget(row)
        return val

    def _build_status_bar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)

        self.status_label = QLabel("Initializing…")
        self.status_label.setObjectName("statusReady")
        sb.addWidget(self.status_label)

        sb.addPermanentWidget(QLabel("│"), 0)

        self.file_count_label = QLabel("Files: 0")
        self.file_count_label.setObjectName("statusInfo")
        sb.addPermanentWidget(self.file_count_label)

        sb.addPermanentWidget(QLabel("│"), 0)

        self.station_label = QLabel("Station: —")
        self.station_label.setObjectName("statusInfo")
        sb.addPermanentWidget(self.station_label)

        sb.addPermanentWidget(QLabel("│"), 0)

        ver_label = QLabel(f"T-MEDNet v{VERSION}")
        ver_label.setObjectName("statusVer")
        sb.addPermanentWidget(ver_label)

    # ---------------------------------------------------------------- Menus

    def _build_menus(self):
        mb = self.menuBar()
        mb.setNativeMenuBar(False)

        # File
        file_menu = mb.addMenu("&File")
        self._add_action(file_menu, "Open…",           "Ctrl+O", self.on_open)
        self._add_action(file_menu, "Save Plot…",      "Ctrl+S", self.on_save)
        self._add_action(file_menu, "Plot Hovmöller",  "Ctrl+H",
                         lambda: self.gui_plot.plot_hovmoller(self.dm.mdata))
        self._add_action(file_menu, "Generate Report…","Ctrl+R", self.on_report)
        file_menu.addSeparator()
        self._add_action(file_menu, "Reset",           "Ctrl+W", self.on_reset)
        self._add_action(file_menu, "Exit",            "Ctrl+Q", self.close)

        # Edit
        edit_menu = mb.addMenu("&Edit")
        self._add_action(edit_menu, "Get Original Data", None, self.on_go_back)
        self._add_action(edit_menu, "Merge Files",        None, self.on_merge)
        self._add_action(edit_menu, "Cut Endings",        None, self.on_cut_endings)

        # Tools
        tools_menu = mb.addMenu("&Tools")
        self._add_action(tools_menu, "Historical Merge…",          None,
                         self.on_historical_merge)
        self._add_action(tools_menu, "Create Excel Report…",       None,
                         lambda: self._open_browser_dialog(
                             "Select historical file", self.on_write_excel, "Historical file:"))
        tools_menu.addSeparator()
        self._add_action(tools_menu, "Create netCDF…",             None,
                         lambda: self._open_browser_dialog(
                             "Select historical file", self.on_create_netCDF, "Historical file:"))
        self._add_action(tools_menu, "Create Heat Spikes…",        None,
                         lambda: self._open_browser_dialog(
                             "Select historical file", self.on_create_heat_spikes,
                             "Historical file:", "Start year:"))
        self._add_action(tools_menu, "Create Anomalies…",          None,
                         lambda: self._open_browser_dialog(
                             "Select historical file", self.on_create_anomalies,
                             "Historical file:", "Start year:"))
        self._add_action(tools_menu, "Create Tridepth Anomalies…", None,
                         lambda: self._open_browser_dialog(
                             "Select historical file", self.on_create_tridepth,
                             "Historical file:", "Start year:"))
        self._add_action(tools_menu, "Create Quadradepth Anomalies…", None,
                         lambda: self._open_browser_dialog(
                             "Select historical file", self.on_create_quadradepth,
                             "Historical file:", "Start year:"))

        # Help
        help_menu = mb.addMenu("&Help")
        self._add_action(help_menu, "About T-MEDNet…", "F1", self.on_about)

    def _add_action(self, menu: QMenu, text: str, shortcut, slot) -> QAction:
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(shortcut)
        act.triggered.connect(slot)
        menu.addAction(act)
        return act

    # --------------------------------------------------------- Backend init

    def _init_backend(self):
        """Initialise DataManager and GUIPlot with Qt adapters."""
        self._reportlogger = []

        # Create adapters wrapping Qt widgets
        self.console_adapter  = ConsoleAdapter(self.console_widget.text_edit)
        self.textbox_adapter  = TextBoxAdapter(self.plot_widget.report_text)
        self.listbox_adapter  = ListboxAdapter(self.file_panel.list_widget)

        # DataManager — gets the console_writer function
        self.dm = dm_module.DataManager(self.console_adapter, self._reportlogger)

        # GUIPlot — gets the matplotlib figure + canvas from PlotWidget
        self.gui_plot = gp_module.GUIPlot(
            self.plot_widget.fig,
            self.plot_widget.canvas,
            self.console_adapter,
            self._reportlogger,
            self.dm,
        )

        # Wire threshold-button callbacks into PlotWidget
        self.gui_plot._add_threshold_btn    = self.plot_widget.add_threshold_button
        self.gui_plot._clear_threshold_btns = self.plot_widget.clear_threshold_buttons

    # -------------------------------------------------------- Signal wiring

    def _connect_signals(self):
        self.file_panel.file_selected.connect(self._on_file_selected)
        self.file_panel.context_zoom.connect(self.on_ctx_zoom)
        self.file_panel.context_zoom_all.connect(self.on_ctx_zoom_all)
        self.file_panel.context_plot_diff.connect(lambda: self.gui_plot.plot_dif())
        self.file_panel.context_plot_filter.connect(lambda: self.gui_plot.plot_dif_filter1d())
        self.file_panel.context_hovmoller.connect(lambda: self.gui_plot.plot_hovmoller(self.dm.mdata))
        self.file_panel.context_stratification.connect(self._ctx_stratification)
        self.file_panel.context_annual_cycle.connect(self._ctx_annual_cycle)
        self.file_panel.context_thresholds.connect(self._ctx_thresholds)

    # ------------------------------------------------------ File selection

    def _on_file_selected(self, index: int):
        if not self.dm.mdata:
            return
        try:
            if index in self.gui_plot.index:
                return

            self._current_value = self.dm.files[index]
            self.console_adapter("Plotting: ", "action", self._current_value, True)

            self.gui_plot.index.append(index)
            if self.gui_plot.counter and self.gui_plot.counter[-1] == "Zoom":
                self.gui_plot.clear_plots()

            self.gui_plot.counter.append(index)
            self.gui_plot.plot_ts(self.dm.mdata, self.dm.files, index)

            # Update station info panel
            md = self.dm.mdata[index]
            self._info_site.setText(str(md.get("region_name", "—")))
            self._info_depth.setText(f"{md.get('depth', '—')} m")
            self._info_from.setText(
                md["datainici"].strftime("%Y-%m-%d") if md.get("datainici") else "—")
            self._info_to.setText(
                md["datafin"].strftime("%Y-%m-%d") if md.get("datafin") else "—")
            self._info_sn.setText(str(md.get("S/N", "—")))

            self.station_label.setText(f"Station: {md.get('region_name','—')}")

        except (IndexError, AttributeError):
            pass

    # ------------------------------------------------------ Context actions

    def on_ctx_zoom(self):
        self.gui_plot.plot_zoom(
            self.dm.mdata,
            self.dm.files,
            self.listbox_adapter,
            self._cut_data_manually,
        )

    def on_ctx_zoom_all(self):
        self.gui_plot.plot_all_zoom(self.dm.mdata, self.listbox_adapter)

    def _ctx_stratification(self):
        self._open_browser_dialog(
            "Plot Stratification",
            self._do_stratification,
            "Historical file:",
            "Year:",
        )

    def _ctx_annual_cycle(self):
        self._open_browser_dialog(
            "Plot Annual T Cycles",
            self._do_annual_cycle,
            "Historical file:",
            "Year:",
        )

    def _ctx_thresholds(self):
        self._open_browser_dialog(
            "Plot Thresholds",
            self._do_thresholds,
            "Historical file:",
        )

    # ------------------------------------------------- Cut data callback

    def _cut_data_manually(self, event, ind):
        import matplotlib.dates as dates
        from datetime import timedelta
        try:
            xtime = dates.num2date(event.xdata)
            xtime_rounded = (
                xtime.replace(second=0, microsecond=0, minute=0, hour=xtime.hour)
                + timedelta(hours=xtime.minute // 30)
            ).replace(tzinfo=None)

            index = int(self.dm.mdata[0]["df"].index.get_indexer([xtime_rounded])[0])
            self.console_adapter("Cutting data at depth: ", "action", self.dm.mdata[ind]["depth"])
            self.console_adapter(" at site ", "action", self.dm.mdata[ind]["region"], True)

            if self._recoverindex:
                self._recoverindex.append(ind)
            else:
                self._recoverindex = [ind]

            df = self.dm.mdata[ind]["df"]
            if index < len(df) / 3:
                for i in range(len(df[:index])):
                    df["Temp"].iloc[i] = 999
            else:
                for i in range(1, len(df[index:])):
                    df["Temp"].iloc[i + index] = 999
        except (ValueError, TypeError):
            self.console_adapter("Select a value that is not the start or ending", "warning")

    # --------------------------------------------------- File open / save / report

    def on_open(self):
        initial_dir = str(os.path.join(os.path.dirname(__file__), "..", "data"))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Open temperature data files", initial_dir,
            "Temperature files (*.txt *.csv);;All files (*.*)",
        )
        if not files:
            return
        try:
            filesnames = self.dm.openfile(
                tuple(files), self.textbox_adapter, self.listbox_adapter)
            for f in filesnames:
                self.dm.files.append(f)
            self.dm.load_data()
            self._refresh_file_list()
            count = len(self.dm.mdata)
            self.file_count_label.setText(f"Files: {count}")
            self.status_label.setText(f"Loaded {count} file(s)")
        except (TypeError, Exception) as e:
            self.console_adapter("Unable to read file: " + str(e), "warning")

    def load_and_plot_all(self, file_paths):
        """Load files directly (no dialog) and immediately plot all on time series."""
        try:
            filesnames = self.dm.openfile(
                tuple(file_paths), self.textbox_adapter, self.listbox_adapter)
            for f in filesnames:
                self.dm.files.append(f)
            self.dm.load_data()
            self._refresh_file_list()
            count = len(self.dm.mdata)
            self.file_count_label.setText(f"Files: {count}")
            self.status_label.setText(f"Loaded {count} file(s)")
            for i in range(count):
                self._on_file_selected(i)
        except (TypeError, Exception) as e:
            self.console_adapter("load_and_plot_all error: " + str(e), "warning")

    def _refresh_file_list(self):
        """Rebuild the file list widget from dm.mdata (sorted by depth)."""
        from PyQt6.QtWidgets import QListWidgetItem
        from PyQt6.QtGui import QColor
        self.file_panel.list_widget.clear()
        for md in self.dm.mdata:
            depth = md.get("depth", "?")
            site  = md.get("region_name", "?")
            date_from = md["datainici"].strftime("%Y-%m-%d") if md.get("datainici") else "?"
            date_to   = md["datafin"].strftime("%Y-%m-%d")   if md.get("datafin")   else "?"
            display = f"  {depth} m  —  {site}"
            item = QListWidgetItem(display)
            item.setForeground(QColor("#C8DDE8"))
            item.setToolTip(f"Site: {site}\nDepth: {depth} m\nFrom: {date_from}\nTo:   {date_to}")
            self.file_panel.list_widget.addItem(item)

    def on_save(self):
        try:
            counter = self.gui_plot.counter
            if not counter:
                raise AttributeError

            zoom = ""
            if counter[-1] == "Zoom":
                zoom = self.gui_plot.counter.pop()

            if len(counter) == 1:
                c = counter[0]
                type_map = {
                    "Hovmoller":      str(self._current_value[:-7]) + " Hovmoller",
                    "Cycles":         self.gui_plot.savefilename,
                    "Thresholds":     self.gui_plot.savefilename,
                    "Filter":         str(self._current_value[:-7]) + " filtered differences",
                    "Difference":     str(self._current_value[:-7]) + " differences",
                    "Stratification": self.gui_plot.savefilename,
                }
                filename = type_map.get(c, self._current_value[:-4] + " " + zoom)
            elif len(counter) > 1:
                filename = ""
                for n in counter:
                    filename += "_" + self.dm.files[n][-6:-4]
                filename = (
                    self.dm.mdata[0]["datainici"].strftime("%Y-%m-%d") + "_"
                    + self.dm.mdata[0]["datafin"].strftime("%Y-%m-%d")
                    + "_Combo of depths" + filename + " " + zoom
                )
            else:
                filename = "plot"

            path, _ = QFileDialog.getSaveFileName(
                self, "Save plot",
                os.path.join(os.path.dirname(__file__), "..", "data", filename),
                "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*.*)",
            )
            if zoom == "Zoom":
                self.gui_plot.counter.append(zoom)
            if path:
                self.gui_plot.fig.savefig(path, dpi=150, bbox_inches="tight")
                self.dm.mdata[0]["images"].append(path)
                self.console_adapter("Saving plot: ", "action", path, True)

        except (AttributeError, UnboundLocalError, IndexError):
            self.console_adapter("No plot to save", "warning")

    def on_report(self):
        if not self.dm.mdata:
            self.console_adapter("Load a file before generating a report", "warning")
            return
        self.dm.report(self.textbox_adapter)
        # Switch to report tab in plot widget
        self.plot_widget.show_report_tab()

    def on_reset(self):
        reply = QMessageBox.question(
            self, "Reset", "Clear all data and plots?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.gui_plot.clear_plots()
            self.file_panel.list_widget.clear()
            self.plot_widget.report_text.clear()
            self.console_widget.text_edit.clear()
            self._init_backend()
            self._recoverindex = None
            self._current_value = ""
            self.file_count_label.setText("Files: 0")
            self.station_label.setText("Station: —")
            self._clear_info_panel()
            self.status_label.setText("Ready")

    def _clear_info_panel(self):
        for lbl in (self._info_site, self._info_depth,
                    self._info_from, self._info_to, self._info_sn):
            lbl.setText("—")

    # --------------------------------------------------- Edit actions

    def on_go_back(self):
        try:
            if self._recoverindex:
                for i in self._recoverindex:
                    self.dm.mdata[i]["df"] = self.dm.tempdataold[i]["df"].copy()
                self._recoverindex = None
            else:
                for i, data in enumerate(self.dm.mdata):
                    data["df"] = self.dm.tempdataold[i]["df"].copy()
            self.console_adapter("Recovering original data", "action")
            self.gui_plot.clear_plots()
        except (AttributeError, TypeError):
            self.console_adapter("Cut data before trying to recover it", "warning")

    def on_merge(self):
        try:
            self.console_adapter("Creating GeoJSON + TXT merge…", "action")
            df, depths, SN, merging = self.dm.merge()
            if not merging:
                self.console_adapter(
                    "Only one file loaded — single-file output created", "warning")
            t0 = time.time()
            self.dm.df_to_geojson(df, depths, SN)
            self.dm.df_to_txt(df, SN)
            elapsed = time.time() - t0
            self.console_adapter(f"Merge complete in {elapsed:.1f}s — saved to: {_OUTPUT_DIR}", "action")
            self._reportlogger.append("GeoJSON and CSV file created")
        except IndexError:
            self.console_adapter("Load a file first", "warning")

    def on_cut_endings(self):
        if self.dm.mdata:
            self.dm.zoom_data_loop()
            self.console_adapter("Endings of all files cut", "action", liner=True)
            self._reportlogger.append("Endings and start automatically cut")
        else:
            self.console_adapter("Load a file before trying to cut it", "warning")

    # -------------------------------------------------- Tools actions

    def on_historical_merge(self):
        dlg = HistoricalMergeDialog(self)
        if dlg.exec():
            f1, f2, out = dlg.values()
            self.console_adapter("Running historical merge…", "action")
            try:
                duplicity = fw_module.big_merge(f1, f2, out)
                if duplicity:
                    self.console_adapter(
                        f"Found {len(duplicity)} duplicate dates. "
                        f"First: {duplicity[0]}, last: {duplicity[-1]}", "warning")
                self.console_adapter("Historical merge successful!", "action")
            except Exception as e:
                self.console_adapter("Merge failed: " + str(e), "warning")

    def _open_browser_dialog(self, title, callback, label1, label2=None):
        dlg = BrowserDialog(self, title, label1, label2)
        dlg.dialog_accepted.connect(callback)
        dlg.show()

    def on_write_excel(self, historical, second=None):
        self.console_adapter(f"Writing Excel report — this may take a minute…", "action")
        self.console_adapter(f"Output folder: {_OUTPUT_DIR}", "action")

        def _run():
            er = ew_module.ExcelReport(historical)
            er.excel_writer()

        def _on_done():
            self.console_adapter(f"Excel report created in: {_OUTPUT_DIR}", "action")
            reply = QMessageBox.information(
                self, "Excel Report Created",
                f"Report saved to:\n\n{_OUTPUT_DIR}\n\nOpen the output folder?",
                QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Close,
            )
            if reply == QMessageBox.StandardButton.Open:
                self._open_folder(_OUTPUT_DIR)

        self._run_in_thread(_run, on_done=_on_done)

    def on_create_netCDF(self, historical, second=None):
        df = pd.read_csv(historical, sep="\t")
        self.dm.convert_to_netCDF("finalCDM", df)

    def on_create_heat_spikes(self, historical, year):
        if not year:
            self.console_adapter("Please provide a start year", "warning")
            return
        self.console_adapter(f"Creating heat spike plots from {year}…", "action")
        self.console_adapter(f"Output folder: {_IMG_DIR}", "action")
        def _run():
            historic = st_module.HistoricData(historical)
            for i in range(int(year), historic.last_year):
                historic.browse_heat_spikes(i)
        def _done():
            self.console_adapter(f"Heat spike plots saved to: {_IMG_DIR}", "action")
            QMessageBox.information(self, "Done", f"Images saved to:\n\n{_IMG_DIR}")
        self._run_in_thread(_run, on_done=_done)

    def on_create_anomalies(self, historical, year):
        if not year:
            self.console_adapter("Please provide a start year", "warning")
            return
        self.console_adapter(f"Creating anomaly plots from {year}…", "action")
        self.console_adapter(f"Output folder: {_IMG_DIR}", "action")
        def _run():
            historic = st_module.HistoricData(historical)
            for i in range(int(year), historic.last_year):
                historic.browse_anomalies(i)
        def _done():
            self.console_adapter(f"Anomaly plots saved to: {_IMG_DIR}", "action")
            QMessageBox.information(self, "Done", f"Images saved to:\n\n{_IMG_DIR}")
        self._run_in_thread(_run, on_done=_done)

    def on_create_tridepth(self, historical, year):
        if not year:
            return
        self.console_adapter(f"Creating tridepth anomalies from {year}…", "action")
        def _run():
            historic = st_module.HistoricData(historical)
            for i in range(int(year), historic.last_year):
                historic.multidepth_anomaly_plotter(i)
        def _done():
            self.console_adapter(f"Tridepth plots saved to: {_IMG_DIR}", "action")
        self._run_in_thread(_run, on_done=_done)

    def on_create_quadradepth(self, historical, year):
        if not year:
            return
        self.console_adapter(f"Creating quadradepth anomalies from {year}…", "action")
        def _run():
            historic = st_module.HistoricData(historical)
            for i in range(int(year), historic.last_year):
                historic.multidepth_anomaly_plotter(i, ["10", "15", "20", "25"], zoom=True)
        def _done():
            self.console_adapter(f"Quadradepth plots saved to: {_IMG_DIR}", "action")
        self._run_in_thread(_run, on_done=_done)

    # ---- plot callbacks from context dialogs ----

    def _do_stratification(self, historical, year):
        self.gui_plot.plot_stratification(historical, year)

    def _do_annual_cycle(self, historical, year):
        self.gui_plot.plot_annual_T_cycle(historical, year)

    def _do_thresholds(self, historical, year=None):
        self.gui_plot.plot_thresholds(historical, None, self.console_adapter)

    # -------------------------------------------------- Help

    def on_about(self):
        dlg = AboutDialog(self, VERSION, BUILD)
        dlg.exec()

    # -------------------------------------------------- Folder helper

    def _open_folder(self, path: str):
        """Open a folder in the OS file manager."""
        import subprocess
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.console_adapter(f"Could not open folder: {e}", "warning")

    # -------------------------------------------------- Threading helper
    #
    # Uses Python threading.Thread + a QTimer that polls every 200 ms.
    # All callbacks run on the main thread (inside the timer slot) so Qt
    # widget calls are always safe.  This is more reliable than QThread +
    # moveToThread in frozen/windowed executables.

    def _run_in_thread(self, fn, on_done=None, on_err=None):
        # State shared between the worker thread and the poll timer
        _state = {'done': False, 'error': None}   # error = traceback str or None

        def _worker():
            try:
                fn()
            except BaseException:
                tb = _traceback.format_exc()
                _log_error(tb)
                _state['error'] = tb
            finally:
                _state['done'] = True

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        poll = QTimer(self)
        poll.setInterval(200)

        def _check():
            if not _state['done']:
                return
            poll.stop()
            poll.deleteLater()
            self._set_busy(False)
            if _state['error']:
                short = _state['error'].strip().splitlines()[-1]
                self.console_adapter(f"Error: {short}", "warning")
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Operation Failed")
                dlg.setIcon(QMessageBox.Icon.Critical)
                dlg.setText(f"An error occurred:\n\n{short}")
                dlg.setDetailedText(_state['error'])
                dlg.exec()
                if on_err:
                    try:
                        on_err(short)
                    except Exception:
                        pass
            else:
                if on_done:
                    try:
                        on_done()
                    except Exception as e:
                        self.console_adapter(f"Callback error: {e}", "warning")

        poll.timeout.connect(_check)
        self._set_busy(True)
        poll.start()

    def _set_busy(self, busy: bool):
        if busy:
            self.status_label.setObjectName("statusWorking")
            self.status_label.setText("Working…")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            self.status_label.setObjectName("statusReady")
            self.status_label.setText("Ready")
            QApplication.restoreOverrideCursor()
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    # -------------------------------------------------- Theme toggle

    def on_toggle_theme(self):
        import matplotlib
        self._dark_mode = not self._dark_mode
        matplotlib.rcParams.update(DARK_MPL if self._dark_mode else LIGHT_MPL)
        QApplication.instance().setStyleSheet(OCEAN_DARK if self._dark_mode else OCEAN_LIGHT)
        self._theme_btn.setText("☀" if self._dark_mode else "🌙")
        self._theme_btn.setToolTip(
            "Switch to light theme" if self._dark_mode else "Switch to dark theme")
        self._apply_mpl_theme_to_figure()

    def _apply_mpl_theme_to_figure(self):
        params = DARK_MPL if self._dark_mode else LIGHT_MPL
        fig = self.plot_widget.fig
        fig.patch.set_facecolor(params['figure.facecolor'])
        fig.set_facecolor(params['figure.facecolor'])
        fig.set_edgecolor(params['figure.edgecolor'])
        for ax in fig.get_axes():
            ax.set_facecolor(params['axes.facecolor'])
            ax.spines['bottom'].set_color(params['axes.edgecolor'])
            ax.spines['left'].set_color(params['axes.edgecolor'])
            ax.tick_params(colors=params['xtick.color'],
                           labelcolor=params['xtick.labelcolor'])
            ax.xaxis.label.set_color(params['axes.labelcolor'])
            ax.yaxis.label.set_color(params['axes.labelcolor'])
            ax.title.set_color(params['axes.titlecolor'])
            legend = ax.get_legend()
            if legend:
                legend.get_frame().set_facecolor(params['legend.facecolor'])
                legend.get_frame().set_edgecolor(params['legend.edgecolor'])
                for text in legend.get_texts():
                    text.set_color(params['legend.labelcolor'])
        self.plot_widget.canvas.draw_idle()

    # -------------------------------------------------- Close

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Exit", "Quit T-MEDNet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
