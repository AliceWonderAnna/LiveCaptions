"""Tests for frozen-safe path helpers and the app icon."""
import os
import sys
from pathlib import Path

import pytest

import paths


def test_app_dir_is_project_root_when_not_frozen():
    assert paths.app_dir() == Path(paths.__file__).resolve().parent
    assert not paths.is_frozen()


def test_settings_path_next_to_app_dir():
    assert paths.settings_path() == paths.app_dir() / "settings.json"
    assert paths.settings_path("vlc1") == paths.app_dir() / "settings-vlc1.json"


def test_resource_path_points_at_icon():
    icon = paths.resource_path("assets", "livecaptions.ico")
    assert icon == paths.bundle_dir() / "assets" / "livecaptions.ico"
    assert icon.is_file()
    assert icon.stat().st_size > 0


def test_model_cache_dir_under_localappdata(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    cache = paths.model_cache_dir()
    assert cache == tmp_path / "LiveCaptions" / "models"
    assert cache.is_dir()


def test_app_dir_uses_executable_when_frozen(monkeypatch, tmp_path):
    fake_exe = tmp_path / "LiveCaptions.exe"
    fake_exe.write_bytes(b"")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    assert paths.app_dir() == tmp_path
    assert paths.settings_path() == tmp_path / "settings.json"


def test_resource_path_uses_meipass_when_frozen(monkeypatch, tmp_path):
    meipass = tmp_path / "_internal"
    icon_dir = meipass / "assets"
    icon_dir.mkdir(parents=True)
    (icon_dir / "livecaptions.ico").write_bytes(b"ico")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass), raising=False)
    assert paths.resource_path("assets", "livecaptions.ico").is_file()


def test_icon_loads_as_qicon():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    icon = QIcon(str(paths.resource_path("assets", "livecaptions.ico")))
    assert not icon.isNull()
    assert app is not None
