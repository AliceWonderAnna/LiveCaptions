"""Tests for caption text outline/shadow drawing."""
import os

from core import DEFAULTS
from text_fx import color_with_opacity, draw_caption_path, line_origin, text_path


def test_color_with_opacity_alpha():
    color = color_with_opacity('#000000', 86)
    assert color.red() == 0
    assert color.alpha() == round(86 * 2.55)


def test_line_origin_and_path():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    font = QFont('Segoe UI', 24)
    x, y = line_origin('Hallo', font, 800, 0, 30)
    assert x >= 16
    assert y > 0
    path = text_path('Hallo', font, x, y)
    assert not path.isEmpty()
    assert app is not None


def test_draw_caption_path_with_fx_on_and_off():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtGui import QFont, QImage, QPainter
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    font = QFont('Segoe UI', 28)
    path = text_path('CC', font, 40, 50)
    image = QImage(200, 100, QImage.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)

    settings = DEFAULTS.copy()
    draw_caption_path(painter, path, settings)

    settings['outline_enabled'] = False
    settings['shadow_enabled'] = False
    draw_caption_path(painter, path, settings)

    settings['outline_enabled'] = True
    settings['outline_width'] = 0
    settings['shadow_enabled'] = True
    settings['shadow_blur'] = 0
    draw_caption_path(painter, path, settings)
    painter.end()
    assert app is not None
    assert not image.isNull()
