"""Host operating system and native build architecture."""

import os
import platform
import sys
from pathlib import Path


def is_macos():
    return sys.platform == "darwin"


def is_x64():
    """The Windows x64 beta, never an Intel/Rosetta Mac."""
    return sys.platform == "win32" and platform.machine().upper() in {"AMD64", "X86_64"}


def data_directory():
    if os.environ.get("LECTURELIVE_DATA"):
        return Path(os.environ["LECTURELIVE_DATA"]).expanduser()
    if is_macos():
        return Path.home() / "Library/Application Support/LectureLive"
    root = Path(__file__).resolve().parents[2]
    return Path(os.environ.get("LOCALAPPDATA", str(root))) / (
        "LectureLive Beta" if is_x64() else "LectureLive"
    )


def default_profile():
    return "fast" if is_x64() or is_macos() else "balanced"


def cpu_profile(profile):
    return profile if is_macos() else "fast"
