"""Select native window/shortcut integration without importing another OS backend."""

from app.system.architecture import is_macos

if is_macos():
    from app.system.macos import Hotkeys, overlay_input, parse_shortcut
else:
    from app.system.windows import Hotkeys, overlay_input
    from app.system.shortcuts import parse_shortcut
