"""Tests for profile-aware settings paths."""
import pytest

import paths


def test_settings_path_default():
    assert paths.settings_path() == paths.settings_dir() / 'settings.json'
    assert paths.settings_path('') == paths.settings_dir() / 'settings.json'
    assert paths.settings_path(None) == paths.settings_dir() / 'settings.json'


def test_settings_path_with_profile():
    assert paths.settings_path('vlc1') == paths.settings_dir() / 'settings-vlc1.json'
    assert paths.settings_path('vlc2') == paths.settings_dir() / 'settings-vlc2.json'


def test_normalize_profile_rejects_bad_names():
    assert paths.normalize_profile('') == ''
    assert paths.normalize_profile(None) == ''
    with pytest.raises(ValueError):
        paths.normalize_profile('../evil')
    with pytest.raises(ValueError):
        paths.normalize_profile('has space')


def test_parse_profile_arg():
    assert paths.parse_profile_arg([]) == ''
    assert paths.parse_profile_arg(['--demo']) == ''
    assert paths.parse_profile_arg(['--profile', 'vlc1']) == 'vlc1'
    assert paths.parse_profile_arg(['--profile=vlc2', '--demo']) == 'vlc2'
