"""Live Captions — Windows desktop overlay, v0.6.1."""
import os
import sys

try:
    from Secret import TOKEN
except ImportError:
    TOKEN = None
if TOKEN:
    os.environ["HF_TOKEN"] = TOKEN.strip()

import ctypes
from ctypes import wintypes
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QAbstractNativeEventFilter
from PySide6.QtGui import QColor, QFont, QPainter, QTextLayout, QTextOption, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QFontComboBox, QColorDialog,
    QCheckBox, QSystemTrayIcon, QMenu, QMessageBox, QFileDialog)
from audio_devices import list_capture_devices, source_choices
from caption_buffer import CaptionBuffer
from core import load_settings, save_settings
from audio_engine import Engine
from file_engine import FileEngine
from paths import parse_profile_arg, resource_path, settings_path
from text_fx import draw_caption_path, line_origin, text_path
from transcript_export import is_supported_media
from transcript_window import TranscriptWindow
from version import VERSION

PROFILE = ''
SETTINGS = settings_path()


def app_icon() -> QIcon:
    icon_file = resource_path("assets", "livecaptions.ico")
    if icon_file.is_file():
        return QIcon(str(icon_file))
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor("#397deb"))
    painter = QPainter(pixmap)
    painter.setPen(Qt.white)
    painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "CC")
    painter.end()
    return QIcon(pixmap)


class Bus(QObject):
    caption = Signal(str, bool)
    status = Signal(str)
    error = Signal(str)
    done = Signal()
    file_segment = Signal(str)
    file_status = Signal(str)
    file_error = Signal(str)
    file_done = Signal()

class Overlay(QWidget):
    moved = Signal(int, int)

    def __init__(self, settings):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.settings = settings
        self.text = ''
        self.enabled = True
        self.drag = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clear)
        self.apply()
        self.reset_position(saved=True)

    def reset_position(self, saved=False):
        rect = QApplication.primaryScreen().availableGeometry()
        x, y = self.settings['x'], self.settings['y']
        if not saved or x is None or y is None or not any(
                screen.availableGeometry().contains(x + 40, y + 40) for screen in QApplication.screens()):
            x, y = rect.center().x() - self.width() // 2, rect.bottom() - self.height() - 70
        self.move(x, y)
        self.moved.emit(x, y)

    def apply(self):
        s = self.settings
        self.font = QFont(s['font'], s['font_size'], QFont.DemiBold)
        from PySide6.QtGui import QFontMetrics
        self.line_height = QFontMetrics(self.font).lineSpacing()
        self.resize(s['width'], self.line_height * s['lines'] + 32)
        self.setWindowOpacity(s['window_opacity'] / 100)
        self.setWindowFlag(Qt.WindowTransparentForInput, s['click_through'])
        if s.get('persist_text'):
            self.timer.stop()
        self.sync_visibility()
        self.update()

    def sync_visibility(self):
        self.setVisible(self.enabled and bool(self.text))

    def show_caption(self, text):
        self.text = text
        if self.settings.get('persist_text'):
            self.timer.stop()
        else:
            self.timer.start(int(self.settings['hide_seconds'] * 1000))
        self.sync_visibility()
        self.update()

    def clear(self):
        self.text = ''
        self.sync_visibility()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        opacity = self.settings['background_opacity']
        # A barely visible surface provides a drag target in edit mode.
        alpha = max(1 if not self.settings['click_through'] else 0, round(opacity * 2.55))
        painter.setBrush(QColor(0, 0, 0, alpha))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)
        layout = QTextLayout(self.text, self.font)
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        option.setAlignment(Qt.AlignHCenter)
        layout.setTextOption(option)
        layout.beginLayout()
        lines = []
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(self.width() - 32)
            lines.append(line)
        layout.endLayout()
        for i, line in enumerate(lines[-self.settings['lines']:]):
            text = self.text[line.textStart():line.textStart() + line.textLength()].strip()
            if not text:
                continue
            x, y = line_origin(text, self.font, self.width(), i, self.line_height)
            draw_caption_path(painter, text_path(text, self.font, x, y), self.settings)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = event.globalPosition().toPoint() - self.pos()
            self.timer.stop()

    def mouseMoveEvent(self, event):
        if self.drag is not None:
            self.move(event.globalPosition().toPoint() - self.drag)

    def mouseReleaseEvent(self, event):
        self.drag = None
        self.moved.emit(self.x(), self.y())
        if not self.settings.get('persist_text'):
            self.timer.start(int(self.settings['hide_seconds'] * 1000))

class Hotkeys(QAbstractNativeEventFilter):
    def __init__(self, owner):
        super().__init__()
        self.owner, self.registered = owner, []
        if sys.platform == 'win32':
            for ident, key in [(1, ord('H')), (2, ord('C')), (3, ord('S'))]:
                if ctypes.windll.user32.RegisterHotKey(None, ident, 0x4003, key):
                    self.registered.append(ident)
        QApplication.instance().installNativeEventFilter(self)

    def nativeEventFilter(self, event_type, message):
        if sys.platform == 'win32':
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312:
                actions = {1: self.owner.toggle_visible, 2: self.owner.toggle_click, 3: self.owner.reveal}
                action = actions.get(int(msg.wParam))
                if action:
                    QTimer.singleShot(0, action)
                    return True, 0
        return False, 0

    def close(self):
        QApplication.instance().removeNativeEventFilter(self)
        for ident in self.registered:
            ctypes.windll.user32.UnregisterHotKey(None, ident)

class Window(QWidget):
    def __init__(self, demo=False, profile=''):
        super().__init__()
        self.profile = profile or ''
        self.settings_file = settings_path(self.profile or None)
        self.s, warning = load_settings(self.settings_file)
        if not QColor(self.s['text_color']).isValid():
            self.s['text_color'] = '#ffffff'
        self.engine = None
        self.file_engine = None
        self.demo = demo
        self.closing = False
        self.buffer = CaptionBuffer()
        profile_bit = f' · {self.profile}' if self.profile else ''
        self.setWindowTitle(f'Live Captions {VERSION}{profile_bit} · Instellingen')
        self.setMinimumWidth(470)
        self.bus = Bus()
        self.overlay = Overlay(self.s)
        self.transcript = TranscriptWindow()
        self.overlay.moved.connect(self.position_changed)
        self.bus.caption.connect(self.receive_caption)
        self.bus.status.connect(self.set_status)
        self.bus.error.connect(self.on_error)
        self.bus.file_segment.connect(self.on_file_segment)
        self.bus.file_status.connect(self.on_file_status)
        self.bus.file_error.connect(self.on_file_error)
        self.bus.file_done.connect(self.file_finished)
        self.bus.done.connect(self.finished)
        outer = QVBoxLayout(self)
        title = QLabel(f'Live Captions {VERSION}{profile_bit}')
        title.setStyleSheet('font-size:24px; font-weight:600')
        outer.addWidget(title)
        outer.addWidget(QLabel('Lokale ondertiteling · geen transcriptopslag'))
        form = QFormLayout()
        outer.addLayout(form)
        self.controls = {}
        source_row = QHBoxLayout()
        self.source_combo = QComboBox()
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        self.controls['source'] = self.source_combo
        source_row.addWidget(self.source_combo, 1)
        self.refresh_button = QPushButton('Vernieuwen')
        self.refresh_button.clicked.connect(self.refresh_sources)
        source_row.addWidget(self.refresh_button)
        form.addRow('Audiobron', source_row)
        self.refresh_sources()
        for key, label, options in [
            ('model', 'Whisper-model', [('Tiny · sneller', 'tiny'), ('Base · standaard', 'base'), ('Small · nauwkeuriger', 'small')]),
            ('language', 'Gesproken taal', [('Nederlands', 'nl'), ('Engels', 'en'), ('Automatisch', 'auto'), ('Duits', 'de'), ('Frans', 'fr'), ('Spaans', 'es')])]:
            combo = QComboBox()
            for text, data in options:
                combo.addItem(text, data)
            combo.setCurrentIndex(combo.findData(self.s[key]))
            combo.currentIndexChanged.connect(lambda _, k=key, c=combo: self.change(k, c.currentData()))
            self.controls[key] = combo
            form.addRow(label, combo)
        font = QFontComboBox()
        font.setCurrentFont(QFont(self.s['font']))
        font.currentFontChanged.connect(lambda f: self.change('font', f.family()))
        form.addRow('Lettertype', font)
        for key, label, low, high in [('font_size', 'Tekstgrootte (pt)', 12, 80),
                                     ('width', 'Breedte (px)', 250, 3000), ('lines', 'Regels', 1, 12),
                                     ('background_opacity', 'Achtergronddekking (%)', 0, 100),
                                     ('window_opacity', 'Vensterdekking incl. tekst (%)', 10, 100)]:
            spin = QSpinBox()
            spin.setRange(low, high)
            spin.setValue(self.s[key])
            spin.valueChanged.connect(lambda v, k=key: self.change(k, v))
            if key == 'lines':
                self.controls[key] = spin
            form.addRow(label, spin)
        for key, label, low, high, decimals in [
            ('hide_seconds', 'Verbergen na laatste tekst (sec)', .5, 20, 1),
            ('threshold', 'Spraakdrempel (lager = gevoeliger)', .0001, .2, 4),
            ('max_seconds', 'Max. spraakblok (sec)', 1, 10, 1),
            ('partial_seconds', 'Tussentijdse tekst (sec)', .3, 1.5, 1),
            ('silence_seconds', 'Pauze vóór afronden (sec)', .15, 1.0, 2)]:
            spin = QDoubleSpinBox()
            spin.setDecimals(decimals)
            spin.setRange(low, high)
            if key == 'threshold':
                step = .001
            elif key in ('partial_seconds', 'silence_seconds'):
                step = .1
            else:
                step = .5
            spin.setSingleStep(step)
            spin.setValue(self.s[key])
            spin.valueChanged.connect(lambda v, k=key: self.change(k, v))
            self.controls[key] = spin
            form.addRow(label, spin)
        color = QPushButton('Tekstkleur kiezen…')
        color.clicked.connect(lambda: self.choose_color('text_color'))
        form.addRow('Tekstkleur', color)

        outer.addWidget(QLabel('Tekstweergave'))
        fx = QFormLayout()
        outer.addLayout(fx)
        self.outline = QCheckBox('Outline')
        self.outline.setChecked(self.s['outline_enabled'])
        self.outline.toggled.connect(lambda v: self.change('outline_enabled', v))
        fx.addRow(self.outline)
        for key, label, low, high in [
            ('outline_width', 'Outline-dikte (px)', 0, 12),
            ('outline_opacity', 'Outline-dekking (%)', 0, 100),
        ]:
            spin = QSpinBox()
            spin.setRange(low, high)
            spin.setValue(self.s[key])
            spin.valueChanged.connect(lambda v, k=key: self.change(k, v))
            fx.addRow(label, spin)
        outline_color = QPushButton('Outline-kleur kiezen…')
        outline_color.clicked.connect(lambda: self.choose_color('outline_color'))
        fx.addRow('Outline-kleur', outline_color)
        self.shadow = QCheckBox('Drop shadow')
        self.shadow.setChecked(self.s['shadow_enabled'])
        self.shadow.toggled.connect(lambda v: self.change('shadow_enabled', v))
        fx.addRow(self.shadow)
        for key, label, low, high in [
            ('shadow_offset_x', 'Shadow X (px)', -20, 20),
            ('shadow_offset_y', 'Shadow Y (px)', -20, 20),
            ('shadow_blur', 'Shadow softheid', 0, 20),
            ('shadow_opacity', 'Shadow-dekking (%)', 0, 100),
        ]:
            spin = QSpinBox()
            spin.setRange(low, high)
            spin.setValue(self.s[key])
            spin.valueChanged.connect(lambda v, k=key: self.change(k, v))
            fx.addRow(label, spin)
        shadow_color = QPushButton('Shadow-kleur kiezen…')
        shadow_color.clicked.connect(lambda: self.choose_color('shadow_color'))
        fx.addRow('Shadow-kleur', shadow_color)

        self.persist_text = QCheckBox('Tekst blijft zichtbaar')
        self.persist_text.setChecked(self.s['persist_text'])
        self.persist_text.toggled.connect(self.on_persist_toggled)
        outer.addWidget(self.persist_text)
        self.accumulate = QCheckBox('Monoloog opbouwen')
        self.accumulate.setChecked(self.s['accumulate_text'])
        self.accumulate.toggled.connect(lambda v: self.change('accumulate_text', v))
        outer.addWidget(self.accumulate)
        self.click = QCheckBox('Muisklikken doorlaten (Ctrl+Alt+C)')
        self.click.setChecked(self.s['click_through'])
        self.click.toggled.connect(lambda v: self.change('click_through', v))
        outer.addWidget(self.click)
        self.sync_hide_enabled()
        row = QHBoxLayout()
        self.start_button = QPushButton('Start captions')
        self.start_button.clicked.connect(self.toggle_capture)
        row.addWidget(self.start_button)
        self.file_button = QPushButton('Bestand STT…')
        self.file_button.clicked.connect(self.toggle_file_stt)
        row.addWidget(self.file_button)
        preview = QPushButton('Voorbeeld / slepen')
        preview.clicked.connect(self.preview)
        row.addWidget(preview)
        reset = QPushButton('Positie herstellen')
        reset.clicked.connect(lambda: self.overlay.reset_position())
        row.addWidget(reset)
        outer.addLayout(row)
        self.status = QLabel(warning or ('Demomodus · geen audio of model nodig' if demo else 'Gereed. Kies Start captions.'))
        self.status.setWordWrap(True)
        outer.addWidget(self.status)
        outer.addWidget(QLabel('Ctrl+Alt+H: overlay aan/uit · Ctrl+Alt+S: instellingen\nVerbergen stopt de opname niet. Stop via Start/Stop of de tray.'))
        quit_button = QPushButton('Afsluiten')
        quit_button.clicked.connect(self.shutdown)
        outer.addWidget(quit_button)
        self.tray = QSystemTrayIcon(self)
        icon = app_icon()
        self.setWindowIcon(icon)
        self.tray.setIcon(icon)
        self.tray.setToolTip(f'Live Captions {VERSION}{profile_bit}')
        menu = QMenu()
        for label, action in [('Instellingen', self.reveal), ('Start / Stop', self.toggle_capture),
                              ('Bestand STT…', self.toggle_file_stt),
                              ('Overlay aan / uit', self.toggle_visible), ('Click-through aan / uit', self.toggle_click),
                              ('Afsluiten', self.shutdown)]:
            menu.addAction(label, action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.reveal() if reason == QSystemTrayIcon.DoubleClick else None)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        self.hotkeys = Hotkeys(self)
        if sys.platform == 'win32' and len(self.hotkeys.registered) != 3:
            self.status.setText('Een sneltoets is bezet. Gebruik de knoppen of het systeemvak.')

    def persist(self):
        try:
            save_settings(self.settings_file, self.s)
        except OSError as exc:
            self.status.setText(f'Opslaan instellingen mislukt: {exc}. Pak de ZIP uit in een schrijfbare map.')

    def sync_hide_enabled(self):
        hide = self.controls.get('hide_seconds')
        if hide is not None:
            hide.setEnabled(not self.s['persist_text'])

    def on_persist_toggled(self, value):
        self.change('persist_text', value)
        self.sync_hide_enabled()

    def refresh_sources(self):
        devices = []
        try:
            import pyaudiowpatch as audio
            pa = audio.PyAudio()
            try:
                devices = list_capture_devices(pa)
            finally:
                pa.terminate()
        except Exception:
            devices = []
        current = (self.s.get('source', 'system'), self.s.get('device_name', ''))
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        selected = 0
        for i, (label, source, device_name) in enumerate(source_choices(devices)):
            self.source_combo.addItem(label, (source, device_name))
            if (source, device_name) == current:
                selected = i
            elif source == current[0] == 'device' and device_name and current[1] and (
                    device_name in current[1] or current[1] in device_name):
                selected = i
        if current[0] == 'device' and current[1] and self.source_combo.findData(current) < 0:
            self.source_combo.addItem(f'Apparaat (niet gevonden): {current[1]}', current)
            selected = self.source_combo.count() - 1
        self.source_combo.setCurrentIndex(selected)
        self.source_combo.blockSignals(False)

    def on_source_changed(self, _index=None):
        data = self.source_combo.currentData()
        if not data:
            return
        source, device_name = data
        self.s['source'] = source
        self.s['device_name'] = device_name
        self.persist()

    def change(self, key, value):
        self.s[key] = value
        self.overlay.apply()
        self.persist()

    def position_changed(self, x, y):
        self.s.update(x=x, y=y)
        self.persist()

    def choose_color(self, key='text_color'):
        color = QColorDialog.getColor(QColor(self.s[key]), self)
        if color.isValid():
            self.change(key, color.name())

    def preview(self):
        self.overlay.enabled = True
        self.click.setChecked(False)
        self.overlay.show_caption('Dit is jouw live ondertiteling. Sleep deze tekst naar de gewenste plek.')
        if not self.s.get('persist_text'):
            self.overlay.timer.start(15000)

    def clear_captions(self):
        self.buffer.clear()
        self.overlay.clear()

    def toggle_visible(self):
        self.overlay.enabled = not self.overlay.enabled
        self.overlay.sync_visibility()
        self.status.setText('Overlay ingeschakeld.' if self.overlay.enabled else 'Overlay verborgen; herkenning kan nog actief zijn.')

    def toggle_click(self):
        self.click.setChecked(not self.click.isChecked())

    def reveal(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def busy(self):
        return bool(self.engine or self.file_engine)

    def set_live_controls_enabled(self, enabled):
        for control in self.controls.values():
            control.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        if enabled:
            self.sync_hide_enabled()

    def toggle_capture(self):
        if self.file_engine:
            self.status.setText('Bestand-STT loopt nog. Stop die eerst.')
            return
        if self.engine:
            self.engine.stop()
            self.clear_captions()
            self.start_button.setEnabled(False)
            self.status.setText('Stoppen… lopende modelbewerking wordt afgewacht.')
            return
        if self.demo:
            self.preview()
            return
        self.buffer.clear()
        self.engine = Engine(self.s, self.bus.caption.emit, self.bus.status.emit,
                             self.bus.error.emit, self.bus.done.emit)
        self.set_live_controls_enabled(False)
        self.file_button.setEnabled(False)
        self.start_button.setText('Stop captions')
        self.engine.start()

    def toggle_file_stt(self):
        if self.file_engine:
            self.file_engine.stop()
            self.file_button.setEnabled(False)
            self.status.setText('Bestand-STT stoppen…')
            return
        if self.engine:
            self.status.setText('Live captions lopen nog. Stop die eerst.')
            return
        if self.demo:
            self.status.setText('Bestand-STT is niet beschikbaar in demomodus.')
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Kies audio- of videobestand',
            '',
            'Media (*.mp4 *.mp3 *.m4a *.wav *.mkv);;Alle bestanden (*.*)',
        )
        if not path:
            return
        if not is_supported_media(path):
            self.status.setText('Kies een mp4, mp3, m4a, wav of mkv-bestand.')
            return
        self.transcript.prepare(f'Transcript · {Path(path).name}')
        self.overlay.enabled = True
        self.file_engine = FileEngine(
            self.s, path,
            segment=lambda text, start, end: self.bus.file_segment.emit(text),
            status=self.bus.file_status.emit,
            error=self.bus.file_error.emit,
            done=self.bus.file_done.emit,
        )
        self.set_live_controls_enabled(False)
        self.start_button.setEnabled(False)
        self.file_button.setText('Stop bestand')
        self.file_engine.start()

    def on_file_segment(self, text):
        if self.closing or not self.file_engine:
            return
        self.transcript.append_segment(text)
        self.overlay.show_caption(text)

    def on_file_status(self, text):
        if not self.closing:
            self.status.setText(text)

    def on_file_error(self, text):
        self.status.setText(text)
        self.transcript.set_finished(text)

    def file_finished(self):
        engine = self.file_engine
        self.file_engine = None
        self.file_button.setEnabled(True)
        self.file_button.setText('Bestand STT…')
        self.start_button.setEnabled(True)
        self.set_live_controls_enabled(True)
        if engine and engine.srt_path:
            self.transcript.set_finished(f'Klaar · opgeslagen: {engine.srt_path}')

    def receive_caption(self, text, final=True):
        if self.engine and not self.engine.stop_event.is_set() and not self.closing:
            display = self.buffer.update(text, final, self.s['accumulate_text'])
            self.overlay.show_caption(display)

    def set_status(self, text):
        if not self.closing and self.engine and not self.engine.stop_event.is_set():
            self.status.setText(text)

    def on_error(self, text):
        self.status.setText(text)

    def finished(self):
        self.engine = None
        self.start_button.setEnabled(True)
        self.start_button.setText('Start captions')
        self.file_button.setEnabled(True)
        self.set_live_controls_enabled(True)
        if self.status.text().startswith(('Luistert', 'Stoppen')):
            self.status.setText('Gestopt.')

    def closeEvent(self, event):
        if not self.closing and self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            self.shutdown()
            event.accept()

    def shutdown(self):
        if self.closing:
            return
        self.closing = True
        if self.engine:
            self.engine.stop()
        if self.file_engine:
            self.file_engine.stop()
        self.persist()
        self.hotkeys.close()
        self.tray.hide()
        self.overlay.close()
        self.transcript.close()
        QApplication.instance().quit()

def main():
    global PROFILE, SETTINGS
    try:
        PROFILE = parse_profile_arg()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)
    SETTINGS = settings_path(PROFILE or None)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(app_icon())
    window = Window(demo='--demo' in sys.argv, profile=PROFILE)
    window.show()
    if '--smoke-test' in sys.argv:
        window.preview()
        QTimer.singleShot(700, window.shutdown)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
