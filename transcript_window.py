"""Scrollable, resizable transcript viewer for file STT."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QTextOption
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)


class TranscriptWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Transcript')
        self.setMinimumSize(420, 280)
        self.resize(560, 420)
        self.setWindowFlags(Qt.Window)

        layout = QVBoxLayout(self)
        self.status = QLabel('')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.editor.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        layout.addWidget(self.editor, 1)

        row = QHBoxLayout()
        self.copy_button = QPushButton('Transcript kopiëren')
        self.copy_button.clicked.connect(self.copy_transcript)
        row.addWidget(self.copy_button)
        row.addStretch(1)
        layout.addLayout(row)

        self._follow_tail = True
        self.editor.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def prepare(self, title: str):
        self.setWindowTitle(title)
        self.editor.clear()
        self.status.setText('Bezig…')
        self._follow_tail = True
        self.show()
        self.raise_()
        self.activateWindow()

    def append_segment(self, text: str):
        text = (text or '').strip()
        if not text:
            return
        current = self.editor.toPlainText()
        if current:
            self.editor.appendPlainText(text)
        else:
            self.editor.setPlainText(text)
        if self._follow_tail:
            bar = self.editor.verticalScrollBar()
            bar.setValue(bar.maximum())

    def set_finished(self, message: str):
        self.status.setText(message)

    def transcript_text(self) -> str:
        return self.editor.toPlainText()

    def copy_transcript(self) -> bool:
        text = self.transcript_text()
        if not text:
            return False
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        self.status.setText('Transcript gekopieerd naar klembord.')
        return True

    def _on_scroll(self, value):
        bar = self.editor.verticalScrollBar()
        self._follow_tail = value >= bar.maximum() - 2
