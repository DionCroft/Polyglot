"""Native Windows no-activation/click-through and global hotkeys."""

import ctypes, sys
from ctypes import wintypes
from PySide6.QtCore import QAbstractNativeEventFilter

if sys.platform == "win32":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.RegisterHotKey.argtypes = [
        wintypes.HWND,
        ctypes.c_int,
        wintypes.UINT,
        wintypes.UINT,
    ]
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]


def overlay_input(hwnd, locked):
    if sys.platform != "win32":
        return
    style = (
        user32.GetWindowLongPtrW(hwnd, -20) | 0x08000000 | 0x00080000
    )  # NOACTIVATE | LAYERED
    style = style | 0x20 if locked else style & ~0x20
    ctypes.set_last_error(0)
    result = user32.SetWindowLongPtrW(hwnd, -20, style)
    if not result and ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    user32.SetWindowPos(hwnd, wintypes.HWND(-1), 0, 0, 0, 0, 0x1 | 0x2 | 0x10 | 0x20)


class Hotkeys(QAbstractNativeEventFilter):
    def __init__(self, app, on_lock, on_pause):
        super().__init__()
        self.app = app
        self.actions = {4101: on_lock, 4102: on_pause}
        self.registered = []
        self.errors = []
        if sys.platform == "win32":
            for identifier, key in [(4101, 0x43), (4102, 0x20)]:
                if user32.RegisterHotKey(None, identifier, 0x1 | 0x2 | 0x4000, key):
                    self.registered.append(identifier)
                else:
                    self.errors.append(
                        "Ctrl+Alt+C" if identifier == 4101 else "Ctrl+Alt+Space"
                    )
            app.installNativeEventFilter(self)

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x312 and msg.wParam in self.actions:
            self.actions[msg.wParam]()
            return True, 0
        return False, 0

    def close(self):
        for identifier in self.registered:
            user32.UnregisterHotKey(None, identifier)
        self.registered = []
        self.app.removeNativeEventFilter(self)
