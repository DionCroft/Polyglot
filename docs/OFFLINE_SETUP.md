# Offline setup and recovery

Copy the entire `dist/LectureLive` directory to a second drive. Launch the executable
from that copy once before travel. The build includes Fast and Balanced NPU models,
the independent CPU speech model, translation, VAD and tokenization assets.

The recovery directory retains:
- Native CPython 3.11.9 embeddable ARM64 ZIP.
- Pinned ARM64/pure-Python dependency wheels.
- Original Qualcomm model ZIPs.
- `SHA256SUMS.json` for downloaded dependencies/models and the deployable files.
- The app bundle and these instructions in the generated recovery ZIP.

Run `runtime/python.exe scripts/checksums.py --verify` to detect damaged files.
The development runtime can reinstall dependencies with
`runtime/python.exe -m pip install --no-index --find-links offline_dependencies/wheels -r requirements-lock.txt`.
A packaged application already contains its dependencies and needs no pip operation.

The Python `_pth` file explicitly includes only the private runtime and project.
There are no model downloads at ordinary startup. Setup scripts are separate tools
and may use networking only when preparing a new installation.

Qualcomm QNN libraries were supplied by the official onnxruntime-qnn wheel. The
working system driver is supplied by Windows/Surface; it is not copied into the
recovery ZIP. Obtain any required device driver from the Surface/Qualcomm vendor
before travel. Do not redistribute a separately acquired proprietary SDK without
checking its own terms. The archive is for this installation's recovery; review all
third-party notices before wider redistribution.

If the NPU cannot initialize, the app reports local CPU recovery. If translation
cannot initialize, English continues and a warning is shown. Never use an online
translator as a hidden replacement.

The generated recovery ZIP is in `recovery/LectureLive-Windows-ARM64-Recovery.zip`.
Extract it to a local folder. Launch `dist/LectureLive/LectureLive.exe` directly.
For development recovery, run `scripts/restore-runtime.ps1` using only the included
Python ZIP and wheels. Then `runtime/python.exe scripts/checksums.py --verify --recovery`
verifies the original extracted files. No network is needed for either path.
