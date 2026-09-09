# Installation and reproducible builds

> **Intel/AMD Windows beta:** start with the [Windows beta guide](WINDOWS_BETA.md).
> It covers the separate launcher, Fast profile, GPU and optional experimental NPU setup.

The ready-to-run app is `dist/LectureLive/LectureLive.exe` on Windows 11 ARM64. Keep
its entire `_internal` directory. The existing Surface/Qualcomm driver supplies the
NPU device runtime; no separate QAIRT SDK was needed on the tested machine.
The build is unsigned and still requires classroom acceptance.

## First installation: double-click setup

The README included with the source download has the full beginner walkthrough. Download the
source ZIP from GitHub, use **Extract All**, open the extracted folder, and double-click
**Setup.cmd**. Keep the window open until **SETUP COMPLETE**, then use **Launch.cmd**
or the **LectureLive** Start menu shortcut. No separate Python or Git installation is needed.

Setup checks for Windows 11 ARM64, a writable extracted folder and a closed application.
It keeps a **setup.log** in the project folder. A failed shortcut does not prevent you
using Launch.cmd. Keep the project folder in place after setup.

Use a Snapdragon ARM64 PC, a microphone, an internet connection for the initial download,
and preferably at least 15 GB free disk space. First setup downloads several GB; time
depends on your connection and computer. This is an unsigned preview build. Follow your
organisation's software approval process if Windows or IT policy blocks it.

If you already have a complete ready-to-run application folder, open **LectureLive.exe**
inside that folder. Keep **_internal** beside it. The **READ_ME_FIRST.txt** file covers
that distribution. Source ZIPs and ready-to-run copies are different downloads.

## Repair or interrupted setup

Close LectureLive, then run **Setup.cmd** again from the same folder. It reuses verified
files and resumes downloads where the server supports it. Read **setup.log** if it fails.
If you moved the folder, rerunning setup also refreshes the Start menu shortcut.
Settings and text transcripts remain under `%LOCALAPPDATA%\LectureLive`.

## Advanced setup commands

For scripts or development, run this in the extracted project directory while internet access is available:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -Build
```

This downloads the pinned CPython ARM64 ZIP, verifies it before extraction, fetches
exact dependency wheels from `dependencies.lock.json`, installs them with pip using
`--no-index`, downloads/verifies `assets.lock.json`, and builds the native bundle.
There is no runtime network fallback. The setup script does not change system PATH.

Each model URL includes a fixed release or repository revision. Downloads use temporary
files and resume when the server supports ranges; SHA-256 and byte counts must match
before a file is installed. Corrupt extracted QNN files are repaired from verified
archives. Extraction rejects paths outside the target folder.

To verify without downloading or changing models:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -VerifyOnly
```

Run setup normally again to repair missing/corrupt assets. Use `-Offline` when all
required artifacts are cached. Offline failures are reported rather than fetching data.
The first offline installation was verified in a separate directory; see
`evidence/fresh-setup-verification.json`. A real pinned HTTPS download and bootstrap
URL were checked separately in `evidence/online-setup-check.json`.

## Development checks

```powershell
.\runtime\python.exe -m pytest -q
.\runtime\python.exe scripts\setup_assets.py --fixtures
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\prepare_fixtures.ps1
.\runtime\python.exe scripts\verify_workflow.py
.\runtime\python.exe scripts\classroom_check.py
.\runtime\python.exe scripts\stress_test.py --seconds 7200 --noise-snr 20
```

The optional public speech fixture is pinned in `fixtures.lock.json`; other speech
fixtures are synthesised locally using an installed Windows voice. Voice-dependent
results vary by machine. Developer fixtures are excluded from Git and recovery ZIPs.
Normal app use requires none of these test commands.

Use `scripts/build.ps1` for subsequent builds and `scripts/install-shortcut.ps1` for
an optional Start Menu launcher. Neither enables startup-at-login nor audio recording.
Package versions remain pinned in `requirements-lock.txt`; QNN and all runtime binaries
are native ARM64. The existing x64 Python installation is not modified.
