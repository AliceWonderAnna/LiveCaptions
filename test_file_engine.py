"""Tests for FileEngine with mocked decode/transcribe."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from file_engine import FileEngine


def _settings():
    return {'model': 'tiny', 'language': 'nl'}


def test_file_engine_rejects_bad_extension(tmp_path: Path):
    path = tmp_path / 'notes.doc'
    path.write_bytes(b'x')
    errors, statuses, done = [], [], []
    engine = FileEngine(
        _settings(), path,
        segment=lambda *a: None,
        status=statuses.append,
        error=errors.append,
        done=lambda: done.append(True),
    )
    engine.run()
    assert done == [True]
    assert errors
    assert 'Niet-ondersteund' in errors[0] or 'Bestand-STT' in errors[0]


def test_file_engine_writes_outputs_and_emits_segments(tmp_path: Path):
    media = tmp_path / 'talk.wav'
    media.write_bytes(b'RIFF')
    segments_out = []
    statuses, errors, done = [], [], []

    fake_segments = [
        SimpleNamespace(start=0.0, end=1.0, text=' Een '),
        SimpleNamespace(start=1.0, end=2.5, text='twee'),
    ]

    class FakeModel:
        def __init__(self, *a, **k):
            pass

        def transcribe(self, audio, **kwargs):
            assert audio is not None
            assert kwargs.get('vad_filter') is True
            return iter(fake_segments), SimpleNamespace()

    with patch('faster_whisper.audio.decode_audio', return_value=np.zeros(16000, dtype=np.float32)), \
            patch('faster_whisper.WhisperModel', FakeModel), \
            patch('file_engine.model_cache_dir', return_value=tmp_path / 'models'):
        (tmp_path / 'models').mkdir()
        engine = FileEngine(
            _settings(), media,
            segment=lambda text, start, end: segments_out.append((text, start, end)),
            status=statuses.append,
            error=errors.append,
            done=lambda: done.append(True),
        )
        engine.run()

    assert errors == []
    assert done == [True]
    assert segments_out == [('Een', 0.0, 1.0), ('twee', 1.0, 2.5)]
    assert not (tmp_path / 'talk.txt').exists()
    assert 'Een' in (tmp_path / 'talk.srt').read_text(encoding='utf-8')
    assert any('Klaar' in s for s in statuses)


def test_file_engine_stop_skips_write(tmp_path: Path):
    media = tmp_path / 'talk.mp3'
    media.write_bytes(b'ID3')
    statuses, errors, done = [], [], []

    class SlowSegments:
        def __iter__(self):
            yield SimpleNamespace(start=0, end=1, text='hallo')
            raise AssertionError('should have stopped')

    class FakeModel:
        def __init__(self, *a, **k):
            pass

        def transcribe(self, audio, **kwargs):
            return SlowSegments(), SimpleNamespace()

    with patch('faster_whisper.audio.decode_audio', return_value=np.zeros(8000, dtype=np.float32)), \
            patch('faster_whisper.WhisperModel', FakeModel), \
            patch('file_engine.model_cache_dir', return_value=tmp_path / 'models'):
        (tmp_path / 'models').mkdir()
        engine = FileEngine(
            _settings(), media,
            segment=lambda *a: engine.stop(),
            status=statuses.append,
            error=errors.append,
            done=lambda: done.append(True),
        )
        engine.run()

    assert done == [True]
    assert errors == []
    assert not (tmp_path / 'talk.txt').exists()
    assert any('gestopt' in s.lower() for s in statuses)
