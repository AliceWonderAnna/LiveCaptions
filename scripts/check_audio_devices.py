"""List WASAPI loopback and input devices visible to Live Captions."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from audio_devices import list_capture_devices


def main():
    try:
        import pyaudiowpatch as audio
    except ImportError as exc:
        print(f'PyAudioWPatch ontbreekt: {exc}', file=sys.stderr)
        return 1
    pa = audio.PyAudio()
    try:
        devices = list_capture_devices(pa)
    finally:
        pa.terminate()
    if not devices:
        print('Geen capture-apparaten gevonden.')
        return 1
    print(f'{len(devices)} apparaat(en):')
    for device in devices:
        print(f'  [{device.kind:8}] {device.index:3}  {device.name}')
    names = ' '.join(d.name.lower() for d in devices)
    if 'voicemeeter' in names or 'vaio' in names or 'aux' in names:
        print('\nVoiceMeeter-achtige namen gevonden. Kies VAIO voor vlc1 en AUX voor vlc2.')
    else:
        print('\nGeen VoiceMeeter-namen gezien. Installeer Banana en herstart; zie docs/SETUP_MULTICHANNEL.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
