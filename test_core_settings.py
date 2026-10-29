"""Tests for settings defaults, clamps, and legacy JSON."""
import json
from pathlib import Path

from core import DEFAULTS, load_settings


def test_defaults_include_text_fx_keys():
    for key in (
        'outline_enabled', 'outline_width', 'outline_color', 'outline_opacity',
        'shadow_enabled', 'shadow_offset_x', 'shadow_offset_y', 'shadow_blur',
        'shadow_color', 'shadow_opacity',
        'partial_seconds', 'silence_seconds',
        'persist_text', 'accumulate_text',
        'device_name',
    ):
        assert key in DEFAULTS
    assert DEFAULTS['persist_text'] is False
    assert DEFAULTS['accumulate_text'] is False
    assert DEFAULTS['device_name'] == ''


def test_legacy_json_gets_fx_defaults(tmp_path: Path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'font_size': 28, 'text_color': '#abcdef'}), encoding='utf-8')
    settings, warning = load_settings(path)
    assert warning == ''
    assert settings['font_size'] == 28
    assert settings['text_color'] == '#abcdef'
    assert settings['outline_enabled'] is True
    assert settings['outline_width'] == 3
    assert settings['shadow_enabled'] is True
    assert settings['shadow_blur'] == 4
    assert settings['partial_seconds'] == 0.5
    assert settings['silence_seconds'] == 0.25
    assert settings['persist_text'] is False
    assert settings['accumulate_text'] is False


def test_clamps_fx_values(tmp_path: Path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({
        'outline_width': 99,
        'outline_opacity': -5,
        'shadow_offset_x': -100,
        'shadow_blur': 50,
        'shadow_opacity': 200,
    }), encoding='utf-8')
    settings, warning = load_settings(path)
    assert warning == ''
    assert settings['outline_width'] == 12
    assert settings['outline_opacity'] == 0
    assert settings['shadow_offset_x'] == -20
    assert settings['shadow_blur'] == 20
    assert settings['shadow_opacity'] == 100


def test_clamps_latency_values(tmp_path: Path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({
        'partial_seconds': 9,
        'silence_seconds': 0.01,
        'lines': 99,
    }), encoding='utf-8')
    settings, warning = load_settings(path)
    assert warning == ''
    assert settings['partial_seconds'] == 1.5
    assert settings['silence_seconds'] == 0.15
    assert settings['lines'] == 12


def test_device_source_without_name_falls_back(tmp_path: Path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'source': 'device', 'device_name': ''}), encoding='utf-8')
    settings, warning = load_settings(path)
    assert warning == ''
    assert settings['source'] == 'system'


def test_device_source_keeps_name(tmp_path: Path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({
        'source': 'device',
        'device_name': 'Voicemeeter Aux Input',
    }), encoding='utf-8')
    settings, warning = load_settings(path)
    assert warning == ''
    assert settings['source'] == 'device'
    assert settings['device_name'] == 'Voicemeeter Aux Input'


def test_invalid_colors_fall_back(tmp_path: Path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({
        'text_color': 'red',
        'outline_color': '#gg0000',
        'shadow_color': '#00ff00',
    }), encoding='utf-8')
    settings, warning = load_settings(path)
    assert warning == ''
    assert settings['text_color'] == DEFAULTS['text_color']
    assert settings['outline_color'] == DEFAULTS['outline_color']
    assert settings['shadow_color'] == '#00ff00'
