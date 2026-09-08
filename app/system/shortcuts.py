"""Parse a deliberately small, predictable set of Windows global shortcuts."""


def parse_shortcut(text):
    parts = [p.strip().upper() for p in text.split("+")]
    if len(parts) < 2 or len(set(parts)) != len(parts):
        raise ValueError("Use Ctrl/Alt/Shift plus a letter, digit, Space or F1–F12")
    modifiers = {"CTRL": 2, "ALT": 1, "SHIFT": 4}
    if any(p not in modifiers for p in parts[:-1]):
        raise ValueError("Supported modifiers are Ctrl, Alt and Shift")
    if not any(p in {"CTRL", "ALT"} for p in parts[:-1]):
        raise ValueError("Include Ctrl or Alt to avoid intercepting ordinary typing")
    key = parts[-1]
    if len(key) == 1 and key.isascii() and key.isalnum():
        code = ord(key)
    elif key == "SPACE":
        code = 0x20
    elif key.startswith("F") and key[1:].isdigit() and 1 <= int(key[1:]) <= 12:
        code = 0x70 + int(key[1:]) - 1
    else:
        raise ValueError("Use a letter, digit, Space or F1–F12")
    flags = 0x4000
    for part in parts[:-1]:
        flags |= modifiers[part]
    return flags, code
