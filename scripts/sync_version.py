"""Propagate VERSION from version.py into README and app.py docstring."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from version import VERSION  # noqa: E402

README = ROOT / "README.md"
APP_PY = ROOT / "app.py"

TITLE_RE = re.compile(r"^# Live Captions — Windows \d+\.\d+\.\d+", re.M)
GPU_RE = re.compile(r"CUDA/Intel-GPU wordt in \d+\.\d+\.\d+ niet gebruikt\.")
DOCSTRING_RE = re.compile(
    r'^"""Live Captions — Windows desktop overlay, v\d+\.\d+\.\d+\."""',
    re.M,
)


def sync_readme(text: str, version: str) -> str:
    text = TITLE_RE.sub(f"# Live Captions — Windows {version}", text, count=1)
    text = GPU_RE.sub(
        f"CUDA/Intel-GPU wordt in {version} niet gebruikt.",
        text,
        count=1,
    )
    return text


def sync_app_docstring(text: str, version: str) -> str:
    return DOCSTRING_RE.sub(
        f'"""Live Captions — Windows desktop overlay, v{version}."""',
        text,
        count=1,
    )


def main() -> int:
    changed = []
    readme = README.read_text(encoding="utf-8")
    new_readme = sync_readme(readme, VERSION)
    if new_readme != readme:
        README.write_text(new_readme, encoding="utf-8")
        changed.append(README.name)

    app = APP_PY.read_text(encoding="utf-8")
    new_app = sync_app_docstring(app, VERSION)
    if new_app != app:
        APP_PY.write_text(new_app, encoding="utf-8")
        changed.append(APP_PY.name)

    if changed:
        print(f"Synced version {VERSION} -> {', '.join(changed)}")
    else:
        print(f"Version {VERSION} already synced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
