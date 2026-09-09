"""Build architecture, independent of the CPU vendor reported by emulation."""

import platform


def is_x64():
    return platform.machine().upper() in {"AMD64", "X86_64"}
