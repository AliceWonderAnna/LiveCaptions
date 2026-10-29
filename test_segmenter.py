"""Tests for live partial chunks and pause finals."""
import numpy as np

from core import OVERLAP_SAMPLES, Segmenter


def test_partial_emits_without_reset():
    segmenter = Segmenter(partial_seconds=0.5, silence_seconds=0.25, max_seconds=4)
    voice = np.full(1600, .1, np.float32)
    chunks = [segmenter.push(voice) for _ in range(5)]
    partials = [item for item in chunks if item is not None]
    assert len(partials) == 1
    assert partials[0].final is False
    assert len(partials[0].samples) == 8000
    assert segmenter.size == 8000
    assert segmenter.push(voice) is None
    assert segmenter.size == 9600


def test_silence_emits_final_and_resets():
    segmenter = Segmenter(partial_seconds=0.5, silence_seconds=0.25, max_seconds=4)
    voice = np.full(1600, .1, np.float32)
    silence = np.zeros_like(voice)
    for _ in range(10):
        segmenter.push(voice)
    finals = [item for item in (segmenter.push(silence) for _ in range(5)) if item is not None]
    assert len(finals) == 1
    assert finals[0].final is True
    assert len(finals[0].samples) >= 16000
    assert segmenter.size == 0
    assert segmenter.parts == []


def test_max_seconds_keeps_overlap():
    segmenter = Segmenter(partial_seconds=0.5, silence_seconds=0.25, max_seconds=1.0)
    voice = np.full(1600, .1, np.float32)
    emitted = [segmenter.push(voice) for _ in range(10)]
    finals = [item for item in emitted if item is not None and item.final]
    assert len(finals) == 1
    assert len(finals[0].samples) == 16000
    assert segmenter.size == OVERLAP_SAMPLES
