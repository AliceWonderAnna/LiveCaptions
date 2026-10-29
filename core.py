"""Settings and bounded, in-memory audio segmentation. No transcript logging."""
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.signal import resample_poly

_HEX_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')
SAMPLE_RATE = 16000
MIN_SAMPLES = 6400
OVERLAP_SAMPLES = 4800

DEFAULTS = dict(
    font='Segoe UI', font_size=30, text_color='#ffffff',
    background_opacity=25, window_opacity=100, width=900,
    x=None, y=None, lines=2, hide_seconds=2.5, click_through=True,
    persist_text=False, accumulate_text=False,
    source='system', device_name='',
    model='base', language='nl', threshold=0.006,
    max_seconds=4.0, partial_seconds=0.5, silence_seconds=0.25,
    outline_enabled=True, outline_width=3, outline_color='#000000', outline_opacity=86,
    shadow_enabled=True, shadow_offset_x=2, shadow_offset_y=2, shadow_blur=4,
    shadow_color='#000000', shadow_opacity=55,
)


@dataclass(frozen=True)
class Chunk:
    samples: np.ndarray
    final: bool


def _valid_color(value, fallback):
    if isinstance(value, str) and _HEX_COLOR.match(value):
        return value.lower()
    return fallback


def load_settings(path):
    result = DEFAULTS.copy()
    if not Path(path).exists():
        return result, ''
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('JSON moet een object zijn')
        for key, default in DEFAULTS.items():
            value = data.get(key, default)
            if key in ('x', 'y'):
                if value is None or type(value) is int:
                    result[key] = value
            elif type(value) is type(default):
                result[key] = value
            elif type(default) is float and type(value) is int:
                result[key] = float(value)
        for key, low, high in [
            ('font_size', 12, 80), ('width', 250, 3000),
            ('lines', 1, 12), ('background_opacity', 0, 100),
            ('window_opacity', 10, 100), ('hide_seconds', .5, 20),
            ('threshold', .0001, .2), ('max_seconds', 1, 10),
            ('partial_seconds', .3, 1.5), ('silence_seconds', .15, 1.0),
            ('outline_width', 0, 12), ('outline_opacity', 0, 100),
            ('shadow_offset_x', -20, 20), ('shadow_offset_y', -20, 20),
            ('shadow_blur', 0, 20), ('shadow_opacity', 0, 100),
        ]:
            value = result[key]
            result[key] = max(low, min(high, value)) if math.isfinite(value) else DEFAULTS[key]
        for key, choices in [('source', ('system', 'microphone', 'device')),
                             ('model', ('tiny', 'base', 'small')),
                             ('language', ('nl', 'en', 'auto', 'de', 'fr', 'es'))]:
            if result[key] not in choices:
                result[key] = DEFAULTS[key]
        if not isinstance(result.get('device_name'), str):
            result['device_name'] = DEFAULTS['device_name']
        else:
            result['device_name'] = result['device_name'].strip()
        if result['source'] == 'device' and not result['device_name']:
            result['source'] = DEFAULTS['source']
        for key in ('text_color', 'outline_color', 'shadow_color'):
            result[key] = _valid_color(result[key], DEFAULTS[key])
        return result, ''
    except (ValueError, OSError) as exc:
        return result, f'Instellingen konden niet worden gelezen: {exc}'


def save_settings(path, settings):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def mono_16k(raw, channels, rate):
    samples = np.frombuffer(raw, dtype=np.float32).reshape(-1, channels).mean(axis=1)
    divisor = math.gcd(int(rate), 16000)
    return resample_poly(samples, 16000 // divisor, int(rate) // divisor).astype(np.float32)


class Segmenter:
    """Energy gate with pre-roll; emits live partials, then a final on pause or max length."""
    def __init__(self, threshold=.006, max_seconds=4, silence_seconds=.25, partial_seconds=.5):
        self.threshold = threshold
        self.limit = int(max_seconds * SAMPLE_RATE)
        self.silence_limit = int(silence_seconds * SAMPLE_RATE)
        self.partial_limit = int(partial_seconds * SAMPLE_RATE)
        self.parts, self.pre = [], []
        self.size = self.silence = self.since_partial = 0

    def _reset(self, keep_overlap=False):
        if keep_overlap and self.parts:
            combined = np.concatenate(self.parts)
            overlap = combined[-OVERLAP_SAMPLES:] if len(combined) > OVERLAP_SAMPLES else combined
            self.parts = [overlap]
            self.size = len(overlap)
        else:
            self.parts = []
            self.size = 0
        self.silence = 0
        self.since_partial = 0
        self.pre = []

    def push(self, samples):
        voiced = float(np.sqrt(np.mean(samples * samples))) >= self.threshold
        if not self.parts and not voiced:
            self.pre.append(samples)
            self.pre = self.pre[-3:]
            return None
        if not self.parts:
            self.parts = list(self.pre)
            self.pre = []
            self.size = sum(len(x) for x in self.parts)
            self.since_partial = self.size
        self.parts.append(samples)
        self.size += len(samples)
        self.since_partial += len(samples)
        self.silence = 0 if voiced else self.silence + len(samples)
        if self.silence >= self.silence_limit:
            result = np.concatenate(self.parts)
            self._reset()
            return Chunk(result, True) if len(result) >= MIN_SAMPLES else None
        if self.size >= self.limit:
            result = np.concatenate(self.parts)
            self._reset(keep_overlap=True)
            return Chunk(result, True) if len(result) >= MIN_SAMPLES else None
        if self.since_partial >= self.partial_limit and self.size >= MIN_SAMPLES:
            self.since_partial = 0
            return Chunk(np.concatenate(self.parts), False)
        return None
