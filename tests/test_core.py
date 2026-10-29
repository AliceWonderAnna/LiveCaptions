import json
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import DEFAULTS, Segmenter, load_settings, save_settings, mono_16k
from audio_engine import Engine

class CoreTests(unittest.TestCase):
    def test_stereo_resampling(self):
        t = np.arange(4800) / 48000
        tone = (.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        result = mono_16k(np.column_stack((tone, tone)).tobytes(), 2, 48000)
        self.assertEqual(len(result), 1600)
        self.assertAlmostEqual(float(np.sqrt(np.mean(result**2))), .1414, places=3)

    def test_silence_never_emits(self):
        segmenter = Segmenter()
        for _ in range(1000):
            self.assertIsNone(segmenter.push(np.zeros(1600, np.float32)))
        self.assertLessEqual(len(segmenter.pre), 3)

    def test_pause_flushes_and_continuous_speech_is_bounded(self):
        segmenter = Segmenter()
        voice = np.full(1600, .1, np.float32)
        silence = np.zeros_like(voice)
        for _ in range(10):
            chunk = segmenter.push(voice)
            if chunk is not None:
                self.assertFalse(chunk.final)
        outputs = [segmenter.push(silence) for _ in range(5)]
        finals = [item for item in outputs if item is not None]
        self.assertEqual(len(finals), 1)
        self.assertTrue(finals[0].final)
        self.assertGreaterEqual(len(finals[0].samples), 16000)
        results = [segmenter.push(voice) for _ in range(80)]
        emitted = [item for item in results if item is not None]
        self.assertGreaterEqual(sum(item.final for item in emitted), 2)
        self.assertLessEqual(segmenter.size, 16000 * 4)

    def test_settings_corrupt_and_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.json'
            path.write_text('broken')
            result, warning = load_settings(path)
            self.assertTrue(warning)
            self.assertEqual(result, DEFAULTS)
            save_settings(path, DEFAULTS)
            self.assertEqual(load_settings(path), (DEFAULTS, ''))
            path.write_text(json.dumps(dict(lines=999, width=-1, source='bad', click_through='false')))
            result, _ = load_settings(path)
            self.assertEqual((result['lines'], result['width'], result['source'], result['click_through']),
                             (12, 250, 'system', True))

    def test_engine_delivers_and_stops(self):
        captions, errors = [], []
        ended = threading.Event()
        class Model:
            def __init__(self, *args, **kwargs):
                pass
            def transcribe(self, *args, **kwargs):
                return iter([types.SimpleNamespace(text=' Test tekst ', no_speech_prob=.1)]), None
        class FakeCaptureEngine(Engine):
            def capture(self):
                self.jobs.put((time.monotonic(), np.ones(16000, np.float32), True))
                self.stop_event.wait(3)
        def on_caption(text, final=True):
            captions.append((text, final))
        engine = FakeCaptureEngine(DEFAULTS, on_caption, lambda x: None, errors.append, ended.set)
        with patch.dict(sys.modules, faster_whisper=types.SimpleNamespace(WhisperModel=Model)):
            engine.start()
            deadline = time.monotonic() + 3
            while not captions and time.monotonic() < deadline:
                time.sleep(.01)
            engine.stop()
            self.assertTrue(ended.wait(3))
        self.assertEqual(captions, [('Test tekst', True)])
        self.assertFalse(errors)

if __name__ == '__main__':
    unittest.main()
