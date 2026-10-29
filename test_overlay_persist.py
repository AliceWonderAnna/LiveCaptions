"""Overlay hide timer respects persist_text."""
import os

from core import DEFAULTS


def test_show_caption_skips_timer_when_persist():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from app import Overlay

    app = QApplication.instance() or QApplication([])
    settings = DEFAULTS.copy()
    settings['persist_text'] = True
    overlay = Overlay(settings)
    overlay.show_caption('blijf staan')
    assert overlay.text == 'blijf staan'
    assert not overlay.timer.isActive()
    overlay.close()
    assert app is not None


def test_show_caption_starts_timer_when_not_persist():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from app import Overlay

    app = QApplication.instance() or QApplication([])
    settings = DEFAULTS.copy()
    settings['persist_text'] = False
    settings['hide_seconds'] = 2.5
    overlay = Overlay(settings)
    overlay.show_caption('tijdelijk')
    assert overlay.timer.isActive()
    overlay.close()
    assert app is not None
