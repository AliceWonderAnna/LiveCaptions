"""Finish VoiceMeeter routing for two VLC channels + write LiveCaptions profiles.

Uses VoicemeeterRemote64.dll (Potato/Banana already running).
VLC 8080 → In 1 / VAIO loopback
VLC 8081 → AUX loopback
Both virtual strips → Hardware Out A1 (so you still hear them).
"""
from __future__ import annotations

import ctypes
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DLL = Path(r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll")

# Exact names from check_audio_devices.py on this machine
DEVICE_VLC1 = "Voicemeeter In 1 (VB-Audio Voicemeeter VAIO) [Loopback]"
DEVICE_VLC2 = "Voicemeeter AUX Input (VB-Audio Voicemeeter VAIO) [Loopback]"


def load_remote():
    if not DLL.is_file():
        raise FileNotFoundError(DLL)
    dll = ctypes.WinDLL(str(DLL))
    dll.VBVMR_Login.restype = ctypes.c_long
    dll.VBVMR_Logout.restype = ctypes.c_long
    dll.VBVMR_GetVoicemeeterType.argtypes = [ctypes.POINTER(ctypes.c_long)]
    dll.VBVMR_GetVoicemeeterType.restype = ctypes.c_long
    dll.VBVMR_SetParameterFloat.argtypes = [ctypes.c_char_p, ctypes.c_float]
    dll.VBVMR_SetParameterFloat.restype = ctypes.c_long
    dll.VBVMR_GetParameterFloat.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)]
    dll.VBVMR_GetParameterFloat.restype = ctypes.c_long
    dll.VBVMR_IsParametersDirty.restype = ctypes.c_long
    return dll


def vm_type_name(code: int) -> str:
    return {1: "Voicemeeter", 2: "Banana", 3: "Potato"}.get(code, f"unknown({code})")


def virtual_strips(vm_type: int) -> list[int]:
    # Potato: strips 0-4 hardware, 5=VAIO, 6=AUX, 7=VAIO3
    # Banana: strips 0-2 hardware, 3=VAIO, 4=AUX
    if vm_type >= 3:
        return [5, 6]
    if vm_type == 2:
        return [3, 4]
    return [2]


def set_float(dll, name: str, value: float) -> None:
    code = dll.VBVMR_SetParameterFloat(name.encode("ascii"), ctypes.c_float(value))
    if code != 0:
        raise RuntimeError(f"SetParameterFloat {name}={value} failed ({code})")


def get_float(dll, name: str) -> float:
    value = ctypes.c_float()
    code = dll.VBVMR_GetParameterFloat(name.encode("ascii"), ctypes.byref(value))
    if code != 0:
        raise RuntimeError(f"GetParameterFloat {name} failed ({code})")
    return float(value.value)


def write_profile(path: Path, device_name: str, x: int, y: int) -> None:
    base = {
        "font": "Segoe UI",
        "font_size": 30,
        "text_color": "#ffffff",
        "background_opacity": 0,
        "window_opacity": 100,
        "width": 900,
        "x": x,
        "y": y,
        "lines": 3,
        "hide_seconds": 6.0,
        "click_through": True,
        "persist_text": False,
        "accumulate_text": False,
        "source": "device",
        "device_name": device_name,
        "model": "tiny",
        "language": "en",
        "threshold": 0.006,
        "max_seconds": 6.0,
        "partial_seconds": 0.5,
        "silence_seconds": 0.25,
        "outline_enabled": True,
        "outline_width": 3,
        "outline_color": "#000000",
        "outline_opacity": 86,
        "shadow_enabled": True,
        "shadow_offset_x": 2,
        "shadow_offset_y": 2,
        "shadow_blur": 4,
        "shadow_color": "#000000",
        "shadow_opacity": 55,
    }
    path.write_text(json.dumps(base, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Schreef {path.name} -> {device_name}")


def main() -> int:
    dll = load_remote()
    login = dll.VBVMR_Login()
    if login not in (0, 1):
        print(
            f"VoiceMeeter Remote login mislukt ({login}). "
            "Start VoiceMeeter Potato/Banana en probeer opnieuw.",
            file=sys.stderr,
        )
        return 1
    try:
        # Give the client a moment after login.
        time.sleep(0.2)
        while dll.VBVMR_IsParametersDirty() == 1:
            time.sleep(0.05)

        vm_type = ctypes.c_long()
        code = dll.VBVMR_GetVoicemeeterType(ctypes.byref(vm_type))
        if code != 0:
            print(f"Kon VoiceMeeter-type niet lezen ({code})", file=sys.stderr)
            return 1
        print(f"VoiceMeeter type: {vm_type_name(vm_type.value)}")

        strips = virtual_strips(vm_type.value)
        print(f"Zet A1 aan voor virtuele strips {strips} (horen via Hardware Out A1)…")
        for strip in strips:
            set_float(dll, f"Strip[{strip}].A1", 1.0)
            # Unmute bus path if muted
            try:
                set_float(dll, f"Strip[{strip}].Mute", 0.0)
            except RuntimeError:
                pass
            a1 = get_float(dll, f"Strip[{strip}].A1")
            print(f"  Strip[{strip}].A1 = {a1}")

        # Profiles next to project + dist if present
        targets = [ROOT, ROOT / "dist" / "LiveCaptions-v0.5.0"]
        for folder in targets:
            if not folder.is_dir():
                continue
            write_profile(folder / "settings-vlc1.json", DEVICE_VLC1, x=200, y=1600)
            write_profile(folder / "settings-vlc2.json", DEVICE_VLC2, x=1100, y=1600)

        print()
        print("Klaar. Controleer in VoiceMeeter:")
        print("  1) Rechtsboven A1 = jouw speakers/headset (niet 'WDM: Voicemeeter…').")
        print("  2) Op de VAIO/In1- en AUX-strips brandt knop A1.")
        print("  3) Start start-vlc1.cmd + start-vlc2.cmd en druk Start captions.")
        return 0
    finally:
        dll.VBVMR_Logout()


if __name__ == "__main__":
    raise SystemExit(main())
