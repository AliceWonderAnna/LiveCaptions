"""Packaging name includes the v-prefixed version."""
from version import APP_NAME, VERSION


def test_version_is_061():
    assert VERSION == '0.6.1'


def test_app_name_includes_v061():
    assert APP_NAME == 'LiveCaptions-v0.6.1'
