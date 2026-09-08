# Offline setup and recovery

Copy the complete `dist/LectureLive` folder to a second drive and launch it there before
travel. The bundle contains Fast and Balanced NPU speech models, independent CPU
speech recovery, translation, VAD, tokenisation assets and required libraries.

`recovery/LectureLive-Windows-ARM64-Recovery.zip` contains the app bundle, source,
documentation, pinned manifests, Python ARM64 ZIP and dependency wheels. QNN models
are already expanded inside the bundle; original model ZIPs are retained in the
project's `offline_dependencies` directory but are not duplicated in the recovery ZIP.
Microphone recordings and private transcripts are excluded.

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
