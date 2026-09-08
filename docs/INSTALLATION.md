# Installation

## Current native build

Use `dist/LectureLive/LectureLive.exe` on Windows 11 ARM64. Keep its `_internal`
directory intact: it contains Qt, Python, native inference libraries and models.
The Surface's installed Qualcomm driver is used. No separately installed QAIRT SDK
was needed for the successful NPU test. A local CPU model is bundled for recovery.

The executable is a development build and is not code-signed. Complete the acceptance
checklist before teaching. Do not describe it as production validated yet.

A Start Menu shortcut can be created by `scripts/install-shortcut.ps1` after the
bundle is placed in its final location. It never enables startup-at-login or recording.

## Build from this repository

Run `scripts/build.ps1` with the bundled runtime. Python 3.11.9 ARM64, PySide6 6.11.2,
ONNX Runtime 1.29.0, QNN plugin 2.5.0 and PyInstaller 6.22.2 are pinned in
`requirements-lock.txt`. PyInstaller 6.22.2 has a `win_arm64` wheel and ARM64 bootloader;
this build does not package an x64 emulator executable.

The project-local CPython embeddable distribution is an application runtime with a
private site-packages directory, not a system Python replacement. It does not modify
PATH or the existing x64 Python installation. Its official redistribution license is
retained in `runtime/LICENSE.txt` and the recovery archive.
