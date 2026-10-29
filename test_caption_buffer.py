"""Tests for CaptionBuffer replace vs accumulate and RAM cap."""
from caption_buffer import MAX_CHARS, CaptionBuffer


def test_without_accumulate_replaces_text():
    buf = CaptionBuffer()
    assert buf.update('Hallo', False, False) == 'Hallo'
    assert buf.update('Wereld', False, False) == 'Wereld'
    assert buf.update('Klaar.', True, False) == 'Klaar.'
    assert buf.pending == ''
    assert buf.committed == 'Klaar.'


def test_accumulate_partial_then_final():
    buf = CaptionBuffer()
    assert buf.update('Dit is', False, True) == 'Dit is'
    assert buf.update('Dit is een', False, True) == 'Dit is een'
    assert buf.update('Dit is een zin.', True, True) == 'Dit is een zin.'
    assert buf.pending == ''
    assert buf.update('Nog', False, True) == 'Dit is een zin. Nog'
    assert buf.update('Nog een.', True, True) == 'Dit is een zin. Nog een.'


def test_clear_empties_buffer():
    buf = CaptionBuffer()
    buf.update('blijf', True, True)
    buf.clear()
    assert buf.display() == ''
    assert buf.committed == ''
    assert buf.pending == ''


def test_cap_keeps_newest_chars():
    buf = CaptionBuffer(max_chars=20)
    buf.update('aaaaaaaaaa', True, True)
    buf.update('bbbbbbbbbb', True, True)
    text = buf.display()
    assert len(text) <= 20
    assert text.endswith('b')
    assert MAX_CHARS == 4000
