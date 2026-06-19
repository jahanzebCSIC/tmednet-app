"""
ConsoleWidget — styled read-only log console that shows backend messages
with colour-coded severity (action = blue, warning = red).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ConsoleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 2, 8, 6)
        root.setSpacing(2)

        # Toolbar row
        hbar = QHBoxLayout()
        hbar.setContentsMargins(0, 0, 0, 0)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(20)
        clear_btn.setFixedWidth(46)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #3A6080;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover { color: #E94560; }
        """)
        clear_btn.clicked.connect(lambda: self.text_edit.clear())
        hbar.addStretch()
        hbar.addWidget(clear_btn)
        root.addLayout(hbar)

        # The actual log area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setObjectName("consoleLog")
        self.text_edit.setFont(QFont("Cascadia Code", 10))
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #060F1A;
                color: #6A9AB0;
                border: 1px solid #0E2035;
                border-radius: 5px;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 10px;
                padding: 4px;
            }
        """)
        root.addWidget(self.text_edit)
