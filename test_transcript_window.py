"""Tests for the file-STT transcript window."""
import os

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from transcript_window import TranscriptWindow


def _app():
    return QApplication.instance() or QApplication([])


def test_transcript_window_append_and_copy():
    app = _app()
    window = TranscriptWindow()
    window.prepare('Transcript · demo.wav')
    assert window.windowTitle() == 'Transcript · demo.wav'
    assert window.editor.isReadOnly()
    flags = window.editor.textInteractionFlags()
    assert flags & Qt.TextSelectableByMouse
    assert flags & Qt.TextSelectableByKeyboard

    window.append_segment('Eerste zin')
    window.append_segment('Tweede zin')
    assert window.transcript_text() == 'Eerste zin\nTweede zin'

    assert window.copy_transcript() is True
    assert app.clipboard().text() == 'Eerste zin\nTweede zin'
    assert 'klembord' in window.status.text().lower()

    window.set_finished('Klaar · opgeslagen: demo.srt')
    assert 'demo.srt' in window.status.text()
    window.close()


def test_copy_empty_returns_false():
    _app()
    window = TranscriptWindow()
    window.prepare('Transcript')
    assert window.copy_transcript() is False
    window.close()
