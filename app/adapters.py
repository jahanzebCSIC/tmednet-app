"""
Adapter classes that bridge the Tkinter widget API used in the backend
modules to PyQt6 widgets. This allows the original backend code (data_manager,
gui_plots, etc.) to run unchanged inside a PyQt6 application.
"""

from PyQt6.QtWidgets import QTextEdit, QListWidget
from PyQt6.QtCore import Qt


# ---------------------------------------------------------------------------
# Console adapter  (wraps QTextEdit used as the log console)
# ---------------------------------------------------------------------------

class ConsoleAdapter:
    """Wraps a QTextEdit and exposes the Tkinter Text widget API used by the backend."""

    _TAG_COLORS = {
        "action":  "#5BA4CF",   # steel-blue for normal actions
        "warning": "#E94560",   # red for warnings
    }

    def __init__(self, qt_widget: QTextEdit):
        self._w = qt_widget
        self._tags: dict = {}

    # --- Tkinter-compatible API ---

    def tag_config(self, tagName: str, **kwargs):
        """Store tag style so insert() can use it later."""
        self._tags[tagName] = kwargs

    def insert(self, index, chars: str, *tags):
        color = "#ECEFF4"
        bold = False
        for tag in tags:
            cfg = self._tags.get(tag, {})
            if cfg:
                tk_color = cfg.get("foreground", "")
                # Map some Tkinter color names to hex
                _TK_MAP = {
                    "firebrick3": "#E94560",
                    "steelblue4": "#5BA4CF",
                    "white":      "#ECEFF4",
                }
                color = _TK_MAP.get(tk_color, tk_color or "#ECEFF4")
                bold = "bold" in cfg.get("font", "")
                break
            # Also check class-level defaults
            if tag in self._TAG_COLORS:
                color = self._TAG_COLORS[tag]
                break

        safe = (str(chars)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>")
                .replace(" ", "&nbsp;"))

        weight = "bold" if bold else "normal"
        html = (f'<span style="color:{color}; font-weight:{weight}; '
                f'font-family:Consolas,monospace;">{safe}</span>')

        cursor = self._w.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertHtml(html)
        self._w.setTextCursor(cursor)

        # Auto-scroll
        sb = self._w.verticalScrollBar()
        sb.setValue(sb.maximum())

    def see(self, index):
        sb = self._w.verticalScrollBar()
        sb.setValue(sb.maximum())

    def delete(self, index1, index2=None):
        self._w.clear()

    def config(self, **kwargs):
        pass

    # Allow the adapter to be called as a function (some backend code calls
    # console_writer directly, others call self.consolescreen methods)
    def __call__(self, msg, mod="action", var=False, liner=False):
        """Mimics the tmednet.console_writer function signature."""
        if var:
            self.insert("end", msg, mod)
            self.insert("end", str(var))
            if liner:
                self.insert("end", "\n =============\n")
        else:
            self.insert("end", msg + "\n", mod)
            self.insert("end", "=============\n")
        self.see("end")


# ---------------------------------------------------------------------------
# Report / text-box adapter  (wraps the QTextEdit used for the report tab)
# ---------------------------------------------------------------------------

class TextBoxAdapter:
    """Wraps a QTextEdit used for displaying the generated report text."""

    def __init__(self, qt_widget: QTextEdit):
        self._w = qt_widget

    def insert(self, index, chars: str, *tags):
        safe = (str(chars)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>"))
        html = f'<span style="color:#C8DDE8;">{safe}</span>'
        cursor = self._w.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertHtml(html)
        self._w.setTextCursor(cursor)
        sb = self._w.verticalScrollBar()
        sb.setValue(sb.maximum())

    def get(self, index1, index2=None):
        return self._w.toPlainText()

    def delete(self, index1, index2=None):
        self._w.clear()

    def see(self, index):
        sb = self._w.verticalScrollBar()
        sb.setValue(sb.maximum())

    def tag_config(self, tagName, **kwargs):
        pass

    def config(self, **kwargs):
        pass


# ---------------------------------------------------------------------------
# Listbox adapter  (wraps QListWidget — used by data_manager.openfile)
# ---------------------------------------------------------------------------

class ListboxAdapter:
    """Wraps a QListWidget and exposes the Tkinter Listbox API."""

    def __init__(self, qt_widget: QListWidget):
        self._w = qt_widget

    def insert(self, index, *elements):
        for e in elements:
            self._w.addItem(str(e))

    def curselection(self):
        row = self._w.currentRow()
        return (row,) if row >= 0 else ()

    def get(self, index):
        item = self._w.item(index)
        return item.text() if item else None

    def delete(self, first, last=None):
        self._w.clear()

    def size(self):
        return self._w.count()

    def selection_set(self, index):
        self._w.setCurrentRow(index)
