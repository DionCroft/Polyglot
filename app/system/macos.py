"""Cocoa overlays and Carbon global hotkeys; no key logging or Accessibility access."""

import ctypes
import logging

_KEYS = dict(
    zip("ASDFHGZXCVBQWERYT", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17])
)
_KEYS.update(dict(zip("1234659780", [18, 19, 20, 21, 22, 23, 25, 26, 28, 29])))
_KEYS.update(
    dict(zip("OIULJKNP M".replace(" ", ""), [31, 34, 32, 37, 38, 40, 45, 35, 46]))
)
_KEYS["SPACE"] = 49
_KEYS.update(
    {
        f"F{i}": key
        for i, key in enumerate(
            [122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111], 1
        )
    }
)


def parse_shortcut(text):
    aliases = {"COMMAND": "CMD", "META": "CMD", "OPTION": "ALT", "CONTROL": "CTRL"}
    parts = [aliases.get(p.strip().upper(), p.strip().upper()) for p in text.split("+")]
    modifiers = {"CMD": 256, "SHIFT": 512, "ALT": 2048, "CTRL": 4096}
    if (
        len(parts) < 2
        or len(set(parts)) != len(parts)
        or any(p not in modifiers for p in parts[:-1])
    ):
        raise ValueError(
            "Use Cmd/Control/Option/Shift plus a letter, digit, Space or F1–F12"
        )
    if (
        not any(p in {"CMD", "CTRL", "ALT"} for p in parts[:-1])
        or parts[-1] not in _KEYS
    ):
        raise ValueError("Include Cmd, Control or Option with a supported key")
    return sum(modifiers[p] for p in parts[:-1]), _KEYS[parts[-1]]


def overlay_input(view_id, locked):
    import objc
    import AppKit

    view = objc.objc_object(c_void_p=ctypes.c_void_p(view_id))
    window = view.window()
    if window is None:
        return
    window.setIgnoresMouseEvents_(bool(locked))
    window.setHidesOnDeactivate_(False)
    window.setLevel_(AppKit.NSFloatingWindowLevel)
    window.setCollectionBehavior_(
        AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
        | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
    )


class _HotKeyID(ctypes.Structure):
    _fields_ = [("signature", ctypes.c_uint32), ("identifier", ctypes.c_uint32)]


class _EventType(ctypes.Structure):
    _fields_ = [("event_class", ctypes.c_uint32), ("kind", ctypes.c_uint32)]


class Hotkeys:
    def __init__(
        self, app, on_lock, on_pause, lock="Ctrl+Alt+C", pause="Ctrl+Alt+Space"
    ):
        self.errors = []
        self.registered = []
        self.handler = ctypes.c_void_p()
        parsed = [parse_shortcut(lock), parse_shortcut(pause)]
        if parsed[0] == parsed[1]:
            raise ValueError("Lock and pause shortcuts must differ")
        self.actions = {4101: on_lock, 4102: on_pause}
        self.carbon = ctypes.CDLL("/System/Library/Frameworks/Carbon.framework/Carbon")
        callback_type = ctypes.CFUNCTYPE(
            ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )
        c = self.carbon
        c.GetApplicationEventTarget.restype = ctypes.c_void_p
        c.InstallEventHandler.argtypes = [
            ctypes.c_void_p,
            callback_type,
            ctypes.c_uint32,
            ctypes.POINTER(_EventType),
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        c.InstallEventHandler.restype = ctypes.c_int32
        c.GetEventParameter.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        c.GetEventParameter.restype = ctypes.c_int32
        c.RegisterEventHotKey.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            _HotKeyID,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        c.RegisterEventHotKey.restype = ctypes.c_int32
        c.UnregisterEventHotKey.argtypes = [ctypes.c_void_p]
        c.RemoveEventHandler.argtypes = [ctypes.c_void_p]

        def pressed(next_handler, event, context):
            identifier = _HotKeyID()
            status = c.GetEventParameter(
                event,
                0x2D2D2D2D,
                0x686B6964,
                None,
                ctypes.sizeof(identifier),
                None,
                ctypes.byref(identifier),
            )
            if (
                status == 0
                and identifier.signature == 0x4C65634C
                and identifier.identifier in self.actions
            ):
                try:
                    self.actions[identifier.identifier]()
                except Exception:
                    logging.exception("Global shortcut action failed")
                return 0
            return -9874

        self.callback = callback_type(pressed)
        event_type = _EventType(0x6B657962, 6)
        target = c.GetApplicationEventTarget()
        if c.InstallEventHandler(
            target,
            self.callback,
            1,
            ctypes.byref(event_type),
            None,
            ctypes.byref(self.handler),
        ):
            self.errors = [lock, pause]
            return
        for identifier, text, (modifiers, key) in zip(
            (4101, 4102), (lock, pause), parsed
        ):
            ref = ctypes.c_void_p()
            if c.RegisterEventHotKey(
                key,
                modifiers,
                _HotKeyID(0x4C65634C, identifier),
                target,
                0,
                ctypes.byref(ref),
            ):
                self.errors.append(text)
            else:
                self.registered.append(ref)

    def close(self):
        for ref in self.registered:
            self.carbon.UnregisterEventHotKey(ref)
        self.registered = []
        if self.handler.value:
            self.carbon.RemoveEventHandler(self.handler)
            self.handler = ctypes.c_void_p()
