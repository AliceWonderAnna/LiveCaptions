"""Tests for frozen-safe path helpers and the app icon."""
import os
import sys
from pathlib import Path

import pytest

import paths


def test_app_dir_is_project_root_when_not_frozen():
    assert paths.app_dir() == Path(paths.__file__).resolve().parent
    assert not paths.is_frozen()


def test_settings_path_next_to_app_dir_when_not_frozen():
    assert paths.settings_dir() == paths.app_dir()
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


def test_settings_path_uses_roaming_when_frozen(monkeypatch, tmp_path):
    fake_exe = tmp_path / "install" / "LiveCaptions.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.write_bytes(b"")
    roaming = tmp_path / "roaming"
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    assert paths.settings_dir() == roaming / "LiveCaptions"
    assert paths.settings_path() == roaming / "LiveCaptions" / "settings.json"
    assert paths.settings_path("vlc1") == roaming / "LiveCaptions" / "settings-vlc1.json"
    assert (roaming / "LiveCaptions").is_dir()


def test_migrate_legacy_settings_from_app_dir(monkeypatch, tmp_path):
    install = tmp_path / "install"
    install.mkdir()
    fake_exe = install / "LiveCaptions.exe"
    fake_exe.write_bytes(b"")
    legacy = install / "settings.json"
    legacy.write_text('{"font_size": 42}', encoding="utf-8")
    (install / "settings-vlc1.json").write_text('{"source": "device"}', encoding="utf-8")
    roaming = tmp_path / "roaming"
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    dest = paths.settings_path()
    assert dest == roaming / "LiveCaptions" / "settings.json"
    assert dest.read_text(encoding="utf-8") == '{"font_size": 42}'

    dest_vlc = paths.settings_path("vlc1")
    assert dest_vlc.read_text(encoding="utf-8") == '{"source": "device"}'

    # Do not overwrite existing Roaming settings
    dest.write_text('{"font_size": 99}', encoding="utf-8")
    legacy.write_text('{"font_size": 1}', encoding="utf-8")
    assert paths.settings_path().read_text(encoding="utf-8") == '{"font_size": 99}'


def test_resource_path_uses_meipass_when_frozen(monkeypatch, tmp_path):
    meipass = tmp_path / "runtime"
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
