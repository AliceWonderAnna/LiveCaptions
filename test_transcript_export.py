"""Tests for media extension guards and SRT export."""
from pathlib import Path
from types import SimpleNamespace

from transcript_export import (
    format_srt_timestamp,
    is_supported_media,
    segments_to_srt,
    write_srt,
)


def test_supported_extensions():
    assert is_supported_media('a.mp4')
    assert is_supported_media('B.MP3')
    assert is_supported_media(Path('x.m4a'))
    assert is_supported_media('y.wav')
    assert is_supported_media('z.mkv')
    assert not is_supported_media('nope.txt')
    assert not is_supported_media('clip.avi')


def test_format_srt_timestamp():
    assert format_srt_timestamp(0) == '00:00:00,000'
    assert format_srt_timestamp(61.5) == '00:01:01,500'
    assert format_srt_timestamp(3661.234) == '01:01:01,234'


def test_segments_to_srt():
    segments = [
        SimpleNamespace(start=0.0, end=1.2, text=' Hallo '),
        SimpleNamespace(start=1.2, end=2.0, text='wereld'),
    ]
    srt = segments_to_srt(segments)
    assert '1\n00:00:00,000 --> 00:00:01,200\nHallo' in srt
    assert '2\n00:00:01,200 --> 00:00:02,000\nwereld' in srt


def test_write_srt_only(tmp_path: Path):
    media = tmp_path / 'clip.mp4'
    media.write_bytes(b'')
    segments = [{'start': 0, 'end': 0.8, 'text': 'Test zin'}]
    srt_path = write_srt(media, segments)
    assert srt_path == tmp_path / 'clip.srt'
    assert 'Test zin' in srt_path.read_text(encoding='utf-8')
    assert not (tmp_path / 'clip.txt').exists()
