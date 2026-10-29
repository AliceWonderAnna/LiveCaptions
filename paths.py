"""Frozen-safe filesystem locations for Live Captions."""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

_PROFILE = re.compile(r'^[A-Za-z0-9_-]{1,32}$')


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """Directory of the executable when frozen, otherwise the project root."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundle_dir() -> Path:
    """Directory that contains bundled resources (_MEIPASS when frozen)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def normalize_profile(profile: str | None) -> str:
    """Return a safe profile name or '' for the default settings file."""
    if not profile:
        return ''
    name = profile.strip()
    if not _PROFILE.match(name):
        raise ValueError(
            'Ongeldige profile-naam. Gebruik alleen letters, cijfers, _ of - (max 32).'
        )
    return name


def settings_dir() -> Path:
    """Directory for settings.json files.

    Frozen builds use %APPDATA%\\LiveCaptions (Roaming) so upgrades/uninstall
    can replace binaries without wiping user preferences. Dev runs keep
    settings next to the project root.
    """
    if is_frozen():
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        path = Path(base) / "LiveCaptions"
        path.mkdir(parents=True, exist_ok=True)
        return path
    return app_dir()


def _settings_filename(profile: str | None = None) -> str:
    name = normalize_profile(profile) if profile else ''
    if name:
        return f"settings-{name}.json"
    return "settings.json"


def migrate_legacy_settings(profile: str | None = None) -> None:
    """Copy settings from next-to-exe into Roaming once (frozen builds only)."""
    if not is_frozen():
        return
    dest = settings_dir() / _settings_filename(profile)
    if dest.is_file():
        return
    legacy = app_dir() / _settings_filename(profile)
    if not legacy.is_file():
        return
    try:
        shutil.copy2(legacy, dest)
    except OSError:
        pass


def settings_path(profile: str | None = None) -> Path:
    migrate_legacy_settings(profile)
    return settings_dir() / _settings_filename(profile)


def parse_profile_arg(argv: list[str] | None = None) -> str:
    """Read --profile NAME from argv; empty string means default profile."""
    args = list(sys.argv[1:] if argv is None else argv)
    for i, arg in enumerate(args):
        if arg == '--profile' and i + 1 < len(args):
            return normalize_profile(args[i + 1])
        if arg.startswith('--profile='):
            return normalize_profile(arg.split('=', 1)[1])
    return ''


def resource_path(*parts: str) -> Path:
    return bundle_dir().joinpath(*parts)


def model_cache_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    path = Path(base) / "LiveCaptions" / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path
