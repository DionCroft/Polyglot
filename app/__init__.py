"""LectureLive offline bilingual captions."""

from app.system.architecture import is_x64, is_macos

__version__ = "0.5.0b1" if is_macos() else "0.4.0b2" if is_x64() else "0.3.2"
