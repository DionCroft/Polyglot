# Offline setup and recovery

> **Intel/AMD Windows beta:** start with the [Windows beta guide](WINDOWS_BETA.md).
> It covers the separate launcher, Fast profile, GPU and optional experimental NPU setup.

Copy the complete `dist/LectureLive` folder to a second drive and launch it there before
travel. The bundle contains Fast and Balanced NPU speech models, independent CPU
speech recovery, both translation directions, VAD, tokenisation assets and required libraries.
For conversation support, use a 0.6.0b1-or-newer bundle, including `models/translation/opus-zh-en`.
Automatic switching requires 0.7.0b1 or newer. After copying, test English, Mandarin and Auto offline. [Conversation walkthrough](CONVERSATIONS.md).

## Portable conversation ZIPs

The maintainer builds these complete app archives in `recovery`:

- `LectureLive-Windows-ARM64-Beta-0.7.0b1.zip`: Snapdragon PCs, about 1.53 GB.
  Extract it and open `LectureLive/LectureLive.exe`.
- `LectureLive-Windows-x64-Beta-0.7.0b1.zip`: Intel/AMD PCs, about 748 MB.
  Extract it and open `LectureLive-x64-Beta/LectureLive-x64-Beta.exe`.

Keep the whole extracted folder, including `_internal`. The matching `.zip.sha256`
checks the download; `SHA256.json` inside lists the hashes of all included app files.
These portable archives contain the app and models, not a development runtime.
Build them after the appropriate `scripts/build.ps1 -Architecture ARM64` or `x64` run:
`runtime/python.exe -m scripts.package_beta --architecture ARM64` (or `x64`).
See [verification](evidence/auto-language-0.7.md) for the exact tested build and sizes.

## Optional developer recovery archive

A separately generated `recovery/LectureLive-Windows-ARM64-Recovery.zip` contains the app bundle, source,
documentation, pinned manifests, Python ARM64 ZIP and dependency wheels. QNN models
are already expanded inside the bundle; original model ZIPs are retained in the
project's `offline_dependencies` directory but are not duplicated in the recovery ZIP.
Microphone recordings and private transcripts are excluded.
An older recovery archive retains its original app version; it does not acquire conversation
support when source files are updated. Rebuild it with `scripts/package_recovery.py` after
building the current app if you need this larger developer archive.

Extract the archive and launch `dist/LectureLive/LectureLive.exe`. No setup, account
or network is needed for normal use. For development recovery run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\restore-runtime.ps1
.\runtime\python.exe scripts\checksums.py --verify --recovery
```

Restoration copies bundled models into the development model folder if needed, then
uses the pinned offline setup workflow. All wheels are verified and installed with
`--no-index`. `RECOVERY_SHA256.json` verifies original extracted payload files.
The adjacent `.zip.sha256` file verifies the archive before extraction.

For project model repair use `scripts/setup.ps1 -Offline` if cached archives exist,
or run it online before travel to fetch missing pinned assets. Setup networking is
separate from the ordinary app. A corrupted model cannot silently trigger a runtime
download or cloud inference request.

The Qualcomm device driver belongs to the Windows/Surface installation and is not
redistributed in the archive. Prepare vendor-supported device drivers before travel.
Third-party notices are retained in `docs/licenses`; review terms before redistributing.

NPU errors retry locally on CPU. Missing translation allows English to continue with
an explicit warning. Export errors leave captions running; a journal can be recovered
through Diagnostics into a separate new folder.
