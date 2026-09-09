"""LectureLive offline bilingual captions."""

from app.system.architecture import is_x64

__version__ = "0.4.0b1" if is_x64() else "0.3.1"
