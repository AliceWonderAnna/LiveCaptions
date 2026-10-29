"""Packaging name and version propagation stay consistent."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from core import DEFAULTS
from version import APP_NAME, VERSION

ROOT = Path(__file__).resolve().parent
EXE_HARDCODE = re.compile(r"LiveCaptions-v\d+\.\d+\.\d+")
SKIP_DIRS = {".venv", ".git", "dist", "build", "__pycache__", ".cursor"}


class VersionTests(unittest.TestCase):
    def test_version_is_semver(self):
        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")

    def test_app_name_includes_version(self):
        self.assertEqual(APP_NAME, f"LiveCaptions-v{VERSION}")

    def test_readme_matches_version(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"# Live Captions — Windows {VERSION}", text)
        self.assertIn(f"CUDA/Intel-GPU wordt in {VERSION} niet gebruikt.", text)
        titles = re.findall(r"# Live Captions — Windows (\d+\.\d+\.\d+)", text)
        self.assertEqual(titles, [VERSION])

    def test_app_docstring_matches_version(self):
        text = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertTrue(
            text.startswith(f'"""Live Captions — Windows desktop overlay, v{VERSION}."""')
        )

    def test_start_vlc_cmds_are_version_agnostic(self):
        for name in ("start-vlc1.cmd", "start-vlc2.cmd"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, EXE_HARDCODE, msg=name)
            self.assertIn("LiveCaptions-v*.exe", text)

    def test_no_stale_exe_names_in_tracked_sources(self):
        allowed = {APP_NAME}
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.name == "test_version.py":
                continue
            if path.suffix not in {".py", ".cmd", ".md", ".ps1"} and path.name != "build.ps1":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in EXE_HARDCODE.finditer(text):
                name = match.group(0)
                if name not in allowed:
                    offenders.append(f"{path.relative_to(ROOT)}: {name}")
        self.assertEqual(offenders, [], msg="\n".join(offenders))


class SettingsFilesTests(unittest.TestCase):
    def test_settings_json_has_all_defaults_keys(self):
        data = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(set(data), set(DEFAULTS))
        self.assertEqual(data["source"], "system")

    def test_vlc_settings_have_all_defaults_keys_and_devices(self):
        for name in ("settings-vlc1.json", "settings-vlc2.json"):
            data = json.loads((ROOT / name).read_text(encoding="utf-8"))
            self.assertEqual(set(data), set(DEFAULTS), msg=name)
            self.assertEqual(data["source"], "device", msg=name)
            self.assertTrue(data["device_name"].strip(), msg=name)


if __name__ == "__main__":
    unittest.main()
