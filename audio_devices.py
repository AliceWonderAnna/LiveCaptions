"""Enumerate and resolve WASAPI capture devices for Live Captions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaptureDevice:
    index: int
    name: str
    kind: str  # 'loopback' | 'input'
    max_input_channels: int
    default_sample_rate: float


def list_capture_devices(pa) -> list[CaptureDevice]:
    """Return loopback and input devices that can be opened for capture."""
    devices: list[CaptureDevice] = []
    seen: set[str] = set()

    def add(info, kind):
        name = str(info.get('name', '')).strip()
        if not name or name in seen:
            return
        channels = int(info.get('maxInputChannels', 0) or 0)
        if channels < 1:
            return
        seen.add(name)
        devices.append(CaptureDevice(
            index=int(info['index']),
            name=name,
            kind=kind,
            max_input_channels=channels,
            default_sample_rate=float(info.get('defaultSampleRate', 48000) or 48000),
        ))

    try:
        for info in pa.get_loopback_device_info_generator():
            add(info, 'loopback')
    except Exception:
        pass

    try:
        for info in pa.get_device_info_generator():
            if info.get('isLoopbackDevice'):
                continue
            if int(info.get('maxInputChannels', 0) or 0) < 1:
                continue
            add(info, 'input')
    except Exception:
        pass

    return devices


def resolve_device(pa, settings):
    """Pick a PortAudio device info dict from settings.

    Falls back to default system loopback or microphone when the named device
    is missing.
    """
    source = settings.get('source', 'system')
    device_name = (settings.get('device_name') or '').strip()

    if source == 'system':
        return pa.get_default_wasapi_loopback()
    if source == 'microphone':
        return pa.get_default_input_device_info()

    if source == 'device' and device_name:
        for device in list_capture_devices(pa):
            if device.name == device_name:
                return pa.get_device_info_by_index(device.index)
        # Partial match helps when Windows appends suffixes.
        for device in list_capture_devices(pa):
            if device_name in device.name or device.name in device_name:
                return pa.get_device_info_by_index(device.index)

    try:
        return pa.get_default_wasapi_loopback()
    except Exception:
        return pa.get_default_input_device_info()


def source_choices(devices: list[CaptureDevice] | None = None):
    """UI choices: (label, source, device_name)."""
    choices = [
        ('Systeemaudio (WASAPI)', 'system', ''),
        ('Standaardmicrofoon', 'microphone', ''),
    ]
    for device in devices or []:
        label = f"{'Loopback' if device.kind == 'loopback' else 'Invoer'}: {device.name}"
        choices.append((label, 'device', device.name))
    return choices
