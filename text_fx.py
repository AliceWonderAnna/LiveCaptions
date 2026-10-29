"""Caption text outline and soft drop-shadow drawing helpers."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen


def color_with_opacity(hex_color: str, opacity_percent: int) -> QColor:
    color = QColor(hex_color)
    color.setAlpha(max(0, min(255, round(opacity_percent * 2.55))))
    return color


def text_path(text: str, font: QFont, x: float, y: float) -> QPainterPath:
    path = QPainterPath()
    path.addText(x, y, font, text)
    return path


def line_origin(text: str, font: QFont, width: int, line_index: int, line_height: float) -> tuple[float, float]:
    metrics = QFontMetricsF(font)
    x = max(16.0, (width - metrics.horizontalAdvance(text)) / 2)
    y = 16.0 + metrics.ascent() + line_index * line_height
    return x, y


def draw_caption_path(painter: QPainter, path: QPainterPath, settings: dict) -> None:
    """Draw shadow, outline, then fill for one caption glyph path."""
    if settings.get('shadow_enabled', True):
        blur = max(0, int(settings.get('shadow_blur', 0)))
        ox = int(settings.get('shadow_offset_x', 0))
        oy = int(settings.get('shadow_offset_y', 0))
        base = color_with_opacity(settings.get('shadow_color', '#000000'),
                                  int(settings.get('shadow_opacity', 55)))
        steps = max(1, blur // 2 + 1)
        for step in range(steps, 0, -1):
            layer = QColor(base)
            layer.setAlpha(max(1, round(base.alpha() * step / (steps * steps))))
            spread = blur * step / steps if blur else 0
            shadow = QPainterPath(path)
            shadow.translate(ox + spread * 0.15, oy + spread * 0.15)
            painter.fillPath(shadow, layer)

    if settings.get('outline_enabled', True):
        width = float(settings.get('outline_width', 0))
        if width > 0:
            pen = QPen(
                color_with_opacity(settings.get('outline_color', '#000000'),
                                   int(settings.get('outline_opacity', 86))),
                width,
                Qt.SolidLine,
                Qt.RoundCap,
                Qt.RoundJoin,
            )
            painter.strokePath(path, pen)

    painter.fillPath(path, QColor(settings.get('text_color', '#ffffff')))
